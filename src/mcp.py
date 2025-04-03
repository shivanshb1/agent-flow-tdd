# src/mpc.py
"""
Módulo para lidar com o protocolo MCP (Model Context Protocol).
"""
import json
import logging
import os
import sys
import time
from typing import Optional, Dict, Any

from src.app import AgentOrchestrator
from src.core.logger import trace, agent_span, generation_span
from src.core.utils import ModelManager

from openai import OpenAI

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/mcp_server.log")
    ]
)

logger = logging.getLogger(__name__)

try:
    from mcp_sdk import BaseMCPHandler, Message, Response
except ImportError:
    # Mock classes para testes
    class Message:
        """Mock da classe Message do SDK MCP."""
        def __init__(self, content: str, metadata: Dict[str, Any]):
            self.content = content
            self.metadata = metadata

    class Response:
        """Mock da classe Response do SDK MCP."""
        def __init__(self, content: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
            self.content = content
            self.metadata = metadata or {}

    class BaseMCPHandler:
        """Mock da classe BaseMCPHandler do SDK MCP."""
        def __init__(self):
            self.initialized = False
            self.hook = "/prompt-tdd"

        def initialize(self, api_key: str) -> None:
            """Inicializa o handler com a chave da API."""
            self.initialized = True

        def run(self) -> None:
            """Executa o loop principal do handler."""
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break

                    data = json.loads(line)
                    message = Message(data["content"], data["metadata"])
                    response = self.handle_message(message)
                    print(json.dumps({
                        "content": response.content,
                        "metadata": response.metadata
                    }))
                except Exception as e:
                    logging.error(f"Erro ao processar mensagem: {str(e)}")
                    break

        def handle_message(self, message: Message) -> Response:
            """Processa uma mensagem e retorna uma resposta."""
            raise NotImplementedError()


class PromptManager:
    def __init__(self):
        self.templates: Dict[str, str] = {}
        logger.info("PromptManager inicializado")
        
    def add_template(self, name: str, template: str) -> None:
        """Adiciona um novo template de prompt."""
        self.templates[name] = template
        logger.info(f"Template '{name}' adicionado")
        
    def get_template(self, name: str) -> Optional[str]:
        """Recupera um template de prompt pelo nome."""
        template = self.templates.get(name)
        if not template:
            logger.warning(f"Template '{name}' não encontrado")
        return template
        
    def format_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        """Formata um prompt usando um template e variáveis."""
        template = self.get_template(template_name)
        if not template:
            return None
            
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Erro ao formatar prompt: variável {e} não fornecida")
            return None
        except Exception as e:
            logger.error(f"Erro ao formatar prompt: {str(e)}")
            return None 

class LLMProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_KEY")
        if not self.api_key:
            logger.warning("OPENAI_KEY não encontrada nas variáveis de ambiente")
        self.client = OpenAI(api_key=self.api_key)
        
    def generate(self, prompt: str, options: Dict[str, Any]) -> Optional[str]:
        try:
            model = options.get("model", "gpt-3.5-turbo")
            temperature = options.get("temperature", 0.7)
            format = options.get("format", "json")
            
            logger.info(f"Gerando resposta com modelo {model} (temperatura: {temperature})")
            
            # Ajusta o prompt para gerar resposta no formato correto
            if format == "markdown":
                prompt = f"Por favor, formate sua resposta em Markdown com:\n- Títulos e subtítulos\n- Listas\n- Destaques\n- Tabelas quando relevante\n\nPrompt: {prompt}"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            
            # Retorna sempre um dicionário estruturado
            return {
                "content": content,
                "metadata": {
                    "status": "success",
                    "format": format
                }
            }
                
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            return None

class MCPHandler:
    """Manipulador do protocolo MCP."""

    def __init__(self, llm_provider: LLMProvider, prompt_manager: PromptManager):
        """Inicializa o manipulador MCP."""
        self.orchestrator = None
        self.model_manager = ModelManager()
        self.llm_provider = llm_provider
        self.prompt_manager = prompt_manager
        logger.info("MCPHandler inicializado com sucesso")

    def initialize(self, api_key: Optional[str] = None):
        """Inicializa o orquestrador com a chave da API."""
        logger.info("Inicializando MCPHandler...")
        self.orchestrator = AgentOrchestrator(api_key=api_key)
        self.model_manager.configure(
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        logger.info("MCPHandler inicializado com sucesso")

    @trace(workflow_name="MCP Workflow")
    @agent_span()
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Processa uma mensagem recebida."""
        try:
            content = message.get("content")
            metadata = message.get("metadata", {})
            
            if not content:
                logger.warning("Mensagem recebida sem conteúdo")
                return None
                
            logger.info(f"Processando mensagem: {content}")
            logger.info(f"Metadata: {metadata}")
            
            with generation_span(name="LLM Generation"):
                response = self.llm_provider.generate(content, metadata.get("options", {}))
            
            if response:
                logger.info(f"Resposta gerada: {response['content']}")
                return response["content"]
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return None

    def run(self):
        """Executa o manipulador MCP."""
        pipe_path = "logs/mcp_pipe.log"
        logger.info(f"Iniciando leitura do arquivo: {pipe_path}")
        
        try:
            # Espera até que o arquivo exista
            while not os.path.exists(pipe_path):
                logger.info("Aguardando criação do arquivo...")
                time.sleep(1)
            
            # Lê o conteúdo do arquivo
            with open(pipe_path, 'r') as f:
                content = f.read().strip()
                if content:
                    try:
                        message = json.loads(content)
                        response = self.process_message(message)
                        if response:
                            logger.info(f"Resposta gerada: {response}")
                            print(response)
                        else:
                            logger.warning("Nenhuma resposta gerada")
                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao decodificar JSON: {str(e)}")
                else:
                    logger.warning("Arquivo vazio")
                    
        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {str(e)}")
        finally:
            if os.path.exists(pipe_path):
                os.remove(pipe_path)
                logger.info("Arquivo removido")

if __name__ == "__main__":
    # Executar como serviço standalone
    llm_provider = LLMProvider()
    prompt_manager = PromptManager()
    handler = MCPHandler(llm_provider, prompt_manager)
    handler.initialize(api_key=None)  # A chave será obtida das variáveis de ambiente
    handler.run()
