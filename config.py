from typing import Literal, Optional
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model Configuration
    model_name: str = "bigcode/starcoder"
    model_revision: str = "main"  # Git revision/branch
    quantize: bool = True
    quant_method: Literal['bitsandbytes', 'gptq'] = 'bitsandbytes'
    
    # Performance Settings
    cache_ttl: int = 3600  # 1 hour in seconds
    max_code_length: int = 100_000  # Characters
    max_gpu_memory: Optional[str] = None  # e.g., "24GiB"
    
    # Deployment Settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    timeout: int = 300  # seconds
    
    # Security
    allowed_origins: list[str] = ["*"]
    api_key: Optional[str] = None
    
    # Monitoring
    log_level: Literal['DEBUG', 'INFO', 'WARNING'] = 'INFO'
    sentry_dsn: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "STARCODER_"
        case_sensitive = False
        extra = 'ignore'  # Ignore extra env variables

    @property
    def device_map(self) -> dict:
        """Auto-configure device map based on available hardware"""
        return {
            "": "cuda:0" if torch.cuda.is_available() else "cpu",
            "transformer.word_embeddings": 0,
            "transformer.final_layer_norm": 0,
        } if torch.cuda.is_available() else "auto"

    def model_cache_dir(self) -> Path:
        """Standardized model cache location"""
        cache_dir = Path.home() / ".cache" / "starcoder"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

# Initialize settings (import this singleton elsewhere)
try:
    import torch  # Lazy import to avoid CUDA issues during config loading
    settings = Settings()
except ImportError:
    class FallbackSettings:
        model_name = "bigcode/starcoder"
        quantize = False
    settings = FallbackSettings()
