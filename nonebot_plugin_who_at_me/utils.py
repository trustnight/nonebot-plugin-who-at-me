# utils.py
from typing import Dict, Any

def node_custom(
    user_id: int, name: str, time: int, content: str
) -> Dict[str, Any]:
    """
    构建转发消息的节点
    """
    return {
        "type": "node",
        "data": {
            "uin": str(user_id),
            "name": name,
            "content": content,
            "timestamp": str(time),
        },
    }

def get_member_name(member: Dict[str, Any]) -> str:
    """
    根据群成员信息获取成员名称
    """
    return member.get("card") or member.get("nickname") or "未知用户"