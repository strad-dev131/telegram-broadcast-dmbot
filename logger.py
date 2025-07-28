"""
Logging configuration for the Telegram bot
"""

import os
import logging
import logging.handlers
from datetime import datetime
from config import Config

def setup_logger() -> logging.Logger:
    """Setup and configure logger for the application"""
    
    config = Config()
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(config.LOG_FILE) if os.path.dirname(config.LOG_FILE) else '.'
        os.makedirs(log_dir, exist_ok=True)
        
        # Rotating file handler (10MB max, keep 5 files)
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.error(f"Could not setup file logging: {e}")
    
    # Error file handler for critical errors
    try:
        error_file = config.LOG_FILE.replace('.log', '_errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
    except Exception as e:
        logger.error(f"Could not setup error file logging: {e}")
    
    # Log startup message
    logger.info("=" * 50)
    logger.info("Telegram Multi-Account Bot Starting")
    logger.info(f"Log level: {config.LOG_LEVEL}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 50)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)

# Custom exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Handle Ctrl+C gracefully
        logger = logging.getLogger()
        logger.info("Application interrupted by user")
        return
    
    logger = logging.getLogger()
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Set the exception handler
import sys
sys.excepthook = handle_exception
