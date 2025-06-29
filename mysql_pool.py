# -*- coding: utf-8 -*-
import pymysql
from dbutils.pooled_db import PooledDB

# 创建数据库连接池
pool = PooledDB(
    creator=pymysql,  # 使用pymysql创建连接
    host='localhost',  # 数据库地址
    port=3001,  # 数据库端口
    user='root',  # 数据库用户名
    password='7745',  # 数据库密码
    database='etest-mysql',  # 数据库名称
    charset='utf8mb4', # 数据库编码
    autocommit=True,  # 自动提交事务
    maxconnections=30,  # 最大连接数
    mincached=3,  # 初始化时最小空闲连接数
    maxcached=5,  # 最大空闲连接数
    blocking=True,  # 连接池满时是否阻塞等待
)

# 获取数据库连接
def get_connection():
    return pool.connection()
