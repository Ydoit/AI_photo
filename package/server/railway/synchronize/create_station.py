#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/20 19:59
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-create_station.py
@Description : 车站数据批量+多线程插入优化
"""

import csv
import threading
from typing import Tuple, Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import requests
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from railway.db.models.models import Station
from railway.schemas import StationCreate
from railway.db.dependencies import get_db

# ------------------------------ 配置项（可根据实际调整）------------------------------
CSV_CITY_PATH = "../data/city.csv"  # 城市-省份映射CSV路径
CSV_STATION_PATH = "../data/station_name.csv"  # 车站数据CSV路径
BATCH_SIZE = 1000  # 每批插入条数（建议1000-5000，根据数据库性能调整）
MAX_WORKERS = 4  # 多线程最大并发数（建议=CPU核心数，避免数据库压力过大）


# ------------------------------ 工具函数（保留原逻辑，优化CSV读取）------------------------------
def build_city_province_map(csv_path: str) -> dict:
    """构建「城市/区县→省份」映射字典（优化CSV读取稳定性）"""
    city_province_map = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            # 用csv.reader处理，兼容逗号/制表符分隔，避免手动split出错
            reader = csv.reader(f, dialect="excel-tab")  # 优先按制表符分割
            lines = list(reader)
            if len(lines) < 2:
                raise ValueError("CSV文件无有效数据（需包含表头+至少1行数据）")

            # 处理每一行（跳过表头）
            for line_num, fields in enumerate(lines[1:], start=2):
                fields = [field.strip() for field in fields]
                if len(fields) < 3:
                    print(f"⚠️  第{line_num}行格式错误（字段不足3个），跳过：{fields}")
                    continue

                province, city, district = fields[0], fields[1], fields[2]
                if not province or not city:
                    print(f"⚠️  第{line_num}行存在空值，跳过：{fields}")
                    continue

                # 城市→省份映射
                city_province_map[city] = province
                # 区县→省份映射（简化区县名，避免过长）
                if district and len(district) > 4:
                    district = district[:2]
                if district:
                    city_province_map[district] = province

        print(f"✅ 城市-省份映射构建完成，共包含 {len(city_province_map)} 个地区")
        return city_province_map
    except FileNotFoundError:
        raise FileNotFoundError(f"未找到城市CSV文件：{csv_path}")
    except Exception as e:
        raise Exception(f"读取城市CSV失败：{str(e)}")


def get_province_by_city(city: str, city_province_map: dict) -> str:
    """根据城市名查询省份（复用原逻辑）"""
    city_clean = city.strip()
    # 尝试匹配不同后缀的城市名
    suffixes = ['', '市', '地区', '盟', '县', '区', '自治县', '自治州']
    for suffix in suffixes:
        key = city_clean + suffix
        if key in city_province_map:
            return city_province_map[key]
    return ""


# ------------------------------ 数据加载函数（批量读取车站数据）------------------------------
def load_station_data(city_province_map: dict) -> List[Station]:
    """批量读取车站CSV，转换为Station对象列表（去重+数据校验）"""
    station_list: List[Station] = []
    station_names = set()  # 用于内存去重（避免同一CSV内重复）

    try:
        with open(CSV_STATION_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            for line_num, parts in enumerate(reader, start=2):
                parts = [part.strip() for part in parts]
                # 校验CSV字段数量（确保至少有8个字段，对应station[7]是城市）
                if len(parts) < 8:
                    print(f"⚠️  车站CSV第{line_num}行格式错误（字段不足），跳过：{parts}")
                    continue

                # 提取车站数据（按原逻辑对应字段）
                station_name = parts[1]
                telecode = parts[2]
                station_pinyin = parts[3]
                station_py = parts[4]
                city = parts[7]

                # 内存去重（同一文件内重复的车站直接跳过）
                if station_name in station_names:
                    continue
                station_names.add(station_name)

                # 构建Station对象
                station = Station(
                    station_name=station_name,
                    station_pinyin=station_pinyin,
                    station_py=station_py,
                    province=get_province_by_city(city, city_province_map),
                    city=city,
                    district="",
                    telecode=telecode,
                    is_high_speed=0,
                    status=1
                )
                station_list.append(station)

        print(f"✅ 车站数据加载完成，共读取 {len(station_list)} 条不重复数据")
        return station_list
    except FileNotFoundError:
        raise FileNotFoundError(f"未找到车站CSV文件：{CSV_STATION_PATH}")
    except Exception as e:
        raise Exception(f"读取车站CSV失败：{str(e)}")


# ------------------------------ 批量插入核心函数 ------------------------------
def batch_insert_stations(db: Session, stations: List[Station]) -> Tuple[int, str]:
    """
    单批次插入车站数据
    :param db: 数据库会话
    :param stations: 单批次车站对象列表
    :return: (成功插入条数, 状态信息)
    """
    if not stations:
        return 0, "批次无有效数据"

    # 批量查询已存在的车站名称（避免插入重复数据）
    station_names = [s.station_name for s in stations]
    existing_names = db.query(Station.station_name).filter(Station.station_name.in_(station_names)).all()
    existing_names = set([name[0] for name in existing_names])  # 转为集合，快速判断

    # 过滤已存在的数据
    to_insert = [s for s in stations if s.station_name not in existing_names]
    if not to_insert:
        return 0, f"批次内 {len(existing_names)} 条数据已存在，无新数据插入"

    try:
        # 批量插入（bulk_save_objects 效率远高于单条add）
        db.bulk_save_objects(to_insert)
        db.commit()
        return len(to_insert), f"成功插入 {len(to_insert)} 条数据（批次总条数：{len(stations)}）"
    except IntegrityError as e:
        db.rollback()
        return 0, f"批次插入失败（约束冲突）：{str(e.orig)[:100]}"  # 截取错误信息，避免过长
    except SQLAlchemyError as e:
        db.rollback()
        return 0, f"批次插入失败（数据库错误）：{str(e)[:100]}"
    except Exception as e:
        db.rollback()
        return 0, f"批次插入失败：{str(e)[:100]}"


# ------------------------------ 多线程分批处理函数 ------------------------------
def multi_thread_batch_insert(station_list: List[Station]):
    """多线程分批插入（将总数据分成多批，并行处理）"""
    # 分割数据为多个批次
    batches = [
        station_list[i:i + BATCH_SIZE] for i in range(0, len(station_list), BATCH_SIZE)
    ]
    print(f"📦 共分割为 {len(batches)} 个批次，每批最多 {BATCH_SIZE} 条数据")

    total_success = 0  # 总成功插入条数
    # 用线程池执行多批次插入
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有批次任务
        future_to_batch = {
            executor.submit(
                batch_insert_stations,
                next(get_db()),  # 每个线程用独立的数据库会话
                batch
            ): batch for batch in batches
        }

        # 处理任务结果
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                success_cnt, msg = future.result()
                total_success += success_cnt
                print(f"✅ 批次处理完成：{msg}")
            except Exception as e:
                print(f"❌ 批次处理失败（数据范围：{batch[0].station_name}~{batch[-1].station_name}）：{str(e)}")

    print(f"\n🎉 所有批次处理完成！总成功插入：{total_success} 条车站数据")


# ------------------------------ 单线程批量插入（备选，适用于小数据量）------------------------------
def single_thread_batch_insert(station_list: List[Station]):
    """单线程分批插入（简单稳定，无需多线程开销）"""
    db = next(get_db())
    batches = [station_list[i:i + BATCH_SIZE] for i in range(0, len(station_list), BATCH_SIZE)]
    total_success = 0

    for batch_idx, batch in enumerate(batches, start=1):
        success_cnt, msg = batch_insert_stations(db, batch)
        total_success += success_cnt
        print(f"📄 第 {batch_idx}/{len(batches)} 批次：{msg}")

    print(f"\n🎉 单线程批量插入完成！总成功插入：{total_success} 条车站数据")


# ------------------------------ 主函数（入口）------------------------------
if __name__ == "__main__":
    try:
        # 1. 构建城市-省份映射
        city_province_map = build_city_province_map(CSV_CITY_PATH)

        # 2. 批量加载车站数据（去重+校验）
        station_list = load_station_data(city_province_map)

        # 3. 选择插入方式（二选一）
        # 方案A：多线程批量插入（推荐，数据量>1万条时用）
        # multi_thread_batch_insert(station_list)

        # 方案B：单线程批量插入（数据量<1万条时用，更稳定）
        single_thread_batch_insert(station_list)

    except Exception as e:
        print(f"\n❌ 程序执行失败：{str(e)}")