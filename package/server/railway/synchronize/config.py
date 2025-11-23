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

TIMETABLE_URL = "https://kyfw.12306.cn/otn/queryTrainInfo/query"
SEARCH_URL = "https://search.12306.cn/search/v1/train/search"
KM_URL = "https://shike.gaotie.cn/checi.asp"

TRAIN_TYPE = ['G','D','Z','K','T','Y','C','S']
LOG_FILE = "./sync.log"  # 日志文件

REQUEST_INTERVAL = 10  # 每次请求后暂停（防反爬）
RETRY_TIMES = 3  # 单个请求失败后重试次数
RECENT_DAYS = 1  # 获取最近7天的车次（含今天）

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)