#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/23 00:34
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-main.py
@Description : 
"""
import logging
import time
import os
import traceback
from datetime import timedelta, date, datetime
import random
from typing import List, Dict

from sqlalchemy.dialects.mssql.information_schema import sequences

from railway.crud import get_station_single, create_train_operation_plan, create_train_schedule_batch, create_train
from railway.db.dependencies import get_db, init_db
from railway.schemas import StationSingleQuery, TrainOperationPlanCreate, TrainScheduleCreate, TrainScheduleBatchCreate, \
    TrainCreate
from railway.synchronize.get_data import get_type_label, fetch_trains_by_keyword, fetch_schedules_by_train_no
from railway.synchronize.config import KM_URL, TIMETABLE_URL, RETRY_TIMES, REQUEST_INTERVAL, LOG_FILE, TRAIN_TYPE, RECENT_DAYS

init_db()
db = next(get_db())

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

def calculate_accumulated_mileage(accumulated_mileage):
    try:
        return int(accumulated_mileage)
    except:
        return 0

def generate_date_list(recent_days: int) -> List[str]:
    """生成最近N天的日期列表（格式：YYYYMMDD）"""
    date_list = []
    today = date.today()
    for i in range(recent_days):
        target_date = today + timedelta(days=i)
        date_list.append(target_date.strftime("%Y%m%d"))
    return date_list

def load_task_status() -> Dict[str, List[Dict[str, str]]]:
    """加载任务状态（已完成的{类型, 日期, 关键词段}）"""
    pass

def save_task_status(status: Dict[str, List[Dict[str, str]]]):
    """保存任务状态到文件"""
    pass

def is_task_completed(status: Dict[str, List[Dict[str, str]]], train_type: str, train_date: str, keyword: str) -> bool:
    """判断任务（类型+日期+关键词段）是否已完成"""
    return False
    completed_tasks = status.get(train_type, [])
    return any(
        task["date"] == train_date and task["keyword"] == keyword
        for task in completed_tasks
    )

def mark_task_completed(status: Dict[str, List[Dict[str, str]]], train_type: str, train_date: str, keyword: str):
    """标记任务为已完成"""
    completed_tasks = status.get(train_type, [])
    # 避免重复添加
    if not is_task_completed(status, train_type, train_date, keyword):
        completed_tasks.append({
            "date": train_date,
            "keyword": keyword,
            "completed_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
        status[train_type] = completed_tasks
        save_task_status(status)

def random_sleep():
    # 任务间暂停（防反爬：随机1~REQUEST_INTERVAL秒，避免固定间隔被识别）
    random_sleep_time = random.uniform(1, REQUEST_INTERVAL)
    logging.info(f"随机暂停 {random_sleep_time:.1f} 秒...")
    time.sleep(random_sleep_time)


def collect_all_trains():
    """按「类型→日期→关键词段」采集所有车次，支持中断恢复"""
    # 1. 加载任务状态
    task_status = load_task_status()
    # 2. 生成日期列表
    date_list = generate_date_list(RECENT_DAYS)
    logging.info(f"\n===== 开始采集（支持中断恢复）=====")
    logging.info(f"采集日期范围：{date_list}（共{len(date_list)}天）")
    logging.info(f"列车类型数量：{len(TRAIN_TYPE)}种（含普速）")

    # 3. 遍历所有类型→日期→关键词段
    total_tasks = sum(len(keywords) * len(date_list) * 99 for keywords in TRAIN_TYPE)
    # completed_tasks = sum(len(tasks) for tasks in task_status.values())
    completed_tasks = 0
    logging.info(
        f"总任务数：{total_tasks} | 已完成任务数：{completed_tasks} | 待完成任务数：{total_tasks - completed_tasks}")

    current_task = completed_tasks + 1
    for train_type in TRAIN_TYPE:
        type_label = get_type_label(train_type)
        keywords = [f'{train_type}{i}' for i in range(1,100)]
        logging.info(f"\n===== 开始处理类型：{type_label}（关键词段数：{len(keywords)}）=====")
        for train_date in date_list:
            logging.info(f"\n----- 处理日期：{train_date} -----")
            for keyword in keywords:
                try:
                    # 跳过已完成的任务
                    if is_task_completed(task_status, train_type, train_date, keyword):
                        logging.info(
                            f"任务[{current_task}/{total_tasks}] 已完成，跳过："
                            f"类型[{type_label}] 日期[{train_date}] 关键词[{keyword}]"
                        )
                        current_task += 1
                        continue

                    # 执行当前任务：获取数据
                    logging.info(
                        f"任务[{current_task}/{total_tasks}] 开始处理："
                        f"类型[{type_label}] 日期[{train_date}] 关键词[{keyword}]"
                    )

                    trains_info = fetch_trains_by_keyword(train_type, train_date, keyword)

                    # 即时保存数据
                    if trains_info:
                        for train_info in trains_info:
                            try:
                                train_no = train_info["train_no"]
                                station_num = train_info["total_num"]
                                train_code = train_info["station_train_code"]

                                from_station_name = train_info["from_station"]
                                to_station_name = train_info["to_station"]
                                logging.info(f'开始处理 {train_info}')
                                code, msg, from_station = get_station_single(db,
                                                                             StationSingleQuery(
                                                                                 station_id=None,
                                                                                 telecode=None,
                                                                                 station_name=from_station_name
                                                                             ))
                                code, msg, to_station = get_station_single(db,
                                                                           StationSingleQuery(
                                                                               station_id=None,
                                                                               telecode=None,
                                                                               station_name=from_station_name
                                                                           ))
                                # todo 判断车站是否存在，如果不存在则插入一条新车站
                                schedules_data = fetch_schedules_by_train_no(train_no, f"{train_date[:4]}-{train_date[4:6]}-{train_date[6:8]}")
                                random_sleep()
                                schedules_info = schedules_data['timetable']
                                plan = TrainOperationPlanCreate(
                                    train_no=train_no,
                                    start_date=datetime.fromisoformat(train_date),
                                    end_date=None,
                                    station_num=station_num,
                                    custom_run_days=None,
                                    run_rule=0
                                )
                                schedule_list = []
                                train_code_set = {train_code}
                                if schedules_info:
                                    for index, schedule_info in enumerate(schedules_info):
                                        code, msg, station = get_station_single(db,
                                                                     StationSingleQuery(
                                                                         station_id=None,
                                                                         telecode=None,
                                                                         station_name=schedule_info["station_name"]
                                                                     ))
                                        schedule = TrainScheduleCreate(
                                            train_no = train_no,
                                            train_code = schedule_info["station_train_code"],
                                            station_telecode = station.telecode,
                                            station_name=station.station_name,
                                            sequence = int(schedule_info["station_no"]),
                                            arrive_day_diff=int(schedule_info["arrive_day_diff"]),
                                            arrival_time=schedule_info["start_time"] if schedule_info["arrive_time"] == "----" else schedule_info[
                                                "arrive_time"],
                                            departure_time=schedule_info["start_time"],
                                            stop_duration=calculate_stop_duration(schedule_info["arrive_time"], schedule_info["start_time"]),
                                            accumulated_mileage=calculate_accumulated_mileage(
                                                schedule_info.get("accumulated_mileage", "0")),
                                            running_time=time_to_minutes(schedule_info["running_time"]),
                                            is_departure=int(index == 0),
                                            is_arrival=int(index == len(schedules_info) - 1),
                                        )
                                        train_code_set.add(schedule.train_code)
                                        schedule_list.append(schedule)
                                    plan.total_running_time = schedule_list[-1].running_time
                                    plan.total_mileage = schedule_list[-1].accumulated_mileage
                                code,msg,plan0=create_train_operation_plan(db, plan)
                                logging.info(f'{msg} {trains_info}')
                                if schedule_list:
                                    code,msg,d = create_train_schedule_batch(db, TrainScheduleBatchCreate(schedules=schedule_list))
                                    logging.info(f'{msg} {schedules_info}')
                                for train_code_ in train_code_set:
                                    train = TrainCreate(
                                        train_no=train_no,
                                        train_code=train_code_,
                                        train_type=train_type,
                                        from_station=from_station.telecode,
                                        to_station=to_station.telecode
                                    )
                                    code,msg,train_read = create_train(db ,train)
                                    # pydantic的BaseModel输出
                                    logging.info(f'{msg} {train_code}')
                            except:
                                logging.error(traceback.format_exc())
                    random_sleep()
                    current_task += 1
                    current_task += 1
                except:
                    logging.error(traceback.format_exc())
        logging.info(f"----- 日期[{train_date}] 处理完成 -----")

    logging.info(f"\n===== 所有任务处理完毕（累计完成{sum(len(tasks) for tasks in task_status.values())}个任务）=====")

def main():
    logging.info("===== 12306车次数据采集程序启动 =====")
    # 1. 创建请求会话

    try:
        # 2. 开始采集（支持中断恢复）
        collect_all_trains()
    except KeyboardInterrupt:
        logging.warning("\n===== 程序被手动中断！下次启动将从中断处继续 =====")
    except Exception as e:
        logging.error(f"\n===== 程序异常中断：{str(e)} =====", exc_info=True)
    finally:
        logging.info("===== 程序退出 =====")


if __name__ == '__main__':
    main()
