"""
LLM service for generating text completions.
Uses OpenAI-compatible API with abstraction for easy replacement.
"""
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class LLMService:
    """
    Service for interacting with Large Language Models.
    Handles prompt construction and response generation.
    """
    
    def __init__(self):
        """Initialize LLM service with API configuration."""
        self.api_base = settings.llm_api_base
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text completion from a prompt.
        
        Args:
            prompt: User prompt/instruction
            system_prompt: System message for context
            temperature: Sampling temperature (defaults to config)
            max_tokens: Maximum tokens to generate (defaults to config)
            
        Returns:
            Generated text response
        """
        if temperature is None:
            temperature = self.temperature
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self._call_api(messages, temperature, max_tokens)
            return response
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Make API call to OpenAI-compatible endpoint.
        
        Args:
            messages: List of message dicts with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated text
        """
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Extract text from response
            content = result['choices'][0]['message']['content']
            return content
    
    def classify_query(self, query: str) -> str:
        """
        Classify query type for routing retrieval strategy.
        Types: 'factual', 'relational', 'reasoning'
        
        Args:
            query: User query text
            
        Returns:
            Query type classification
        """
        system_prompt = """You are a query classifier. Classify the user's question into one of these types:
- "factual": Questions asking for facts, definitions, or information about entities
- "relational": Questions asking about relationships between entities (who works with, what is related to)
- "reasoning": Questions requiring multi-step reasoning, comparisons, or complex logic

Respond with ONLY the type name (factual, relational, or reasoning)."""
        
        prompt = f"Question: {query}\nType:"
        
        try:
            response = self.generate(prompt, system_prompt=system_prompt, temperature=0.1, max_tokens=10)
            query_type = response.strip().lower()
            
            # Validate response
            if query_type not in ['factual', 'relational', 'reasoning']:
                # Fallback classification
                if any(word in query.lower() for word in ['relationship', 'related', 'connected', 'works with', 'associated']):
                    query_type = 'relational'
                elif any(word in query.lower() for word in ['why', 'how', 'compare', 'difference', 'explain']):
                    query_type = 'reasoning'
                else:
                    query_type = 'factual'
            
            logger.debug(f"Classified query as: {query_type}")
            return query_type
        except Exception as e:
            logger.warning(f"Error classifying query, defaulting to 'factual': {e}")
            return 'factual'
    
    def generate_answer(
        self,
        question: str,
        context: str,
        use_strict_mode: bool = True
    ) -> str:
        """
        Generate answer from question and context.
        Uses strict mode to prevent hallucinations.
        
        Args:
            question: User question
            context: Retrieved context to base answer on
            use_strict_mode: If True, only use provided context (no external knowledge)
            
        Returns:
            Generated answer
        """
        if use_strict_mode:
            system_prompt = """You are a confident question-answering assistant. Answer questions based on the provided context.

IMPORTANT: You MUST answer the question if the context contains relevant information. Do NOT say "I cannot answer" unless the context is completely empty or irrelevant.

RULES:
1. Answer directly using information from the provided context
2. Extract key facts and provide a clear, confident answer
3. Be concise but complete
4. Only express uncertainty if the context truly has NO relevant information

Examples:
- Context: "John Smith works at Tech Corp"
  Question: "Where does John work?"
  Answer: "John Smith works at Tech Corp"

- Context: "Sarah Johnson is the CEO of Tech Corp"
  Question: "Who is the CEO?"
  Answer: "Sarah Johnson is the CEO of Tech Corp"

Always provide an answer when context is available. Never default to "I cannot answer" if context exists."""
        else:
            system_prompt = """You are a helpful question-answering assistant. Answer the user's question based on the provided context. Be accurate and concise."""
        
        prompt = f"""Based on the following context, answer the question directly and confidently.

Context:
{context}

Question: {question}

Instructions:
- If the context contains information relevant to the question, provide a direct answer
- Extract the key information from the context
- Be specific and factual
- Do NOT say "I cannot answer" if the context has relevant information

Answer:"""
        
        response = self.generate(prompt, system_prompt=system_prompt)
        return response

