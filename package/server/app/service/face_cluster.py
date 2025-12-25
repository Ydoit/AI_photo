import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sklearn.cluster import DBSCAN
from app.db.models.face import Face, FaceIdentity
from app.db.models.photo import Photo
from app.crud import face as crud_face
from app.schemas import face as schemas
import logging
import uuid
from datetime import datetime
from sqlalchemy.exc import PendingRollbackError, SQLAlchemyError

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from app.core.config_manager import config_manager

class FaceClusterService:
    def __init__(self, db: Session):
        self.db = db
        # Initialize from config
        self.SIMILARITY_THRESHOLD = config_manager.config.ai.face_recognition_threshold
        self.DISTANCE_THRESHOLD = 1.0 - self.SIMILARITY_THRESHOLD
        self.DBSCAN_EPS = self.DISTANCE_THRESHOLD
        self.DBSCAN_MIN_SAMPLES = 1
        self.CLUSTER_MERGE_THRESHOLD = self.DISTANCE_THRESHOLD
        self.MIN_CLUSTER_SIZE_FOR_IDENTITY = config_manager.config.ai.face_recognition_min_photos

    @staticmethod
    def normalize_embedding(embedding: list | np.ndarray) -> np.ndarray:
        """
        向量L2归一化（全链路统一，避免距离计算失真）
        :param embedding: 人脸特征向量（列表/数组）
        :return: 归一化后的向量
        """
        if isinstance(embedding, list):
            emb = np.array(embedding)
        else:
            emb = embedding.copy()

        # 避免除以0
        norm = np.linalg.norm(emb)
        if norm == 0:
            logger.warning("空向量（范数为0），返回原向量")
            return emb
        return emb / norm

    def assign_face_to_identity(self, face_id: int, embedding: list) -> uuid.UUID | None:
        """
        优化版：用Identity下所有人脸的均值向量匹配，而非单个default_face
        将新人脸分配到已有Identity，无匹配则触发聚类
        :param face_id: 人脸ID
        :param embedding: 人脸特征向量
        :return: 匹配的Identity ID / None（无匹配）
        """
        target_emb = self.normalize_embedding(embedding)
        best_match_id = None
        min_dist = 2.0  # 余弦距离最大值为2

        try:
            # 1. 查询所有未删除的Identity
            identities = crud_face.get_identities(self.db, limit=100000)

            if not identities:
                # logger.info("无已存在的Identity，触发新聚类")
                self._try_create_new_cluster(face_id, embedding)
                return None

            # 2. 遍历Identity，计算均值向量并匹配
            for identity in identities:
                # 查询该Identity下所有有效人脸向量
                face_embeddings = self.db.query(Face.face_feature).filter(
                    Face.face_identity_id == identity.id,
                    Face.is_deleted == False,
                    Face.face_feature.isnot(None)
                ).all()

                if not face_embeddings:
                    continue

                # 计算均值向量（核心优化：替代单个default_face）
                emb_list = [self.normalize_embedding(emb[0]) for emb in face_embeddings]
                mean_emb = np.mean(emb_list, axis=0)
                mean_emb = self.normalize_embedding(mean_emb)  # 二次归一化

                # 计算余弦距离（1 - 点积，归一化后等价）
                dist = 1.0 - np.dot(target_emb, mean_emb)

                # 更新最优匹配
                if dist < min_dist:
                    min_dist = dist
                    best_match_id = identity.id

            # 3. 判断是否匹配成功
            if best_match_id and min_dist < self.DISTANCE_THRESHOLD:
                # 分配到已有Identity
                face = crud_face.get_face(self.db, face_id)
                if not face:
                    logger.error(f"人脸ID {face_id} 不存在")
                    return None

                # 使用 update_face 更新
                update_data = schemas.FaceUpdate(
                    face_identity_id=best_match_id,
                    recognize_confidence=float(1.0 - min_dist)
                )
                crud_face.update_face(self.db, face_id, update_data)

                # logger.info(
                #     f"人脸 {face_id} 匹配到Identity {best_match_id}，"
                #     f"余弦距离={min_dist:.4f}，相似度={1 - min_dist:.4f}"
                # )
                return best_match_id
            else:
                # logger.info(
                #     f"无匹配的Identity（最小距离={min_dist:.4f} > 阈值={self.DISTANCE_THRESHOLD}），触发新聚类"
                # )
                self._try_create_new_cluster(face_id, embedding)
                return None

        except PendingRollbackError:
            # 事务已回滚，重置Session
            self.db.rollback()
            logger.error("事务回滚，重置Session后重试")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"分配Identity失败：{str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"分配Identity异常：{str(e)}", exc_info=True)
            raise

    def _try_create_new_cluster(self, current_face_id: int, current_embedding: list):
        """
        优化版：调整DBSCAN参数 + 簇合并逻辑，解决聚类分散问题
        对未分配的人脸做DBSCAN聚类，合并相似簇后创建新Identity
        """
        try:
            # 1. 查询未分配的人脸（含当前人脸）
            unassigned_faces = self.db.query(Face).filter(
                Face.face_identity_id == None,
                Face.is_deleted == False,
                Face.face_feature.isnot(None)
            ).limit(1000).all()  # 限制数量，避免全表扫描

            # 包含当前人脸（若未在查询结果中）
            current_face = crud_face.get_face(self.db, current_face_id)
            if current_face and current_face not in unassigned_faces:
                unassigned_faces.append(current_face)

            face_count = len(unassigned_faces)
            if face_count < self.DBSCAN_MIN_SAMPLES:
                # logger.info(f"未分配人脸数 {face_count} < 最小样本数 {self.DBSCAN_MIN_SAMPLES}，不聚类")
                return

            # 2. 提取并归一化向量
            embeddings = []
            face_ids = []
            for face in unassigned_faces:
                emb = self.normalize_embedding(face.face_feature)
                embeddings.append(emb)
                face_ids.append(face.id)

            X = np.array(embeddings)

            # 3. DBSCAN聚类（宽松参数，避免拆分）
            clustering = DBSCAN(
                eps=self.DBSCAN_EPS,
                min_samples=self.DBSCAN_MIN_SAMPLES,
                metric='cosine'
            ).fit(X)

            labels = clustering.labels_
            # logger.info(f"DBSCAN聚类完成，共生成 {len(set(labels)) - (1 if -1 in labels else 0)} 个簇")

            # 4. 计算簇中心，合并相似簇（核心：解决同一人拆分为多个簇）
            cluster_centers = {}  # label -> 簇中心向量
            cluster_members = {}  # label -> 成员face ID列表

            # 4.1 计算每个簇的中心（均值向量）
            unique_labels = set(labels)
            for label in unique_labels:
                if label == -1:  # 噪声点，跳过
                    continue

                cluster_indices = np.where(labels == label)[0]
                if len(cluster_indices) < 1:
                    continue

                # 簇内向量的均值作为中心
                cluster_emb = X[cluster_indices]
                center = np.mean(cluster_emb, axis=0)
                center = self.normalize_embedding(center)

                cluster_centers[label] = center
                cluster_members[label] = [face_ids[idx] for idx in cluster_indices]

            # 4.2 合并相似簇（中心距离 < 阈值）
            merged_clusters = []
            used_labels = set()

            for label1 in cluster_centers:
                if label1 in used_labels:
                    continue

                # 初始合并当前簇
                merged_members = cluster_members[label1].copy()
                used_labels.add(label1)

                # 遍历其他簇，判断是否合并
                for label2 in cluster_centers:
                    if label1 == label2 or label2 in used_labels:
                        continue

                    # 计算簇中心的余弦距离
                    dist = 1.0 - np.dot(cluster_centers[label1], cluster_centers[label2])
                    if dist < self.CLUSTER_MERGE_THRESHOLD:
                        merged_members += cluster_members[label2]
                        used_labels.add(label2)
                        logger.info(f"合并簇 {label1} 和 {label2}（中心距离={dist:.4f}）")

                merged_clusters.append(merged_members)

            # 5. 为合并后的簇创建新Identity
            for cluster in merged_clusters:
                cluster_size = len(cluster)
                if cluster_size < self.MIN_CLUSTER_SIZE_FOR_IDENTITY:
                    # logger.info(f"簇大小 {cluster_size} < 阈值 {self.MIN_CLUSTER_SIZE_FOR_IDENTITY}，跳过创建Identity")
                    continue

                # 创建新Identity
                create_identity_data = schemas.FaceIdentityCreate(identity_name="未命名")
                new_identity = crud_face.create_identity(self.db, create_identity_data)

                # 分配人脸到新Identity
                first_face_id = None
                for f_id in cluster:
                    face = crud_face.get_face(self.db, f_id)
                    if not face:
                        continue

                    update_data = schemas.FaceUpdate(
                        face_identity_id=new_identity.id,
                        recognize_confidence=0.9
                    )
                    crud_face.update_face(self.db, f_id, update_data)

                    if not first_face_id:
                        first_face_id = face.id

                # 设置默认人脸
                if first_face_id:
                    update_identity_data = schemas.FaceIdentityUpdate(default_face_id=first_face_id)
                    crud_face.update_identity(self.db, new_identity.id, update_identity_data)

                logger.info(
                    f"创建新Identity {new_identity.id}，包含 {cluster_size} 个人脸（合并后）"
                )

        except PendingRollbackError:
            self.db.rollback()
            logger.error("聚类时事务回滚，重置Session", exc_info=True)
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"聚类数据库错误：{str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"聚类异常：{str(e)}", exc_info=True)
            raise