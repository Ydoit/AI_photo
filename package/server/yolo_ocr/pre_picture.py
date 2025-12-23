import cv2
import numpy as np


def red_mask_v2(roi_bgr: np.ndarray,
                red_s_min=20, red_v_min=40,
                kernel_size=3, dilate_iter=1) -> np.ndarray:
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0,   red_s_min, red_v_min], np.uint8)
    upper1 = np.array([18,  255,       255],       np.uint8)
    lower2 = np.array([160, red_s_min, red_v_min], np.uint8)
    upper2 = np.array([179, 255,       255],       np.uint8)
    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=1)
    mask = cv2.dilate(mask, k, iterations=dilate_iter)
    return mask


def remove_red_order_id_v3(
    img_bgr: np.ndarray,
    roi_top_ratio: float = 0.20,        # 只看顶部：0.12~0.25 之间调
    keep_left_ratio: float = 0.75,      # 只保留左侧区域连通域
    # 红度阈值（会在ROI里自适应Otsu）
    redness_floor: int = 8,             # 最低红度门槛，防止Otsu过低
    # 色度约束（过滤灰/白）
    chroma_min: int = 10,               # 10~18可调，越大越“严格”
    # 亮白排除
    white_v_min: int = 230,
    white_s_max: int = 35,
    # 形态学
    k_open: int = 3,
    k_close: int = 5,
    dilate_iter: int = 1,
    # 连通域
    min_area: int = 25,
    max_area: int = 20000,
    # 修复
    inpaint_radius: int = 3,
    method: str = "telea",
):
    H, W = img_bgr.shape[:2]
    y_end = max(1, int(H * roi_top_ratio))
    x_end_keep = int(W * keep_left_ratio)

    roi = img_bgr[:y_end, :]
    b, g, r = cv2.split(roi)

    # 1) 红度 score：R - max(G,B)
    score = (r.astype(np.int16) - np.maximum(g, b).astype(np.int16))
    score_u8 = np.clip(score + 128, 0, 255).astype(np.uint8)  # 便于阈值

    # 2) 在 ROI 内用 Otsu 自适应，但加一个下限避免过松
    # Otsu 输出阈值在 0~255，映射回 score 需要 -128
    otsu_thr, _ = cv2.threshold(score_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thr_score = max(int(otsu_thr) - 128, redness_floor)
    mask_red = (score >= thr_score).astype(np.uint8) * 255

    # 3) 色度约束：过滤灰白（关键！）
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    a = lab[:, :, 1].astype(np.int16) - 128
    bb = lab[:, :, 2].astype(np.int16) - 128
    chroma = np.sqrt(a * a + bb * bb)
    mask_chroma = (chroma >= chroma_min).astype(np.uint8) * 255

    # 4) 亮白区域剔除（反光/发白误检经常在这里）
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    Hh, Ss, Vv = cv2.split(hsv)
    white_like = ((Vv >= white_v_min) & (Ss <= white_s_max)).astype(np.uint8) * 255

    # 5) 融合：红度 & 色度 & 非白亮
    mask = cv2.bitwise_and(mask_red, mask_chroma)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(white_like))

    # 6) 形态学：去噪 + 补全笔画
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_open, k_open))
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_close, k_close))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k1, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k2, iterations=1)
    mask = cv2.dilate(mask, k2, iterations=dilate_iter)

    # 7) 连通域筛选：只保留顶部且偏左的“订单号块”
    num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    filtered = np.zeros_like(mask)

    for i in range(1, num):
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]

        if area < min_area or area > max_area:
            continue
        # 顶部区域 + 左侧区域（避免把右上角、其他区域抓进来）
        if cx > x_end_keep:
            continue
        # 订单号通常非常靠上：可以更严格一点
        if cy > y_end * 0.70:
            continue
        # 排除极端扁长噪声（可按样本调）
        if h < 6 or w < 10:
            continue

        filtered[labels == i] = 255

    mask = filtered

    # 8) 回填到全图 mask，只修复顶部 ROI
    mask_full = np.zeros((H, W), dtype=np.uint8)
    mask_full[:y_end, :] = mask

    inpaint_flag = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
    cleaned = cv2.inpaint(img_bgr, mask_full, inpaintRadius=inpaint_radius, flags=inpaint_flag)

    return cleaned, mask_full

