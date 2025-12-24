"""
Hallucination control module.
Ensures answers are grounded in retrieved context and provides confidence scoring.
"""
import re
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger


class HallucinationGuard:
    """
    Service for controlling hallucinations in LLM responses.
    Validates answers against context and provides confidence scores.
    """
    
    def __init__(self):
        """Initialize hallucination guard with threshold settings."""
        self.confidence_threshold = settings.confidence_threshold
        self.min_context_length = settings.min_context_length
    
    def validate_answer(
        self,
        answer: str,
        context: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate answer against context and compute confidence.
        
        Args:
            answer: Generated answer text
            context: Retrieved context used for generation
            sources: List of source chunks with metadata
            
        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - confidence: float (0-1)
            - reasoning: str
            - needs_rejection: bool
        """
        # Check for rejection phrases (indicating uncertainty)
        rejection_phrases = [
            "i cannot answer",
            "i don't know",
            "not enough information",
            "cannot determine",
            "unclear from the context",
            "insufficient information"
        ]
        
        answer_lower = answer.lower()
        has_rejection_phrase = any(phrase in answer_lower for phrase in rejection_phrases)
        
        # Compute confidence based on multiple factors
        confidence_factors = []
        
        # Factor 1: Context length (more context = potentially higher confidence)
        context_score = min(1.0, len(context) / (self.min_context_length * 2))
        confidence_factors.append(("context_length", context_score))
        
        # Factor 2: Number of sources (more sources = potentially more reliable)
        source_score = min(1.0, len(sources) / 5.0)
        confidence_factors.append(("source_count", source_score))
        
        # Factor 3: Source quality (average similarity scores)
        # Higher weight for high-quality sources
        # Use maximum of similarity_score and score fields
        def get_source_score(s):
            """Get the maximum score from either similarity_score or score field."""
            return max(s.get('similarity_score', 0.0), s.get('score', 0.0))
        
        if sources:
            scores = [get_source_score(s) for s in sources]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores) if scores else 0.0
            
            # Use max score for very high quality sources
            if max_score > 0.7:
                avg_score = max_score  # Use best score when quality is high
                logger.debug(f"High-quality source detected ({max_score:.2%}) - using max score")
            confidence_factors.append(("source_quality", avg_score))
        else:
            confidence_factors.append(("source_quality", 0.0))
        
        # Factor 4: Answer length (too short might indicate uncertainty)
        answer_length_score = min(1.0, len(answer) / 100.0)
        confidence_factors.append(("answer_length", answer_length_score))
        
        # Factor 5: Answer mentions rejection (low confidence)
        if has_rejection_phrase:
            confidence_factors.append(("has_rejection", 0.2))
        else:
            confidence_factors.append(("has_rejection", 1.0))
        
        # Factor 6: Text overlap between answer and context (groundedness)
        overlap_score = self._compute_text_overlap(answer, context)
        confidence_factors.append(("text_overlap", overlap_score))
        
        # Weighted average of confidence factors
        # Adjust weights to favor high-quality sources
        # Use maximum of similarity_score and score fields
        def get_source_score(s):
            """Get the maximum score from either similarity_score or score field."""
            return max(s.get('similarity_score', 0.0), s.get('score', 0.0))
        
        if sources and any(get_source_score(s) > 0.7 for s in sources):
            # High-quality source available - trust it more
            weights = {
                "context_length": 0.05,
                "source_count": 0.05,
                "source_quality": 0.6,  # Very high weight for quality sources
                "answer_length": 0.05,
                "has_rejection": 0.1,  # Lower penalty when sources are good
                "text_overlap": 0.15
            }
        else:
            # Normal weights
            weights = {
                "context_length": 0.1,
                "source_count": 0.1,
                "source_quality": 0.3,
                "answer_length": 0.1,
                "has_rejection": 0.2,
                "text_overlap": 0.2
            }
        
        confidence = sum(
            weights.get(factor, 0.0) * score
            for factor, score in confidence_factors
        )
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        # Determine if answer should be rejected
        # Don't reject if source quality is very high, even if LLM says "cannot answer"
        # Use maximum of similarity_score and score fields
        def get_source_score(s):
            """Get the maximum score from either similarity_score or score field."""
            return max(s.get('similarity_score', 0.0), s.get('score', 0.0))
        
        high_quality_source = sources and any(
            get_source_score(s) > 0.7 for s in sources
        )
        
        needs_rejection = (
            confidence < self.confidence_threshold and not high_quality_source or
            (has_rejection_phrase and not high_quality_source) or
            len(context) < self.min_context_length
        )
        
        # Override: if source quality is very high, don't reject even with rejection phrase
        if high_quality_source:
            # Trust the source over LLM's uncertainty
            if has_rejection_phrase:
                needs_rejection = False
            # Boost confidence significantly for high-quality sources
            max_source_score = max(get_source_score(s) for s in sources)
            # Set confidence to at least 70% of source quality, minimum 0.6
            confidence = max(confidence, max_source_score * 0.7, 0.6)
            logger.debug(f"High-quality source ({max_source_score:.2%}) - boosted confidence to {confidence:.2%}")
        
        reasoning = f"Confidence: {confidence:.2f}. Factors: {dict(confidence_factors)}"
        
        result = {
            "is_valid": not needs_rejection,
            "confidence": confidence,
            "reasoning": reasoning,
            "needs_rejection": needs_rejection,
            "factors": dict(confidence_factors)
        }
        
        logger.debug(f"Hallucination guard result: confidence={confidence:.2f}, needs_rejection={needs_rejection}")
        return result
    
    def _compute_text_overlap(self, answer: str, context: str) -> float:
        """
        Compute text overlap between answer and context.
        Measures how grounded the answer is in the context.
        
        Args:
            answer: Generated answer
            context: Source context
            
        Returns:
            Overlap score (0-1)
        """
        # Extract significant words (nouns, verbs, adjectives)
        answer_words = set(re.findall(r'\b[a-z]{3,}\b', answer.lower()))
        context_words = set(re.findall(r'\b[a-z]{3,}\b', context.lower()))
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'for', 'with', 'from', 'this', 'that', 'was', 'were', 'are', 'is', 'be', 'been', 'have', 'has', 'had'}
        answer_words -= stop_words
        context_words -= stop_words
        
        if not answer_words:
            return 0.0
        
        # Compute Jaccard similarity (intersection over union)
        intersection = len(answer_words & context_words)
        union = len(answer_words | context_words)
        
        overlap = intersection / union if union > 0 else 0.0
        return overlap
    
    def should_reject_answer(self, validation_result: Dict[str, Any]) -> bool:
        """
        Determine if answer should be rejected based on validation.
        
        Args:
            validation_result: Result from validate_answer()
            
        Returns:
            True if answer should be rejected
        """
        return validation_result.get("needs_rejection", True)
    
    def get_rejection_message(self) -> str:
        """
        Get standard message for rejected answers.
        
        Returns:
            Rejection message
        """
        return "I cannot provide a confident answer based on the available information. The retrieved context does not contain sufficient details to answer this question accurately."

