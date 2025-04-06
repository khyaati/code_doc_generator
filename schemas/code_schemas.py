from pydantic import BaseModel, field_validator
from typing import Optional

class CodeInput(BaseModel):
    code: str
    language: Optional[str] = None

    @field_validator('code')
    def code_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Code cannot be empty")
        return v.strip()

    @field_validator('language')
    def normalize_language(cls, v):
        return v.lower() if v else v

class CodeOutput(BaseModel):
    commented_code: str
    language: str