def remove_red_order_id_fusion(
    img_bgr: np.ndarray,
    roi_top_ratio: float = 0.22,
    keep_left_ratio: float = 0.80,

    # v2 参数（偏“召回”）
    v2_red_s_min: int = 15,
    v2_red_v_min: int = 30,

    # v3 参数（偏“精度”）
    v3_kwargs: dict | None = None,

    # 连通域过滤
    min_area: int = 25,
    max_area: int = 40000,

    # inpaint
    inpaint_radius: int = 3,
    method: str = "telea",
):
    H, W = img_bgr.shape[:2]
    y_end = max(1, int(H * roi_top_ratio))
    x_keep = int(W * keep_left_ratio)

    roi = img_bgr[:y_end, :]

    # --- mask_v2（召回强）---
    mask2 = red_mask_v2(
        roi,
        red_s_min=v2_red_s_min,
        red_v_min=v2_red_v_min,
        kernel_size=3,
        dilate_iter=1
    )

    # --- mask_v3（误检抑制强）---
    if v3_kwargs is None:
        v3_kwargs = {}
    # 复用你已有的 v3：它会返回 full mask，我们只截 ROI
    _, mask3_full = remove_red_order_id_v3(img_bgr, roi_top_ratio=roi_top_ratio, **v3_kwargs)
    mask3 = mask3_full[:y_end, :]

    # --- 融合：OR ---
    mask = cv2.bitwise_or(mask2, mask3)

    # --- 再做一次“只保留订单号区域”的过滤（顶部 + 左侧 + 连通域）---
    num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    filtered = np.zeros_like(mask)
    for i in range(1, num):
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]

        if area < min_area or area > max_area:
            continue
        if cx > x_keep:
            continue
        # 订单号一般更靠上：你可以把 0.75 调到 0.60~0.85
        if cy > y_end * 0.75:
            continue
        if h < 6 or w < 6:
            continue

        filtered[labels == i] = 255

    mask = filtered

    # --- 回填到全图mask并修复 ---
    mask_full = np.zeros((H, W), dtype=np.uint8)
    mask_full[:y_end, :] = mask

    inpaint_flag = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
    cleaned = cv2.inpaint(img_bgr, mask_full, inpaintRadius=inpaint_radius, flags=inpaint_flag)

    return cleaned, mask_full

def refine_mask_to_orderid_band(
    mask_roi: np.ndarray,
    band_half: int = 26,           # 18~40：图片越大可越大
    min_row_sum: int = 60,         # 行内白点数阈值：太小会不稳定
    left_keep_ratio: float = 0.90, # 订单号通常靠左，防止右上误检
    min_area: int = 20,
    max_area: int = 80000,
) -> np.ndarray:
    h, w = mask_roi.shape[:2]

    row_sum = (mask_roi > 0).sum(axis=1)
    y_peak = int(np.argmax(row_sum))

    # 如果候选红像素过少，直接返回原 mask（避免“瞎 refine”）
    if row_sum[y_peak] < min_row_sum:
        return mask_roi

    y0 = max(0, y_peak - band_half)
    y1 = min(h, y_peak + band_half + 1)

    band = np.zeros_like(mask_roi)
    band[y0:y1, :int(w * left_keep_ratio)] = 255

    mask_band = cv2.bitwise_and(mask_roi, band)

    # 连通域过滤，去掉大块噪声
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask_band, connectivity=8)
    filtered = np.zeros_like(mask_band)

    for i in range(1, num):
        x, y, ww, hh, area = stats[i]
        if area < min_area or area > max_area:
            continue
        if hh < 6 or ww < 3:
            continue
        filtered[labels == i] = 255

    return filtered

