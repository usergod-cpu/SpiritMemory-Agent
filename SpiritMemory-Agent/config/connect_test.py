import redis
from pymongo import MongoClient
from pymilvus import connections
from db_config import REDIS_CONFIG, MONGODB_CONFIG, MILVUS_CONFIG

def test_redis_connection():
    """测试 Redis 连接"""
    try:
        r = redis.Redis(
            host=REDIS_CONFIG["HOST"],
            port=REDIS_CONFIG["PORT"],
            password=REDIS_CONFIG["PASSWORD"],
            db=REDIS_CONFIG["DB"],
            socket_connect_timeout=REDIS_CONFIG["CONNECTION_TIMEOUT"]
        )
        r.ping()
        print("[OK] Redis 连接成功")
        return True
    except Exception as e:
        print(f"[FAIL] Redis 连接失败: {e}")
        return False

def test_mongodb_connection():
    """测试 MongoDB 连接"""
    try:
        client = MongoClient(
            host=MONGODB_CONFIG["HOST"],
            port=MONGODB_CONFIG["PORT"],
            serverSelectionTimeoutMS=MONGODB_CONFIG["CONNECTION_TIMEOUT"] * 1000
        )
        client.admin.command('ping')
        print("[OK] MongoDB 连接成功")
        return True
    except Exception as e:
        print(f"[FAIL] MongoDB 连接失败: {e}")
        return False

def test_milvus_connection():
    """测试 Milvus 连接"""
    try:
        connections.connect(
            alias="default",
            host=MILVUS_CONFIG["HOST"],
            port=MILVUS_CONFIG["PORT"]
        )
        print("[OK] Milvus 连接成功")
        return True
    except Exception as e:
        print(f"[FAIL] Milvus 连接失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试数据库连接...")
    print("=" * 50)
    
    redis_success = test_redis_connection()
    mongodb_success = test_mongodb_connection()
    milvus_success = test_milvus_connection()
    
    print("=" * 50)
    print("测试结果汇总:")
    print(f"Redis: {'成功' if redis_success else '失败'}")
    print(f"MongoDB: {'成功' if mongodb_success else '失败'}")
    print(f"Milvus: {'成功' if milvus_success else '失败'}")
