"""
Configuration module for DreamHeaven RAG API
"""

import os
from typing import Optional


class Config:
    """Configuration class for the application"""
    
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.PORT = int(os.getenv("PORT", 8001))
        self.HOST = os.getenv("HOST", "0.0.0.0")
        
        # Validate required environment variables
        if not self.DATABASE_URL or not self.OPENAI_API_KEY:
            raise ValueError("DATABASE_URL and OPENAI_API_KEY must be set in environment variables. Please add them in Railway dashboard under Variables tab.")
    
    @property
    def database_url(self) -> str:
        return self.DATABASE_URL
    
    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY
    
    @property
    def port(self) -> int:
        return self.PORT
    
    @property
    def host(self) -> str:
        return self.HOST
