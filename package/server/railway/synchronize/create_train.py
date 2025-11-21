#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/20 20:27
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-create_train.py
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

from railway.db.models.models import Station, Train, TrainOperationPlan
from railway.schemas import StationCreate
from railway.db.dependencies import get_db

# ------------------------------ 配置项（可根据实际调整）------------------------------
TRAIN_TYPE = ['G','D','Z','K','T','Y','C','S']
data_dir = '../test_sync_data/train_data'
BATCH_SIZE = 1000  # 每批插入条数（建议1000-5000，根据数据库性能调整）
MAX_WORKERS = 4  # 多线程最大并发数（建议=CPU核心数，避免数据库压力过大）

# 将20251118 转成 2025-11-18
def format_date(date_str):
    """格式化日期字符串"""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

def format_station_name(station_name: str):
    """格式化车站名称（去除空格）"""
    return station_name.strip().replace(' ', '')

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



def bulk_insert_operation_plans(db: Session, trains: List[Train]) -> int:
    """
    批量插入 TrainOperationPlan（无重复、无约束冲突）
    :return: 实际成功插入数量
    """
    if not trains:
        return 0

    # 1. 去重（train_no）
    train_no_set = {(t.train_no,) for t in trains}

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
            start_date= format_date("20251120")
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
def single_thread_batch_insert(train_list: List[Train]):
    """单线程分批插入（简单稳定，无需多线程开销）"""
    db = next(get_db())
    batches = [train_list[i:i + BATCH_SIZE] for i in range(0, len(train_list), BATCH_SIZE)]
    total_success = 0

    for batch_idx, batch in enumerate(batches, start=1):
        bulk_insert_operation_plans(db,batch)
        success_cnt= bulk_insert_trains(db, batch)
        total_success += success_cnt
        print(f"📄 第 {batch_idx}/{len(batches)}")

    print(f"\n🎉 单线程批量插入完成！总成功插入：{total_success} 条车站数据")


# ------------------------------ 主函数（入口）------------------------------
if __name__ == "__main__":
    try:
        train_list = load_train_data()
        # 3. 选择插入方式（二选一）
        # 方案A：多线程批量插入（推荐，数据量>1万条时用）
        # multi_thread_batch_insert(station_list)

        # 方案B：单线程批量插入（数据量<1万条时用，更稳定）
        single_thread_batch_insert(train_list)

    except Exception as e:
        print(traceback.format_exc())
        print(f"\n❌ 程序执行失败：{str(e)}")
