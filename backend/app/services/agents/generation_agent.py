"""
Generation Agent - Specialized in generating accurate answers.
Handles answer generation, validation, and confidence scoring.
"""
from typing import Dict, Any, List
from app.services.llm_service import LLMService
from app.services.hallucination_guard import HallucinationGuard
from app.core.config import settings
from app.core.logging import logger


class GenerationAgent:
    """
    Agent responsible for generating answers from context.
    Handles answer generation, validation, and quality assessment.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        hallucination_guard: HallucinationGuard
    ):
        """
        Initialize Generation Agent.
        
        Args:
            llm_service: LLM service for answer generation
            hallucination_guard: Hallucination guard for validation
        """
        self.llm_service = llm_service
        self.hallucination_guard = hallucination_guard
    
    def generate_answer(
        self,
        question: str,
        context: str,
        sources: List[Dict[str, Any]],
        query_type: str
    ) -> Dict[str, Any]:
        """
        Generate answer from context with validation.
        Agent decides on generation strategy based on query type.
        
        Args:
            question: User question
            context: Retrieved context
            sources: Source chunks used
            query_type: Type of query (factual/relational/reasoning)
            
        Returns:
            Dictionary with:
            - answer: Generated answer
            - confidence: Confidence score
            - validation: Validation details
            - reasoning: Agent's reasoning steps
        """
        reasoning_steps = []
        
        # Step 1: Check if context is sufficient
        if not context or len(context.strip()) < settings.min_context_length:
            reasoning_steps.append("Insufficient context - rejecting answer")
            return {
                "answer": self.hallucination_guard.get_rejection_message(),
                "confidence": 0.0,
                "validation": {"needs_rejection": True, "reasoning": "Insufficient context"},
                "reasoning": reasoning_steps,
                "rejected": True
            }
        
        # Step 2: Generate answer using LLM
        # Agent adapts prompt based on query type
        reasoning_steps.append("Generating answer using LLM")
        answer = self.llm_service.generate_answer(
            question,
            context,
            use_strict_mode=True
        )
        
        # Step 3: Validate answer using hallucination guard
        reasoning_steps.append("Validating answer quality")
        validation = self.hallucination_guard.validate_answer(
            answer,
            context,
            sources
        )
        
        reasoning_steps.append(f"Confidence score: {validation['confidence']:.2f}")
        reasoning_steps.append(f"Validation factors: {list(validation.get('factors', {}).keys())}")
        
        # Step 4: Agent decides on rejection based on validation
        # Check if we have high-quality sources (score > 0.7)
        # Use the MAXIMUM of similarity_score and score fields
        def get_source_score(s):
            """Get the maximum score from either similarity_score or score field."""
            return max(s.get('similarity_score', 0.0), s.get('score', 0.0))
        
        high_quality_source = sources and any(
            get_source_score(s) > 0.7 for s in sources
        )
        
        # Get max source score for logging (using maximum of both fields)
        max_source_score = max((get_source_score(s) for s in sources), default=0.0) if sources else 0.0
        
        rejected = False
        
        # CRITICAL: If source quality is very high, NEVER reject
        if high_quality_source:
            # High-quality source - trust it over LLM uncertainty
            rejected = False
            # Boost confidence to reflect source quality
            if validation["confidence"] < max_source_score * 0.7:
                validation["confidence"] = max_source_score * 0.7
                reasoning_steps.append(
                    f"High-quality source detected ({max_source_score:.1%}) - "
                    f"confidence boosted to {validation['confidence']:.1%}"
                )
            
            # If LLM generated rejection phrase, extract answer from context
            rejection_phrases = ["cannot provide", "cannot answer", "insufficient", "i cannot", "i don't know"]
            has_rejection_phrase = any(phrase in answer.lower() for phrase in rejection_phrases)
            
            if has_rejection_phrase:
                # Extract answer directly from context
                reasoning_steps.append(
                    f"LLM generated uncertainty phrase but high-quality source ({max_source_score:.1%}) overrides - "
                    "extracting answer from context"
                )
                # Simple extraction: find sentence containing key terms from question
                question_words = [w.lower() for w in question.split() if len(w) > 3]
                context_sentences = [s.strip() for s in context.split('.') if s.strip()]
                
                # Find most relevant sentence
                best_sentence = None
                best_score = 0
                for sentence in context_sentences:
                    sentence_lower = sentence.lower()
                    score = sum(1 for word in question_words if word in sentence_lower)
                    if score > best_score and len(sentence) > 20:
                        best_score = score
                        best_sentence = sentence
                
                if best_sentence:
                    answer = best_sentence.strip()
                    if not answer.endswith('.'):
                        answer += '.'
                    reasoning_steps.append("Answer extracted from high-quality source context")
                else:
                    # Fallback: use first substantial sentence
                    for sentence in context_sentences:
                        if len(sentence) > 30:
                            answer = sentence.strip() + '.'
                            break
        elif validation["needs_rejection"] and validation["confidence"] < 0.3:
            # Low confidence AND low source quality - reject
            answer = self.hallucination_guard.get_rejection_message()
            validation["confidence"] = 0.0
            rejected = True
            reasoning_steps.append("Answer rejected due to low confidence and low source quality")
        elif validation["needs_rejection"]:
            # Confidence below threshold but not critically low - retain
            rejected = False
            reasoning_steps.append(
                f"Answer retained despite confidence below threshold "
                f"(confidence: {validation['confidence']:.2f}, threshold: {settings.confidence_threshold})"
            )
        
        return {
            "answer": answer,
            "confidence": validation["confidence"],
            "validation": validation,
            "reasoning": reasoning_steps,
            "rejected": rejected
        }
    
    def classify_query(self, question: str) -> str:
        """
        Classify query type for routing to appropriate agents.
        
        Args:
            question: User question
            
        Returns:
            Query type: 'factual', 'relational', or 'reasoning'
        """
        return self.llm_service.classify_query(question)

