#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:45 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : TrailSnap-init_db.py 
@Description : 
"""

import asyncio
from app.db.session import engine
from app.db.base import Base


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(init_models())
