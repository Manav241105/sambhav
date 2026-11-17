"""
Response Strategy Engine - Enterprise Conversation Intelligence
Selects and rotates response strategies to ensure information novelty every turn.

Strategies:
  DATA_EDUCATION          → Share new technical data points
  EMPATHY_VALIDATION      → Acknowledge and validate customer feelings
  TRUST_BUILDING          → Build credibility through transparency
  RISK_EXPLANATION        → Explain failure consequences clearly
  LOGISTICS_HELP          → Solve scheduling / availability constraints
  PRECAUTION_GUIDANCE     → Provide interim safety advice
  SOCIAL_PROOF            → Reference industry standards / norms
  SOFT_SCHEDULING_PUSH    → Gentle, non-pressuring scheduling nudge
  SECOND_OPINION_SUPPORT  → Actively support getting another opinion
  COST_CONTEXTUALIZATION  → Frame cost in context of failure cost
"""

from typing import Dict, List, Optional
from conversation_stage_manager import ConversationStage


class ResponseStrategyEngine:
    """
    Selects the optimal response strategy for each conversation turn.
    Ensures strategy rotation — never repeats the same strategy consecutively.
    """

    # Strategy → Intent mapping (which strategies work best for which intents)
    INTENT_STRATEGY_MAP: Dict[str, List[str]] = {
        "LOGISTICS_BLOCKER":      ["LOGISTICS_HELP", "PRECAUTION_GUIDANCE", "SOFT_SCHEDULING_PUSH"],
        "SKEPTICISM":             ["TRUST_BUILDING", "DATA_EDUCATION", "SOCIAL_PROOF"],
        "COST_CONCERN":           ["COST_CONTEXTUALIZATION", "EMPATHY_VALIDATION", "SOFT_SCHEDULING_PUSH"],
        "SECOND_OPINION_SEEKING": ["SECOND_OPINION_SUPPORT", "TRUST_BUILDING", "DATA_EDUCATION"],
        "INFO_GATHERING":         ["DATA_EDUCATION", "RISK_EXPLANATION", "TRUST_BUILDING"],
        "READY_TO_BOOK":          ["SOFT_SCHEDULING_PUSH", "EMPATHY_VALIDATION"],
        "SOFT_DECLINE":           ["EMPATHY_VALIDATION", "PRECAUTION_GUIDANCE", "SOFT_SCHEDULING_PUSH"],
        "HARD_DECLINE":           ["EMPATHY_VALIDATION", "PRECAUTION_GUIDANCE"],
    }

    # Stage → preferred strategies
    STAGE_STRATEGY_MAP: Dict[str, List[str]] = {
        ConversationStage.STAGE_1_EDUCATE.value:           ["DATA_EDUCATION", "RISK_EXPLANATION", "TRUST_BUILDING"],
        ConversationStage.STAGE_2_VALIDATE.value:          ["EMPATHY_VALIDATION", "TRUST_BUILDING", "DATA_EDUCATION"],
        ConversationStage.STAGE_3_HANDLE_OBJECTIONS.value: ["LOGISTICS_HELP", "COST_CONTEXTUALIZATION", "SECOND_OPINION_SUPPORT", "SOCIAL_PROOF"],
        ConversationStage.STAGE_4_DECISION_SUPPORT.value:  ["SOFT_SCHEDULING_PUSH", "EMPATHY_VALIDATION", "PRECAUTION_GUIDANCE"],
        ConversationStage.STAGE_5_SOFT_CLOSE.value:        ["EMPATHY_VALIDATION", "PRECAUTION_GUIDANCE", "SOFT_SCHEDULING_PUSH"],
    }

    # Strategy descriptions for prompt injection
    STRATEGY_PROMPTS: Dict[str, str] = {
        "DATA_EDUCATION": (
            "Share a NEW specific data point the customer hasn't heard yet. "
            "Reference exact measurements, sensor readings, or diagnostic specifics. "
            "Explain what the data means in plain language."
        ),
        "EMPATHY_VALIDATION": (
            "Deeply acknowledge the customer's specific concern. Mirror their language. "
            "Show you genuinely understand their situation before offering any information. "
            "Do NOT jump to solutions immediately."
        ),
        "TRUST_BUILDING": (
            "Build credibility through transparency. Explain HOW the diagnostic system works. "
            "Offer to share the full diagnostic report. Acknowledge limitations honestly. "
            "Invite them to verify the data independently."
        ),
        "RISK_EXPLANATION": (
            "Explain the failure consequence in realistic, non-alarmist terms. "
            "Describe what actually happens when this component fails while driving. "
            "Reference industry safety standards. Be factual, not fear-based."
        ),
        "LOGISTICS_HELP": (
            "Proactively solve their scheduling constraint. Offer: "
            "(1) Remote/advance booking for when they return, "
            "(2) Local partner service center near their current location, "
            "(3) Mobile service option if available, "
            "(4) Flexible timing options. "
            "Make it easy for them to say yes."
        ),
        "PRECAUTION_GUIDANCE": (
            "Provide specific, actionable driving precautions they can follow until service. "
            "Include: speed limits, braking technique, warning signs to watch for, "
            "when to stop driving immediately. Be specific and practical."
        ),
        "SOCIAL_PROOF": (
            "Reference industry standards, manufacturer recommendations, or safety regulations. "
            "Mention what other customers in similar situations typically do. "
            "Use authoritative but accessible language."
        ),
        "SOFT_SCHEDULING_PUSH": (
            "Gently offer a specific scheduling option without pressure. "
            "Suggest a concrete time slot. Make it easy to say yes. "
            "Respect their timeline. Offer flexibility."
        ),
        "SECOND_OPINION_SUPPORT": (
            "ACTIVELY ENCOURAGE them to get a second opinion. Offer to share the full diagnostic report. "
            "Provide the data in a format their mechanic can review. "
            "Express confidence that any qualified mechanic will confirm the findings. "
            "Do NOT be defensive — this builds trust."
        ),
        "COST_CONTEXTUALIZATION": (
            "Frame the repair cost in context of the cost of failure. "
            "Explain: early repair cost vs emergency repair cost vs accident liability. "
            "Mention payment plan options if available. "
            "Focus on value and safety, not price pressure."
        ),
    }

    def select_strategy(self, intent: str, stage: str, strategies_used: List[str],
                        last_strategy: Optional[str] = None) -> str:
        """
        Select the best strategy for this turn.
        Ensures no consecutive repetition and prioritizes novelty.
        """
        # Get candidate strategies from intent map
        intent_candidates = self.INTENT_STRATEGY_MAP.get(intent, ["DATA_EDUCATION", "EMPATHY_VALIDATION"])
        # Get candidates from stage map
        stage_candidates = self.STAGE_STRATEGY_MAP.get(stage, ["DATA_EDUCATION"])

        # Merge: intent takes priority, then stage
        all_candidates = intent_candidates + [s for s in stage_candidates if s not in intent_candidates]

        # Filter out last strategy (no consecutive repeats)
        if last_strategy:
            filtered = [s for s in all_candidates if s != last_strategy]
            if not filtered:
                filtered = all_candidates  # fallback if only one option
        else:
            filtered = all_candidates

        # Prefer strategies not yet used
        unused = [s for s in filtered if s not in strategies_used]
        if unused:
            return unused[0]

        # All used — pick least recently used
        for s in reversed(strategies_used):
            if s in filtered:
                # Return the one used longest ago
                pass
        return filtered[0]

    def get_strategy_prompt(self, strategy: str) -> str:
        """Return the prompt instruction for the selected strategy"""
        return self.STRATEGY_PROMPTS.get(strategy, "Respond helpfully and empathetically.")

    def get_strategy_label(self, strategy: str) -> str:
        """Human-readable strategy label"""
        labels = {
            "DATA_EDUCATION": "📊 Data Education",
            "EMPATHY_VALIDATION": "💙 Empathy & Validation",
            "TRUST_BUILDING": "🤝 Trust Building",
            "RISK_EXPLANATION": "⚠️ Risk Explanation",
            "LOGISTICS_HELP": "📅 Logistics Help",
            "PRECAUTION_GUIDANCE": "🛡️ Safety Precautions",
            "SOCIAL_PROOF": "📋 Industry Standards",
            "SOFT_SCHEDULING_PUSH": "🗓️ Scheduling Nudge",
            "SECOND_OPINION_SUPPORT": "🔍 Second Opinion Support",
            "COST_CONTEXTUALIZATION": "💰 Cost Contextualization",
        }
        return labels.get(strategy, strategy)
