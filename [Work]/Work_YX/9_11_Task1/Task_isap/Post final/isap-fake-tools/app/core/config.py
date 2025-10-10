import os
from dotenv import load_dotenv

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Settings:
    PROJECT_NAME: str = "ISAP Demo Data Generator"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "172.16.10.196")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "isap_admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "113RfkdsDMDb6H7T")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "db_house")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    print(f"数据库连接URL----: {DATABASE_URL}")
    # 数据生成配置
    DEFAULT_RECORDS_PER_DAY: int = int(os.getenv("DEFAULT_RECORDS_PER_DAY", "100"))
    
    # 时间规律配置
    PEAK_HOURS: list = [9, 10, 11, 12, 18, 19, 20, 21]  # 高峰期时段
    PEAK_DAYS: list = [5, 6, 7]  # 高峰期星期（1=周一）
    
    # 配置文件路径
    CONFIG_FILE_PATH: str = os.getenv("CONFIG_FILE_PATH", "configs/")

settings = Settings()