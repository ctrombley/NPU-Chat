from typing import Optional

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    template_id: Optional[str] = None


class UpdateChatRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    emoji: Optional[str] = Field(default=None, max_length=10)
    template_id: Optional[str] = None
    is_favorite: Optional[bool] = None


class CreateTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    prefix: str
    postfix: str


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    prefix: Optional[str] = None
    postfix: Optional[str] = None


class SearchRequest(BaseModel):
    input_text: str = Field(min_length=1)
    session_id: Optional[str] = None
