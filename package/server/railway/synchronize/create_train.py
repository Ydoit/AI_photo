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
from typing import Tuple, Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import requests
from sqlalchemy import tuple_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from railway.db.models.models import Station, Train
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


# ------------------------------ 批量插入核心函数（支持跳过失败数据） ------------------------------
def batch_insert_trains(db: Session, trains: List[Train]) -> Tuple[int, int, List[Dict]]:
    """
    批量插入车次数据，跳过违反约束的记录，返回成功数、失败数、失败详情
    :param db: 数据库会话
    :param trains: 待插入的Train对象列表
    :return: (成功插入数, 失败数, 失败详情列表)
    """
    if not trains:
        return 0, 0, [{"reason": "批次无有效数据"}]

    # 1. 双重去重：先过滤列表内部重复（train_no+train_code）
    insert_combinations = [(train.train_no, train.train_code) for train in trains]
    unique_map = {}  # 用字典去重，保留最后一个重复项（可根据需求调整为保留第一个）
    for train in trains:
        key = (train.train_no, train.train_code)
        unique_map[key] = train
    unique_trains = list(unique_map.values())  # 去重后的待插入列表

    # 2. 过滤数据库中已存在的记录（避免重复插入约束冲突）
    unique_combinations = list(unique_map.keys())
    existing_trains = db.query(Train.train_no, Train.train_code).filter(
        tuple_(Train.train_no, Train.train_code).in_(unique_combinations)
    ).all()
    existing_set = set(existing_trains)
    new_trains = [
        train for train in unique_trains
        if (train.train_no, train.train_code) not in existing_set
    ]

    if not new_trains:
        return 0, 0, [{"reason": "所有数据均已存在或内部重复，无需插入"}]

    # 3. 逐个插入+重试，跳过失败数据
    success_count = 0
    fail_count = 0
    fail_details = []

    for train in new_trains:
        try:
            db.add(train)
            db.commit()  # 单条提交，失败仅影响当前记录
            db.refresh(train)  # 可选：刷新对象获取自增ID等默认值
            success_count += 1
        except SQLAlchemyError as e:
            db.rollback()  # 回滚当前单条记录的插入操作
            fail_count += 1
            # 记录失败详情：包含关键标识+错误原因（截取前150字符避免过长）
            fail_details.append({
                "train_no": train.train_no,
                "train_code": train.train_code,
                "reason": str(e)[:150]
            })
        except Exception as e:
            db.rollback()
            fail_count += 1
            fail_details.append({
                "train_no": train.train_no,
                "train_code": train.train_code,
                "reason": f"未知错误：{str(e)[:150]}"
            })

    # 4. 整理返回结果
    if not fail_details:
        fail_details = [{"reason": "无失败数据"}]
    return success_count, fail_count, fail_details


# ------------------------------ 多线程分批处理函数 ------------------------------
def multi_thread_batch_insert(train_list: List[Train]):
    """多线程分批插入（将总数据分成多批，并行处理）"""
    # 分割数据为多个批次
    batches = [
        train_list[i:i + BATCH_SIZE] for i in range(0, len(train_list), BATCH_SIZE)
    ]
    print(f"📦 共分割为 {len(batches)} 个批次，每批最多 {BATCH_SIZE} 条数据")

    total_success = 0  # 总成功插入条数
    # 用线程池执行多批次插入
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有批次任务
        future_to_batch = {
            executor.submit(
                batch_insert_trains,
                next(get_db()),  # 每个线程用独立的数据库会话
                batch
            ): batch for batch in batches
        }

        # 处理任务结果
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                success_cnt,fail_cnt, msg = future.result()
                total_success += success_cnt
                print(f"✅ 批次处理完成：{msg}")
            except Exception as e:
                print(f"❌ 批次处理失败（数据范围：{batch[0].station_name}~{batch[-1].station_name}）：{str(e)}")

    print(f"\n🎉 所有批次处理完成！总成功插入：{total_success} 条车站数据")


# ------------------------------ 单线程批量插入（备选，适用于小数据量）------------------------------
def single_thread_batch_insert(train_list: List[Train]):
    """单线程分批插入（简单稳定，无需多线程开销）"""
    db = next(get_db())
    batches = [train_list[i:i + BATCH_SIZE] for i in range(0, len(train_list), BATCH_SIZE)]
    total_success = 0

    for batch_idx, batch in enumerate(batches, start=1):
        success_cnt, fail_cnt, msg = batch_insert_trains(db, batch)
        total_success += success_cnt
        print(f"📄 第 {batch_idx}/{len(batches)} 批次：{msg}")

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
