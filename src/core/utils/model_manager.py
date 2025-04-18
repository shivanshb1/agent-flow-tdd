"""
Gerenciador de modelos de IA com suporte a múltiplos provedores e fallback automático.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import os

import google.generativeai as genai
import openai
import openrouter
from cachetools import TTLCache
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.utils.env import get_env_var
from src.core.utils.logger import get_logger

logger = get_logger(__name__)


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
        self.model = None
        self.temperature = None
        self.api_key = None

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

    def configure(self, model: str, temperature: float = 0.7):
        """Configura o modelo a ser usado."""
        self.model = model
        self.temperature = temperature

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def generate(
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
        try:
            # Verifica se o modelo está disponível
            config = self.get_model_config(model_name)
            if not config:
                raise ValueError(f"Modelo {model_name} não disponível")

            # Tenta usar o cache
            cache_key = f"{model_name}:{prompt}"
            if cached := self.cache.get(cache_key):
                return cached

            # Adiciona parâmetros do modelo aos kwargs
            kwargs.update({
                "model": model_name,
                "force": force,
            })

            # Gera a resposta usando o modelo apropriado
            response = self._generate_with_provider(config, prompt, **kwargs)
            self.cache[cache_key] = response
            return response

        except Exception as e:
            if force or not elevation_model:
                raise e

            # Tenta usar o modelo de elevação
            elevation_config = self.get_model_config(elevation_model)
            if not elevation_config:
                raise ValueError(f"Modelo de elevação {elevation_model} não disponível")

            # Adiciona parâmetros do modelo aos kwargs
            kwargs.update({
                "model": elevation_model,
                "elevation_model": None,  # Evita recursão infinita
                "force": True,  # Força o uso do modelo de elevação
            })

            return self._generate_with_provider(elevation_config, prompt, **kwargs)

    def _generate_with_provider(
        self,
        config: ModelConfig,
        prompt: str,
        **kwargs: Any,
    ) -> Union[str, Dict[str, Any]]:
        """Gera uma resposta usando um provedor específico."""
        try:
            if config.provider == ModelProvider.OPENAI:
                client = openai.Client(api_key=config.api_key)
                messages = []
                
                # Se houver system_prompt nos kwargs, adiciona como mensagem do sistema
                if "system_prompt" in kwargs:
                    messages.append({"role": "system", "content": kwargs.pop("system_prompt")})
                
                # Adiciona o prompt do usuário
                messages.append({"role": "user", "content": prompt})
                
                # Remove parâmetros não suportados
                kwargs.pop("model", None)
                kwargs.pop("elevation_model", None)
                kwargs.pop("force", None)
                
                # Configura parâmetros padrão
                if "temperature" not in kwargs:
                    kwargs["temperature"] = config.temperature
                if "max_tokens" not in kwargs and config.max_tokens:
                    kwargs["max_tokens"] = config.max_tokens
                
                try:
                    response = client.chat.completions.create(
                        model=config.model_id,
                        messages=messages,
                        **kwargs,
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Erro ao gerar resposta com {config.model_id}: {str(e)}")
                    raise

            elif config.provider == ModelProvider.OPENROUTER:
                client = openrouter.Client(api_key=config.api_key)
                messages = []
                
                # Se houver system_prompt nos kwargs, adiciona como mensagem do sistema
                if "system_prompt" in kwargs:
                    messages.append({"role": "system", "content": kwargs.pop("system_prompt")})
                
                # Adiciona o prompt do usuário
                messages.append({"role": "user", "content": prompt})
                
                # Remove parâmetros não suportados
                kwargs.pop("model", None)
                kwargs.pop("elevation_model", None)
                kwargs.pop("force", None)
                
                # Configura parâmetros padrão
                if "temperature" not in kwargs:
                    kwargs["temperature"] = config.temperature
                if "max_tokens" not in kwargs and config.max_tokens:
                    kwargs["max_tokens"] = config.max_tokens
                
                try:
                    response = client.chat.completions.create(
                        model=config.model_id,
                        messages=messages,
                        **kwargs,
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Erro ao gerar resposta com {config.model_id}: {str(e)}")
                    raise

            elif config.provider == ModelProvider.GEMINI:
                genai.configure(api_key=config.api_key)
                model = genai.GenerativeModel(config.model_id)
                
                # Remove parâmetros não suportados
                kwargs.pop("system_prompt", None)
                kwargs.pop("model", None)
                kwargs.pop("elevation_model", None)
                kwargs.pop("force", None)
                
                # Configura os parâmetros do modelo
                generation_config = {
                    "temperature": kwargs.pop("temperature", config.temperature),
                    "max_output_tokens": kwargs.pop("max_tokens", config.max_tokens),
                }
                
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config,
                        **kwargs
                    )
                    return response.text
                except Exception as e:
                    logger.error(f"Erro ao gerar resposta com {config.model_id}: {str(e)}")
                    raise

            raise ValueError(f"Provedor {config.provider} não suportado")
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com {config.provider}: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_response(self, prompt: str) -> Dict[str, Any]:
        """Gera uma resposta usando o modelo configurado."""
        if not self.model:
            raise ValueError("Modelo não configurado")

        if "gpt" in self.model:
            return self._generate_openai_response(prompt)
        elif "gemini" in self.model:
            return self._generate_gemini_response(prompt)
        elif "claude" in self.model:
            return self._generate_anthropic_response(prompt)
        else:
            raise ValueError(f"Modelo não suportado: {self.model}")

    def _generate_openai_response(self, prompt: str) -> Dict[str, Any]:
        """Gera uma resposta usando o modelo OpenAI."""
        client = openai.OpenAI(api_key=os.getenv("OPENAI_KEY"))
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return {
            "content": response.choices[0].message.content,
            "model": self.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    def _generate_gemini_response(self, prompt: str) -> Dict[str, Any]:
        """Gera uma resposta usando o modelo Gemini."""
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        return {
            "content": response.text,
            "model": self.model,
            "usage": {}  # Gemini não fornece informações de uso
        }

    def _generate_anthropic_response(self, prompt: str) -> Dict[str, Any]:
        """Gera uma resposta usando o modelo Anthropic via OpenRouter."""
        client = openrouter.OpenRouter(api_key=os.getenv("OPENROUTER_KEY"))
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return {
            "content": response.choices[0].message.content,
            "model": self.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        } 