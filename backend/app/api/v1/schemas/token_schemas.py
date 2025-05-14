from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """
    JWT令牌响应模型
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    JWT令牌数据模型，用于存储令牌中的用户信息
    """
    username: Optional[str] = None
    role: Optional[str] = None 