# database.py
from pathlib import Path
import peewee as pw
from nonebot.log import logger

# 定义数据库路径
db_path = Path().absolute() / "data" / "who@me" / "data.db"
db_path.parent.mkdir(exist_ok=True, parents=True)

# 初始化数据库
db = pw.SqliteDatabase(db_path)

class MainTable(pw.Model):
    operator_id = pw.IntegerField()    # 谁发的
    operator_name = pw.CharField()
    target_id = pw.IntegerField()      # @了谁，没有@时记0
    group_id = pw.IntegerField()
    time = pw.CharField()              # 建议改成 pw.IntegerField() 便于比较大小
    message = pw.TextField()           # 存原始消息文本(含CQ码)
    message_id = pw.IntegerField()

    class Meta:
        database = db
        primary_key = pw.CompositeKey(
            "operator_id",
            "operator_name",
            "target_id",
            "group_id",
            "time",
            "message",
            "message_id",
        )


def initialize_database():
    try:
        db.connect()
        db.create_tables([MainTable], safe=True)
        logger.info("Database tables created or already exist.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    finally:
        db.close()

# 执行数据库初始化
initialize_database()
