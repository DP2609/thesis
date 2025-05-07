from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class DetectionResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    confidence_scores: List[float]
    processing_time: float

class ChatHistoryBase(BaseModel):
    message: str
    response: str
    image_path: Optional[str] = None

class ChatHistoryCreate(ChatHistoryBase):
    pass

class ChatHistory(ChatHistoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistoryList(BaseModel):
    items: List[ChatHistory]
    total: int

class UserList(BaseModel):
    items: List[User]
    total: int

class UserWithChatHistory(User):
    chat_histories: List[ChatHistory] = [] 