import re
import json


def extract_text(json_path):
    """
    从OCR保存的JSON文件中提取所有识别文本
    """
    texts = []
    polys = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rec_texts = data.get("rec_texts", [])
        rec_polys = data.get("rec_polys", [])

        # 同时遍历，只保留非空文本及其对应的 poly
        for txt, poly in zip(rec_texts, rec_polys):
            stripped = txt.strip()
            if stripped:  # 非空才保留
                texts.append(stripped)
                polys.append(poly)

    except Exception as e:
        print(f"读取JSON文件失败: {e}")
    return texts, polys


def _fix_ocr_text(s):
    return s.replace('I', '1').replace('l', '1').replace('O', '0').replace('o', '0')


_STATION_INTERFERENCE = {"上铺", "中铺", "下铺", "限乘", "当日", "当次", "车", "号", "开", "元", "报销", "使用"}


def _normalize_station_name(name: str) -> str:
    return (name or "").strip()


def _is_valid_station_name(name: str) -> bool:
    if not name:
        return False
    name = name.strip()
    if not (2 <= len(name) <= 8):
        return False
    if not re.fullmatch(r'[\u4e00-\u9fa5]+', name):
        return False
    if any(w in name for w in _STATION_INTERFERENCE):
        return False
    return True


def _poly_center(poly):
    if not poly or len(poly) < 4:
        return 0.0, 0.0
    cx = sum(p[0] for p in poly) / 4
    cy = sum(p[1] for p in poly) / 4
    return cx, cy


def _pick_left_right_station_names(station_with_y):
    """
    station_with_y: List[(name, cx, cy)]
    返回同一带内按 x 左->右的两个站名（去重）。
    """
    row_sorted = sorted(station_with_y, key=lambda x: x[1])
    uniq = []
    seen = set()
    for n, cx, cy in row_sorted:
        if n not in seen and _is_valid_station_name(n):
            uniq.append((n, cx, cy))
            seen.add(n)
        if len(uniq) >= 2:
            break
    if len(uniq) >= 2:
        return uniq[0][0], uniq[1][0]
    if len(uniq) == 1:
        return uniq[0][0], ""
    return "", ""


def _pick_dep_arr_from_station_candidates(station_with_y):
    """
    station_with_y: List[(name, cx, cy)]
    策略：
    1) 先按 y 聚类（阈值略放宽），优先找“同一行>=2个不同站名”的行；
    2) 若找不到，则回退到“整体最靠上的两个不同站名”（按 y,x）。
    """
    if not station_with_y:
        return "", ""

    cleaned = []
    for name, cx, cy in station_with_y:
        name = _normalize_station_name(name)
        if _is_valid_station_name(name):
            cleaned.append((name, cx, cy))
    if not cleaned:
        return "", ""

    cleaned.sort(key=lambda x: (x[2], x[1]))  # y,x

    y_threshold = 45  # 比你原先 top_row 的 30 稍放宽
    rows = []
    for item in cleaned:
        if not rows:
            rows.append([item])
        else:
            if abs(item[2] - rows[-1][0][2]) <= y_threshold:
                rows[-1].append(item)
            else:
                rows.append([item])

    # 找到最靠上的“同一行出现2个不同站名”的行
    for row in rows:
        row_sorted = sorted(row, key=lambda x: x[1])
        uniq = []
        seen = set()
        for n, cx, cy in row_sorted:
            if n not in seen:
                uniq.append((n, cx, cy))
                seen.add(n)
        if len(uniq) >= 2:
            return uniq[0][0], uniq[1][0]

    # 回退：选“水平距离最大”的两站（抗倾斜/分行）
    # 先去重（同名站可能出现多次）
    uniq = []
    seen = set()
    for n, cx, cy in cleaned:
        if n not in seen:
            uniq.append((n, cx, cy))
            seen.add(n)

    if len(uniq) >= 2:
        best_pair = None
        best_dx = -1

        # 直接全量两两组合；站名候选一般很少，O(n^2)足够
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                dx = abs(uniq[i][1] - uniq[j][1])
                if dx > best_dx:
                    best_dx = dx
                    best_pair = (uniq[i], uniq[j])

        (n1, x1, _), (n2, x2, _) = best_pair
        if x1 <= x2:
            return n1, n2
        else:
            return n2, n1

    if len(uniq) == 1:
        return uniq[0][0], ""
    return "", ""



