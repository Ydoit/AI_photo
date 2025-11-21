#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/20 20:05
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-build_database.py
@Description : 
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/20 10:00
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : railway_crud.py
@Description : 铁路时刻表系统完整CRUD工具（适配运行计划版本化）
"""

from typing import List, Optional, Dict, Any
from datetime import date, time, datetime
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# 导入数据库模型和Pydantic Schema
from railway.db.models.models import (
    Base, Station, Train, TrainOperationPlan, TrainSchedule
)
from railway.schemas.server_schemas import (
    StationCreate, StationRead,
    TrainCreate, TrainRead,
    TrainOperationPlanCreate, TrainOperationPlanRead,
    TrainScheduleCreate, TrainScheduleRead
)

# ------------------------------ 数据库连接配置（用户需替换为自己的配置） ------------------------------
DATABASE_CONFIG = {
    "driver": "postgresql",  # 数据库驱动（postgresql/mysql/sqlite等）
    "user": "your_username",
    "password": "your_password",
    "host": "localhost",
    "port": 5432,
    "db_name": "railway_db"
}

# 构建数据库URL
DATABASE_URL = f"{DATABASE_CONFIG['driver']}://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}" \
               f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['db_name']}"

# 创建数据库引擎和会话工厂
engine = create_engine(DATABASE_URL, echo=False)  # echo=True 开启SQL日志（调试用）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ------------------------------ 基础工具函数 ------------------------------
def get_db() -> Session:
    """获取数据库会话（依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    print("数据库表初始化成功！")


# ------------------------------ 车站 CRUD ------------------------------
def create_station(db: Session, station: StationCreate) -> Tuple[Optional[Station], str]:
    """
    创建车站
    :param db: 数据库会话
    :param station: 车站创建模型
    :return: (创建成功的车站对象, 状态信息)
    """
    try:
        # 先检查车站是否已存在
        existing = db.query(Station).filter(Station.station_name == station.station_name).first()
        if existing:
            return None, f"车站「{station.station_name}」已存在"

        db_station = Station(**station.model_dump())
        db.add(db_station)
        db.commit()
        db.refresh(db_station)
        return db_station, f"车站「{station.station_name}」创建成功"
    except IntegrityError as e:
        db.rollback()
        return None, f"创建失败：数据约束冲突（{str(e.orig)[:100]}）"
    except SQLAlchemyError as e:
        db.rollback()
        return None, f"创建失败：数据库错误（{str(e)[:100]}）"


def get_station(db: Session, station_name: str) -> Optional[Station]:
    """
    根据名称获取车站详情
    :param db: 数据库会话
    :param station_name: 车站名称
    :return: 车站对象（None表示不存在）
    """
    return db.query(Station).filter(Station.station_name == station_name).first()


def get_stations(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        province: Optional[str] = None,
        city: Optional[str] = None,
        is_high_speed: Optional[int] = None
) -> List[Station]:
    """
    获取车站列表（支持筛选和分页）
    :param db: 数据库会话
    :param skip: 跳过条数（分页用）
    :param limit: 每页条数（分页用）
    :param province: 省份筛选（可选）
    :param city: 城市筛选（可选）
    :param is_high_speed: 是否高铁站（0=普速，1=高铁，可选）
    :return: 车站列表
    """
    query = db.query(Station)
    # 条件筛选
    if province:
        query = query.filter(Station.province == province)
    if city:
        query = query.filter(Station.city == city)
    if is_high_speed is not None:
        query = query.filter(Station.is_high_speed == is_high_speed)
    # 分页查询
    return query.offset(skip).limit(limit).order_by(Station.station_name).all()


def update_station(
        db: Session,
        station_name: str,
        update_data: Dict[str, Any]
) -> Tuple[Optional[Station], str]:
    """
    更新车站信息（仅更新允许修改的字段）
    :param db: 数据库会话
    :param station_name: 要更新的车站名称
    :param update_data: 更新数据（字典格式）
    :return: (更新后的车站对象, 状态信息)
    """
    try:
        db_station = get_station(db, station_name)
        if not db_station:
            return None, f"车站「{station_name}」不存在"

        # 不允许修改的字段
        forbidden_fields = ["station_name", "create_time"]
        for field in forbidden_fields:
            update_data.pop(field, None)

        # 批量更新字段
        for field, value in update_data.items():
            if hasattr(db_station, field):
                setattr(db_station, field, value)

        db.commit()
        db.refresh(db_station)
        return db_station, f"车站「{station_name}」更新成功"
    except SQLAlchemyError as e:
        db.rollback()
        return None, f"更新失败：数据库错误（{str(e)[:100]}）"


