from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "KubeSentinel AI Backend"
    DEBUG: bool = True
    
    # LLM Settings — DashScope (通义千问)
    DASHSCOPE_API_KEY: str = ""
    LLM_MODEL: str = "qwen-turbo"
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.1

    # LLM Provider switch: "dashscope" | "openai"
    LLM_PROVIDER: str = "dashscope"

    # OpenAI-compatible API (for DeepSeek / GPT-4 etc.)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # ZhipuAI (GLM-4/5)
    ZHIPUAI_API_KEY: str = Field("your-zhipu-api-key", description="智谱清言(GLM-5) API 密钥")
    
    # Database Overhaul Overrides
    POSTGRES_URL: str = Field("postgresql+asyncpg://postgres:postgres@localhost:5432/kubesentinel", description="PostgreSQL 连接串")
    REDIS_URL: str = Field("redis://localhost:6379/0", description="Redis 连接串")

    # n8n Workflow Automation Phase 5
    N8N_WEBHOOK_URL: str = Field("http://localhost:5678/webhook/kubesentinel", description="n8n 接收 KubeSentinel 告警的触发流入口")
    N8N_SECRET_TOKEN: str = Field("super-secure-token", description="n8n 双向通信秘钥")
    
    # Healing behavior
    HEALING_CONFIDENCE_THRESHOLD: float = 0.75
    HEALING_COOLDOWN_SECONDS: int = 300
    MAX_AUTO_HEALING_RETRIES: int = 3
    HIGH_RISK_REQUIRE_APPROVAL: bool = True
    
    # K8s Settings
    IN_CLUSTER: bool = False
    
    # Prometheus
    PROMETHEUS_URL: str = "http://localhost:9090"

    # Loki
    LOKI_URL: str = "http://localhost:3100"

    # Alertmanager
    ALERTMANAGER_URL: Optional[str] = None

    # Notification
    FEISHU_WEBHOOK_URL: Optional[str] = None
    DINGTALK_WEBHOOK_URL: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
