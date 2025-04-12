import re
import logging
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class CodeInput(BaseModel):
    """
    Input schema for code processing requests.
    
    Attributes:
        code (str): The source code to be analyzed (non-empty).
        language (Optional[str]): Programming language hint (e.g., 'python', 'javascript').
    """
    code: str = Field(..., min_length=1, max_length=100_000, 
                     examples=["def hello():\n    print('world')"],
                     description="Source code to be commented")
    
    language: Optional[str] = Field(
        default=None,
        examples=["python"],
        description="Programming language for syntax-aware commenting"
    )

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Ensure code is non-empty and doesn't contain forbidden patterns."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Code cannot be empty")
        
        # Basic security check (optional)
        if re.search(r'(?:system|exec|eval|subprocess)\(', stripped, re.IGNORECASE):
            raise ValueError("Potentially dangerous code patterns detected")
            
        return stripped

    @field_validator('language')
    @classmethod
    def normalize_language(cls, v: Optional[str]) -> Optional[str]:
        """Normalize language names and validate against supported list."""
        if v is None:
            return None
            
        normalized = v.lower().strip()
        supported_languages = {
            'python', 'javascript', 'java', 'c', 'cpp', 
            'go', 'rust', 'ruby', 'php', 'typescript'
        }
        
        if normalized not in supported_languages:
            logger.warning(f"Unsupported language: {v}. Proceeding with generic commenting.")
            
        return normalized


class CodeOutput(BaseModel):
    """
    Output schema for commented code responses.
    
    Attributes:
        commented_code (str): The original code with added comments.
        language (str): Detected/confirmed programming language.
    """
    commented_code: str = Field(
        ...,
        examples=["# Prints 'world'\ndef hello():\n    print('world')"],
        description="Original code with generated comments"
    )
    
    language: str = Field(
        ...,
        examples=["python"],
        description="Language used for comment formatting"
    )

    @field_validator('commented_code')
    @classmethod
    def validate_commented_code(cls, v: str) -> str:
        """Ensure output contains both code and comments."""
        lines = v.split('\n')
        if not any(line.strip().startswith('#') for line in lines):
            raise ValueError("No comments were generated")
        return v
