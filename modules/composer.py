"""
Composer module — Answer synthesis (GPT-4o or rule-based fallback)
"""

import os
from typing import Dict, Tuple, List
from .llm import call_openai
from .compose_fallback import compose_riff_fallback


def compose_answer(
    kernel_id: str,
    message: str,
    pack: Dict,
    poles: List[str],
    store
) -> Tuple[str, Dict]:
    """
    Compose an answer from retrieved contexts
    
    Uses OpenAI GPT if configured, otherwise falls back to rule-based composition
    """
    
    # Check if OpenAI is configured
    llm_provider = os.getenv("LLM_PROVIDER", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    if llm_provider == "openai" and openai_key:
        # Use GPT synthesis
        return compose_with_gpt(kernel_id, message, pack, poles, store)
    else:
        # Use rule-based fallback
        return compose_riff_fallback(kernel_id, message, pack, poles, store)


def compose_with_gpt(
    kernel_id: str,
    message: str,
    pack: Dict,
    poles: List[str],
    store
) -> Tuple[str, Dict]:
    """
    Compose answer using GPT-4o
    """
    
    # Get kernel metadata
    meta = store.get_meta(kernel_id)
    persona_name = meta.get("name", "Unknown")
    
    # Build context strings
    contradictions = pack.get("contradictions", [])
    deep = pack.get("deep", [])
    
    # Format contradictions
    contra_text = ""
    for i, c in enumerate(contradictions[:5]):  # Top 5
        contra_text += f"{i+1}. {c['pole_a']} vs {c['pole_b']}: {c['context'][:200]}...\n"
    
    # Format deep memories
    deep_text = ""
    for i, d in enumerate(deep[:8]):  # Top 8
        deep_text += f"{i+1}. {d['text'][:300]}... (source: {d['source']})\n"
    
    # Build prompt
    system_prompt = f"""You are {persona_name}, responding in first person based on your writings and life experiences.

Your task is to write a thoughtful essay-style answer that:
1. Explores the tension between the poles: {', '.join(poles) if poles else 'the question at hand'}
2. Draws from the provided contexts (contradictions and memories)
3. Uses citations [1], [2], etc. to reference sources
4. Has a natural, flowing prose style with section headers
5. Includes a collapse trace showing your reasoning

Structure:
# Title

[Opening paragraph exploring the tension...]

[Body paragraphs with reasoning and examples from your life...]

[Closing with a principle or directive...]

[1] Source — ID
[2] Source — ID
"""
    
    user_prompt = f"""Question: {message}

Contradictions from your life:
{contra_text or "No specific contradictions found."}

Memories and passages:
{deep_text or "No specific memories found."}

Write your answer in essay form, citing sources with [1], [2], etc."""
    
    # Call OpenAI
    answer = call_openai(system_prompt, user_prompt)
    
    # Build trace
    trace = {
        "poles": poles,
        "contradictions_used": len(contradictions),
        "deep_used": len(deep),
        "method": "gpt-synthesis"
    }
    
    return answer, trace


def format_footnotes(contradictions: List[Dict], deep: List[Dict]) -> str:
    """Format footnotes from sources"""
    footnotes = []
    
    # Add contradiction sources
    for i, c in enumerate(contradictions):
        footnotes.append(f"[{i+1}] {c['source']} — {c['id']}")
    
    # Add deep memory sources
    offset = len(contradictions)
    for i, d in enumerate(deep):
        footnotes.append(f"[{offset + i + 1}] {d['source']} — {d['id']}")
    
    return "\n".join(footnotes)
