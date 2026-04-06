"""
向量生成封装模块

提供企业级向量生成功能：
- 封装文本生成向量的统一接口
- 模型接口可替换
- 输入：str / list[str]
- 输出：vector / list[vector]
- 异常捕获
- 与 Milvus 对齐维度
"""

from typing import List, Union, Optional
import numpy as np
from .logger import get_logger
from .utils_config import EMBEDDING_CONFIG


logger = get_logger("Embedding")

DEFAULT_EMBEDDING_DIM = EMBEDDING_CONFIG["DEFAULT_EMBEDDING_DIM"]
DEFAULT_MODEL_NAME = EMBEDDING_CONFIG["DEFAULT_MODEL_NAME"]
DEFAULT_DEVICE = EMBEDDING_CONFIG["DEFAULT_DEVICE"]
DEFAULT_NORMALIZE = EMBEDDING_CONFIG["DEFAULT_NORMALIZE"]


class EmbeddingGenerator:
    """
    向量生成器
    
    封装文本生成向量的统一接口，支持多种模型
    """
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        device: str = DEFAULT_DEVICE
    ):
        """
        初始化向量生成器
        
        Args:
            model_name: 模型名称
            embedding_dim: 向量维度
            device: 运行设备 (cpu/cuda)
        """
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.device = device
        self.model = None
        self._initialized = False
        
        logger.info(f"向量生成器初始化: model={model_name}, dim={embedding_dim}, device={device}")
    
    def _lazy_init(self) -> None:
        """
        延迟初始化模型
        """
        if self._initialized:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self._initialized = True
            logger.info(f"模型加载成功: {self.model_name}")
        
        except ImportError:
            logger.warning("sentence-transformers 未安装，使用模拟向量")
            self._initialized = True
        
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def encode(
        self,
        text: Union[str, List[str]],
        normalize: bool = DEFAULT_NORMALIZE
    ) -> Union[List[float], List[List[float]]]:
        """
        生成向量
        
        Args:
            text: 输入文本或文本列表
            normalize: 是否归一化
        
        Returns:
            Union[List[float], List[List[float]]]: 向量或向量列表
        """
        self._lazy_init()
        
        try:
            if isinstance(text, str):
                return self._encode_single(text, normalize)
            elif isinstance(text, list):
                return self._encode_batch(text, normalize)
            else:
                raise ValueError(f"不支持的输入类型: {type(text)}")
        
        except Exception as e:
            logger.error(f"向量生成失败: {e}")
            raise
    
    def _encode_single(
        self,
        text: str,
        normalize: bool
    ) -> List[float]:
        """
        生成单个文本的向量
        
        Args:
            text: 输入文本
            normalize: 是否归一化
        
        Returns:
            List[float]: 向量
        """
        if not text:
            logger.warning("输入文本为空，返回零向量")
            return [0.0] * self.embedding_dim
        
        try:
            if self.model is not None:
                embedding = self.model.encode(text, normalize_embeddings=normalize)
                return embedding.tolist()
            else:
                return self._generate_mock_vector(text, normalize)
        
        except Exception as e:
            logger.error(f"单文本向量生成失败: {e}")
            raise
    
    def _encode_batch(
        self,
        texts: List[str],
        normalize: bool
    ) -> List[List[float]]:
        """
        批量生成向量
        
        Args:
            texts: 输入文本列表
            normalize: 是否归一化
        
        Returns:
            List[List[float]]: 向量列表
        """
        if not texts:
            logger.warning("输入文本列表为空，返回空列表")
            return []
        
        try:
            if self.model is not None:
                embeddings = self.model.encode(texts, normalize_embeddings=normalize)
                return embeddings.tolist()
            else:
                return [self._generate_mock_vector(text, normalize) for text in texts]
        
        except Exception as e:
            logger.error(f"批量向量生成失败: {e}")
            raise
    
    def _generate_mock_vector(
        self,
        text: str,
        normalize: bool
    ) -> List[float]:
        """
        生成模拟向量（用于测试）
        
        Args:
            text: 输入文本
            normalize: 是否归一化
        
        Returns:
            List[float]: 模拟向量
        """
        np.random.seed(hash(text) % (2 ** 32))
        vector = np.random.randn(self.embedding_dim).astype(np.float32)
        
        if normalize:
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
        
        return vector.tolist()
    
    def get_embedding_dim(self) -> int:
        """
        获取向量维度
        
        Returns:
            int: 向量维度
        """
        return self.embedding_dim
    
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized


def create_embedding_generator(
    model_name: str = DEFAULT_MODEL_NAME,
    embedding_dim: int = DEFAULT_EMBEDDING_DIM,
    device: str = DEFAULT_DEVICE
) -> EmbeddingGenerator:
    """
    创建向量生成器
    
    Args:
        model_name: 模型名称
        embedding_dim: 向量维度
        device: 运行设备
    
    Returns:
        EmbeddingGenerator: 向量生成器实例
    """
    return EmbeddingGenerator(
        model_name=model_name,
        embedding_dim=embedding_dim,
        device=device
    )


def encode_text(
    text: Union[str, List[str]],
    generator: Optional[EmbeddingGenerator] = None,
    normalize: bool = DEFAULT_NORMALIZE
) -> Union[List[float], List[List[float]]]:
    """
    编码文本为向量
    
    Args:
        text: 输入文本或文本列表
        generator: 向量生成器实例
        normalize: 是否归一化
    
    Returns:
        Union[List[float], List[List[float]]]: 向量或向量列表
    """
    if generator is None:
        generator = EmbeddingGenerator()
    
    return generator.encode(text, normalize)
