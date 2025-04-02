"""
Utils package - Utilitários e ferramentas do framework
"""

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.api_key = os.getenv("OPENAI_KEY")
        logger.info("ModelManager inicializado")
        
    def configure(self, model: Optional[str] = None, temperature: Optional[float] = None) -> None:
        """Configura os parâmetros do modelo."""
        if model:
            self.model = model
        if temperature is not None:
            self.temperature = temperature
        logger.info(f"Modelo configurado: {self.model} (temperatura: {self.temperature})")
        
    def get_config(self) -> Dict:
        """Retorna a configuração atual do modelo."""
        return {
            "model": self.model,
            "temperature": self.temperature
        }

def get_env_status() -> Dict[str, bool]:
    """Verifica o status das variáveis de ambiente necessárias."""
    return {
        "OPENAI_KEY": bool(os.getenv("OPENAI_KEY"))
    }

def validate_env() -> bool:
    """Valida se todas as variáveis de ambiente necessárias estão configuradas."""
    status = get_env_status()
    missing = [key for key, value in status.items() if not value]
    
    if missing:
        logger.error(f"Variáveis de ambiente faltando: {', '.join(missing)}")
        return False
        
    logger.info("Todas as variáveis de ambiente estão configuradas")
    return True

