"""
文本处理工具模块

提供企业级文本处理功能：
- 文本清洗
- 过长文本自动截断
- 提取关键词
- 结构化预处理
"""

import re
from typing import List, Optional, Set
from .logger import get_logger
from .utils_config import TEXT_PROCESS_CONFIG


logger = get_logger("TextProcess")

DEFAULT_MAX_LENGTH = TEXT_PROCESS_CONFIG["DEFAULT_MAX_LENGTH"]
DEFAULT_MIN_KEYWORD_LENGTH = TEXT_PROCESS_CONFIG["DEFAULT_MIN_KEYWORD_LENGTH"]
DEFAULT_MAX_KEYWORDS = TEXT_PROCESS_CONFIG["DEFAULT_MAX_KEYWORDS"]
DEFAULT_TRUNCATE_SUFFIX = TEXT_PROCESS_CONFIG["DEFAULT_TRUNCATE_SUFFIX"]
DEFAULT_CHUNK_SIZE = TEXT_PROCESS_CONFIG["DEFAULT_CHUNK_SIZE"]
DEFAULT_OVERLAP = TEXT_PROCESS_CONFIG["DEFAULT_OVERLAP"]
DEFAULT_STOP_WORDS = TEXT_PROCESS_CONFIG["DEFAULT_STOP_WORDS"]


def clean_text(
    text: str,
    remove_extra_spaces: bool = True,
    remove_special_chars: bool = False,
    lowercase: bool = False
) -> str:
    """
    文本清洗
    
    Args:
        text: 原始文本
        remove_extra_spaces: 是否移除多余空格
        remove_special_chars: 是否移除特殊字符
        lowercase: 是否转为小写
    
    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""
    
    try:
        cleaned = text.strip()
        
        if remove_extra_spaces:
            cleaned = re.sub(r'\s+', ' ', cleaned)
        
        if remove_special_chars:
            cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned)
        
        if lowercase:
            cleaned = cleaned.lower()
        
        logger.debug(f"文本清洗完成: 原长度={len(text)}, 新长度={len(cleaned)}")
        return cleaned
    
    except Exception as e:
        logger.error(f"文本清洗失败: {e}")
        return text


def truncate_text(
    text: str,
    max_length: int = DEFAULT_MAX_LENGTH,
    suffix: str = DEFAULT_TRUNCATE_SUFFIX
) -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
    
    Returns:
        str: 截断后的文本
    """
    if not text:
        return ""
    
    try:
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length - len(suffix)] + suffix
        logger.debug(f"文本截断完成: 原长度={len(text)}, 新长度={len(truncated)}")
        return truncated
    
    except Exception as e:
        logger.error(f"文本截断失败: {e}")
        return text


def extract_keywords(
    text: str,
    min_length: int = DEFAULT_MIN_KEYWORD_LENGTH,
    max_keywords: int = DEFAULT_MAX_KEYWORDS,
    stop_words: Optional[Set[str]] = None
) -> List[str]:
    """
    提取关键词（简单实现，基于词频）
    
    Args:
        text: 原始文本
        min_length: 最小关键词长度
        max_keywords: 最大关键词数量
        stop_words: 停用词集合
    
    Returns:
        List[str]: 关键词列表
    """
    if not text:
        return []
    
    try:
        if stop_words is None:
            stop_words = DEFAULT_STOP_WORDS
        
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        
        word_freq = {}
        for word in words:
            if len(word) >= min_length and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        keywords = [word for word, _ in sorted_words[:max_keywords]]
        
        logger.debug(f"关键词提取完成: 提取数量={len(keywords)}")
        return keywords
    
    except Exception as e:
        logger.error(f"关键词提取失败: {e}")
        return []


def preprocess_text(
    text: str,
    clean: bool = True,
    truncate: bool = True,
    max_length: int = DEFAULT_MAX_LENGTH
) -> str:
    """
    文本预处理
    
    Args:
        text: 原始文本
        clean: 是否清洗
        truncate: 是否截断
        max_length: 最大长度
    
    Returns:
        str: 预处理后的文本
    """
    if not text:
        return ""
    
    try:
        processed = text
        
        if clean:
            processed = clean_text(processed)
        
        if truncate:
            processed = truncate_text(processed, max_length)
        
        logger.debug(f"文本预处理完成: 原长度={len(text)}, 新长度={len(processed)}")
        return processed
    
    except Exception as e:
        logger.error(f"文本预处理失败: {e}")
        return text


def split_text_by_length(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> List[str]:
    """
    按长度分割文本
    
    Args:
        text: 原始文本
        chunk_size: 分块大小
        overlap: 重叠大小
    
    Returns:
        List[str]: 文本块列表
    """
    if not text:
        return []
    
    try:
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        logger.debug(f"文本分割完成: 原长度={len(text)}, 分块数={len(chunks)}")
        return chunks
    
    except Exception as e:
        logger.error(f"文本分割失败: {e}")
        return [text] if text else []


def count_words(text: str) -> int:
    """
    统计词数
    
    Args:
        text: 原始文本
    
    Returns:
        int: 词数
    """
    if not text:
        return 0
    
    try:
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        return len(words)
    
    except Exception as e:
        logger.error(f"词数统计失败: {e}")
        return 0


def remove_duplicates(texts: List[str]) -> List[str]:
    """
    移除重复文本
    
    Args:
        texts: 文本列表
    
    Returns:
        List[str]: 去重后的文本列表
    """
    if not texts:
        return []
    
    try:
        seen = set()
        unique_texts = []
        
        for text in texts:
            if text not in seen:
                seen.add(text)
                unique_texts.append(text)
        
        logger.debug(f"去重完成: 原数量={len(texts)}, 新数量={len(unique_texts)}")
        return unique_texts
    
    except Exception as e:
        logger.error(f"去重失败: {e}")
        return texts
