#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/23 00:19
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-config.py
@Description : 
"""
import logging
import os
from logging.handlers import RotatingFileHandler

TIMETABLE_URL = "https://kyfw.12306.cn/otn/queryTrainInfo/query"
SEARCH_URL = "https://search.12306.cn/search/v1/train/search"
KM_URL = "https://shike.gaotie.cn/checi.asp"

TRAIN_TYPE = ['G','D','Z','K','T','Y','C','S']
os.makedirs('./logs', exist_ok=True)
LOG_FILE = "./logs/sync.log"  # 日志文件

REQUEST_INTERVAL = 10  # 每次请求后暂停（防反爬）
RETRY_TIMES = 3  # 单个请求失败后重试次数
RECENT_DAYS = 1  # 获取最近7天的车次（含今天）

# ------------------------------ 日志配置（支持5M分割+多文件轮转）------------------------------
# 1. 定义日志格式（与原有一致）
log_format = "%(asctime)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(log_format)

# 2. 配置控制台输出（保留原有功能）
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# 3. 配置文件输出（核心修改：使用 RotatingFileHandler 按大小分割）
file_handler = RotatingFileHandler(
    filename=LOG_FILE,          # 主日志文件路径
    maxBytes=5 * 1024 * 1024,   # 单个文件最大尺寸：5M（1024*1024=1M）
    backupCount=100,              # 最多保留5个备份文件（可按需调整，如10）
    encoding="utf-8",           # 编码格式（避免中文乱码）
    delay=False,                # 立即创建文件（默认False，无需修改）
    mode="a"                    # 追加模式（默认a，无需修改）
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# 4. 配置根日志器（整合控制台+文件输出）
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)  # 根日志级别（需低于处理器级别才生效）

# 先清空已有处理器（避免重复输出）
root_logger.handlers.clear()

# 添加处理器
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)