def delete_station(db: Session, station_name: str) -> str:
    """
    删除车站（谨慎使用！会受外键约束限制）
    :param db: 数据库会话
    :param station_name: 车站名称
    :return: 状态信息
    """
    try:
        db_station = get_station(db, station_name)
        if not db_station:
            return f"车站「{station_name}」不存在"

        db.delete(db_station)
        db.commit()
        return f"车站「{station_name}」删除成功"
    except IntegrityError as e:
        db.rollback()
        return f"删除失败：该车站已关联车次/时刻表（{str(e.orig)[:100]}）"
    except SQLAlchemyError as e:
        db.rollback()
        return f"删除失败：数据库错误（{str(e)[:100]}）"


# ------------------------------ 车次 CRUD ------------------------------
def create_train(db: Session, train: TrainCreate) -> Tuple[Optional[Train], str]:
    """
    创建车次（仅基础固定信息）
    :param db: 数据库会话
    :param train: 车次创建模型
    :return: (创建成功的车次对象, 状态信息)
    """
    try:
        # 检查车次编码是否唯一
        existing = db.query(Train).filter(Train.train_code == train.train_code).first()
        if existing:
            return None, f"车次「{train.train_code}」已存在"

        # 检查出发站/到达站是否存在
        if not get_station(db, train.from_station):
            return None, f"出发站「{train.from_station}」不存在"
        if not get_station(db, train.to_station):
            return None, f"到达站「{train.to_station}」不存在"

        db_train = Train(**train.model_dump())
        db.add(db_train)
        db.commit()
        db.refresh(db_train)
        return db_train, f"车次「{train.train_code}」创建成功"
    except IntegrityError as e:
        db.rollback()
        return None, f"创建失败：数据约束冲突（{str(e.orig)[:100]}）"
    except SQLAlchemyError as e:
        db.rollback()
        return None, f"创建失败：数据库错误（{str(e)[:100]}）"


def get_train(
        db: Session,
        train_id: Optional[int] = None,
        train_code: Optional[str] = None
) -> Optional[Train]:
    """
    获取车次详情（支持按ID或车次编码查询）
    :param db: 数据库会话
    :param train_id: 车次ID（可选）
    :param train_code: 车次编码（可选）
    :return: 车次对象（含关联的出发站/到达站信息）
    """
    query = db.query(Train).options(
        joinedload(Train.departure_station),
        joinedload(Train.arrival_station)
    )
    if train_id:
        return query.filter(Train.train_id == train_id).first()
    elif train_code:
        return query.filter(Train.train_code == train_code).first()
    else:
        return None


def get_trains(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        from_station: Optional[str] = None,
        to_station: Optional[str] = None,
        train_type: Optional[str] = None
) -> List[Train]:
    """
    获取车次列表（支持筛选和分页）
    :param db: 数据库会话
    :param skip: 跳过条数
    :param limit: 每页条数
    :param from_station: 出发站筛选（可选）
    :param to_station: 到达站筛选（可选）
    :param train_type: 列车类型筛选（如G/D/Z，可选）
    :return: 车次列表
    """
    query = db.query(Train).options(
        joinedload(Train.departure_station),
        joinedload(Train.arrival_station)
    )
    # 条件筛选
    if from_station:
        query = query.filter(Train.from_station == from_station)
    if to_station:
        query = query.filter(Train.to_station == to_station)
    if train_type:
        query = query.filter(Train.train_type == train_type)
    # 分页查询
    return query.offset(skip).limit(limit).order_by(Train.train_code).all()


def delete_train(db: Session, train_code: str) -> str:
    """
    删除车次（会级联删除关联的运行计划和时刻表）
    :param db: 数据库会话
    :param train_code: 车次编码
    :return: 状态信息
    """
    try:
        db_train = get_train(db, train_code=train_code)
        if not db_train:
            return f"车次「{train_code}」不存在"

        db.delete(db_train)
        db.commit()
        return f"车次「{train_code}」及关联数据删除成功"
    except SQLAlchemyError as e:
        db.rollback()
        return f"删除失败：数据库错误（{str(e)[:100]}）"


