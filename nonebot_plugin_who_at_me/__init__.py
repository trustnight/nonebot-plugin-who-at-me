import time
import random
from typing import List
from nonebot import on_message, on_regex, get_driver
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    MessageEvent,
    MessageSegment,
    Message,
)
from peewee import fn

# =============== 你自己的数据库、工具等 ===============
from .database import MainTable, db
from .data_source import extract_member_at
from .utils import node_custom
# =====================================================

__plugin_meta__ = PluginMetadata(
    name="who_at_me",
    description="看看是谁又艾特了我（空艾特自动拼接前后，但分别展示）",
    usage="谁@我了？ / 谁艾特我",
    extra={
        "author": "xxx",
        "version": "1.0.0",
    },
)

global_config = get_driver().config

REMINDER_EXPIRE_TIME = 3 * 24 * 3600  # 超过这个时间就不再显示
NO_AT_RESPONSES = [
    "没有人@你，别问了，没人想起你～",
    "大家都没@你，看来你的存在感比空气还弱……",
    "没有人@你，不过我可以先@你一下，给你找点存在感～",
]

def is_empty_mention(msg_str: str) -> bool:
    """
    判断消息是否空艾特：只包含[CQ:at]段，去掉后没任何文字
    """
    msg = Message(msg_str)
    msg_copy = Message(msg)
    for seg in msg:
        if seg.type == "at":
            msg_copy.remove(seg)
    leftover = str(msg_copy).strip()
    return len(leftover) == 0

# ==========================================
# 1. 监听并存表
# ==========================================
monitor = on_message(block=False)

@monitor.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    监听所有群消息：
      - 若消息包含@xxx => 对每个被@者各插一条(target_id=对方)
      - 否则插一条(target_id=0)
    """
    group_id = event.group_id
    operator_id = event.user_id
    operator_name = event.sender.card or event.sender.nickname
    raw_msg = str(event.message)
    msg_id = event.message_id
    now_ts = int(time.time())

    at_members = await extract_member_at(group_id, event.message, bot)
    if at_members:
        for target in at_members:
            MainTable.create(
                operator_id=operator_id,
                operator_name=operator_name,
                target_id=target,
                group_id=group_id,
                time=now_ts,
                message=raw_msg,
                message_id=msg_id,
            )
    else:
        MainTable.create(
            operator_id=operator_id,
            operator_name=operator_name,
            target_id=0,
            group_id=group_id,
            time=now_ts,
            message=raw_msg,
            message_id=msg_id,
        )


# ==========================================
# 2. “谁@我” 命令
# ==========================================
who_at_me = on_regex(r"^谁.*(@|艾特|圈|[aA][tT])+.?我")

@who_at_me.handle()
async def _(bot: Bot, event: MessageEvent):
    """
    查找 target_id=自己 的记录
    对空艾特 => 取上一条、当前、下一条 分3条节点
    对带文字@ => 仅当前
    最后按时间顺序合并
    """
    is_group = isinstance(event, GroupMessageEvent)
    group_id = event.group_id if is_group else None
    user_id = event.user_id
    now_ts = int(time.time())

    # 1) 查询所有 @ 我的记录
    base_query = (
        MainTable.select()
        .where(MainTable.target_id == user_id)
        .where((now_ts - MainTable.time) <= REMINDER_EXPIRE_TIME)  # 未过期
    )
    if is_group:
        base_query = base_query.where(MainTable.group_id == group_id)

    # 按时间顺序
    records = list(base_query.order_by(MainTable.time))
    if not records:
        await who_at_me.finish(random.choice(NO_AT_RESPONSES))

    # 2) 汇总所有需要发送的节点
    #    注意：空艾特 => 上一条/当前/下一条 分别做 3 个节点
    #          带文字@ => 只做 1 个节点
    forward_nodes: List[MessageSegment] = []

    for row in records:
        # 若空艾特
        if is_empty_mention(row.message):
            # 拿到上一条、下一条(同群、同人)
            # 分别做 node
            prev_row = get_prev_message(row)
            curr_row = row
            next_row = get_next_message(row)

            # 可能没有上一条或下一条，这都要判断
            if prev_row:
                forward_nodes.append(
                    make_forward_node(prev_row)
                )
            # 当前这条
            forward_nodes.append(
                make_forward_node(curr_row)
            )
            if next_row:
                forward_nodes.append(
                    make_forward_node(next_row)
                )
        else:
            # 带文字@ => 只做单条
            forward_nodes.append(
                make_forward_node(row)
            )

    # 如果最终没有节点
    if not forward_nodes:
        await who_at_me.finish(random.choice(NO_AT_RESPONSES))

    # 3) 发送合并转发
    if is_group:
        event: GroupMessageEvent
        await bot.send_group_forward_msg(
            group_id=event.group_id,
            messages=forward_nodes
        )
        # 清空记录(可选)
        # MainTable.delete().where(
        #     (MainTable.target_id==user_id) & (MainTable.group_id==group_id)
        # ).execute()
    else:
        await bot.send_private_forward_msg(
            user_id=event.user_id,
            messages=forward_nodes
        )
        # 清空记录(可选)
        # MainTable.delete().where(MainTable.target_id==user_id).execute()


# ==========================================
# 3. 查上一条、下一条
# ==========================================
def get_prev_message(current_row: MainTable) -> MainTable:
    """
    查找同群、同发送者、时间比 current_row 小的消息里，
    最接近 current_row 的那条(上一条)。
    """
    query = (
        MainTable.select()
        .where(
            MainTable.group_id == current_row.group_id,
            MainTable.operator_id == current_row.operator_id,
            MainTable.time < current_row.time
        )
        .order_by(MainTable.time.desc())
        .limit(1)
    )
    return query.first()


def get_next_message(current_row: MainTable) -> MainTable:
    """
    查找同群、同发送者、时间比 current_row 大的消息里，
    最接近 current_row 的那条(下一条)。
    """
    query = (
        MainTable.select()
        .where(
            MainTable.group_id == current_row.group_id,
            MainTable.operator_id == current_row.operator_id,
            MainTable.time > current_row.time
        )
        .order_by(MainTable.time.asc())
        .limit(1)
    )
    return query.first()


# ==========================================
# 4. 构造转发节点（每条消息一个节点）
# ==========================================
def make_forward_node(row: MainTable) -> MessageSegment:
    """
    将row的一条消息转换为合并转发节点
    你自己的 node_custom(...) 里可能需要:
       user_id: 发送者
       name: 显示名 (若你不要展示名字，就传空字符串)
       time: 字符串或整数
       content: Message 对象
    """
    return node_custom(
        user_id=row.operator_id,  # 要显示原作者
        name="",                  # 不想出现艾特人名字则留空
        time=str(row.time),       # 时间戳
        content=Message(row.message)
    )
