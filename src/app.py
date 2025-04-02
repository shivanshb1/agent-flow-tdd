import time
from typing import List, Dict, Any
import json

from src.core.utils import ModelManager

class Message:
    def __init__(self, content: str, source: str, timestamp: float):
        self.content = content
        self.source = source
        self.timestamp = timestamp

class ConversationHistory:
    def __init__(self):
        self.messages = []
    
    def add_message(self, message: Message):
        self.messages.append(message)
    
    def get_context(self, window_size=5) -> str:
        return "\n".join([f"{msg.source}: {msg.content}" for msg in self.messages[-window_size:]])

class TriageAgent:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.system_prompt = """
        Você é um roteador especializado em desenvolvimento de software. Sua tarefa é analisar a conversa e decidir quais agentes devem ser acionados:
        - Pré-processamento: Quando precisar clarificar requisitos ou processar dados
        - Análise: Quando detectar necessidade de validação técnica ou métricas
        - Visualização: Quando precisar apresentar resultados ou formatar saídas

        Responda apenas com JSON contendo lista de agentes relevantes.
        """
    
    def route(self, context: str) -> List[str]:
        response = self.model_manager.generate(
            prompt=context,
            system_prompt=self.system_prompt,
            temperature=0
        )
        return json.loads(response)

class DeterministicPreprocessingAgent:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.system_prompt = """
        Você é um especialista em engenharia de requisitos. Suas tarefas:
        1. Limpeza: Remover ambiguidades e subjetividades
        2. Transformação: Estruturar em formato Feature -> Critérios de Aceite
        3. Agregação: Combinar com histórico mantendo consistência

        Mantenha neutralidade técnica e foco em testabilidade.
        """
    
    def process(self, input_text: str, context: str) -> str:
        prompt = f"Contexto:\n{context}\n\nInput:\n{input_text}"
        return self.model_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.3
        )

class AnalyticalAnalysisAgent:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.system_prompt = """
        Você é um arquiteto de software experiente. Realize:
        1. Análise Estatística: Quantidade/Complexidade de requisitos
        2. Correlação: Identificar dependências entre requisitos
        3. Regressão: Prever gaps de implementação

        Use métricas técnicas e padrões de mercado.
        """
    
    def analyze(self, processed_data: str, context: str) -> str:
        prompt = f"Dados Processados:\n{processed_data}\n\nContexto:\n{context}"
        return self.model_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.5
        )

class ToolVisualizationAgent:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.markdown_prompt = """
        Transforme a análise em markdown com:
        - Seções hierárquicas
        - Tabelas comparativas
        - Destaques para pontos críticos
        """
        
        self.json_prompt = """
        Estruture em JSON com:
        - feature (string)
        - acceptance_criteria (array)
        - test_scenarios (array)
        - complexity (int 1-5)
        - dependencies (array)
        """
    
    def visualize(self, analysis: str, format_type: str) -> str:
        prompt = f"Análise:\n{analysis}"
        system_prompt = self.markdown_prompt if format_type == "markdown" else self.json_prompt
        return self.model_manager.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0
        )

class AgentOrchestrator:
    def __init__(self, api_key: str = None):
        self.history = ConversationHistory()
        self.model_manager = ModelManager()
        
        if api_key:
            self.model_manager.configure(
                model="gpt-3.5-turbo",
                elevation_model="gpt-4-turbo",
                api_key=api_key
            )
            
        self.triage = TriageAgent(self.model_manager)
        self.preprocessor = DeterministicPreprocessingAgent(self.model_manager)
        self.analyst = AnalyticalAnalysisAgent(self.model_manager)
        self.visualizer = ToolVisualizationAgent(self.model_manager)
    
    def handle_input(self, user_input: str) -> Dict[str, Any]:
        # Registrar entrada do usuário
        self.history.add_message(Message(user_input, "User", time.time()))
        
        # Loop de processamento iterativo
        final_output = None
        processed = None
        analysis = None
        
        context = self.history.get_context()
        
        # Etapa 1: Triagem
        agents = self.triage.route(context)
        
        # Etapa 2: Pré-processamento
        if "preprocessor" in agents:
            processed = self.preprocessor.process(user_input, context)
            self.history.add_message(Message(processed, "Preprocessor", time.time()))
        
        # Etapa 3: Análise
        if "analyst" in agents:
            analysis = self.analyst.analyze(processed or user_input, context)
            self.history.add_message(Message(analysis, "Analyst", time.time()))
            
            # Visualização intermediária
            markdown_output = self.visualizer.visualize(analysis, "markdown")
            print(f"Análise Parcial:\n{markdown_output}")
        
        # Etapa 4: Visualização Final
        if "visualizer" in agents:
            final_output = self.visualizer.visualize(analysis or processed or user_input, "json")
            self.history.add_message(Message(final_output, "Visualizer", time.time()))
            return json.loads(final_output)
        
        # Se não houver visualizador, retorna o último resultado disponível
        last_output = analysis or processed or user_input
        if isinstance(last_output, str):
            try:
                return json.loads(last_output)
            except:
                return {"result": last_output}
        return last_output

# Uso
if __name__ == "__main__":
    import os
    api_key = os.getenv("OPENAI_KEY")
    if not api_key:
        print("ERRO: A variável de ambiente OPENAI_KEY não está definida")
        exit(1)
        
    orchestrator = AgentOrchestrator(api_key=api_key)
    user_prompt = "Preciso de um sistema de login com autenticação de dois fatores"
    result = orchestrator.handle_input(user_prompt)
    print("Resultado Final:", json.dumps(result, indent=2))