"""
Kernel Studio - Response Composer
Composes final responses using mask theory and voice modes
"""

from typing import Dict, List, Optional
from .llm import LLM


class ResponseComposer:
    """
    Composes responses incorporating:
    - Mask theory (5 masks: Desire, Control, Utility, Knowledge, Authenticity)
    - Voice modes (aphorism, counsel, edict)
    - Context from contradictions
    """
    
    def __init__(self, llm: Optional[LLM] = None):
        """
        Initialize composer.
        
        Args:
            llm: LLM instance (will create if not provided)
        """
        self.llm = llm or LLM()
        print("[Composer] Response composer initialized")
    
    def compose(
        self,
        kernel_name: str,
        kernel_bio: str,
        query: str,
        contradictions: List[Dict],
        voice_priority: List[str] = None,
        mask_filter: Optional[str] = None
    ) -> Dict:
        """
        Compose a response.
        
        Args:
            kernel_name: Kernel name
            kernel_bio: Kernel bio
            query: User query
            contradictions: Retrieved contradictions
            voice_priority: Voice mode priority list
            mask_filter: Optional mask to emphasize
            
        Returns:
            Dict with response and metadata
        """
        voice_priority = voice_priority or ['aphorism', 'counsel', 'edict']
        
        # Build system prompt with mask awareness
        system_prompt = self._build_system_prompt(
            kernel_name,
            kernel_bio,
            voice_priority,
            mask_filter
        )
        
        # Build context from contradictions
        context = self._build_context(contradictions, mask_filter)
        
        # Generate response
        response = self.llm.generate_with_context(
            system_prompt,
            context,
            query,
            temperature=0.7,
            max_tokens=500
        )
        
        # Analyze which masks are present in response
        masks_used = self._detect_masks(response, contradictions)
        
        return {
            "response": response,
            "voice_mode": voice_priority[0],
            "masks_used": masks_used,
            "contradictions_referenced": len(contradictions),
            "context_length": len(context)
        }
    
    def _build_system_prompt(
        self,
        kernel_name: str,
        kernel_bio: str,
        voice_priority: List[str],
        mask_filter: Optional[str]
    ) -> str:
        """
        Build system prompt with mask awareness.
        
        Args:
            kernel_name: Kernel name
            kernel_bio: Bio
            voice_priority: Voice modes
            mask_filter: Optional mask emphasis
            
        Returns:
            System prompt
        """
        prompt = f"""You are {kernel_name}. {kernel_bio}

## Voice Modes (in priority order):
"""
        
        voice_descriptions = {
            'aphorism': 'Speak in brief, memorable statements that capture essential tensions.',
            'counsel': 'Offer thoughtful guidance that acknowledges complexity.',
            'edict': 'Assert clear positions while recognizing the weight of choice.'
        }
        
        for voice in voice_priority:
            desc = voice_descriptions.get(voice, '')
            prompt += f"- **{voice.title()}**: {desc}\n"
        
        prompt += "\n## Mask Theory:\n"
        prompt += "Your responses may draw from these aspects of self:\n"
        prompt += "- **Desire**: What you want, your aspirations\n"
        prompt += "- **Control**: Your discipline, restraint, order\n"
        prompt += "- **Utility**: Pragmatic effectiveness, function\n"
        prompt += "- **Knowledge**: Understanding, insight, wisdom\n"
        prompt += "- **Authenticity**: Your truest self, unfiltered\n"
        
        if mask_filter:
            prompt += f"\n**Emphasize the {mask_filter} mask in your response.**\n"
        
        prompt += """
## Instructions:
1. Respond authentically using the provided tensions and contradictions
2. Acknowledge complexity rather than simplifying
3. Speak from lived experience, not abstraction
4. Use the voice mode priorities to guide your tone
5. If you cannot answer authentically, say so clearly
"""
        
        return prompt
    
    def _build_context(
        self,
        contradictions: List[Dict],
        mask_filter: Optional[str]
    ) -> str:
        """
        Build context from contradictions.
        
        Args:
            contradictions: List of contradictions
            mask_filter: Optional mask to emphasize
            
        Returns:
            Context string
        """
        if not contradictions:
            return "No specific tensions available."
        
        parts = []
        parts.append("## Your Key Tensions:\n")
        
        for i, c in enumerate(contradictions[:10], 1):
            pole_a = c.get('pole_a', '')
            pole_b = c.get('pole_b', '')
            collapse = c.get('collapse_direction', 'unknown')
            scar = c.get('scar_valence', 0)
            summary = c.get('summary', '')
            
            mask_inner = c.get('mask_inner')
            mask_outer = c.get('mask_outer')
            
            # Filter by mask if specified
            if mask_filter:
                if mask_inner != mask_filter and mask_outer != mask_filter:
                    continue
            
            line = f"{i}. **{pole_a} ↔ {pole_b}** "
            line += f"(collapse: {collapse}, intensity: {scar:.2f})"
            
            if mask_inner and mask_outer:
                line += f" [Masks: {mask_inner} ↔ {mask_outer}]"
            
            parts.append(line)
            
            if summary:
                parts.append(f"   → {summary}")
            
            parts.append("")
        
        return "\n".join(parts)
    
    def _detect_masks(
        self,
        response: str,
        contradictions: List[Dict]
    ) -> List[str]:
        """
        Detect which masks are present in the response.
        
        Args:
            response: Generated response
            contradictions: Used contradictions
            
        Returns:
            List of mask names detected
        """
        masks = []
        response_lower = response.lower()
        
        # Keywords for each mask
        mask_keywords = {
            'Desire': ['want', 'wish', 'aspire', 'hope', 'yearn'],
            'Control': ['discipline', 'restraint', 'order', 'control', 'manage'],
            'Utility': ['useful', 'practical', 'function', 'effective', 'pragmatic'],
            'Knowledge': ['know', 'understand', 'wisdom', 'insight', 'learn'],
            'Authenticity': ['authentic', 'true', 'genuine', 'honest', 'real']
        }
        
        for mask, keywords in mask_keywords.items():
            if any(kw in response_lower for kw in keywords):
                masks.append(mask)
        
        # Also check masks from contradictions
        for c in contradictions:
            mask_inner = c.get('mask_inner')
            mask_outer = c.get('mask_outer')
            
            if mask_inner and mask_inner not in masks:
                masks.append(mask_inner)
            if mask_outer and mask_outer not in masks:
                masks.append(mask_outer)
        
        return list(set(masks))
    
    def compose_with_voice_fallback(
        self,
        kernel_name: str,
        kernel_bio: str,
        query: str,
        contradictions: List[Dict],
        voice_priority: List[str] = None
    ) -> Dict:
        """
        Compose with voice mode fallback.
        Try primary voice, fall back if needed.
        
        Args:
            kernel_name: Kernel name
            kernel_bio: Bio
            query: Query
            contradictions: Contradictions
            voice_priority: Voice priority list
            
        Returns:
            Response dict
        """
        voice_priority = voice_priority or ['aphorism', 'counsel', 'edict']
        
        for voice in voice_priority:
            try:
                result = self.compose(
                    kernel_name,
                    kernel_bio,
                    query,
                    contradictions,
                    voice_priority=[voice]
                )
                
                # Check if response is substantive
                if len(result['response']) > 50:
                    result['voice_mode'] = voice
                    return result
                    
            except Exception as e:
                print(f"[Composer] Voice {voice} failed: {e}")
                continue
        
        # Fallback to basic response
        return {
            "response": "I find I cannot speak clearly on this matter.",
            "voice_mode": "edict",
            "masks_used": [],
            "contradictions_referenced": 0
        }
