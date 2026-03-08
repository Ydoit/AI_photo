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
    def __init__(self, db: Session, user_id: uuid.UUID = None):
        self.db = db
        # Initialize from config
        if user_id:
            config = config_manager.get_user_config(user_id, db)
            self.SIMILARITY_THRESHOLD = config.ai.face_recognition_threshold
            self.DISTANCE_THRESHOLD = config.ai.face_cluster_threshold
            self.MIN_CLUSTER_SIZE_FOR_IDENTITY = config.ai.face_recognition_min_photos
        else:
            # Fallback (should be avoided)
            self.SIMILARITY_THRESHOLD = 0.7
            self.DISTANCE_THRESHOLD = 0.4
            self.MIN_CLUSTER_SIZE_FOR_IDENTITY = 5
            
        self.DBSCAN_EPS = self.DISTANCE_THRESHOLD
        self.DBSCAN_MIN_SAMPLES = 5
        self.CLUSTER_MERGE_THRESHOLD = self.DISTANCE_THRESHOLD + 0.08

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

    def assign_face_to_identity(self, face_id: int, embedding: list, owner_id: uuid.UUID = None) -> uuid.UUID | None:
        """
        优化版：利用pgvector索引查找最近邻人脸，快速分配Identity
        :param face_id: 人脸ID
        :param embedding: 人脸特征向量
        :return: 匹配的Identity ID / None（无匹配）
        """
        target_emb = self.normalize_embedding(embedding)
        
        try:
            # 1. 利用pgvector <=> 操作符查找最近邻人脸（排除当前人脸，且必须有Identity）
            # <=> 是 cosine distance
            query = self.db.query(Face).join(Photo).filter(
                Face.id != face_id,
                Face.face_identity_id.isnot(None),
                Face.is_deleted == False
            )
            
            if owner_id:
                query = query.filter(Photo.owner_id == owner_id)
                
            nearest_face = query.order_by(
                Face.face_feature.cosine_distance(target_emb)
            ).limit(1).first()

            if not nearest_face:
                # 无参考人脸，返回None由外部决定是否触发聚类
                return None

            # 2. 计算距离
            # 注意：数据库中的向量通常应该是归一化的，但为了保险起见，再次归一化
            nearest_emb = self.normalize_embedding(nearest_face.face_feature)
            dist = 1.0 - np.dot(target_emb, nearest_emb)

            # 3. 判断是否匹配成功
            if dist < config_manager.get_user_config(owner_id, self.db).ai.face_cluster_threshold:
                # 分配到已有Identity
                best_match_id = nearest_face.face_identity_id

                # 使用 update_face 更新
                update_data = schemas.FaceUpdate(
                    face_identity_id=best_match_id,
                    recognize_confidence=float(1.0 - dist)
                )
                crud_face.update_face(self.db, face_id, update_data, owner_id=owner_id)

                return best_match_id
            else:
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

    def rescan_identity(self, identity_id: uuid.UUID, owner_id: uuid.UUID = None) -> int:
        """
        重新扫描指定人物的人脸：
        1. 计算当前人物的人脸中心向量
        2. 查找未分配的人脸中与中心向量距离小于阈值的人脸
        3. 将符合条件的人脸关联到该人物
        :return: 关联的人脸数量
        """
        try:
            # 1. 获取人物关联的人脸
            assigned_faces = self.db.query(Face).filter(
                Face.face_identity_id == identity_id,
                Face.is_deleted == False,
                Face.face_feature.isnot(None)
            ).all()

            if not assigned_faces:
                return 0

            # 2. 计算中心向量
            embeddings = []
            for face in assigned_faces:
                embeddings.append(self.normalize_embedding(face.face_feature))

            if not embeddings:
                return 0

            center = np.mean(embeddings, axis=0)
            center = self.normalize_embedding(center)

            # 3. 查找未分配的人脸
            # 这里先获取一部分候选（按距离排序），再精确过滤
            candidates_query = self.db.query(Face).join(Photo).filter(
                Face.face_identity_id == None,
                Face.is_deleted == False,
                Face.face_feature.isnot(None)
            )
            
            if owner_id:
                candidates_query = candidates_query.filter(Photo.owner_id == owner_id)
                
            candidates = candidates_query.order_by(
                Face.face_feature.cosine_distance(center)
            ).all()

            count = 0
            for face in candidates:
                face_emb = self.normalize_embedding(face.face_feature)
                dist = 1.0 - np.dot(center, face_emb)

                if dist < self.DISTANCE_THRESHOLD:
                    # 关联到该人物
                    update_data = schemas.FaceUpdate(
                        face_identity_id=identity_id,
                        recognize_confidence=float(1.0 - dist)
                    )
                    crud_face.update_face(self.db, face.id, update_data, owner_id=owner_id)
                    count += 1

            return count

        except Exception as e:
            logger.error(f"重新扫描人物 {identity_id} 失败：{str(e)}", exc_info=True)
            # 不抛出异常，以免影响 API 返回
            return 0

    def process_unassigned_faces(self, owner_id: uuid.UUID = None):
        """
        批量处理未分配的人脸（DBSCAN聚类）
        """
        # 只要有未分配的人脸，就尝试聚类
        # 为了避免过多无效调用，可以先count一下? 
        # _try_create_new_cluster 内部有查询逻辑，可以直接调用，但我们需要稍微修改一下 _try_create_new_cluster
        # 让它不依赖 current_face_id
        self._cluster_unassigned_faces(owner_id)

    def _cluster_unassigned_faces(self, owner_id: uuid.UUID = None):
        """
        优化版：调整DBSCAN参数 + 簇合并逻辑，解决聚类分散问题
        对未分配的人脸做DBSCAN聚类，合并相似簇后创建新Identity
        """
        try:
            # 1. 查询未分配的人脸
            unassigned_faces = self.db.query(Face).filter(
                Face.face_identity_id == None,
                Face.is_deleted == False,
                Face.face_feature.isnot(None)
            ).all()

            face_count = len(unassigned_faces)
            if face_count < self.DBSCAN_MIN_SAMPLES:
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
                eps=config_manager.config.ai.face_cluster_threshold,
                min_samples=self.DBSCAN_MIN_SAMPLES,
                metric='cosine'
            ).fit(X)

            labels = clustering.labels_
            
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
                    if dist < self.DISTANCE_THRESHOLD + 0.08:
                        merged_members += cluster_members[label2]
                        used_labels.add(label2)
                        logger.info(f"合并簇 {label1} 和 {label2}（中心距离={dist:.4f}）")

                merged_clusters.append(merged_members)

            # 5. 为合并后的簇创建新Identity
            for cluster in merged_clusters:
                cluster_size = len(cluster)
                if cluster_size < self.MIN_CLUSTER_SIZE_FOR_IDENTITY:
                    continue

                # 创建新Identity
                create_identity_data = schemas.FaceIdentityCreate(identity_name="未命名")
                new_identity = crud_face.create_identity(self.db, create_identity_data, owner_id)

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