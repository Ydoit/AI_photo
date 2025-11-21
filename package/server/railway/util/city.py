#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/21 16:36
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-city.py
@Description : 
"""
from typing import Optional

# 核心映射表：key=数据库存储的规范值，value=所有可能的用户输入（含简称、别名）
PROVINCE_MAPPING = {
    # 省份（含简称）
    "河南省": ["河南", "河南省", "豫"],
    "河北省": ["河北", "河北省", "冀"],
    "山东省": ["山东", "山东省", "鲁"],
    "山西省": ["山西", "山西省", "晋"],
    "陕西省": ["陕西", "陕西省", "陕", "秦"],
    "甘肃省": ["甘肃", "甘肃省", "甘", "陇"],
    "青海省": ["青海", "青海省", "青"],
    "辽宁省": ["辽宁", "辽宁省", "辽"],
    "吉林省": ["吉林", "吉林省", "吉"],
    "黑龙江省": ["黑龙江", "黑龙江省", "黑"],
    "江苏省": ["江苏", "江苏省", "苏"],
    "浙江省": ["浙江", "浙江省", "浙"],
    "安徽省": ["安徽", "安徽省", "皖"],
    "福建省": ["福建", "福建省", "闽"],
    "江西省": ["江西", "江西省", "赣"],
    "湖北省": ["湖北", "湖北省", "鄂"],
    "湖南省": ["湖南", "湖南省", "湘"],
    "广东省": ["广东", "广东省", "粤"],
    "海南省": ["海南", "海南省", "琼"],
    "四川省": ["四川", "四川省", "川", "蜀"],
    "贵州省": ["贵州", "贵州省", "贵", "黔"],
    "云南省": ["云南", "云南省", "云", "滇"],
    # 直辖市（既是省份也是城市）
    "北京市": ["北京", "北京市", "京", "首都"],
    "上海市": ["上海", "上海市", "沪", "申"],
    "天津市": ["天津", "天津市", "津"],
    "重庆市": ["重庆", "重庆市", "渝"],
    # 自治区
    "新疆维吾尔自治区": ["新疆", "新疆自治区", "新疆维吾尔自治区", "疆"],
    "内蒙古自治区": ["内蒙古", "内蒙古自治区", "蒙"],
    "广西壮族自治区": ["广西", "广西壮族自治区", "桂"],
    "宁夏回族自治区": ["宁夏", "宁夏回族自治区", "宁"],
    "西藏自治区": ["西藏", "西藏自治区", "藏"],
    # 特别行政区
    "香港特别行政区": ["香港", "香港特区", "港"],
    "澳门特别行政区": ["澳门", "澳门特区", "澳"],
    "台湾省": ["台湾", "台湾省", "台"]
}

# 反向映射：用户输入→数据库规范值（用于快速查找）
REVERSE_ADMIN_MAPPING = {}
for standard, inputs in PROVINCE_MAPPING.items():
    for input_val in inputs:
        REVERSE_ADMIN_MAPPING[input_val.strip()] = standard

# ------------------------------ 输入标准化函数（新增）------------------------------
def standardize_city_name(input_str: Optional[str]) -> Optional[str]:
    if not input_str:
        return None
    clean_str = input_str.strip().lower()
    if not clean_str:
        return None
    # 去除冗余后缀
    redundant_suffixes = [
        "特别行政区", "自治区", "壮族", "维吾尔", "回族",
        "省", "市", "特区", "地区", "盟", "自治州"
    ]
    for suffix in redundant_suffixes:
        clean_str = clean_str.replace(suffix.lower(), "")
    # 匹配规范值
    for input_val, standard_val in REVERSE_ADMIN_MAPPING.items():
        if input_val.lower() == clean_str:
            return standard_val
    # 未匹配到，返回清洗后的关键词
    return clean_str
