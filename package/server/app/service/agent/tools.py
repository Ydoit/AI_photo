import json
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.tools import tool, StructuredTool

from app.db.session import SessionLocal
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.db.models.image_description import ImageDescription
from app.db.models.trip import TrainTicket, FlightTicket

def get_agent_tools(user_id: str) -> List[StructuredTool]:
    """
    根据 user_id 动态生成绑定了用户的工具列表
    """
    
    @tool
    def search_photos_tool(
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        location: Optional[str] = None,
        limit: int = 10,
        sort_by: str = "photo_time"
    ) -> str:
        """
        搜索用户的相册照片。
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            location: 模糊的地点名称（如"北京", "西湖"）
            limit: 返回的照片数量上限
            sort_by: 排序方式，可选 "photo_time"（按时间）, "quality_score"（按美观度）, "memory_score"（按回忆价值）
        Returns:
            包含照片ID、拍摄时间、地点和一句话描述的 JSON 字符串。
        """
        with SessionLocal() as db:
            query = db.query(Photo, PhotoMetadata, ImageDescription).outerjoin(
                PhotoMetadata, Photo.id == PhotoMetadata.photo_id
            ).outerjoin(
                ImageDescription, Photo.id == ImageDescription.photo_id
            ).filter(Photo.owner_id == user_id)

            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    query = query.filter(Photo.photo_time >= start_dt)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_dt = datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
                    query = query.filter(Photo.photo_time <= end_dt)
                except ValueError:
                    pass

            if location:
                query = query.filter(
                    (PhotoMetadata.city.ilike(f"%{location}%")) |
                    (PhotoMetadata.province.ilike(f"%{location}%")) |
                    (PhotoMetadata.address.ilike(f"%{location}%"))
                )

            if sort_by == "quality_score":
                query = query.order_by(ImageDescription.quality_score.desc().nulls_last())
            elif sort_by == "memory_score":
                query = query.order_by(ImageDescription.memory_score.desc().nulls_last())
            else:
                query = query.order_by(Photo.photo_time.desc().nulls_last())

            results = query.limit(limit).all()

            if not results:
                return "没有找到符合条件的照片。"

            response_data = []
            for photo, meta, desc in results:
                response_data.append({
                    "photo_id": str(photo.id),
                    "photo_time": photo.photo_time.strftime("%Y-%m-%d %H:%M:%S") if photo.photo_time else None,
                    "location": meta.address if meta else "未知地点",
                    "narrative": desc.narrative if desc else "无描述",
                    "quality_score": desc.quality_score if desc else None
                })
            
            return json.dumps(response_data, ensure_ascii=False)

    @tool
    def get_travel_history_tool(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        查询用户的火车票和机票出行记录。
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        Returns:
            包含出行时间、出发地、目的地的 JSON 字符串。
        """
        with SessionLocal() as db:
            train_query = db.query(TrainTicket).filter(TrainTicket.owner_id == user_id)
            flight_query = db.query(FlightTicket).filter(FlightTicket.owner_id == user_id)

            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    train_query = train_query.filter(TrainTicket.date_time >= start_dt)
                    flight_query = flight_query.filter(FlightTicket.date_time >= start_dt)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_dt = datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
                    train_query = train_query.filter(TrainTicket.date_time <= end_dt)
                    flight_query = flight_query.filter(FlightTicket.date_time <= end_dt)
                except ValueError:
                    pass

            train_results = train_query.order_by(TrainTicket.date_time.asc()).all()
            flight_results = flight_query.order_by(FlightTicket.date_time.asc()).all()

            records = []
            for t in train_results:
                records.append({
                    "type": "火车",
                    "date": t.date_time.strftime("%Y-%m-%d %H:%M:%S") if t.date_time else None,
                    "train_code": t.train_code,
                    "departure": t.departure_station,
                    "arrival": t.arrival_station
                })
            
            for f in flight_results:
                records.append({
                    "type": "飞机",
                    "date": f.date_time.strftime("%Y-%m-%d %H:%M:%S") if f.date_time else None,
                    "flight_no": f.flight_no,
                    "departure": f.departure_airport,
                    "arrival": f.arrival_airport
                })
            
            if not records:
                return "这段时间内没有出行记录。"

            # 按时间排序
            records.sort(key=lambda x: x["date"] if x["date"] else "")
            return json.dumps(records, ensure_ascii=False)

    @tool
    def get_photo_details_tool(photo_ids: List[str]) -> str:
        """
        根据照片 ID 列表获取照片的详细描述和标签，用于撰写朋友圈文案。
        Args:
            photo_ids: 照片 ID 的字符串列表
        Returns:
            包含照片详细描述、标签和一句话旁白的 JSON 字符串。
        """
        with SessionLocal() as db:
            # 过滤 owner_id 确保安全
            results = db.query(ImageDescription).join(
                Photo, Photo.id == ImageDescription.photo_id
            ).filter(
                ImageDescription.photo_id.in_(photo_ids),
                Photo.owner_id == user_id
            ).all()
            
            if not results:
                return "没有找到这些照片的详细信息。"

            response_data = []
            for desc in results:
                response_data.append({
                    "photo_id": str(desc.photo_id),
                    "description": desc.description,
                    "tags": desc.tags,
                    "narrative": desc.narrative
                })
            return json.dumps(response_data, ensure_ascii=False)

    return [search_photos_tool, get_travel_history_tool, get_photo_details_tool]
