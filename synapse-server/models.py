from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    message: str
    context_files: List[str] = []

class FileItem(BaseModel):
    id: int
    title: str
    date: str

class FolderResponse(BaseModel):
    folders: dict[str, List[FileItem]]

class ChatResponse(BaseModel):
    thought: Optional[str] = None
    answer: str
    sources: List[str] = []

class AnalyzeRequest(BaseModel):
    text: str
    source_type: str = "text" # "text" or "audio"
