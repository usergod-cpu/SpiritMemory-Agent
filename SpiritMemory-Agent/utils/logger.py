"""
全局统一日志模块

基于 logging 封装，提供企业级日志功能：
- 同时输出控制台 + 文件落盘
- 日志分级：DEBUG/INFO/WARN/ERROR
- 日志文件按天切割
- 所有模块统一使用
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional
from datetime import datetime
from .utils_config import LOG_CONFIG


_loggers = {}

LOG_DIR = LOG_CONFIG["LOG_DIR"]
LOG_FORMAT = LOG_CONFIG["LOG_FORMAT"]
DATE_FORMAT = LOG_CONFIG["DATE_FORMAT"]
DEFAULT_LOG_LEVEL = getattr(logging, LOG_CONFIG["DEFAULT_LOG_LEVEL"])
DEFAULT_LOGGER_NAME = LOG_CONFIG["DEFAULT_LOGGER_NAME"]


def setup_logger(
    name: str = DEFAULT_LOGGER_NAME,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    设置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_dir: 日志文件目录
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if file_output:
        if log_dir is None:
            log_dir = LOG_DIR
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=LOG_CONFIG["LOG_FILE_BACKUP_COUNT"],
            encoding=LOG_CONFIG["LOG_FILE_ENCODING"]
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def get_logger(name: str = DEFAULT_LOGGER_NAME) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        logging.Logger: 日志记录器
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)


def set_log_level(level: int) -> None:
    """
    设置所有日志记录器的日志级别
    
    Args:
        level: 日志级别
    """
    for logger in _loggers.values():
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


def log_debug(message: str, logger_name: str = DEFAULT_LOGGER_NAME) -> None:
    """记录 DEBUG 级别日志"""
    get_logger(logger_name).debug(message)


def log_info(message: str, logger_name: str = DEFAULT_LOGGER_NAME) -> None:
    """记录 INFO 级别日志"""
    get_logger(logger_name).info(message)


def log_warning(message: str, logger_name: str = DEFAULT_LOGGER_NAME) -> None:
    """记录 WARNING 级别日志"""
    get_logger(logger_name).warning(message)


def log_error(message: str, logger_name: str = DEFAULT_LOGGER_NAME) -> None:
    """记录 ERROR 级别日志"""
    get_logger(logger_name).error(message)


def log_exception(message: str, logger_name: str = DEFAULT_LOGGER_NAME) -> None:
    """记录异常日志（包含堆栈信息）"""
    get_logger(logger_name).exception(message)
