#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 20:50
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-schemas.py
@Description : 铁路时刻表系统 Pydantic Schema（适配版本化运行计划）
"""

from datetime import date, time, datetime
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, validator

# 定义泛型类型（支持不同业务数据类型）
T = TypeVar("T")

# ------------------------------ 通用响应模型（统一错误码载体）------------------------------
class BaseResponse(BaseModel, Generic[T]):
    """所有接口的统一响应模型：包含错误码、提示信息、业务数据"""
    code: int = Field(default=200, description="错误码：200=成功，4xx=客户端错误，5xx=服务端错误")
    msg: str = Field(default="操作成功", description="提示信息")
    data: Optional[T] = Field(default=None, description="业务数据（成功时返回，失败时为None）")

    class Config:
        from_attributes = True  # 支持从 ORM 模型直接转换

# ------------------------------ 基础模型 ------------------------------
class BaseSchema(BaseModel):
    """基础 Schema，包含公共字段"""
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True  # 支持从 ORM 模型直接转换

# ------------------------------ 车站相关 ------------------------------
class StationCreate(BaseModel):
    telecode: Optional[str] = Field(max_length=3, description="电报码")
    station_name: str = Field(description="车站名称")
    station_pinyin: str = Field(description="拼音（全拼，如beijingxi）")
    station_py: str = Field(description="拼音（首字母，如bjx）")
    province: str = Field(description="所属省份")
    city: str = Field(description="所属城市")
    district: Optional[str] = Field(None, description="所属区县")
    is_high_speed: int = Field(ge=0, le=1, default=0, description="是否高铁站（0=普速，1=高铁）")
    status: int = Field(ge=0, le=1, default=1, description="状态（1=运营，0=暂停）")

class StationRead(BaseSchema):
    station_name: str
    station_pinyin: str
    province: str
    city: str
    district: Optional[str]
    telecode: Optional[str]
    is_high_speed: int
    status: int

# ------------------------------ 查询入参Schema（新增）------------------------------
class StationSingleQuery(BaseModel):
    """单条车站查询参数（支持ID/电报码/名称，三选一）"""
    station_id: Optional[int] = Field(None, description="车站ID（与telecode/name三选一）")
    telecode: Optional[str] = Field(None, max_length=3, description="车站电报码（唯一，三选一）")
    station_name: Optional[str] = Field(None, description="车站名称（精确匹配，三选一）")

class StationListQuery(BaseModel):
    """车站列表查询参数（支持筛选、模糊搜索、分页）"""
    # 筛选条件
    province: Optional[str] = Field(None, description="所属省份（精确匹配，如：北京市）")
    city: Optional[str] = Field(None, description="所属城市（精确匹配，如：北京市）")
    district: Optional[str] = Field(None, description="所属区县（精确匹配，如：丰台区）")
    is_high_speed: Optional[int] = Field(None, ge=0, le=1, description="是否高铁站（0=普速，1=高铁）")
    status: Optional[int] = Field(1, ge=0, le=1, description="状态（1=运营，0=暂停，默认查运营）")
    # 模糊搜索（名称/全拼/简拼）
    keyword: Optional[str] = Field(None, description="搜索关键词（匹配名称/全拼/简拼，如：bjx/北京西/beijingxi）")
    # 分页参数
    page: int = Field(1, ge=1, description="页码（默认第1页）")
    page_size: int = Field(20, ge=1, le=100, description="每页条数（1-100，默认20）")

# 定义列表查询的响应数据结构（明确 list 是 StationRead 列表）
class StationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_page: int
    list: List[StationRead]  # 明确是 StationRead 列表

# ------------------------------ 车次相关（仅固定基础信息） ------------------------------
class TrainCreate(BaseModel):
    train_no: str = Field(description="铁路内部唯一编号（如0G12300）")
    train_code: str = Field(description="对外公布车次（G123/D456）")
    train_type: str = Field(max_length=2, description="列车类型编码（G/D/Z/T/K等）")
    from_station: str = Field(description="固定出发站名称")
    to_station: str = Field(description="固定到达站名称")

class TrainRead(BaseSchema):
    train_id: int  # 新增：车次唯一ID（用于关联运行计划）
    train_no: str
    train_code: str
    train_type: str
    from_station: str
    departure_station: StationRead  # 关联出发站详情
    to_station: str
    arrival_station: StationRead  # 关联到达站详情

# ------------------------------ 运行计划（版本表）相关 ------------------------------
class TrainOperationPlanCreate(BaseModel):
    train_no: str = Field(description="关联车次编号")
    plan_version: str = Field(description="版本号（如20251120V1）")
    start_date: date = Field(description="生效开始日期（含）")
    end_date: Optional[date] = Field(None, description="生效结束日期（含），NULL=永久有效")
    run_rule: int = Field(ge=0, le=5, default=0, description="开行规律：0=每日，1=工作日，2=周末，3=单日，4=双日，5=自定义")
    custom_run_days: Optional[List[str]] = Field(None, description="自定义开行日期（格式：YYYY-MM-DD）")
    station_num: int = Field(ge=2, description="途经车站个数（含起止站）")
    total_mileage: float = Field(ge=0, default=0, description="全程里程（公里）")
    is_canceled: int = Field(ge=0, le=1, default=0, description="该版本是否停运（0=正常，1=停运）")

    @validator("custom_run_days")
    def check_custom_days(cls, v, values):
        """校验：自定义日期仅在run_rule=5时必填"""
        if values.get("run_rule") == 5 and not v:
            raise ValueError("自定义开行规律（run_rule=5）时，custom_run_days不能为空")
        return v

class TrainOperationPlanRead(BaseSchema):
    operation_id: int  # 运行计划唯一ID
    train_id: int
    train_no: str
    train: TrainRead  # 关联车次基础信息
    plan_version: str
    start_date: date
    end_date: Optional[date]
    run_rule: int
    custom_run_days: Optional[List[str]]
    station_num: int
    total_mileage: float
    is_canceled: int

# ------------------------------ 时刻表相关（关联运行计划） ------------------------------
class TrainScheduleCreate(BaseModel):
    operation_id: int = Field(description="关联运行计划ID")
    station_name: str = Field(description="途经站名称")
    sequence: int = Field(ge=1, description="途经顺序（1=出发站，递增）")
    arrive_day_diff: int = Field(ge=0, default=0, description="到达时间距发车的天数差（跨天填1）")
    arrival_time: Optional[time] = Field(None, description="到站时间（出发站为NULL）")
    departure_time: Optional[time] = Field(None, description="发车时间（到达站为NULL）")
    stop_duration: int = Field(ge=0, default=0, description="停留时长（分钟）")
    accumulated_mileage: float = Field(ge=0, description="累计里程（公里）")
    running_time: time = Field(description="累计运行时间（格式：HH:MM）")
    is_departure: int = Field(ge=0, le=1, default=0, description="是否出发站（1=是）")
    is_arrival: int = Field(ge=0, le=1, default=0, description="是否到达站（1=是）")

class TrainScheduleRead(BaseSchema):
    schedule_id: int
    operation_id: int
    operation_plan: TrainOperationPlanRead  # 关联运行计划（可选，按需返回）
    station_name: str
    station: StationRead  # 关联途经站详情
    sequence: int
    arrive_day_diff: int
    arrival_time: Optional[time]
    departure_time: Optional[time]
    stop_duration: int
    accumulated_mileage: float
    running_time: time
    is_departure: int
    is_arrival: int

# ------------------------------ 组合响应模型（适配查询需求） ------------------------------
class TrainOperationPlanWithSchedulesRead(TrainOperationPlanRead):
    """包含时刻表的运行计划（核心查询响应模型）"""
    schedules: List[TrainScheduleRead] = Field(description="该版本对应的途经站点时刻表")

class TrainWithOperationPlansRead(TrainRead):
    """包含所有运行计划的车次信息（用于车次详情查询）"""
    operation_plans: List[TrainOperationPlanWithSchedulesRead] = Field(description="车次的所有运行计划版本")