# ------------------------------ 运行计划 CRUD（核心版本化管理） ------------------------------
def is_run_day(plan: TrainOperationPlan, query_date: date) -> bool:
    """
    辅助函数：判断查询日期是否符合运行计划的开行规律
    :param plan: 运行计划对象
    :param query_date: 查询日期
    :return: True=开行，False=不开行
    """
    if plan.run_rule == 0:  # 每日开行
        return True
    elif plan.run_rule == 1:  # 工作日（周一至周五）
        return query_date.weekday() < 5
    elif plan.run_rule == 2:  # 周末（周六至周日）
        return query_date.weekday() >= 5
    elif plan.run_rule == 3:  # 单日（日期为奇数）
        return query_date.day % 2 == 1
    elif plan.run_rule == 4:  # 双日（日期为偶数）
        return query_date.day % 2 == 0
    elif plan.run_rule == 5:  # 自定义日期
        return str(query_date) in (plan.custom_run_days or [])
    return False


def create_operation_plan(
        db: Session,
        plan: TrainOperationPlanCreate
) -> Tuple[Optional[TrainOperationPlan], str]:
    """
    创建运行计划（时刻表版本）
    :param db: 数据库会话
    :param plan: 运行计划创建模型
    :return: (创建成功的运行计划对象, 状态信息)
    """
    try:
        # 检查车次是否存在
        db_train = get_train(db, train_id=plan.train_id)
        if not db_train:
            return None, f"车次ID「{plan.train_id}」不存在"

        # 检查版本号是否重复（同一车次）
        existing_version = db.query(TrainOperationPlan).filter(
            TrainOperationPlan.train_id == plan.train_id,
            TrainOperationPlan.plan_version == plan.plan_version
        ).first()
        if existing_version:
            return None, f"车次「{db_train.train_code}」已存在版本「{plan.plan_version}」"

        # 校验生效时间（开始日期不能晚于结束日期）
        if plan.end_date and plan.start_date > plan.end_date:
            return None, f"生效开始日期不能晚于结束日期"

        db_plan = TrainOperationPlan(**plan.model_dump())
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan, f"运行计划「{db_train.train_code}-{plan.plan_version}」创建成功"
    except IntegrityError as e:
        db.rollback()
        return None, f"创建失败：数据约束冲突（{str(e.orig)[:100]}）"
    except SQLAlchemyError as e:
        db.rollback()
        return None, f"创建失败：数据库错误（{str(e)[:100]}）"


def get_operation_plan(
        db: Session,
        operation_id: Optional[int] = None,
        train_id: Optional[int] = None,
        plan_version: Optional[str] = None
) -> Optional[TrainOperationPlan]:
    """
    获取运行计划详情
    :param db: 数据库会话
    :param operation_id: 运行计划ID（可选）
    :param train_id: 车次ID（可选）
    :param plan_version: 版本号（可选）
    :return: 运行计划对象（含关联车次信息）
    """
    query = db.query(TrainOperationPlan).options(joinedload(TrainOperationPlan.train))
    if operation_id:
        return query.filter(TrainOperationPlan.operation_id == operation_id).first()
    elif train_id and plan_version:
        return query.filter(
            TrainOperationPlan.train_id == train_id,
            TrainOperationPlan.plan_version == plan_version
        ).first()
    else:
        return None


def get_effective_operation_plan(
        db: Session,
        train_code: str,
        query_date: date
) -> Optional[TrainOperationPlan]:
    """
    核心查询：获取某天某车次的有效运行计划
    :param db: 数据库会话
    :param train_code: 车次编码
    :param query_date: 查询日期
    :return: 有效运行计划对象（含关联时刻表）
    """
    # 1. 获取车次ID
    db_train = get_train(db, train_code=train_code)
    if not db_train:
        return None

    # 2. 筛选生效时间包含查询日期、未停运的计划
    query = db.query(TrainOperationPlan).filter(
        TrainOperationPlan.train_id == db_train.train_id,
        TrainOperationPlan.start_date <= query_date,
        or_(TrainOperationPlan.end_date.is_(None), TrainOperationPlan.end_date >= query_date),
        TrainOperationPlan.is_canceled == 0
    ).options(
        joinedload(TrainOperationPlan.schedules).joinedload(TrainSchedule.station)
    )

    # 3. 遍历计划，校验开行规律
    for plan in query.all():
        if is_run_day(plan, query_date):
            # 对时刻表按顺序排序
            plan.schedules.sort(key=lambda x: x.sequence)
            return plan

    return None


