#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/23 00:38
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-get_data.py
@Description : 
"""
import requests
import json
import time
import os
import logging
import random
from datetime import date, timedelta

from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Set, Tuple

from railway.synchronize.config import RETRY_TIMES, SEARCH_URL, TIMETABLE_URL, KM_URL

proxies = {
    # HTTP 请求走本地 HTTP 代理
    "http": "http://127.0.0.1:7890",
    # HTTPS 请求走本地 HTTPS 代理（多数代理工具统一端口，可与 HTTP 共用）
    "https": "http://127.0.0.1:7890"
}

with open('UA.txt', 'r', encoding='utf-8') as f:
    ua_list = f.readlines()

def get_random_user_agent():
    return random.choice(ua_list).strip()

def get_type_label(train_type: str) -> str:
    """获取列车类型的显示标签（空字符串→PU_SU=普速）"""
    return train_type if train_type else "PU_SU"

def create_request_session():
    """创建请求会话（添加重试机制+完善请求头）"""
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRY_TIMES,
        backoff_factor=1.5,  # 指数退避：1.5s → 3s → 6s
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "Referer": "https://kyfw.12306.cn/",
        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/141.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
        # 建议添加Cookie：登录12306后，从浏览器复制Cookie到这里，提高成功率
        # "Cookie": "你的12306 Cookie字符串"
    })
    return session

def create_km_request_session():
    """创建请求会话（添加重试机制+完善请求头）"""
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRY_TIMES,
        backoff_factor=1.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "Referer": "https://shike.gaotie.cn/checi.asp",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    })
    return session

session_12306 = create_request_session()
session_km = create_km_request_session()

def fetch_trains_by_keyword(train_type: str, train_date: str, keyword: str) -> List[Dict]:
    """
    获取单个类型+日期+关键词段的车次数据
    增强版：增加403专用多级退避机制
    """
    params = {
        "keyword": keyword,
        "date": train_date
    }

    max_forbidden_retry = 6          # 403 专用最大重试次数
    base_sleep = 5                   # 初始退避秒数
    multiplier = 2                   # 指数倍数（如 5 → 10 → 20 → 40）
    jitter = 0.3                     # 随机抖动（防止节奏固定被封）

    forbidden_retry_count = 0

    while True:
        try:
            session_12306.headers.update(
                {"User-Agent": get_random_user_agent()}
            )
            response = session_12306.get(SEARCH_URL, params=params, timeout=15, proxies=proxies)

            # 特殊处理 HTTP 403
            if response.status_code == 403:
                forbidden_retry_count += 1
                if forbidden_retry_count > max_forbidden_retry:
                    logging.error(
                        f"类型[{get_type_label(train_type)}] 日期[{train_date}] 关键词[{keyword}] "
                        f"403 连续失败 {max_forbidden_retry} 次，放弃此次请求"
                    )
                    return []

                # 计算退避时间
                sleep_time = base_sleep * (multiplier ** (forbidden_retry_count - 1))
                sleep_time = sleep_time * random.uniform(1 - jitter, 1 + jitter)

                logging.warning(
                    f"类型[{get_type_label(train_type)}] 日期[{train_date}] 关键词[{keyword}] "
                    f"返回 403，触发多级退避：第 {forbidden_retry_count}/{max_forbidden_retry} 次，"
                    f"暂停 {sleep_time:.1f} 秒后重试"
                )

                time.sleep(sleep_time)
                continue  # 重试请求

            # 正常处理其他 HTTP 状态
            response.raise_for_status()
            result = response.json()

            if not result.get("status"):
                logging.warning(
                    f"类型[{get_type_label(train_type)}] 日期[{train_date}] 关键词[{keyword}] "
                    f"请求失败：{result.get('errorMsg', '未知错误')}"
                )
                return []

            data = result.get("data", [])
            logging.info(
                f"类型[{get_type_label(train_type)}] 日期[{train_date}] 关键词[{keyword}] "
                f"获取成功，共 {len(data)} 条数据"
            )
            return data

        except requests.exceptions.RequestException as e:
            logging.error(
                f"类型[{get_type_label(train_type)}] 日期[{train_date}] 关键词[{keyword}] "
                f"请求异常：{str(e)}"
            )
            return []
    return []

def fetch_km_by_train_code(train_code: str) -> List[Dict]:
    """查询单个车次+日期的时刻表"""
    params = {
        "checi": train_code,
    }
    try:
        session_km.headers.update(
            {"User-Agent": get_random_user_agent()}
        )
        response = session_km.get(KM_URL, params=params, timeout=15, proxies=proxies)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        # 提取所有时刻表行
        schedule_rows = soup.find_all('ul', class_='shikebiao-content')
        train_schedule = []
        # 定义列名（与HTML中顺序对应）
        columns = ["站次", "途径车站", "到达时间", "停留", "开车时间", "天数", "运行时间", "里程", "二等/一等/商务座",
                   "二等卧上/中/下", "一等卧上/下"]
        for row in schedule_rows:
            # 提取当前行的所有单元格数据
            cells = row.find_all('li')
            row_data = {}
            for i, cell in enumerate(cells):
                # 去除空格和换行符，获取单元格文本
                cell_text = cell.get_text(strip=True)
                row_data[columns[i]] = cell_text
            train_schedule.append(row_data)
        return train_schedule
    except requests.exceptions.RequestException as e:
        logging.error(f"train_no[{train_code}] 请求异常：{str(e)}")
        return []

def fetch_schedules_by_train_no(train_no: str, train_date: str) -> Dict:
    """查询单个车次+日期的时刻表"""
    params = {
        "leftTicketDTO.train_no": train_no,
        "leftTicketDTO.train_date": train_date,
        "rand_code": ""
    }
    try:
        session_12306.headers.update(
            {"User-Agent": get_random_user_agent()}
        )
        response = session_12306.get(TIMETABLE_URL, params=params, timeout=15, proxies=proxies)
        response.raise_for_status()
        result = response.json()

        # 处理返回结果
        if not result.get("status"):
            logging.warning(
                f"train_no[{train_no}] 日期[{train_date}] 查询失败：{result.get('messages', ['未知错误'])[0]}")
            return {}

        timetable_data = result.get("data", {}).get("data", [])
        if not timetable_data:
            logging.warning(f"train_no[{train_no}] 日期[{train_date}] 未查询到时刻表数据")
            return {}
        train_schedule = fetch_km_by_train_code(timetable_data[0]['station_train_code'])
        if train_schedule and len(timetable_data) == len(train_schedule):
            for i in range(len(timetable_data)):
                timetable_data[i]['accumulated_mileage'] = train_schedule[i]['里程'].strip('km')
        logging.info(f"train_no[{train_no}] 日期[{train_date}] 查询成功，共{len(timetable_data)}个站点")
        return {
            "train_no": train_no,
            "train_date": train_date,
            "timetable": timetable_data,
            "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
    except Exception as e:
        logging.error(f"train_no[{train_no}] 日期[{train_date}] 请求异常：{str(e)}")
        return {
            "train_no": train_no,
            "train_date": train_date,
            "timetable": [],
            "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }