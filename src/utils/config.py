"""Configuration management system for loading and managing application settings."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """Central configuration loader and manager."""
    
    _instance: Optional['Config'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            load_dotenv()
            self.project_root = Path(__file__).parent.parent.parent
            self.config_dir = self.project_root / "config"
            self._configs: Dict[str, Dict[str, Any]] = {}
            self._initialized = True
    
    def load_yaml(self, config_name: str) -> Dict[str, Any]:
        """Load a YAML configuration file.
        
        Args:
            config_name: Name of the config file (without .yaml extension)
            
        Returns:
            Dictionary containing configuration data
        """
        if config_name in self._configs:
            return self._configs[config_name]
        
        config_path = self.config_dir / f"{config_name}.yaml"
        if not config_path.exists():
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
        
        self._configs[config_name] = config_data
        return config_data
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """Get environment variable with optional default."""
        return os.getenv(key, default)
    
    @property
    def youtube_api_key(self) -> str:
        """Get YouTube API key from environment."""
        return self.get_env("YOUTUBE_API_KEY", "")
    
    @property
    def gemini_api_key(self) -> str:
        """Get Gemini API key from environment."""
        return self.get_env("GEMINI_API_KEY", "")
    
    @property
    def sora_api_key(self) -> str:
        """Get Sora API key from environment."""
        return self.get_env("SORA_API_KEY", "")
    
    @property
    def sora_api_url(self) -> str:
        """Get Sora API URL from environment."""
        return self.get_env("SORA_API_URL", "https://api.sora.example.com")
    
    @property
    def database_url(self) -> str:
        """Get database URL from environment."""
        db_url = self.get_env("DATABASE_URL", "sqlite:///database/youtube_shorts.db")
        if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
            db_path = db_url.replace("sqlite:///", "")
            abs_path = self.project_root / db_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{abs_path}"
        return db_url
    
    @property
    def log_level(self) -> str:
        """Get log level from environment."""
        return self.get_env("LOG_LEVEL", "INFO")
    
    @property
    def log_dir(self) -> Path:
        """Get log directory path."""
        log_dir = Path(self.get_env("LOG_DIR", "logs"))
        if not log_dir.is_absolute():
            log_dir = self.project_root / log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    @property
    def max_workers(self) -> int:
        """Get maximum number of workers."""
        return int(self.get_env("MAX_WORKERS", "4"))
    
    @property
    def download_timeout(self) -> int:
        """Get download timeout in seconds."""
        return int(self.get_env("DOWNLOAD_TIMEOUT", "300"))


# Global config instance
config = Config()