def _post_fix_arrival_station(ticket_info: dict, ocr_texts: list):
    """
    仅做 arrival_station 的缺失回填，不触碰 berth_type 等字段。
    兼容两类站名来源：
    1) 'XX站' 文本块
    2) 纯站名块（如“兰考南”“郑州东”），仅接受以 东/西/南/北 结尾以降低误判
    """
    if ticket_info.get("arrival_station"):
        return ticket_info

    stations = []
    seen = set()

    for t in ocr_texts:
        # 1) 'XX站' 模式
        for m in re.finditer(r'([\u4e00-\u9fa5]{2,8})站', t):
            nm = _normalize_station_name(m.group(1))
            if _is_valid_station_name(nm) and nm not in seen:
                stations.append(nm)
                seen.add(nm)

        # 2) 纯站名块模式（末尾东/西/南/北）
        stripped = _normalize_station_name(t)
        if _is_valid_station_name(stripped) and stripped.endswith(("东", "西", "南", "北")) and stripped not in seen:
            stations.append(stripped)
            seen.add(stripped)

    dep = ticket_info.get("departure_station", "")
    if dep:
        for s in stations:
            if s != dep:
                ticket_info["arrival_station"] = s
                break
    else:
        if len(stations) >= 2:
            ticket_info["departure_station"] = stations[0]
            ticket_info["arrival_station"] = stations[1]

    # 基础一致性保护
    if ticket_info.get("departure_station") and ticket_info.get("arrival_station"):
        if ticket_info["departure_station"] == ticket_info["arrival_station"]:
            ticket_info["arrival_station"] = ""

    return ticket_info


# 新增：票面固定提示/字段标签等（这些不可能是姓名）
_NAME_BLOCKLIST_SUBSTR = {
    "事由", "动车组", "中国铁路", "祝您旅途愉快",
    "仅供报销", "报销", "凭证", "遗失", "不补", "退票", "改签",
    "检票", "限乘", "当日", "当次", "中途下车失效",
    "买票请到", "请到", "12306", "95306",
    "车站", "售", "出发", "到达"
}


def _is_name_candidate_text(txt: str, ticket_info: dict, station_name_set: set) -> bool:
    """
    判断一个纯中文文本块是否可能是姓名（仅用于兜底规则）。
    设计目标：宁可漏，不可错（避免把票面提示词当姓名）。
    """
    if not txt:
        return False
    s = txt.strip()
    if not re.fullmatch(r'[\u4e00-\u9fa5]{2,6}', s):
        return False

    # 1) 站名互斥：只要这个块被识别/候选为站名，就绝不作为姓名
    if s in (station_name_set or set()):
        return False

    # 2) 票面固定提示/字段标签：包含这些子串就排除
    for bad in _NAME_BLOCKLIST_SUBSTR:
        if bad in s:
            return False

    # 4) 常见席别/无座等
    if s in {"无座", "站票", "一等座", "二等座", "商务座", "特等座", "硬座", "软座", "硬卧", "软卧"}:
        return False

    return True


def _is_id_like_text(t: str) -> bool:
    """身份证/证件号碎片/星号掩码块的粗判"""
    if not t:
        return False
    s = t.strip()
    # 含星号（掩码）
    if "*" in s and re.search(r'\d', s):
        return True
    # 纯数字且长度较长（身份证拆块、票号等）
    if s.isdigit() and len(s) >= 6:
        return True
    return False


def _is_low_confidence_name(name: str, station_name_set: set) -> bool:
    """判断当前 name 是否明显不可信，若不可信允许被纠正覆盖"""
    if not name:
        return True
    n = name.strip()
    if "站" in n:
        return True
    if n in (station_name_set or set()):
        return True
    for bad in _NAME_BLOCKLIST_SUBSTR:
        if bad in n:
            return True
    # 常见席别/提示词也视为低置信
    if n in {"无座", "站票", "一等座", "二等座", "商务座", "特等座", "硬座", "软座", "硬卧", "软卧"}:
        return True
    return False


def _extract_tail_name_from_masked_id_block(txt: str) -> str:
    """
    从类似 '****8035周帅康' / '4114****8035周帅康' 这种块中提取尾部中文姓名。
    只提取 2~6 个中文字符，并排除包含'站'的情况。
    """
    if not txt:
        return ""
    s = txt.strip()

    # 关键：前面是若干 * 或数字（长度>=4），后面紧跟 2~6 个中文
    m = re.search(r'[\d\*]{4,}([\u4e00-\u9fa5]{2,6})$', s)
    if not m:
        return ""

    name = m.group(1).strip()
    if "站" in name:  # 防止误把“XX站”之类提成姓名
        return ""
    return name


