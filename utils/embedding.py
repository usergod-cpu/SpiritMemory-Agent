"""
向量生成封装模块

提供企业级向量生成功能：
- 支持线上模型 (智谱 AI, OpenAI)
- 支持本地模型 (sentence-transformers)
- 模型接口可替换
- 输入：str / list[str]
- 输出：vector / list[vector]
- 异常捕获
"""

from typing import List, Union, Optional
import os
import numpy as np
import requests
from .logger import get_logger
from .utils_config import EMBEDDING_CONFIG


logger = get_logger("Embedding")

EMBEDDING_TYPE = EMBEDDING_CONFIG.get("EMBEDDING_TYPE", "online")
DEFAULT_NORMALIZE = EMBEDDING_CONFIG.get("DEFAULT_NORMALIZE", True)
DEFAULT_EMBEDDING_DIM = EMBEDDING_CONFIG.get("DEFAULT_EMBEDDING_DIM", 1024)


class OnlineEmbedding:
    """
    线上向量生成器
    
    支持智谱 AI 和 OpenAI 的 embedding API
    """
    
    def __init__(
        self,
        provider: str = None,
        model_name: str = None,
        api_key: str = None,
        api_base: str = None,
        embedding_dim: int = None
    ):
        """
        初始化线上向量生成器
        
        Args:
            provider: 服务提供商 (zhipuai, openai)
            model_name: 模型名称
            api_key: API 密钥
            api_base: API 基础地址
            embedding_dim: 向量维度
        """
        self.provider = provider or EMBEDDING_CONFIG.get("ONLINE_PROVIDER", "zhipuai")
        self.model_name = model_name or EMBEDDING_CONFIG.get("ONLINE_MODEL_NAME", "embedding-3")
        self.api_base = api_base or EMBEDDING_CONFIG.get("ONLINE_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
        self.embedding_dim = embedding_dim or EMBEDDING_CONFIG.get("ONLINE_EMBEDDING_DIM", 1024)
        
        self.api_key = self._get_api_key(api_key)
        
        if not self.api_key:
            logger.warning(f"{self.provider} API Key 未配置，请设置环境变量或在配置中指定")
        
        logger.info(f"线上向量生成器初始化: provider={self.provider}, model={self.model_name}")
    
    def _get_api_key(self, api_key: str = None) -> str:
        """
        获取 API Key
        
        Args:
            api_key: 直接传入的 API Key
        
        Returns:
            str: API Key
        """
        if api_key:
            return api_key
        
        if self.provider == "zhipuai":
            return os.environ.get("ZHIPUAI_API_KEY") or EMBEDDING_CONFIG.get("ONLINE_API_KEY", "")
        elif self.provider == "openai":
            return os.environ.get("OPENAI_API_KEY") or EMBEDDING_CONFIG.get("OPENAI_API_KEY", "")
        
        return ""
    
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
        if not self.api_key:
            logger.warning("API Key 未配置，使用模拟向量")
            return self._generate_mock_vectors(text, normalize)
        
        try:
            if self.provider == "zhipuai":
                return self._encode_zhipuai(text, normalize)
            elif self.provider == "openai":
                return self._encode_openai(text, normalize)
            else:
                logger.error(f"不支持的提供商: {self.provider}")
                return self._generate_mock_vectors(text, normalize)
        except Exception as e:
            logger.error(f"线上向量生成失败: {e}")
            return self._generate_mock_vectors(text, normalize)
    
    def _encode_zhipuai(
        self,
        text: Union[str, List[str]],
        normalize: bool
    ) -> Union[List[float], List[List[float]]]:
        """
        智谱 AI 向量生成
        
        Args:
            text: 输入文本或文本列表
            normalize: 是否归一化
        
        Returns:
            Union[List[float], List[List[float]]]: 向量或向量列表
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        all_embeddings = []
        
        for t in texts:
            payload = {
                "model": self.model_name,
                "input": t
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            embedding = result["data"][0]["embedding"]
            
            if normalize:
                embedding = self._normalize_vector(embedding)
            
            all_embeddings.append(embedding)
        
        logger.debug(f"智谱 AI 向量生成成功: {len(all_embeddings)} 条")
        
        return all_embeddings[0] if is_single else all_embeddings
    
    def _encode_openai(
        self,
        text: Union[str, List[str]],
        normalize: bool
    ) -> Union[List[float], List[List[float]]]:
        """
        OpenAI 向量生成
        
        Args:
            text: 输入文本或文本列表
            normalize: 是否归一化
        
        Returns:
            Union[List[float], List[List[float]]]: 向量或向量列表
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        model_name = EMBEDDING_CONFIG.get("OPENAI_MODEL_NAME", "text-embedding-3-small")
        
        payload = {
            "model": model_name,
            "input": texts
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        embeddings = [item["embedding"] for item in result["data"]]
        
        if normalize:
            embeddings = [self._normalize_vector(e) for e in embeddings]
        
        logger.debug(f"OpenAI 向量生成成功: {len(embeddings)} 条")
        
        return embeddings[0] if is_single else embeddings
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        归一化向量
        
        Args:
            vector: 输入向量
        
        Returns:
            List[float]: 归一化后的向量
        """
        vec = np.array(vector)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
    
    def _generate_mock_vectors(
        self,
        text: Union[str, List[str]],
        normalize: bool
    ) -> Union[List[float], List[List[float]]]:
        """
        生成模拟向量（用于测试或 API 不可用时）
        
        Args:
            text: 输入文本或文本列表
            normalize: 是否归一化
        
        Returns:
            Union[List[float], List[List[float]]]: 模拟向量
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        vectors = []
        for t in texts:
            np.random.seed(hash(t) % (2 ** 32))
            vector = np.random.randn(self.embedding_dim).astype(np.float32)
            
            if normalize:
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            
            vectors.append(vector.tolist())
        
        return vectors[0] if is_single else vectors
    
    def get_embedding_dim(self) -> int:
        """
        获取向量维度
        
        Returns:
            int: 向量维度
        """
        return self.embedding_dim


class LocalEmbedding:
    """
    本地向量生成器
    
    使用 sentence-transformers 本地模型
    """
    
    def __init__(
        self,
        model_name: str = None,
        embedding_dim: int = None,
        device: str = None
    ):
        """
        初始化本地向量生成器
        
        Args:
            model_name: 模型名称
            embedding_dim: 向量维度
            device: 运行设备 (cpu/cuda)
        """
        self.model_name = model_name or EMBEDDING_CONFIG.get("LOCAL_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_dim = embedding_dim or EMBEDDING_CONFIG.get("LOCAL_EMBEDDING_DIM", 768)
        self.device = device or EMBEDDING_CONFIG.get("LOCAL_DEVICE", "cpu")
        self.model = None
        self._initialized = False
        
        logger.info(f"本地向量生成器初始化: model={self.model_name}, dim={self.embedding_dim}, device={self.device}")
    
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
            logger.info(f"本地模型加载成功: {self.model_name}")
        
        except ImportError:
            logger.warning("sentence-transformers 未安装，使用模拟向量")
            self._initialized = True
        
        except Exception as e:
            logger.error(f"本地模型加载失败: {e}")
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
            logger.error(f"本地向量生成失败: {e}")
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


class EmbeddingGenerator:
    """
    向量生成器
    
    统一接口，支持线上和本地模型
    """
    
    def __init__(
        self,
        embedding_type: str = None,
        provider: str = None,
        model_name: str = None,
        embedding_dim: int = None,
        device: str = None,
        api_key: str = None,
        api_base: str = None
    ):
        """
        初始化向量生成器
        
        Args:
            embedding_type: 向量类型 (online/local)
            provider: 线上服务提供商 (zhipuai/openai)
            model_name: 模型名称
            embedding_dim: 向量维度
            device: 本地模型运行设备 (cpu/cuda)
            api_key: API 密钥
            api_base: API 基础地址
        """
        self.embedding_type = embedding_type or EMBEDDING_TYPE
        self.embedding_dim = embedding_dim or DEFAULT_EMBEDDING_DIM
        
        if self.embedding_type == "online":
            self._generator = OnlineEmbedding(
                provider=provider,
                model_name=model_name,
                api_key=api_key,
                api_base=api_base,
                embedding_dim=self.embedding_dim
            )
        else:
            self._generator = LocalEmbedding(
                model_name=model_name,
                embedding_dim=self.embedding_dim,
                device=device
            )
        
        logger.info(f"向量生成器初始化: type={self.embedding_type}")
    
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
        return self._generator.encode(text, normalize)
    
    def get_embedding_dim(self) -> int:
        """
        获取向量维度
        
        Returns:
            int: 向量维度
        """
        return self._generator.get_embedding_dim()
    
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        if hasattr(self._generator, 'is_initialized'):
            return self._generator.is_initialized()
        return True


def create_embedding_generator(
    embedding_type: str = None,
    provider: str = None,
    model_name: str = None,
    embedding_dim: int = None,
    device: str = None,
    api_key: str = None,
    api_base: str = None
) -> EmbeddingGenerator:
    """
    创建向量生成器
    
    Args:
        embedding_type: 向量类型 (online/local)
        provider: 线上服务提供商
        model_name: 模型名称
        embedding_dim: 向量维度
        device: 本地模型运行设备
        api_key: API 密钥
        api_base: API 基础地址
    
    Returns:
        EmbeddingGenerator: 向量生成器实例
    """
    return EmbeddingGenerator(
        embedding_type=embedding_type,
        provider=provider,
        model_name=model_name,
        embedding_dim=embedding_dim,
        device=device,
        api_key=api_key,
        api_base=api_base
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
