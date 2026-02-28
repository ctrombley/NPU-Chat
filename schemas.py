from typing import Optional

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    sign_id: Optional[str] = None


class UpdateChatRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    emoji: Optional[str] = Field(default=None, max_length=10)
    sign_id: Optional[str] = None
    is_favorite: Optional[bool] = None
    metadata: Optional[dict] = None
    goal: Optional[str] = None


class CreateSignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    prefix: str
    postfix: str
    values: Optional[str] = None
    interests: Optional[str] = None
    default_goal: Optional[str] = None
    aspects: Optional[str] = None


class UpdateSignRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    prefix: Optional[str] = None
    postfix: Optional[str] = None
    values: Optional[str] = None
    interests: Optional[str] = None
    default_goal: Optional[str] = None
    aspects: Optional[str] = None


class SearchRequest(BaseModel):
    input_text: str = Field(min_length=1)
    session_id: Optional[str] = None
