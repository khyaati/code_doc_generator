from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_name: str = "bigcode/starcoder"
    quantize: bool = True
    cache_ttl: int = 3600 

settings = Settings()