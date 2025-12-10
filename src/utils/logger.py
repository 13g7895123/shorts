"""Unified logging system with module and date-based organization."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class LoggerManager:
    """Centralized logger management with support for console and file output."""
    
    _loggers = {}
    _initialized = False
    _log_dir: Optional[Path] = None
    _log_level: str = "INFO"
    
    @classmethod
    def initialize(cls, log_dir: Path, log_level: str = "INFO"):
        """Initialize the logging system.
        
        Args:
            log_dir: Directory to store log files
            log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        cls._log_dir = log_dir
        cls._log_level = log_level
        cls._log_dir.mkdir(parents=True, exist_ok=True)
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str, module: Optional[str] = None) -> logging.Logger:
        """Get or create a logger instance.
        
        Args:
            name: Logger name (usually __name__ of the module)
            module: Optional module category for file organization
            
        Returns:
            Configured logger instance
        """
        if not cls._initialized:
            from .config import config
            cls.initialize(config.log_dir, config.log_level)
        
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, cls._log_level))
        logger.propagate = False
        
        if logger.handlers:
            logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, cls._log_level))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler - Daily rotation
        if module:
            log_file = cls._log_dir / module / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        else:
            log_file = cls._log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, cls._log_level))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Error file handler - Separate file for errors
        error_log_file = cls._log_dir / "errors" / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        error_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        error_handler = TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=90,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def cleanup_old_logs(cls, days: int = 30):
        """Remove log files older than specified days.
        
        Args:
            days: Number of days to retain logs
        """
        if not cls._log_dir or not cls._log_dir.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for log_file in cls._log_dir.rglob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                except Exception as e:
                    print(f"Failed to delete old log file {log_file}: {e}")


def get_logger(name: str, module: Optional[str] = None) -> logging.Logger:
    """Convenience function to get a logger.
    
    Args:
        name: Logger name (usually __name__)
        module: Optional module category
        
    Returns:
        Configured logger instance
    """
    return LoggerManager.get_logger(name, module)


# Module-specific logger factories
def get_discovery_logger(name: str) -> logging.Logger:
    """Get logger for discovery module."""
    return get_logger(name, "discovery")


def get_analysis_logger(name: str) -> logging.Logger:
    """Get logger for analysis module."""
    return get_logger(name, "analysis")


def get_generation_logger(name: str) -> logging.Logger:
    """Get logger for generation module."""
    return get_logger(name, "generation")


def get_processing_logger(name: str) -> logging.Logger:
    """Get logger for processing module."""
    return get_logger(name, "processing")


def get_publishing_logger(name: str) -> logging.Logger:
    """Get logger for publishing module."""
    return get_logger(name, "publishing")


def get_pipeline_logger(name: str) -> logging.Logger:
    """Get logger for pipeline module."""
    return get_logger(name, "pipeline")
