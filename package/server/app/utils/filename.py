#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/12/10 22:26
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-filename.py
@Description : 
"""

import re
from datetime import datetime

start_time = datetime(1970, 1, 1, 0, 0, 0)
end_time = datetime(2045, 1, 1, 0, 0, 0)


def is_within_range(dt, start, end):
    """
    检查给定时间是否在指定范围内
    :param dt: 要检查的时间 (datetime 对象)
    :param start: 范围起始时间 (datetime 对象)
    :param end: 范围结束时间 (datetime 对象)
    :return: 布尔值，True 表示在范围内，False 表示不在范围内
    """
    return start <= dt <= end


def valid_time(dt):
    if start_time <= dt <= datetime.now():
        return dt
    else:
        return None

def _extract_datetime_from_filename(filename)-> datetime | None:
    # 定义正则表达式，匹配常见的时间格式
    patterns = [
        r"(\d{4})[ _\.-](\d{2})[ _\.-](\d{2})[ _\.-](\d{2})[ _\.-](\d{2})[ _\.-](\d{2})",  # 格式：YYYY_MM_DD_HH-MM-SS
        r"(\d{4})[ _\.-](\d{2})[ _\.-](\d{2})[ _\.-](\d{6})",  # 格式：YYYY-MM-DD_HHMMSS YYYY-MM-DD HHMMSS
        r"(\d{2})[ _\.-](\d{2})[ _\.-](\d{4})[ _\.-](\d{6})",  # 格式：DD-MM-YYYY_HHMMSS
        r"(\d{8})[ _\.-](\d{2})[ _\.-](\d{2})[ _\.-](\d{2})",  # 格式：YYYYMMDD_HH-MM-SS
        r"(\d{8})[ _T\.-](\d{6})",  # 格式：YYYYMMDD_HHMMSS
        r"(\d{14})",  # 格式：YYYYMMDDHHMMSS
        r"(\d{13}|\d{10})",  # 格式：TIMESTAMP (13位毫秒级时间戳)
    ]
    try:
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                # 根据匹配的模式提取日期和时间
                if len(match.groups()) == 2:  # 格式：YYYYMMDD_HHMMSS
                    date_str = match.group(1)
                    time_str = match.group(2)
                    dt = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M%S")
                    return dt
                elif len(match.groups()) == 1:  # 格式：TIMESTAMP
                    timestamp = match.group(1)
                    try:
                        if len(timestamp) == 14:
                            datetime_str = match.group(1)
                            dt = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
                            return dt
                        elif len(timestamp) == 13:
                            result = datetime.fromtimestamp(int(timestamp) / 1000)  # 转换为秒
                            return valid_time(result)
                        else:
                            result = datetime.fromtimestamp(int(timestamp))  # 转换为秒
                            return valid_time(result)
                    except (ValueError, OverflowError):
                        try:
                            # 取前十位当做时间戳
                            if timestamp.startswith('1'):
                                timestamp = timestamp[:10]
                                result = datetime.fromtimestamp(int(timestamp))  # 转换为秒
                                return valid_time(result)
                        except (ValueError, OverflowError):
                            continue
                elif len(match.groups()) == 4:  # 格式：YYYY-MM-DD HHMMSS
                    year, month, day, time_str = match.groups()
                    if len(year) == 4:
                        # 格式：YYYY-MM-DD_HHMMSS YYYY-MM-DD HHMMSS
                        dt = datetime.strptime(f"{year}-{month}-{day} {time_str}", "%Y-%m-%d %H%M%S")
                    elif len(year) == 8:
                        # 格式：YYYYMMDD_HH-MM-SS
                        dt = datetime.strptime(f"{year} {month}-{day}-{time_str}", "%Y%m%d %H-%-M-%S")
                    else:
                        # DD-MM-YYYY_HHMMSS
                        dt = datetime.strptime(f"{year}-{month}-{day} {time_str}", "%m-%d-%Y %H%M%S")
                    return dt
                elif len(match.groups()) == 6:  # 格式：YYYY_MM_DD_HH-MM-SS
                    year, month, day, hour, minute, second = match.groups()
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                    return dt
        print('文件名解析失败:', filename)
        return None  # 如果没有匹配到任何模式，返回 None
    except:
        print('文件名解析失败:', filename)
        return None  # 如果没有匹配到任何模式，返回 None


def extract_datetime_from_filename(filename) -> datetime | None:
    file_time = _extract_datetime_from_filename(filename)
    if file_time and is_within_range(file_time, start_time, end_time):
        return file_time
    return None

