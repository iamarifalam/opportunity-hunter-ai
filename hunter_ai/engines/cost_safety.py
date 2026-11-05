"""
Cost & Safety Policy Engine
Enforces 100% Free Participation and catches hidden fees, payment traps,
and auto-converting subscriptions.
"""

from typing import Dict, Any, Tuple
import re

DISALLOWED_TERMS = [
    r"credit card required",
    r"card details required",
    r"payment method required",
    r"billing information required",
    r"auto-renews at",
    r"renews automatically at",
    r"first month free then",
    r"free trial.*credit card",
    r"registration fee:\s*\$",
    r"entry fee:\s*\$",
    r"participation fee:\s*\$",
    r"ticket price:\s*\$",
    r"₹\s*[1-9][0-9]*",
    r"\$\s*[1-9][0-9]*",
]


class CostSafetyCheckResult:
    def __init__(self, is_safe: bool, participation_fee: float, hidden_costs: str, flags: list[str]):
        self.is_safe = is_safe
        self.participation_fee = participation_fee
        self.hidden_costs = hidden_costs
        self.flags = flags

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "participation_fee": self.participation_fee,
            "hidden_costs": self.hidden_costs,
            "flags": self.flags,
        }


def evaluate_cost_safety(
    participation_fee: float,
    terms_text: str = "",
    description_text: str = "",
    requires_credit_card: bool = False,
) -> CostSafetyCheckResult:
    """
    Evaluates whether an opportunity strictly complies with the Zero-Cost rule.
    Any non-zero participation fee or requirement of payment details immediately fails.
    """
    flags = []
    
    # Check explicit fee
    if participation_fee > 0.0:
        flags.append(f"Explicit participation fee charged: ${participation_fee:.2f}")

    if requires_credit_card:
        flags.append("Requires payment method or credit card activation")

    combined_text = f"{terms_text} {description_text}".lower()

    for pattern in DISALLOWED_TERMS:
        matches = re.findall(pattern, combined_text, flags=re.IGNORECASE)
        if matches:
            flags.append(f"Found suspicious billing clause: '{matches[0]}'")

    # Free tier or sponsored verification
    has_free_tier = any(k in combined_text for k in ["100% free", "no cost", "sponsored", "free admission", "free entry", "free credits", "no credit card required", "free registration"])
    
    is_safe = len(flags) == 0
    hidden_costs = "; ".join(flags) if flags else ("Verified 100% Free - No billing required" if has_free_tier else "None detected")

    return CostSafetyCheckResult(
        is_safe=is_safe,
        participation_fee=participation_fee,
        hidden_costs=hidden_costs,
        flags=flags,
    )
