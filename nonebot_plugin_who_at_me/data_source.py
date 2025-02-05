# data_source.py
from typing import Set
from nonebot.adapters.onebot.v11 import Message, Bot

async def extract_member_at(
    group_id: int, message: Message, bot: Bot = None
) -> Set[str]:
    """提取消息中被艾特人的QQ号
    参数:
        group_id: 群组ID
        message: 消息对象
        bot: Bot实例
    返回:
        被艾特集合
    """
    if bot is None:
        return set()
    
    qq_list = await bot.get_group_member_list(group_id=group_id)
    
    result = {
        segment.data["qq"]
        for segment in message
        if segment.type == "at" and "qq" in segment.data
    }
    if "all" in result:
        result.remove("all")
        result |= {str(member["user_id"]) for member in qq_list}
    return result
