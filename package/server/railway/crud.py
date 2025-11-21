#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 20:50
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-crud.py
@Description : 
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date, time, datetime
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, NoResultFound

# 导入数据库模型和Pydantic Schema
from railway.db.models.models import (
    Base, Station, Train, TrainOperationPlan, TrainSchedule
)

from railway.schemas import (
    StationCreate, StationRead,
    TrainCreate, TrainRead,
    TrainOperationPlanCreate, TrainOperationPlanRead,
    TrainScheduleCreate, TrainScheduleRead, StationListQuery, StationSingleQuery
)
from railway.util.city import standardize_city_name, PROVINCE_MAPPING


# ------------------------------ 车站 CRUD ------------------------------
def create_station(db: Session, station: StationCreate) -> Tuple[int, str, Optional[Station]]:
    """
    创建车站
    :param db: 数据库会话
    :param station: 车站创建模型
    :return: (创建成功的车站对象, 状态信息)
    """
    """
    创建/更新车站（存在则检查更新）
    返回格式：(code, msg, data)
    """
    try:
        # 1. 验证必填字段（telecode 可选，但 station_name 等必填）
        required_fields = ["station_name", "station_pinyin", "station_py", "province", "city"]
        for field in required_fields:
            if not getattr(station, field):
                return 400, f"缺少必填字段：{field}", None

        # 2. 检查是否已存在（按 telecode 或 station_name 匹配）
        query = db.query(Station)
        if station.telecode:
            existing = query.filter(Station.telecode == station.telecode).first()
        else:
            # 无电报码时，按名称+城市唯一匹配（避免重复创建）
            existing = query.filter(
                Station.station_name == station.station_name,
                Station.city == station.city
            ).first()

        if existing:
            # 3. 已存在：更新字段（不覆盖 telecode，除非显式传入）
            for key, value in station.dict(exclude_unset=True).items():
                if key != "telecode":  # 电报码不允许更新（唯一标识）
                    setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return 200, "车站已存在，已更新信息", existing
        else:
            # 4. 不存在：新增车站
            new_station = Station(**station.dict())
            db.add(new_station)
            db.commit()
            db.refresh(new_station)
            return 200, "车站创建成功", new_station

    except IntegrityError:
        db.rollback()
        return 409, f"电报码{station.telecode}已存在（唯一约束冲突）", None
    except Exception as e:
        db.rollback()
        return 500, f"服务端错误：{str(e)}", None


def get_station_single(db: Session, query: StationSingleQuery) -> Tuple[int, str, Optional[Station]]:
    """
    单条车站查询（支持ID/电报码/名称三选一）
    返回：(code, msg, station对象)
    """
    try:
        # 校验查询条件（三选一）
        query_count = sum([1 for x in [query.station_id, query.telecode, query.station_name] if x is not None])
        if query_count == 0:
            return 400, "必须指定查询条件（station_id/telecode/station_name三选一）", None
        if query_count > 1:
            return 400, "查询条件冲突（station_id/telecode/station_name只能选一个）", None

        # 构建查询
        db_query = db.query(Station)
        if query.station_id:
            station = db_query.filter(Station.station_id == query.station_id).first()
        elif query.telecode:
            station = db_query.filter(Station.telecode == query.telecode).first()
        else:  # station_name（精确匹配）
            station = db_query.filter(Station.station_name == query.station_name).first()

        if not station:
            return 404, f"未找到符合条件的车站", None
        return 200, "查询成功", station
    except Exception as e:
        return 500, f"查询失败：{str(e)}", None


def get_station_list(db: Session, query: StationListQuery) -> Tuple[int, str, Dict[str, Any]]:
    try:
        db_query = db.query(Station)

        # 🌟 关键修改：标准化用户输入的省份和城市
        standard_province = standardize_city_name(query.province)
        standard_city = standardize_city_name(query.city)
        print(standard_city,standard_province)
        # 1. 省份筛选（前缀模糊匹配，兼容数据库存储的全称）
        if standard_province:
            # 两种情况：1. 标准化后是规范值（如“河南省”）→ 精确匹配；2. 是关键词（如“henan”）→ 模糊匹配
            if standard_province in PROVINCE_MAPPING.keys():
                # 规范值直接精确匹配（高效）
                db_query = db_query.filter(Station.province == standard_province)
            else:
                # 关键词前缀模糊匹配（避免过度模糊）
                db_query = db_query.filter(Station.province.ilike(f"{standard_province}%"))

        # 2. 城市筛选（同理，前缀模糊匹配）
        if standard_city:
            # 数据库可能存“商丘”或“商丘市”，所以用前缀匹配（如“商丘”→ 匹配“商丘”“商丘市”）
            db_query = db_query.filter(Station.city.ilike(f"{standard_city}%"))

        # 3. 其他筛选条件（不变）
        if query.district:
            db_query = db_query.filter(Station.district.ilike(f"{query.district}%"))  # 区县也支持模糊
        if query.is_high_speed is not None:
            db_query = db_query.filter(Station.is_high_speed == query.is_high_speed)
        if query.status is not None:
            db_query = db_query.filter(Station.status == query.status)

        # 4. 模糊搜索（名称/全拼/简拼，不变）
        if query.keyword:
            keyword = f"%{query.keyword}%"
            db_query = db_query.filter(
                or_(
                    Station.station_name.ilike(keyword),
                    Station.station_pinyin.ilike(keyword),
                    Station.station_py.ilike(keyword)
                )
            )

        # 5. 分页查询
        total = db_query.count()
        offset = (query.page - 1) * query.page_size
        stations_orm = db_query.order_by(Station.station_name.asc()).offset(offset).limit(query.page_size).all()


        # 7. 构造返回数据
        data = {
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_page": (total + query.page_size - 1) // query.page_size,
            "list": stations_orm
        }
        return 200, "列表查询成功", data
    except Exception as e:
        return 500, f"列表查询失败：{str(e)}", {
            "total": 0,
            "page": query.page,
            "page_size": query.page_size,
            "total_page": 0,
            "list": []
        }