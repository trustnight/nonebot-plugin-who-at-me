# rule.py
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, Bot
from nonebot.params import EventMessage
from .data_source import extract_member_at
from nonebot.log import logger
from nonebot.rule import Rule
from nonebot import get_driver

async def message_at_rule(event: GroupMessageEvent, message: Message = EventMessage()) -> bool:
    """
    定义需要记录的消息规则，例如包含@的消息或是回复消息
    """
    driver = get_driver()

    if not driver.bots:
        logger.error("No bots found!")
        return False

    # 尝试从事件中获取bot，如果没有则使用第一个bot
    if hasattr(event, 'bot') and isinstance(event.bot, Bot):
        bot = event.bot
    else:
        bot = list(driver.bots.values())[0]

    at_members = await extract_member_at(event.group_id, message=message, bot=bot)

    logger.debug(f"Extracted @members: {at_members}, Reply: {event.reply}")
    return bool(at_members) or bool(event.reply)

# 将函数转换为Rule对象
message_at_rule = Rule(message_at_rule)
