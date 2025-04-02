"""
Gerenciador de modelos de IA com suporte a múltiplos provedores e fallback automático.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import google.generativeai as genai
import openai
import openrouter
from cachetools import TTLCache
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.utils.env import get_env_var


class ModelProvider(str, Enum):
    """Provedores de modelos suportados."""
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class ModelConfig(BaseModel):
    """Configuração de um modelo."""
    provider: ModelProvider
    model_id: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class ModelManager:
    """Gerenciador de modelos de IA."""

    def __init__(self) -> None:
        """Inicializa o gerenciador de modelos."""
        self.cache = TTLCache(
            maxsize=int(get_env_var("CACHE_MAXSIZE", "100")),
            ttl=int(get_env_var("CACHE_TTL", "3600"))
        )
        self.configs: Dict[str, ModelConfig] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        """Carrega as configurações dos modelos."""
        # OpenAI
        openai_key = get_env_var("OPENAI_KEY")
        if openai_key:
            self._add_openai_models(openai_key)

        # OpenRouter
        openrouter_key = get_env_var("OPENROUTER_KEY")
        if openrouter_key:
            self._add_openrouter_models(openrouter_key)

        # Gemini
        gemini_key = get_env_var("GEMINI_KEY")
        if gemini_key:
            self._add_gemini_models(gemini_key)

    def _add_openai_models(self, api_key: str) -> None:
        """Adiciona modelos OpenAI."""
        models = [
            ("gpt-4-turbo", "gpt-4-turbo-preview"),
            ("gpt-4", "gpt-4"),
            ("gpt-3.5-turbo", "gpt-3.5-turbo"),
        ]
        
        for name, model_id in models:
            self.configs[name] = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_id=model_id,
                api_key=api_key,
                timeout=int(get_env_var(f"OPENAI_{name.upper()}_TIMEOUT", get_env_var("OPENAI_TIMEOUT", "30"))),
                max_retries=int(get_env_var(f"OPENAI_{name.upper()}_MAX_RETRIES", get_env_var("OPENAI_MAX_RETRIES", "3"))),
                temperature=float(get_env_var(f"OPENAI_{name.upper()}_TEMPERATURE", get_env_var("OPENAI_TEMPERATURE", "0.7"))),
                max_tokens=int(get_env_var(f"OPENAI_{name.upper()}_MAX_TOKENS", get_env_var("OPENAI_MAX_TOKENS", "4000"))),
            )

    def _add_openrouter_models(self, api_key: str) -> None:
        """Adiciona modelos OpenRouter."""
        models = [
            ("openrouter/auto", "auto"),
            ("anthropic/claude-3-opus", "anthropic/claude-3-opus"),
            ("anthropic/claude-3-sonnet", "anthropic/claude-3-sonnet"),
        ]
        
        for name, model_id in models:
            self.configs[name] = ModelConfig(
                provider=ModelProvider.OPENROUTER,
                model_id=model_id,
                api_key=api_key,
                timeout=int(get_env_var(f"OPENROUTER_{name.upper().replace('/', '_')}_TIMEOUT", get_env_var("OPENROUTER_TIMEOUT", "30"))),
                max_retries=int(get_env_var(f"OPENROUTER_{name.upper().replace('/', '_')}_MAX_RETRIES", get_env_var("OPENROUTER_MAX_RETRIES", "3"))),
                temperature=float(get_env_var(f"OPENROUTER_{name.upper().replace('/', '_')}_TEMPERATURE", get_env_var("OPENROUTER_TEMPERATURE", "0.7"))),
                max_tokens=int(get_env_var(f"OPENROUTER_{name.upper().replace('/', '_')}_MAX_TOKENS", get_env_var("OPENROUTER_MAX_TOKENS", "4000"))),
            )

    def _add_gemini_models(self, api_key: str) -> None:
        """Adiciona modelos Gemini."""
        models = [
            ("gemini-pro", "gemini-pro"),
            ("gemini-pro-vision", "gemini-pro-vision"),
        ]
        
        for name, model_id in models:
            self.configs[name] = ModelConfig(
                provider=ModelProvider.GEMINI,
                model_id=model_id,
                api_key=api_key,
                timeout=int(get_env_var(f"GEMINI_{name.upper().replace('-', '_')}_TIMEOUT", get_env_var("GEMINI_TIMEOUT", "30"))),
                max_retries=int(get_env_var(f"GEMINI_{name.upper().replace('-', '_')}_MAX_RETRIES", get_env_var("GEMINI_MAX_RETRIES", "3"))),
                temperature=float(get_env_var(f"GEMINI_{name.upper().replace('-', '_')}_TEMPERATURE", get_env_var("GEMINI_TEMPERATURE", "0.7"))),
                max_tokens=int(get_env_var(f"GEMINI_{name.upper().replace('-', '_')}_MAX_TOKENS", get_env_var("GEMINI_MAX_TOKENS", "4000"))),
            )

    def get_available_models(self) -> List[str]:
        """Retorna a lista de modelos disponíveis."""
        return list(self.configs.keys())

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Retorna a configuração de um modelo."""
        return self.configs.get(model_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def generate(
        self,
        prompt: str,
        model_name: str = "gpt-4-turbo",
        elevation_model: Optional[str] = None,
        force: bool = False,
        **kwargs: Any,
    ) -> Union[str, Dict[str, Any]]:
        """
        Gera uma resposta usando o modelo especificado.

        Args:
            prompt: O prompt para gerar a resposta.
            model_name: Nome do modelo a ser usado.
            elevation_model: Modelo alternativo para fallback.
            force: Se True, força o uso do modelo especificado sem fallback.
            **kwargs: Argumentos adicionais para a API do modelo.

        Returns:
            A resposta gerada pelo modelo.

        Raises:
            ValueError: Se o modelo não estiver disponível.
            Exception: Se ocorrer um erro na geração.
        """
        # Verifica se o modelo está disponível
        config = self.get_model_config(model_name)
        if not config:
            raise ValueError(f"Modelo {model_name} não disponível")

        # Tenta usar o cache
        cache_key = f"{model_name}:{prompt}"
        if cached := self.cache.get(cache_key):
            return cached

        try:
            # Gera a resposta usando o modelo apropriado
            response = await self._generate_with_provider(config, prompt, **kwargs)
            self.cache[cache_key] = response
            return response

        except Exception as e:
            if force or not elevation_model:
                raise e

            # Tenta usar o modelo de elevação
            elevation_config = self.get_model_config(elevation_model)
            if not elevation_config:
                raise ValueError(f"Modelo de elevação {elevation_model} não disponível")

            return await self._generate_with_provider(elevation_config, prompt, **kwargs)

    async def _generate_with_provider(
        self,
        config: ModelConfig,
        prompt: str,
        **kwargs: Any,
    ) -> Union[str, Dict[str, Any]]:
        """Gera uma resposta usando um provedor específico."""
        if config.provider == ModelProvider.OPENAI:
            client = openai.AsyncClient(api_key=config.api_key)
            response = await client.chat.completions.create(
                model=config.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content

        elif config.provider == ModelProvider.OPENROUTER:
            client = openrouter.AsyncClient(api_key=config.api_key)
            response = await client.chat.completions.create(
                model=config.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content

        elif config.provider == ModelProvider.GEMINI:
            genai.configure(api_key=config.api_key)
            model = genai.GenerativeModel(config.model_id)
            response = await model.generate_content_async(prompt, **kwargs)
            return response.text

        raise ValueError(f"Provedor {config.provider} não suportado") 