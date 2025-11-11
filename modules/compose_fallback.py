"""
Compose fallback — Rule-based answer composition
Used when OpenAI is not configured
"""

from typing import Dict, Tuple, List


def compose_riff_fallback(
    kernel_id: str,
    message: str,
    pack: Dict,
    poles: List[str],
    store
) -> Tuple[str, Dict]:
    """
    Compose answer using rule-based template
    """
    
    contradictions = pack.get("contradictions", [])
    deep = pack.get("deep", [])
    
    # Build answer sections
    sections = []
    
    # 1. Aphorism (quote from first contradiction if available)
    if contradictions:
        first_contra = contradictions[0]
        quote = first_contra.get("context", "")[:200]
        sections.append(f'"{quote}..."')
    
    # 2. Counsel (bullet points)
    counsel = []
    if poles:
        counsel.append(f"• Weigh {poles[0]} vs {poles[1] if len(poles) > 1 else 'alternatives'}")
    
    if contradictions:
        avg_scar = sum(c.get("scar", 0.5) for c in contradictions) / len(contradictions)
        counsel.append(f"• Remembered cost: {avg_scar:.2f}")
    
    counsel.append("• Choose what preserves character and the hive")
    
    sections.append("\n".join(counsel))
    
    # 3. Edict (directive)
    if poles:
        sections.append(f"Edict: Balance {poles[0]} with wisdom; maintain agency.")
    else:
        sections.append("Edict: Act with virtue; preserve your character.")
    
    # 4. Footnotes
    footnotes = []
    for i, c in enumerate(contradictions[:3]):
        footnotes.append(f"[{i+1}] {c.get('source', 'Unknown')} — {c.get('id', '')}")
    
    for i, d in enumerate(deep[:3]):
        footnotes.append(f"[{len(contradictions) + i + 1}] {d.get('source', 'Unknown')} — {d.get('id', '')}")
    
    if footnotes:
        sections.append("\n" + "\n".join(footnotes))
    
    # Join sections
    answer = "\n\n".join(sections)
    
    # Build trace
    trace = {
        "poles": poles,
        "contradictions_used": len(contradictions),
        "deep_used": len(deep),
        "method": "rule-based-fallback"
    }
    
    return answer, trace
