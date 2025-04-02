import openai
import time
from typing import List, Dict, Any, Optional
import json
from openai import OpenAI

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
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = """
        Você é um roteador especializado em desenvolvimento de software. Sua tarefa é analisar a conversa e decidir quais agentes devem ser acionados:
        - Pré-processamento: Quando precisar clarificar requisitos ou processar dados
        - Análise: Quando detectar necessidade de validação técnica ou métricas
        - Visualização: Quando precisar apresentar resultados ou formatar saídas

        Responda apenas com JSON contendo lista de agentes relevantes.
        """
    
    def route(self, context: str) -> List[str]:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0
        )
        return json.loads(response.choices[0].message.content)

class DeterministicPreprocessingAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = """
        Você é um especialista em engenharia de requisitos. Suas tarefas:
        1. Limpeza: Remover ambiguidades e subjetividades
        2. Transformação: Estruturar em formato Feature -> Critérios de Aceite
        3. Agregação: Combinar com histórico mantendo consistência

        Mantenha neutralidade técnica e foco em testabilidade.
        """
    
    def process(self, input_text: str, context: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Contexto:\n{context}\n\nInput:\n{input_text}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content

class AnalyticalAnalysisAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = """
        Você é um arquiteto de software experiente. Realize:
        1. Análise Estatística: Quantidade/Complexidade de requisitos
        2. Correlação: Identificar dependências entre requisitos
        3. Regressão: Prever gaps de implementação

        Use métricas técnicas e padrões de mercado.
        """
    
    def analyze(self, processed_data: str, context: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Dados Processados:\n{processed_data}\n\nContexto:\n{context}"}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content

class ToolVisualizationAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
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
        if format_type == "markdown":
            prompt = self.markdown_prompt
        else:
            prompt = self.json_prompt
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": analysis}
            ],
            temperature=0
        )
        return response.choices[0].message.content

class AgentOrchestrator:
    def __init__(self, api_key: Optional[str] = None):
        self.history = ConversationHistory()
        self.triage = TriageAgent(api_key=api_key)
        self.preprocessor = DeterministicPreprocessingAgent(api_key=api_key)
        self.analyst = AnalyticalAnalysisAgent(api_key=api_key)
        self.visualizer = ToolVisualizationAgent(api_key=api_key)
    
    def handle_input(self, user_input: str) -> Dict[str, Any]:
        # Registrar entrada do usuário
        self.history.add_message(Message(user_input, "User", time.time()))
        
        # Loop de processamento iterativo
        final_output = None
        while not final_output:
            context = self.history.get_context()
            
            # Etapa 1: Triagem
            agents = self.triage.route(context)
            
            # Etapa 2: Pré-processamento
            if "preprocessor" in agents:
                processed = self.preprocessor.process(user_input, context)
                self.history.add_message(Message(processed, "Preprocessor", time.time()))
            
            # Etapa 3: Análise
            if "analyst" in agents:
                analysis = self.analyst.analyze(processed, context)
                self.history.add_message(Message(analysis, "Analyst", time.time()))
                
                # Visualização intermediária
                markdown_output = self.visualizer.visualize(analysis, "markdown")
                print(f"Análise Parcial:\n{markdown_output}")
            
            # Verificar critério de saída
            if "visualizer" in agents:
                final_output = self.visualizer.visualize(analysis, "json")
        
        # Saída final formatada
        self.history.add_message(Message(final_output, "Visualizer", time.time()))
        return json.loads(final_output)

# Uso
if __name__ == "__main__":
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERRO: A variável de ambiente OPENAI_API_KEY não está definida")
        exit(1)
        
    orchestrator = AgentOrchestrator(api_key=api_key)
    user_prompt = "Preciso de um sistema de login com autenticação de dois fatores"
    result = orchestrator.handle_input(user_prompt)
    print("Resultado Final:", json.dumps(result, indent=2))