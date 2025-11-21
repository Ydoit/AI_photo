#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/20 23:06
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-create_schedule.py
@Description : 
"""

import csv
import json
import os
import threading
import traceback
from datetime import datetime
from typing import Tuple, Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import requests
from sqlalchemy import tuple_, insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from railway.db.models.models import Station, Train, TrainOperationPlan, TrainSchedule
from railway.schemas import StationCreate
from railway.db.dependencies import get_db

# ------------------------------ 配置项（可根据实际调整）------------------------------
TRAIN_TYPE = ['G','D','Z','K','T','Y','C','S']
data_dir = '../test_sync_data/train_data'
train_list_file = '../test_sync_data/train_timetable/timetable_20251120.json'
BATCH_SIZE = 1000  # 每批插入条数（建议1000-5000，根据数据库性能调整）
MAX_WORKERS = 4  # 多线程最大并发数（建议=CPU核心数，避免数据库压力过大）

# 将20251118 转成 2025-11-18
def format_date(date_str):
    """格式化日期字符串"""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

def format_station_name(station_name: str):
    """格式化车站名称（去除空格）"""
    return station_name.strip().replace(' ', '')

def time_to_minutes(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours*60+minutes

# 计算停留时间考虑跨夜情况 23:59 -> 00:10 (+11分钟)
def calculate_stop_duration(arrival_time, departure_time):
    if arrival_time == '----':
        return 0
    # 停留时间计算逻辑
    arr_hours, arr_minutes = map(int, arrival_time.split(':'))
    dep_hours, dep_minutes = map(int, departure_time.split(':'))
    arr_total_minutes = arr_hours * 60 + arr_minutes
    dep_total_minutes = dep_hours * 60 + dep_minutes
    if dep_total_minutes < arr_total_minutes:
        dep_total_minutes += 24 * 60  # 跨夜处理
    duration = dep_total_minutes - arr_total_minutes
    return duration if duration >= 0 else 0

# ------------------------------ 数据加载函数（批量读取车站数据）------------------------------
def load_train_data() -> List[Train]:
    """批量读取车站CSV，转换为Station对象列表（去重+数据校验）"""
    train_list: List[Train] = []
    train_no_code = set()  # 用于内存去重（避免同一CSV内重复）

    # 2. 批量加载车站数据（去重+校验）
    for train_type in TRAIN_TYPE:
        train_list_file = f'{data_dir}/train_list_{train_type}.json'

        # 检查文件是否存在
        if not os.path.exists(train_list_file):
            print(f"⚠️ {train_list_file} 文件不存在，跳过该类型列车")
            continue

        # 读取列车数据文件（同步读取，文件IO异步收益不大）
        try:
            with open(train_list_file, "r", encoding="utf-8") as f:
                train_list_dic = json.loads(f.read())
            print(f"📊 读取到 {train_type} 字头列车 {len(train_list)} 辆")

            # 构建所有创建列车的异步任务
            for train_info in train_list_dic:
                if (train_info["train_no"],train_info["station_train_code"]) in train_no_code:
                    continue
                train_data = Train(
                    train_no = train_info["train_no"],
                    train_code = train_info["station_train_code"],
                    train_type = train_info["station_train_code"][0],
                    from_station = format_station_name(train_info["from_station"]),
                    to_station = format_station_name(train_info["to_station"]),
                )
                train_no_code.add((train_info["train_no"],train_info["station_train_code"]))
                train_list.append(train_data)
        except Exception as e:
            raise Exception(f"读取车次失败：{str(e)}")
    print(f"✅ 车站数据加载完成，共读取 {len(train_list)} 条不重复数据")
    return train_list

def calculate_accumulated_mileage(accumulated_mileage):
    try:
        return int(accumulated_mileage)
    except:
        return 0

def load_schedule_data() -> List[TrainSchedule]:
    """批量读取车站CSV，转换为Station对象列表（去重+数据校验）"""
    train_no_set = set()  # 用于内存去重（避免同一CSV内重复）
    schedule_list: List[TrainSchedule] = []
    plan_dic = {}
    # 2. 批量加载车站数据（去重+校验）
    # 检查文件是否存在
    if not os.path.exists(train_list_file):
        print(f"⚠️ {train_list_file} 文件不存在，跳过该类型列车")

    # 读取列车数据文件（同步读取，文件IO异步收益不大）
    try:
        with open(train_list_file, "r", encoding="utf-8") as f:
            train_list_dic = json.loads(f.read())
        print(f"📊 读取到列车 {len(train_list_dic)} 辆")

        # 构建所有创建列车的异步任务
        for train_info in train_list_dic:
            train_no = train_info["train_no"]
            timetable = train_info["timetable"]
            if train_no in train_no_set:
                continue
            plan_dic[train_no]={
                "total_running_time":0,
                "total_mileage":0,
                "station_num":2
            }
            for index, item in enumerate(timetable):
                schedule = TrainSchedule(
                    train_no = train_no,
                    train_code = item["station_train_code"],
                    station_name = format_station_name(item["station_name"]),
                    sequence = int(item["station_no"]),
                    arrive_day_diff = int(item["arrive_day_diff"]),
                    arrival_time = item["start_time"] if item["arrive_time"] == "----" else item["arrive_time"],
                    departure_time = item["start_time"],
                    stop_duration = calculate_stop_duration(item["arrive_time"], item["start_time"]),
                    accumulated_mileage = calculate_accumulated_mileage(item.get("accumulated_mileage","0")),
                    running_time = time_to_minutes(item["running_time"]),
                    is_departure = int(index==0),
                    is_arrival = int(index==len(timetable)-1),
                )
                schedule_list.append(schedule)
            plan_dic[train_no]["total_running_time"] = schedule_list[-1].running_time
            plan_dic[train_no]["total_mileage"] = schedule_list[-1].accumulated_mileage
            plan_dic[train_no]["station_num"] = len(timetable)
    except Exception as e:
        print(traceback.format_exc())
        raise Exception(f"读取车次失败：{str(e)}")
    print(f"✅ 时刻表数据加载完成，共读取 {len(schedule_list)} 条不重复数据")
    return schedule_list,plan_dic

def bulk_insert_trains(db: Session, trains: List[Train]) -> int:
    """
    批量插入 Train 表，插入前自动去重 → 去除数据库已存在数据。
    :return: 实际插入数量
    """

    if not trains:
        return 0

    # 1. 内部去重（train_no + train_code）
    unique_map = {(t.train_no, t.train_code): t for t in trains}
    unique_trains = list(unique_map.values())

    keys = list(unique_map.keys())

    # 2. 查询数据库中已存在的记录
    existing_keys = set(
        db.query(Train.train_no, Train.train_code)
        .filter(tuple_(Train.train_no, Train.train_code).in_(keys))
        .all()
    )

    stations = db.query(Station.station_name,Station.telecode).all()

    stations_dic = {station.station_name:station.telecode for station in stations}

    for t in unique_trains:
        if t.from_station in stations_dic and t.to_station in stations_dic:
            t.from_station = stations_dic[t.from_station]
            t.to_station = stations_dic[t.to_station]

    # 3. 过滤出真正需要插入的数据
    new_train_objs = [
        t for t in unique_trains
        if (t.train_no, t.train_code) not in existing_keys
    ]

    if not new_train_objs:
        return 0

    # 5. 批量插入
    db.bulk_save_objects(new_train_objs)
    db.commit()

    return len(new_train_objs)

def bulk_insert_schedules(
    db: Session,
    schedules: List[TrainSchedule],
    batch_size: int = 1000  # 批次大小，默认100条
) -> Tuple[int, List[Dict]]:
    """
    批量插入 TrainSchedule 表：
    1. 先按 batch_size 条一批批量插入（高效）
    2. 若某批失败，拆分为单条逐个插入（跳过错误数据）
    3. 自动去重 + 跳过外键冲突/完整性约束错误数据
    :param db: 数据库会话
    :param schedules: 待插入的 TrainSchedule 对象列表
    :param batch_size: 批次大小（默认100条）
    :return: (总成功插入数, 失败详情列表)
    """
    if not schedules:
        return 0, [{"stage": "预处理", "reason": "无有效待插入数据"}]

    # ------------------------------ 1. 预处理：去重（内部去重 + 数据库筛重） ------------------------------
    # 1.1 内部去重：按 (train_no + station_name) 去重（保留最后一个重复项）
    unique_map = {(s.train_no, s.station_name): s for s in schedules}
    unique_schedules = list(unique_map.values())
    stations = db.query(Station.station_name, Station.telecode).all()

    stations_dic = {station.station_name: station.telecode for station in stations}

    for s in unique_schedules:
        if s.station_name in stations_dic:
            s.station_telecode = stations_dic[s.station_name]
    # 1.2 数据库筛重：过滤已存在的记录，避免重复插入冲突
    existing_keys = set(
        db.query(TrainSchedule.train_no, TrainSchedule.station_name)
        .all()
    )
    new_schedules = [
        s for s in unique_schedules
        if (s.train_no, s.station_name) not in existing_keys
    ]

    if not new_schedules:
        return 0, [{"stage": "预处理", "reason": "所有数据均已存在或内部重复，无需插入"}]

    # ------------------------------ 2. 拆分批次（按 batch_size 拆分） ------------------------------
    batches = [
        new_schedules[i:i + batch_size]
        for i in range(0, len(new_schedules), batch_size)
    ]
    total_batches = len(batches)
    total_success = 0
    fail_details = []

    # ------------------------------ 3. 批量插入 + 批次失败兜底 ------------------------------
    for batch_idx, batch in enumerate(batches, 1):
        batch_name = f"第{batch_idx}/{total_batches}批（{len(batch)}条）"
        try:
            # ------------------------------ 3.1 尝试批量插入当前批次 ------------------------------
            db.bulk_save_objects(batch)
            db.commit()
            # 批量插入成功，统计数量
            batch_success = len(batch)
            total_success += batch_success
            fail_details.append({
                "stage": batch_name,
                "reason": f"批量插入成功，成功{batch_success}条"
            })
        except SQLAlchemyError as e:
            # ------------------------------ 3.2 批量插入失败，拆分为单条逐个插入（兜底） ------------------------------
            db.rollback()  # 回滚当前批次的批量插入操作
            fail_details.append({
                "stage": batch_name,
                "reason": f"批量插入失败，触发单条兜底插入：{str(e)[:100]}"
            })

            # 单条插入当前批次的每条数据（用保存点隔离失败）
            for idx, schedule in enumerate(batch, 1):
                item_name = f"{batch_name}-第{idx}条（train_no={schedule.train_no}, station_name={schedule.station_name}）"
                savepoint = db.begin_nested()  # 创建保存点，隔离单条数据
                try:
                    db.add(schedule)
                    savepoint.commit()  # 提交单条数据
                    total_success += 1
                    fail_details.append({
                        "stage": item_name,
                        "reason": "单条插入成功"
                    })
                except IntegrityError as ie:
                    # 捕获完整性约束异常（外键冲突、唯一约束等）
                    savepoint.rollback()
                    pg_code = ie.orig.pgcode  # PostgreSQL 原生错误码
                    error_type = ""
                    if pg_code == "23503":
                        error_type = "外键依赖冲突"
                    elif pg_code == "23505":
                        error_type = "唯一约束冲突"
                    elif pg_code == "23502":
                        error_type = "非空约束冲突"
                    else:
                        error_type = "完整性约束异常"

                    fail_details.append({
                        "stage": item_name,
                        "reason": f"{error_type}：{str(ie.orig).split('Detail:')[0].strip()}",
                        "error_code": pg_code,
                        "status": "跳过"
                    })
                except SQLAlchemyError as se:
                    # 其他数据库异常（字段类型不匹配、长度超限等）
                    savepoint.rollback()
                    fail_details.append({
                        "stage": item_name,
                        "reason": f"数据库异常：{str(se)[:150]}",
                        "error_code": None,
                        "status": "跳过"
                    })
                except Exception as ex:
                    # 非数据库异常（代码逻辑错误等）
                    savepoint.rollback()
                    fail_details.append({
                        "stage": item_name,
                        "reason": f"未知异常：{str(ex)[:150]}",
                        "error_code": None,
                        "status": "跳过"
                    })

            # 单条插入完成后，统一提交当前批次的成功数据
            db.commit()

    # ------------------------------ 4. 整理结果 ------------------------------
    # 过滤掉「成功」的详情（仅保留失败/批次说明），让结果更清晰
    final_fail_details = [
        detail for detail in fail_details
        if "成功" not in detail.get("reason", "") or "批量插入成功" in detail.get("reason", "")
    ]

    if not final_fail_details:
        final_fail_details = [{"stage": "全部批次", "reason": "所有数据插入成功，无失败记录"}]

    return total_success, final_fail_details

def bulk_insert_operation_plans(db: Session, trains: List[Train], schedule_list: List[TrainSchedule], plan_dic) -> int:
    """
    批量插入 TrainOperationPlan（无重复、无约束冲突）
    :return: 实际成功插入数量
    """
    if not trains:
        return 0

    # 1. 去重（train_no）
    train_no_set = {(t.train_no,) for t in trains}
    schedule_train_no_set = {(s.train_no,) for s in schedule_list}
    train_no_set = train_no_set.union(schedule_train_no_set)

    # 2. 查询数据库中已存在的计划
    existing_train_nos = set(
        db.query(TrainOperationPlan.train_no)
        .filter(TrainOperationPlan.train_no.in_(train_no_set))
        .all()
    )
    # print(existing_train_nos)
    # 3. 过滤新数据
    new_train_nos = train_no_set - existing_train_nos
    # 4. 构建插入列表
    new_plans = [
        TrainOperationPlan(
            train_no = tn[0],
            start_date= format_date("20251120"),
            **plan_dic.get(tn[0],{})
        )
        for tn in new_train_nos
    ]
    if not new_train_nos:
        return 0

    # 5. 批量插入（一次性，无失败风险）
    db.bulk_save_objects(new_plans)
    db.commit()

    return len(new_train_nos)

# ------------------------------ 单线程批量插入（备选，适用于小数据量）------------------------------
def single_thread_batch_insert(train_list: List[Train], schedule_list: List[TrainSchedule], plan_dic):
    """单线程分批插入（简单稳定，无需多线程开销）"""
    db = next(get_db())
    batches = [train_list[i:i + BATCH_SIZE] for i in range(0, len(train_list), BATCH_SIZE)]
    total_success = 0

    bulk_insert_operation_plans(db, train_list, schedule_list, plan_dic)
    for batch_idx, batch in enumerate(batches, start=1):
        success_cnt = bulk_insert_trains(db, batch)
        total_success += success_cnt
        print(f"📄 第 {batch_idx}/{len(batches)}")
    bulk_insert_schedules(db, schedule_list)
    print(f"\n🎉 单线程批量插入完成！总成功插入：{total_success} 条车站数据")


# ------------------------------ 主函数（入口）------------------------------
if __name__ == "__main__":
    try:
        train_list = load_train_data()
        schedule_list, plan_dic = load_schedule_data()
        # 3. 选择插入方式（二选一）
        # 方案A：多线程批量插入（推荐，数据量>1万条时用）
        # multi_thread_batch_insert(station_list)

        # 方案B：单线程批量插入（数据量<1万条时用，更稳定）
        single_thread_batch_insert(train_list, schedule_list, plan_dic)

    except Exception as e:
        print(traceback.format_exc())
        print(f"\n❌ 程序执行失败：{str(e)}")
