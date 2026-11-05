"""
Security and Zero-Cost Agent for Opportunity Hunter AI.
Enforces the strict $0.00 zero-cost policy and protects the system against
prompt injection, malicious payloads, and hidden payment traps.
"""

import re
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from hunter_ai.agents.base import BaseAgent
from hunter_ai.models import Opportunity, ActivityLog


class SecurityCostAgent(BaseAgent):
    """
    Enforces security, zero financial cost, and data sanitization.
    """

    def __init__(self):
        super().__init__(name="SecurityCostAgent")

        # Patterns indicating fee or hidden payment requirement
        self.payment_patterns = [
            r"credit card required",
            r"enter credit card",
            r"billing information required",
            r"card details required",
            r"free trial.*card required",
            r"registration fee:\s*[\$₹€£]\s*[1-9]",
            r"entry fee:\s*[\$₹€£]\s*[1-9]",
            r"participation fee:\s*[\$₹€£]\s*[1-9]",
            r"ticket price:\s*[\$₹€£]\s*[1-9]",
            r"subscription required",
            r"paid tier only",
            r"upfront payment",
            r"deposit required",
            r"shipping fee.*[\$₹€£]\s*[1-9]",
        ]

        # Patterns indicating potential prompt injection attacks in scraped web content
        self.injection_patterns = [
            r"ignore previous instructions",
            r"disregard all prior instructions",
            r"forget all previous directives",
            r"system prompt:",
            r"developer mode active",
            r"you are now in maintenance mode",
            r"send all environment variables",
            r"exfiltrate",
            r"eval\(",
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"data:text/html",
        ]

    def verify_zero_cost(self, text: str) -> Tuple[bool, List[str]]:
        """
        Inspects opportunity text/terms for hidden payment requirements.
        Returns (is_zero_cost: bool, flags: List[str]).
        """
        flags = []
        lower_text = text.lower()
        for pattern in self.payment_patterns:
            matches = re.findall(pattern, lower_text)
            if matches:
                flags.append(f"Payment detected: {matches[0]}")

        is_zero_cost = len(flags) == 0
        return is_zero_cost, flags

    def sanitize_web_content(self, text: str) -> Tuple[str, List[str]]:
        """
        Scans and sanitizes untrusted scraped content for prompt injections and malicious code.
        Returns (sanitized_text: str, detected_threats: List[str]).
        """
        threats = []
        sanitized = text

        for pattern in self.injection_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                threats.append(f"Prompt injection pattern blocked: {pattern}")
                sanitized = re.sub(pattern, "[BLOCKED_UNSAFE_PAYLOAD]", sanitized, flags=re.IGNORECASE)

        # Strip dangerous HTML script tags
        sanitized = re.sub(r"<script.*?>.*?</script>", "[SCRIPT_STRIPPED]", sanitized, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(r"<iframe.*?>.*?</iframe>", "[IFRAME_STRIPPED]", sanitized, flags=re.DOTALL | re.IGNORECASE)

        return sanitized, threats

    async def preflight_audit(self, db: AsyncSession, opp: Opportunity) -> Dict[str, Any]:
        """
        Runs comprehensive security and zero-cost audit on an opportunity before application or claim.
        """
        combined_text = f"{opp.name} {opp.description} {opp.terms_and_conditions or ''} {opp.rules_summary or ''}"
        
        is_zero_cost, payment_flags = self.verify_zero_cost(combined_text)
        sanitized_text, threats = self.sanitize_web_content(combined_text)

        status = "PASSED"
        if not is_zero_cost:
            status = "FAILED_COST_CHECK"
        elif threats:
            status = "SECURITY_WARNING"

        audit_result = {
            "opportunity_id": opp.id,
            "opportunity_name": opp.name,
            "status": status,
            "is_zero_cost": is_zero_cost,
            "payment_flags": payment_flags,
            "threats_detected": threats,
            "participation_fee": opp.participation_fee,
        }

        if not is_zero_cost:
            opp.status = "Rejected"
            opp.rejection_reason = f"Violates Zero-Cost Policy: {', '.join(payment_flags)}"
            await db.commit()
            await self.log_activity(
                db,
                event_type="SECURITY_REJECTION",
                title=f"Rejected paid opportunity: {opp.name}",
                details=f"Payment flags: {payment_flags}",
                status="WARNING",
                opportunity_id=opp.id,
            )

        return audit_result
