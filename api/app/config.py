# API Configuration
import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    """Base configuration class"""
    # Flask settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    DEBUG: bool = FLASK_ENV == 'development'
    
    # MongoDB settings
    MONGO_URI: str = os.getenv('MONGO_URI', 'mongodb://localhost:27017/inventario_new')
    
    # Legacy database (for migration)
    LEGACY_DB_PATH: str = os.getenv('LEGACY_DB_PATH', '/shared/databases/inventario.sqlite3')
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours
    
    # CORS settings - Fixed: using default_factory instead of mutable default
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    )
    
    # Redis/Celery (for background tasks)
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL: str = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    
    # Email settings (migrated from legacy)
    SMTP_HOST: str = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER: str = os.getenv('SMTP_USER', 'sistemasccfnld@laboratoriocelular.net')
    SMTP_PASS: str = os.getenv('SMTP_PASS', '')
    SMTP_FROM_NAME: str = os.getenv('SMTP_FROM_NAME', 'Celulares Crédito Fácil')
    
    # Business settings
    SUCURSALES: list = field(default_factory=lambda: [
        "Colinas", "Hidalgo", "Voluntad 1", "Reservas", "Villas", "Todas"
    ])
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000

@dataclass
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG: bool = True
    TESTING: bool = False

@dataclass 
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG: bool = False
    TESTING: bool = False
    
    # Override with stronger defaults for production
    SECRET_KEY: str = os.getenv('SECRET_KEY')  # Must be set in production
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY')  # Must be set in production
    
    def __post_init__(self):
        if not self.SECRET_KEY or self.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production")
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set in production")

@dataclass
class TestingConfig(Config):
    """Testing configuration"""
    DEBUG: bool = True
    TESTING: bool = True
    MONGO_URI: str = 'mongodb://localhost:27017/inventario_test'

# Configuration factory
def get_config(env_name='development'):
    """Get configuration instance by environment name"""
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'default': DevelopmentConfig
    }
    
    config_class = configs.get(env_name, DevelopmentConfig)
    return config_class()

# For backward compatibility, provide default development config
config = {
    'development': lambda: DevelopmentConfig(),
    'production': lambda: ProductionConfig(),
    'testing': lambda: TestingConfig(),
    'default': lambda: DevelopmentConfig()
}