def update_operation_plan_end_date(
        db: Session,
        operation_id: int,
        end_date: date
) -> Tuple[Optional[TrainOperationPlan], str]:
    """
    更新运行计划的结束日期（用于终止旧版本）
    :param db: 数据库会话
    :param operation_id: 运行计划ID
    :param end_date: 新的结束日期
    :return: (更新后的运行计划对象, 状态信息)
    """
    try:
        db_plan = get_operation_plan(db, operation_id=operation_id)
        if not db_plan:
            return None, f"运行计划ID「{operation_id}」不存在"

        # 校验结束日期（不能早于开始日期）
        if end_date < db_plan.start_date:
            return None, f"结束日期不能早于生效开始日期「{db_plan.start_date}」"

        db_plan.end_date = end_date
        db.commit()
        db.refresh(db_plan)
        return db_plan, f"运行计划「{db_plan.plan_version}」终止成功（生效至{end_date}）"
    except SQLAlchemyError as e:
        db.rollback()
        return None, f"更新失败：数据库错误（{str(e)[:100]}）"


def cancel_operation_plan(db: Session, operation_id: int) -> str:
    """
    停运运行计划（不会删除数据，仅标记为停运）
    :param db: 数据库会话
    :param operation_id: 运行计划ID
    :return: 状态信息
    """
    try:
        db_plan = get_operation_plan(db, operation_id=operation_id)
        if not db_plan:
            return f"运行计划ID「{operation_id}」不存在"

        db_plan.is_canceled = 1
        db.commit()
        return f"运行计划「{db_plan.plan_version}」停运成功"
    except SQLAlchemyError as e:
        db.rollback()
        return f"操作失败：数据库错误（{str(e)[:100]}）"


# ------------------------------ 时刻表 CRUD ------------------------------
def create_train_schedule(
        db: Session,
        schedule: TrainScheduleCreate
) -> Tuple[Optional[TrainSchedule], str]:
    """
    创建时刻表记录（关联运行计划）
    :param db: 数据库会话
    :param schedule: 时刻表创建模型
    :return: (创建成功的时刻表对象, 状态信息)
    """
    try:
        # 检查运行计划是否存在
        db_plan = get_operation_plan(db, operation_id=schedule.operation_id)
        if not db_plan:
            return None, f"运行计划ID「{schedule.operation_id}」不存在"

        # 检查车站是否存在
        if not get_station(db, schedule.station_name):
            return None, f"车站「{schedule.station_name}」不存在"

        # 检查同一运行计划下的顺序是否重复
        existing_seq = db.query(TrainSchedule).filter(
            TrainSchedule.operation_id == schedule.operation_id,
            TrainSchedule.sequence == schedule.sequence
        ).first()
        if existing_seq:
            return None, f"运行计划「{db_plan.plan_version}」已存在顺序「{schedule.sequence}」的记录"

        db_schedule = TrainSchedule(**schedule.model_dump())
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return db_schedule, f"时刻表记录「{db_plan.plan_version}-{schedule.station_name}」创建成功"
    except IntegrityError as e:
        db.rollback()
        return None, f"创建失败：数据约束冲突（{str(e.orig)[:100]}）"
    except SQLAlchemyError as e:
        db.rollback()
        return None, f"创建失败：数据库错误（{str(e)[:100]}）"


def get_train_schedules(
        db: Session,
        operation_id: int,
        sort_by_sequence: bool = True
) -> List[TrainSchedule]:
    """
    获取某个运行计划的所有时刻表
    :param db: 数据库会话
    :param operation_id: 运行计划ID
    :param sort_by_sequence: 是否按顺序排序
    :return: 时刻表列表（含关联车站信息）
    """
    query = db.query(TrainSchedule).filter(
        TrainSchedule.operation_id == operation_id
    ).options(joinedload(TrainSchedule.station))

    if sort_by_sequence:
        query = query.order_by(TrainSchedule.sequence)

    return query.all()


