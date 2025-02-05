from setuptools import setup, find_packages

setup(
    name="nonebot-plugin-whoatme-xqs",  # 插件名称
    version="0.1.0",  # 版本号
    packages=find_packages(),  # 自动查找所有模块
    install_requires=[
        "nonebot2",  # NoneBot 框架依赖
        "nonebot-adapter-onebot",  # OneBot 适配器
        "pydantic",  # 配置管理
        "peewee",  # 轻量级 ORM 数据库
        "aiohttp",  # 异步 HTTP 请求
    ],
    entry_points={
        "nonebot.plugin": [
            "who_at_me = nonebot_plugin_who_at_me",  # 入口模块
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  # Python 版本要求
)