def _select_name_by_proximity(ocr_texts: list, station_name_set: set, ticket_info: dict) -> str:
    """
    额外建议功能：
    若存在证件号碎片/星号掩码块，则从其附近挑选最像姓名的纯中文块。
    """
    if not ocr_texts:
        return ""

    id_indices = [i for i, t in enumerate(ocr_texts) if _is_id_like_text(t)]
    if not id_indices:
        return ""

    candidates = []
    for i, t in enumerate(ocr_texts):
        # 1) 纯中文块候选
        if _is_name_candidate_text(t, ticket_info, station_name_set):
            candidates.append((i, t.strip()))
            continue

        # 2) 粘连块候选（如 '****8035周帅康'）
        glued = _extract_tail_name_from_masked_id_block(t)
        if glued:
            candidates.append((i, glued))

    if not candidates:
        return ""

    # 选择距离任意 id-like 块最近的候选姓名
    best_name = ""
    best_dist = 10**9
    for ci, name in candidates:
        dist = min(abs(ci - ii) for ii in id_indices)
        if dist < best_dist:
            best_dist = dist
            best_name = name

    # 距离阈值：过远就不强行认定（避免误判）
    # 你这张票：4114222002 / ****8035 / 周帅康 距离很近，能通过
    return best_name if best_dist <= 4 else ""