def batch_create_train_schedules(
        db: Session,
        operation_id: int,
        schedules: List[TrainScheduleCreate]
) -> Tuple[int, str]:
    """
    批量创建时刻表（效率更高，适用于单运行计划多站点）
    :param db: 数据库会话
    :param operation_id: 运行计划ID
    :param schedules: 时刻表列表
    :return: (成功创建的条数, 状态信息)
    """
    try:
        # 检查运行计划是否存在
        db_plan = get_operation_plan(db, operation_id=operation_id)
        if not db_plan:
            return 0, f"运行计划ID「{operation_id}」不存在"

        # 批量构造对象
        db_schedules = []
        seq_set = set()
        for s in schedules:
            # 校验顺序不重复
            if s.sequence in seq_set:
                return 0, f"存在重复顺序「{s.sequence}」，批量创建失败"
            seq_set.add(s.sequence)

            # 校验车站存在
            if not get_station(db, s.station_name):
                return 0, f"车站「{s.station_name}」不存在，批量创建失败"

            db_schedules.append(TrainSchedule(**s.model_dump()))

        # 批量插入
        db.add_all(db_schedules)
        db.commit()
        return len(db_schedules), f"批量创建成功：{len(db_schedules)} 条时刻表记录"
    except SQLAlchemyError as e:
        db.rollback()
        return 0, f"批量创建失败：数据库错误（{str(e)[:100]}）"