def remove_red_order_id(
    img_bgr: np.ndarray,
    mode: str = "fusion",          # "v2" | "v3" | "fusion"
    roi_top_ratio: float = 0.15,
    keep_left_ratio: float = 0.80,

    # v2
    v2_red_s_min: int = 15,
    v2_red_v_min: int = 30,

    # v3
    v3_kwargs: dict | None = None,

    # refine(强烈建议开启)
    do_refine_band: bool = True,
    band_half: int = 26,
    min_row_sum: int = 60,
    left_keep_ratio_refine: float = 0.90,

    # inpaint
    inpaint_radius: int = 3,
    method: str = "telea",
):
    H, W = img_bgr.shape[:2]
    y_end = max(1, int(H * roi_top_ratio))

    # 1) 先拿候选 mask_full
    if mode.lower() == "v2":
        roi = img_bgr[:y_end, :]
        mask_roi = red_mask_v2(
            roi,
            red_s_min=v2_red_s_min,
            red_v_min=v2_red_v_min,
            kernel_size=3,
            dilate_iter=1,
        )
        mask_full = np.zeros((H, W), dtype=np.uint8)
        mask_full[:y_end, :] = mask_roi

    elif mode.lower() == "v3":
        if v3_kwargs is None:
            v3_kwargs = {}
        # 复用你现有 v3，取它的 mask_full
        _, mask_full = remove_red_order_id_v3(
            img_bgr,
            roi_top_ratio=roi_top_ratio,
            keep_left_ratio=keep_left_ratio,
            **v3_kwargs
        )

    else:  # fusion
        if v3_kwargs is None:
            v3_kwargs = {}
        _, mask_full = remove_red_order_id_fusion(
            img_bgr,
            roi_top_ratio=roi_top_ratio,
            keep_left_ratio=keep_left_ratio,
            v2_red_s_min=v2_red_s_min,
            v2_red_v_min=v2_red_v_min,
            v3_kwargs=v3_kwargs,
            inpaint_radius=inpaint_radius,
            method=method,
        )

    # 2) refine：把 mask 压到订单号所在的横带，防止误抹出发站/车次
    if do_refine_band:
        mask_roi = mask_full[:y_end, :]
        mask_roi = refine_mask_to_orderid_band(
            mask_roi,
            band_half=band_half,
            min_row_sum=min_row_sum,
            left_keep_ratio=left_keep_ratio_refine
        )
        mask_full2 = np.zeros((H, W), dtype=np.uint8)
        mask_full2[:y_end, :] = mask_roi
    else:
        mask_full2 = mask_full

    # 3) 最终统一 inpaint（以 refine 后的 mask 为准）
    inpaint_flag = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
    cleaned = cv2.inpaint(img_bgr, mask_full2, inpaintRadius=inpaint_radius, flags=inpaint_flag)

    return cleaned, mask_full2


if __name__ == "__main__":
    img = cv2.imread("data/ticket_single/ticket_0120.jpg")
    if img is None:
        raise FileNotFoundError("读不到图片")

    cleaned, mask = remove_red_order_id(
        img,
        mode="fusion",          # 推荐：fusion
        roi_top_ratio=0.15,     # 建议 0.12~0.20
        keep_left_ratio=0.80,

        v2_red_s_min=15,
        v2_red_v_min=30,
        v3_kwargs=dict(
            chroma_min=10,
            dilate_iter=2,      # 不要太大，防止整片扩张
        ),

        do_refine_band=True,    # 建议开启
        band_half=26,
        min_row_sum=60,
        left_keep_ratio_refine=0.90,

        inpaint_radius=3,
        method="telea"
    )

    cv2.imwrite("data/ticket_single/ticket_0120_clean.jpg", cleaned)
    # cv2.imwrite("data/ticket_single/ticket_0100_mask.png", mask)