def parse_ticket_info(ocr_texts, polys):
    """
    解析OCR识别的文本
    """
    ticket_info = {
        "train_code": "",
        "departure_station": "",
        "arrival_station": "",
        "datetime": "",
        "carriage": "",
        "seat_num": "",
        "berth_type": "",
        "price": "",
        "seat_type": "",
        "name": "",
        "discount_type": "",
        "detection_id": 0
    }

    print(f"OCR独立文本块列表: {ocr_texts}\n")

    # 为每个文本块计算中心点
    centers = []
    for i, poly in enumerate(polys):
        if len(poly) >= 4:
            # 计算中心点
            x_sum = sum(p[0] for p in poly)
            y_sum = sum(p[1] for p in poly)
            center_x = x_sum / 4
            center_y = y_sum / 4
            centers.append((center_y, center_x, i))
        else:
            centers.append((0, 0, i))

    # 按中心点的y坐标排序（从上到下）
    centers.sort(key=lambda x: x[0])  # 按y坐标排序
    visual_order_indices = [idx for _, _, idx in centers]

    # 从ocr_texts和visual_order_indices中获取按视觉顺序的文本
    visual_texts = [ocr_texts[i] for i in visual_order_indices]

    # 从visual_texts中提取车站
    station_candidates = []  # (name, visual_idx, cx)
    interference = {"上铺", "中铺", "下铺", "限乘", "当日", "当次", "车", "号", "开", "元", "报销", "使用"}

    for idx, txt in enumerate(visual_texts):
        orig_idx = visual_order_indices[idx]  # 原始索引，用于取 polys
        fixed_txt = _fix_ocr_text(txt)
        for match in re.finditer(r'([\u4e00-\u9fa5]{2,6})站', txt):
            name = match.group(1)
            if not any(w in name for w in interference):
                # 获取该文本块的原始 poly，计算 x 中心
                poly = polys[orig_idx]
                cx = sum(p[0] for p in poly) / 4 if len(poly) >= 4 else 0
                station_candidates.append((name, idx, cx))

    # 从visual_texts中提取车次
    train_code = ""
    train_index_in_visual = -1
    for idx, txt in enumerate(visual_texts):
        fixed_txt = _fix_ocr_text(txt)
        # 提取车次
        if not train_code:
            # 尝试 Gxxx
            g_match = re.search(r'\bG(\d{4})\b', fixed_txt)
            if g_match and len(g_match.group(0)) == 5:
                train_code = f"G{g_match.group(1)}"
                train_index_in_visual = idx
            else:
                # 尝试其他车次
                prefixes = ['C', 'D', 'K', 'T', 'Z']
                for p in prefixes:
                    pattern = rf'\b{p}(\d{{1,4}})\b'
                    match = re.search(pattern, fixed_txt)
                    if match:
                        code = match.group(0)
                        if 4 <= len(code) <= 5:
                            train_code = code
                            train_index_in_visual = idx
                            break

    ticket_info["train_code"] = train_code

    # === 新增：车次的y坐标锚点，用于修正倾斜导致的站名行分裂 ===
    train_anchor_y = None
    if train_index_in_visual >= 0:
        train_orig_idx = visual_order_indices[train_index_in_visual]
        _, train_anchor_y = _poly_center(polys[train_orig_idx])

    if station_candidates:
        # 获取每个候选车站的真实 y 坐标（通过 orig_idx 找到原始 poly）
        station_with_y = []
        for name, visual_idx, cx in station_candidates:
            orig_idx = visual_order_indices[visual_idx]
            poly = polys[orig_idx]
            cy = sum(p[1] for p in poly) / 4 if len(poly) >= 4 else 0
            station_with_y.append((name, cx, cy))

        # 先按 y 分组（取最小 y 的那一行，通常是出发/到达站所在行）
        station_with_y.sort(key=lambda x: (x[2], x[1]))  # 先 y，再 x

        # 提取 y 最小的那一行（顶部行）
        min_y = station_with_y[0][2]
        top_row_stations = [s for s in station_with_y if abs(s[2] - min_y) < 30]  # 阈值可调

        # 按 x 排序（左 → 右）
        top_row_stations.sort(key=lambda x: x[1])

        unique_names = []
        seen = set()
        for name, _, _ in top_row_stations:
            if name not in seen:
                unique_names.append(name)
                seen.add(name)

        if station_candidates:
            station_with_y = []
            for name, visual_idx, cx in station_candidates:
                orig_idx = visual_order_indices[visual_idx]
                poly = polys[orig_idx]
                cy = sum(p[1] for p in poly) / 4 if len(poly) >= 4 else 0
                station_with_y.append((_normalize_station_name(name), cx, cy))

            # === 新增：优先使用“车次所在行”的站名（抗倾斜/旋转）===
            dep, arr = "", ""
            if train_anchor_y is not None:
                # 经验阈值：同一行上下浮动，倾斜票面会拉大y差，所以这里放宽一些
                band = [s for s in station_with_y if abs(s[2] - train_anchor_y) <= 90]
                # band里如果能取到2个站名，按x左->右就是出发->到达
                dep, arr = _pick_left_right_station_names(band)

            # 回退到你原来的逻辑（按y聚类/最靠上两个）
            if not dep or not arr:
                dep, arr = _pick_dep_arr_from_station_candidates(station_with_y)

            if dep and not ticket_info["departure_station"]:
                ticket_info["departure_station"] = dep
            if arr and not ticket_info["arrival_station"]:
                ticket_info["arrival_station"] = arr

    # === 新增：构建站名集合（供姓名候选互斥使用），只构建一次 ===
    station_name_set = set()
    if ticket_info.get("departure_station"):
        station_name_set.add(ticket_info["departure_station"].strip())
        station_name_set.add(ticket_info["departure_station"].strip() + "站")
    if ticket_info.get("arrival_station"):
        station_name_set.add(ticket_info["arrival_station"].strip())
        station_name_set.add(ticket_info["arrival_station"].strip() + "站")

    # station_candidates 里也加入（候选多为不含“站”的形式，但也补全“站”变体）
    for n, _, _ in station_candidates:
        nn = _normalize_station_name(n)
        if _is_valid_station_name(nn):
            station_name_set.add(nn)
            station_name_set.add(nn + "站")

    has_id_like = any(_is_id_like_text(t) for t in ocr_texts)

    # 遍历每个独立文本块，逐个匹配对应字段
    for txt in ocr_texts:
        if not ticket_info["train_code"] or not (ticket_info["departure_station"] and ticket_info["arrival_station"]):
            # 1. 查找所有“XX站”车站及其位置
            stations_in_txt = []
            for match in re.finditer(r'([\u4e00-\u9fa5]{2,6})站', txt):
                name = match.group(1)
                interference = {"上铺", "中铺", "下铺", "限乘", "当日", "当次", "车", "号", "开", "元", "报销", "使用"}
                if not any(w in name for w in interference):
                    stations_in_txt.append((name, match.start(), match.end()))

            # 2. 查找车次及其位置
            train_match = None
            if not ticket_info["train_code"]:
                train_match = re.search(r'(?<![0-9])([GDCKTZ]\d{1,4})(?![0-9])', txt)
                if train_match:
                    ticket_info["train_code"] = train_match.group(1)
                    train_start = train_match.start()
                else:
                    train_start = -1
            else:
                # 车次已知，但仍可尝试定位（用于已有车次但未处理车站的情况）
                tm = re.search(r'(?<![0-9])([GDCKTZ]\d{1,4})(?![0-9])', txt)
                train_start = tm.start() if tm else -1

            # 3. 如果有车站
            if stations_in_txt:
                # 按位置排序
                stations_in_txt.sort(key=lambda x: x[1])

                if train_start >= 0:
                    # 车次存在：找车次之后的第一个车站 → 到达站
                    arrival_candidates = [s for s in stations_in_txt if s[1] > train_start]
                    departure_candidates = [s for s in stations_in_txt if s[1] < train_start]

                    if arrival_candidates and not ticket_info["arrival_station"]:
                        ticket_info["arrival_station"] = arrival_candidates[0][0]  # 最近的右侧车站

                    if departure_candidates and not ticket_info["departure_station"]:
                        ticket_info["departure_station"] = departure_candidates[-1][0]  # 最近的左侧车站

                else:
                    # 无车次：按原逻辑，第一个是出发，第二个是到达
                    if not ticket_info["departure_station"]:
                        ticket_info["departure_station"] = stations_in_txt[0][0]
                    elif not ticket_info["arrival_station"] and len(stations_in_txt) > 1:
                        ticket_info["arrival_station"] = stations_in_txt[1][0]

        # 3. 发车时间匹配（支持中文/英文冒号，带或不带“开”字）
        if not ticket_info["datetime"]:
            # 先在整个 ocr_texts 中分别找日期和时间
            date_candidate = None
            time_candidate = None

            for t in ocr_texts:
                # 匹配日期：YYYY年MM月DD日
                if not date_candidate:
                    d_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', t)
                    if d_match:
                        date_candidate = d_match.group(1)

                # 匹配时间：HH:MM 或 HH：MM，可带“开”
                if not time_candidate:
                    t_match = re.search(r'(\d{1,2})[:：](\d{2})\s*开?', t)
                    if t_match:
                        h = t_match.group(1).zfill(2)
                        m = t_match.group(2).zfill(2)
                        time_candidate = f"{h}:{m}"

                # 如果都找到了，提前退出
                if date_candidate and time_candidate:
                    break

            # 组合结果
            if date_candidate and time_candidate:
                ticket_info["datetime"] = f"{date_candidate} {time_candidate}"
            elif date_candidate:
                # 只有日期（无时间），也保留
                ticket_info["datetime"] = date_candidate

        if not ticket_info["datetime"]:
            # 定义多种时间格式正则（按优先级排序）
            time_patterns = [
                r'(\d{4})(\d{2})月(\d{2})(\d{3})[:：](\d{2})开?',
                r'(\d{4})(\d{2})(\d{2})日(\d{2})(\d{2})',
                # '2024年1005日16:50开'
                r'(\d{4})年(\d{2})(\d{2})日(\d{1,2}):(\d{2})开?',
                r'(\d{4})(\d{2})月(\d{1,2})日(\d{4})开?',
                r'(\d{4}年\d{1,2}月)(\d{1,2})[^\d:\s]{1,3}?(\d{1,2})[:：](\d{2})开?',
                # 格式1: "2020年08月29日20：54开" 或 "2020年08月29日20:54开"
                r'(\d{4}年\d{1,2}月\d{1,2}日)[\s:：]*(\d{1,2})[:：](\d{2})开?',
                # 格式2: "2020年08月29日 20:54"（有空格）
                r'(\d{4}年\d{1,2}月\d{1,2}日)\s+(\d{1,2})[:：](\d{2})',
                # 格式3: 紧凑型 "2020年08月29日2054"
                r'(\d{4}年\d{1,2}月\d{1,2}日)(\d{2})(\d{2})',
            ]

            for i, pattern in enumerate(time_patterns):
                match = re.search(pattern, txt)
                if match:
                    if i == 0:
                        year = match.group(1)
                        month = match.group(2).zfill(2)
                        day = match.group(3).zfill(2)
                        hour = match.group(4)[-2:].zfill(2)
                        minute = match.group(5).zfill(2)
                        ticket_info["datetime"] = f"{year}年{month}月{day}日 {hour}:{minute}"
                    elif i == 1:
                        year = match.group(1)
                        month = match.group(2).zfill(2)
                        day = match.group(3).zfill(2)
                        hour = match.group(4).zfill(2)
                        minute = match.group(5).zfill(2)
                        ticket_info["datetime"] = f"{year}年{month}月{day}日 {hour}:{minute}"

                    elif i == 2:
                        year = match.group(1)
                        month = match.group(2).zfill(2)
                        day = match.group(3).zfill(2)
                        hour = match.group(4).zfill(2)
                        minute = match.group(5).zfill(2)
                        ticket_info["datetime"] = f"{year}年{month}月{day}日 {hour}:{minute}"

                    elif i == 3:
                        # 新规则：202404月07日1022开 → YYYY MM DD HHmm
                        year = match.group(1)
                        month = match.group(2).zfill(2)
                        day = match.group(3).zfill(2)
                        time4 = match.group(4)
                        if len(time4) == 4:
                            hour = time4[:2]
                            minute = time4[2:]
                        else:
                            hour = time4.zfill(4)[:2]
                            minute = time4.zfill(4)[2:]
                        ticket_info["datetime"] = f"{year}年{month}月{day}日 {hour}:{minute}"

                    elif i == 4:
                        # 泛化分隔符模式：如 2025年01月18H13:46
                        year_month = match.group(1)
                        day = match.group(2).zfill(2)
                        hour = match.group(3).zfill(2)
                        minute = match.group(4).zfill(2)
                        ticket_info["datetime"] = f"{year_month}{day}日 {hour}:{minute}"
                    else:
                        date_part = match.group(1)
                        hour = match.group(2).zfill(2)
                        minute = match.group(3).zfill(2)
                        if i == 7:  # 紧凑型：YYYY年MM月DDHHMM
                            hour = match.group(2)
                            minute = match.group(3)
                        ticket_info["datetime"] = f"{date_part} {hour}:{minute}"
                    break

            # 如果没匹配到，尝试粘连时间（如 2024年02月26014:08 → 应为 2024年02月26日 14:08）
            if not ticket_info["datetime"]:
                # 无时间格式（2024年02月26日）
                date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', txt)
                if date_match:
                    ticket_info["datetime"] = date_match.group(1)
                sticky_match = re.search(r'(\d{4}年\d{1,2}月)(\d{4,6}):(\d{2})', txt)
                if sticky_match:
                    year_month = sticky_match.group(1)
                    time_digits = sticky_match.group(2)
                    minute = sticky_match.group(3).zfill(2)

                    if len(time_digits) == 4:
                        day = time_digits[:2]
                        hour = time_digits[2:]
                    elif len(time_digits) == 5:
                        day = time_digits[:2]
                        hour = time_digits[-2:]
                        # 检查：hour 是否合理（00~23）
                        if hour.isdigit() and 0 <= int(hour) <= 23:
                            pass
                        else:
                            hour = time_digits[2:4]
                    elif len(time_digits) == 6:
                        day = time_digits[:2]
                        hour = time_digits[2:4]
                    else:
                        day = time_digits[:2] if len(time_digits) >= 2 else '01'
                        hour = time_digits[2:4] if len(time_digits) >= 4 else '00'
                    # 补零并验证
                    day = day.zfill(2)
                    hour = hour.zfill(2)

                    d = int(day)
                    h = int(hour)
                    if 1 <= d <= 31 and 0 <= h <= 23:
                        ticket_info["datetime"] = f"{year_month}{day}日 {hour}:{minute}"

            # 如果已提取到时间，跳过后续字段处理
            if ticket_info["datetime"]:
                continue

        # 4. 车厢号+座位号+铺位类型匹配（重点优化：同一文本块拆分多个字段）
        if not (ticket_info["carriage"] and ticket_info["seat_num"] and ticket_info["berth_type"]):
            # 匹配格式：数字车+数字+字母号+铺位类型（如09车14F号上铺、3车02号中铺）
            combo_match = re.search(r'(\d+)车(\d+[A-F]?)号(上铺|中铺|下铺)?', txt)
            if combo_match:
                # 拆分车厢号、座位号、铺位类型
                if not ticket_info["carriage"]:
                    ticket_info["carriage"] = combo_match.group(1)
                if not ticket_info["seat_num"]:
                    ticket_info["seat_num"] = combo_match.group(2)
                if not ticket_info["berth_type"] and combo_match.group(3):
                    ticket_info["berth_type"] = combo_match.group(3)
                continue

        # 处理 03403A → 03车03A号
        if not (ticket_info["carriage"] and ticket_info["seat_num"]):
            # 假设前2位是车厢，后2位是座位数字，最后是字母
            short_seat_match = re.fullmatch(r'(\d{2})(\d{2}[A-F])号', txt)
            if short_seat_match:
                ticket_info["carriage"] = short_seat_match.group(1)
                ticket_info["seat_num"] = short_seat_match.group(2)
                continue
            # 074080号
            pure_num_match = re.fullmatch(r'(\d{6,8})号', txt)
            if pure_num_match:
                num_str = pure_num_match.group(1)
                if len(num_str) >= 4:
                    ticket_info["carriage"] = num_str[:2]
                    ticket_info["seat_num"] = num_str[2:]
                continue

            # 03车03A号
            combo_match = re.search(r'(\d+)车(\d+[A-F]?)号', txt)
            if combo_match:
                ticket_info["carriage"] = combo_match.group(1)
                ticket_info["seat_num"] = combo_match.group(2)
                continue

            # OCR错误规则：如 "03403A" → 假设格式为 XX?XXA（6字符，最后是字母）
            if len(txt) == 6 and txt[-1] in 'ABCDEF' and txt[:2].isdigit():
                # 尝试跳过第3位（常见OCR把"车"识别为数字）
                if txt[3:-1].isdigit():  # 如 '03A' 的前部分 '03'
                    ticket_info["carriage"] = txt[:2]
                    ticket_info["seat_num"] = txt[3:]
                    continue

            # 规则2: 泛化OCR错误格式，如 "03+12C号", "05#08A号", "12&01B号"
            ocr_match = re.search(r'(\d{1,2})[^\u4e00-\u9fa5\dA-Za-z]{1,3}?(\d{1,2}[A-F]?)号', txt)
            if ocr_match:
                ticket_info["carriage"] = ocr_match.group(1)
                ticket_info["seat_num"] = ocr_match.group(2)
                continue

            # 规则3: 单独匹配车厢（如 "03车"）
            if not ticket_info["carriage"]:
                carriage_match = re.search(r'(\d+)车', txt)
                if carriage_match:
                    ticket_info["carriage"] = carriage_match.group(1)

            # 规则4: 单独匹配座位（如 "12C号"）
            if not ticket_info["seat_num"]:
                seat_match = re.search(r'(\d+[A-F]?)号', txt)
                if seat_match:
                    ticket_info["seat_num"] = seat_match.group(1)

        # 5. 单独匹配车厢号（兼容只有车厢号的文本块）
        if not ticket_info["carriage"]:
            carriage_match = re.search(r'(\d+)车', txt)
            if carriage_match:
                ticket_info["carriage"] = carriage_match.group(1)
                continue

        # 新增：无座/站票 作为 seat_num（用于普速/无座票）
        if not ticket_info["seat_num"]:
            if txt.strip() in ("无座", "站票"):
                ticket_info["seat_num"] = txt.strip()
                continue

        # 6. 单独匹配座位号（兼容只有座位号的文本块）
        if not ticket_info["seat_num"]:
            # 修改座位号匹配，支持数字+字母的组合
            seat_match = re.search(r'(\d+[A-F]?)号', txt)
            if seat_match:
                ticket_info["seat_num"] = seat_match.group(1)
                continue

        # 7. 单独匹配铺位类型（兼容只有铺位类型的文本块）
        if not ticket_info["berth_type"]:
            berth_types = ["上铺", "中铺", "下铺"]
            for berth in berth_types:
                if berth in txt:
                    ticket_info["berth_type"] = berth
                    break
            if ticket_info["berth_type"]:
                continue

        # 8. 票价匹配（处理价格被分割的情况，如['￥443.', '5元']）
        if not ticket_info["price"]:
            # 检查是否包含价格相关关键词
            price_related = any(keyword in txt for keyword in ['￥', '元'])
            if price_related:
                # 如果当前文本块包含价格相关关键词，尝试与前后文本块组合
                idx = ocr_texts.index(txt)
                # 尝试组合当前文本块和后续文本块
                combined_price = txt
                for i in range(idx + 1, min(idx + 3, len(ocr_texts))):
                    combined_price += ocr_texts[i]
                    # 检查组合后的文本是否符合价格格式
                    price_match = re.search(r'￥?(\d+\.?\d*)元?', combined_price)
                    if price_match:
                        ticket_info["price"] = price_match.group(1)
                        break

                if ticket_info["price"]:
                    continue

                # 单独匹配当前文本块
                price_match = re.search(r'￥?(\d+\.?\d*)元?', txt)
                if price_match:
                    # 只有当匹配到的数字是完整价格时才使用
                    if '.' in price_match.group(1) or len(price_match.group(1)) > 2:
                        ticket_info["price"] = price_match.group(1)
                    continue

            # 符合小数标准的字段
            decimal_match = re.search(r'(\d+\.\d+)', txt)
            if decimal_match:
                val_str = decimal_match.group(1)
                try:
                    num = float(val_str)
                    if 5 <= num <= 3000:
                        ticket_info["price"] = val_str
                except ValueError:
                    pass

        # 9. 座位类型匹配（如新车空调硬卧）
        if not ticket_info["seat_type"]:
            seat_types = ['新空调硬座', '新空调硬卧', '新空调软座', '新空调软卧',"一等座", "二等座", "商务座", "特等座", "硬座", "软座", "硬卧", "软卧"]
            for seat_type in seat_types:
                if seat_type in txt:
                    ticket_info["seat_type"] = seat_type
                    break
            if ticket_info["seat_type"]:
                continue

        # 10. 优惠类型匹配（学生票/儿童票等）
        if not ticket_info["discount_type"]:
            # 扩展优惠类型关键词，包括"学惠"
            discount_types = ["学生票", "儿童票", "优惠票", "残疾军人票", "学惠", "学", "惠"]
            for discount in discount_types:
                if discount in txt:
                    ticket_info["discount_type"] = "学生票" if discount == "学惠" or discount == '学' or discount == '惠' else discount
                    break
            if ticket_info["discount_type"]:
                continue

        # 11. 姓名匹配 - 放在优惠类型之后，避免"学惠"被误识别为姓名
        if not ticket_info["name"]:
            # 主规则：匹配「6位地区码 + 8-10位（数字+*） + 4位校验码」后面的中文
            name_match = re.search(r'(\d{6})([\d\*]{8,10})([\dXx]{4})([\u4e00-\u9fa5]+)', txt)
            if name_match:
                ticket_info["name"] = name_match.group(4).strip()
                continue
            # 备用规则1：只要有15-17位（数字+*）+ 结尾（数字/X/x），后面的中文都算姓名
            backup_match1 = re.search(r'[\d\*]{15,17}[\dXx]([\u4e00-\u9fa5]+)', txt)
            if backup_match1:
                ticket_info["name"] = backup_match1.group(1).strip()
                continue
            # 备用规则2：匹配数字+空格+中文姓名的模式（如"5678 张三"）
            backup_match2 = re.search(r'\d+\s+([\u4e00-\u9fa5]{2,6})', txt)
            if backup_match2:
                ticket_info["name"] = backup_match2.group(1).strip()
                continue

            # 新增规则：掩码证件号与姓名粘连（如 '****8035周帅康'）
            glued = _extract_tail_name_from_masked_id_block(txt)
            if glued:
                ticket_info["name"] = glued
                continue

            # 排除常见的非姓名词汇
            # 备用规则3：纯中文兜底（仅在票面不存在证件号/掩码块时启用）
            if (not has_id_like) and _is_name_candidate_text(txt, ticket_info, station_name_set):
                ticket_info["name"] = txt.strip()
                continue

    # 姓名增强纠正
    # 若当前 name 低置信，则尝试从证件号/掩码附近挑选姓名
    if _is_low_confidence_name(ticket_info.get("name", ""), station_name_set):
        better = _select_name_by_proximity(ocr_texts, station_name_set, ticket_info)
        if better:
            ticket_info["name"] = better
        else:
            # 若没有更可靠候选，则保持空（避免把站名/提示词当姓名）
            if _is_low_confidence_name(ticket_info.get("name", ""), station_name_set):
                ticket_info["name"] = ""

    ticket_info = _post_fix_arrival_station(ticket_info, ocr_texts)
    return ticket_info
