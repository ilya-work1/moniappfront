import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST')
    FLASK_PORT = int(os.getenv('FLASK_PORT'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG').lower()
    
    # Session Configuration
    SESSION_TYPE = os.getenv('SESSION_TYPE')
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT').lower()
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.getenv('SESSION_LIFETIME_MINUTES')))

    # Backend Service URL
    BACKEND_URL = os.getenv('BACKEND_URL')
    
    # File Storage Configuration
    LOGS_DIRECTORY = os.getenv('LOGS_DIRECTORY')

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEBUG_LOG_FORMAT = '%(asctime)s - DEBUG - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s'
    ERROR_LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s\n%(exc_info)s'

    # elastic apm configuration
    SECRET_TOKEN = os.getenv('SECRET_TOKEN')
    SERVER_URL = os.getenv('SERVER_URL')

def setup_logger():
    """Setup logger with daily files"""
    # Create logs directory if it doesn't exist
    if not os.path.exists(Config.LOGS_DIRECTORY):
        os.makedirs(Config.LOGS_DIRECTORY)
    
    # Create logger
    logger = logging.getLogger('frontend')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Clear any existing handlers
    logger.handlers = []
    
    current_date = datetime.now().strftime("%Y%m%d")
    
    # App log file (INFO and higher only)
    app_handler = logging.FileHandler(f'{Config.LOGS_DIRECTORY}/frontend_{current_date}.log')
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(
        Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    ))
    
    # Debug log file (DEBUG level only)
    debug_handler = logging.FileHandler(f'{Config.LOGS_DIRECTORY}/frontend_debug_{current_date}.log')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter(
        Config.DEBUG_LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    ))
    
    # Error log file (ERROR and higher only)
    error_handler = logging.FileHandler(f'{Config.LOGS_DIRECTORY}/frontend_error_{current_date}.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        Config.ERROR_LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    ))
    
    # Console handler (INFO and higher for cleaner console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    
    # Add all handlers to the logger
    logger.addHandler(app_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create logger instance
logger = setup_logger()