# ------------------------------ 核心业务查询函数 ------------------------------
def query_train_schedule_by_code_date(
        db: Session,
        train_code: str,
        query_date: date
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    核心业务：查询某天某车次的完整时刻表（对外提供的统一查询接口）
    :param db: 数据库会话
    :param train_code: 车次编码（如G123）
    :param query_date: 查询日期
    :return: (完整时刻表数据, 状态信息)
    """
    # 1. 获取有效运行计划
    effective_plan = get_effective_operation_plan(db, train_code, query_date)
    if not effective_plan:
        return None, f"车次「{train_code}」在「{query_date}」无有效时刻表（可能停运/不开行/未创建）"

    # 2. 构造返回数据
    result = {
        "train_info": {
            "train_code": effective_plan.train.train_code,
            "train_type": effective_plan.train.train_type,
            "from_station": effective_plan.train.from_station,
            "to_station": effective_plan.train.to_station,
            "departure_station_info": StationRead.from_orm(effective_plan.train.departure_station).model_dump(),
            "arrival_station_info": StationRead.from_orm(effective_plan.train.arrival_station).model_dump()
        },
        "operation_plan_info": {
            "plan_version": effective_plan.plan_version,
            "start_date": effective_plan.start_date,
            "end_date": effective_plan.end_date,
            "run_rule": effective_plan.run_rule,
            "total_mileage": float(effective_plan.total_mileage),
            "station_num": effective_plan.station_num
        },
        "schedules": [
            {
                "sequence": s.sequence,
                "station_name": s.station_name,
                "station_info": StationRead.from_orm(s.station).model_dump(),
                "arrival_time": s.arrival_time.strftime("%H:%M") if s.arrival_time else None,
                "departure_time": s.departure_time.strftime("%H:%M") if s.departure_time else None,
                "stop_duration": s.stop_duration,
                "accumulated_mileage": float(s.accumulated_mileage),
                "running_time": s.running_time.strftime("%H:%M") if s.running_time else None,
                "is_departure": s.is_departure,
                "is_arrival": s.is_arrival
            } for s in effective_plan.schedules
        ]
    }

    return result, "查询成功"


# ------------------------------ 测试用例（直接运行文件时执行） ------------------------------
if __name__ == "__main__":
    # 初始化数据库（首次运行时执行）
    init_db()

    # 获取数据库会话
    db = next(get_db())

    try:
        print("=" * 60)
        print("开始测试CRUD功能...")
        print("=" * 60)

        # 1. 创建车站
        print("\n1. 创建车站...")
        beijingxi = StationCreate(
            station_name="北京西",
            station_pinyin="beijingxi",
            station_py="bjx",
            province="北京",
            city="北京",
            district="丰台区",
            telecode="BXP",
            is_high_speed=1
        )
        guangzhounan = StationCreate(
            station_name="广州南",
            station_pinyin="guangzhounan",
            station_py="gzn",
            province="广东",
            city="广州",
            district="番禺区",
            telecode="GZN",
            is_high_speed=1
        )
        _, msg1 = create_station(db, beijingxi)
        _, msg2 = create_station(db, guangzhounan)
        print(f"创建车站结果：{msg1}，{msg2}")

        # 2. 创建车次
        print("\n2. 创建车次...")
        g123 = TrainCreate(
            train_no="0G12300",
            train_code="G123",
            train_type="G",
            from_station="北京西",
            to_station="广州南"
        )
        train, msg3 = create_train(db, g123)
        print(f"创建车次结果：{msg3}")

        # 3. 创建运行计划
        print("\n3. 创建运行计划...")
        plan = TrainOperationPlanCreate(
            train_id=train.train_id,
            plan_version="20251120V1",
            start_date=date(2025, 11, 20),
            end_date=None,
            run_rule=0,
            station_num=5,
            total_mileage=2298.0,
            is_canceled=0
        )
        operation_plan, msg4 = create_operation_plan(db, plan)
        print(f"创建运行计划结果：{msg4}")

        # 4. 批量创建时刻表
        print("\n4. 批量创建时刻表...")
        schedules = [
            TrainScheduleCreate(
                operation_id=operation_plan.operation_id,
                station_name="北京西",
                sequence=1,
                arrive_day_diff=0,
                arrival_time=None,
                departure_time=time(08, 00),
        stop_duration = 0,
        accumulated_mileage = 0.0,
        running_time = time(00, 00),
        is_departure = 1,
        is_arrival = 0
        ),
        TrainScheduleCreate(
            operation_id=operation_plan.operation_id,
            station_name="石家庄",
            sequence=2,
            arrive_day_diff=0,
            arrival_time=time(0
        9, 30),
        departure_time = time(0
        9, 32),
        stop_duration = 2,
        accumulated_mileage = 281.0,
        running_time = time(01, 30),
        is_departure = 0,
        is_arrival = 0
        ),
        TrainScheduleCreate(
            operation_id=operation_plan.operation_id,
            station_name="郑州东",
            sequence=3,
            arrive_day_diff=0,
            arrival_time=time(11, 05),
            departure_time=time(11, 0
        8),
        stop_duration = 3,
        accumulated_mileage = 693.0,
        running_time = time(03, 05),
        is_departure = 0,
        is_arrival = 0
        ),
        TrainScheduleCreate(
            operation_id=operation_plan.operation_id,
            station_name="长沙南",
            sequence=4,
            arrive_day_diff=0,
            arrival_time=time(13, 40),
            departure_time=time(13, 43),
            stop_duration=3,
            accumulated_mileage=1591.0,
            running_time=time(05, 40),
            is_departure=0,
            is_arrival=0
        ),
        TrainScheduleCreate(
            operation_id=operation_plan.operation_id,
            station_name="广州南",
            sequence=5,
            arrive_day_diff=0,
            arrival_time=time(15, 56),
            departure_time=None,
            stop_duration=0,
            accumulated_mileage=2298.0,
            running_time=time(07, 56),
            is_departure=0,
            is_arrival=1
        )
        ]
        count, msg5 = batch_create_train_schedules(db, operation_plan.operation_id, schedules)
        print(f"批量创建时刻表结果：{msg5}")

        # 5. 核心查询：查询某天某车次时刻表
        print("\n5. 查询G123 2025-11-20时刻表...")
        result, msg6 = query_train_schedule_by_code_date(db, "G123", date(2025, 11, 20))
        if result:
            print(f"查询结果：{msg6}")
            print(
                f"车次：{result['train_info']['train_code']}（{result['train_info']['from_station']}→{result['train_info']['to_station']}）")
            print(f"运行版本：{result['operation_plan_info']['plan_version']}")
            print("时刻表详情：")
            for s in result['schedules']:
                print(
                    f"  第{s['sequence']}站：{s['station_name']} | 到站：{s['arrival_time'] or '—'} | 发车：{s['departure_time'] or '—'} | 停留：{s['stop_duration']}分钟")

        print("\n" + "=" * 60)
        print("CRUD功能测试完成！")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n测试失败：{str(e)}")
    finally:
        db.close()
