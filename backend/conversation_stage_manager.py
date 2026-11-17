"""
Conversation Stage Manager - Enterprise Conversation Intelligence
Tracks and drives conversation stage progression for automotive service advisory.

Stages:
  STAGE_1_EDUCATE         → Explain the issue, build initial context
  STAGE_2_VALIDATE        → Validate customer concerns, show empathy
  STAGE_3_HANDLE_OBJECTIONS → Address specific objections with data
  STAGE_4_DECISION_SUPPORT → Help customer make informed decision
  STAGE_5_SOFT_CLOSE      → Gentle close or graceful exit
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class ConversationStage(Enum):
    STAGE_1_EDUCATE = "STAGE_1_EDUCATE"
    STAGE_2_VALIDATE = "STAGE_2_VALIDATE"
    STAGE_3_HANDLE_OBJECTIONS = "STAGE_3_HANDLE_OBJECTIONS"
    STAGE_4_DECISION_SUPPORT = "STAGE_4_DECISION_SUPPORT"
    STAGE_5_SOFT_CLOSE = "STAGE_5_SOFT_CLOSE"


@dataclass
class StageContext:
    current_stage: ConversationStage = ConversationStage.STAGE_1_EDUCATE
    turn_number: int = 0
    objection_count: int = 0
    engagement_score: float = 0.5   # 0.0 = disengaged, 1.0 = highly engaged
    trust_score: float = 0.5        # 0.0 = distrustful, 1.0 = fully trusting
    resistance_level: int = 0       # 0-5 scale
    topics_covered: List[str] = field(default_factory=list)
    last_strategy: Optional[str] = None
    strategies_used: List[str] = field(default_factory=list)


class ConversationStageManager:
    """
    Manages conversation stage progression.
    Determines which stage the conversation is in and what behavior is appropriate.
    """

    # Stage descriptions for prompt injection
    STAGE_GUIDANCE = {
        ConversationStage.STAGE_1_EDUCATE: {
            "goal": "Educate the customer about the issue clearly and empathetically",
            "tone": "Warm, informative, non-pressuring",
            "focus": "Explain what was found, why it matters, what the data shows",
            "avoid": "Closing language, urgency pressure, repetition of risk stats",
        },
        ConversationStage.STAGE_2_VALIDATE: {
            "goal": "Validate customer's concerns and feelings, show genuine understanding",
            "tone": "Empathetic, patient, collaborative",
            "focus": "Acknowledge their specific concern, mirror their language, show you understand",
            "avoid": "Dismissing concerns, jumping to solutions too fast",
        },
        ConversationStage.STAGE_3_HANDLE_OBJECTIONS: {
            "goal": "Address specific objections with data, alternatives, and creative solutions",
            "tone": "Confident, helpful, solution-oriented",
            "focus": "Provide new information that directly addresses the objection",
            "avoid": "Repeating the same data point, being defensive",
        },
        ConversationStage.STAGE_4_DECISION_SUPPORT: {
            "goal": "Help customer make an informed decision without pressure",
            "tone": "Supportive, transparent, respectful of autonomy",
            "focus": "Summarize options, offer flexibility, respect their timeline",
            "avoid": "Hard selling, fear tactics, repetition",
        },
        ConversationStage.STAGE_5_SOFT_CLOSE: {
            "goal": "Gently close or exit gracefully while maintaining safety messaging",
            "tone": "Warm, professional, non-pushy",
            "focus": "Leave door open, provide safety precautions, offer future contact",
            "avoid": "Pressure, guilt, repetitive risk warnings",
        },
    }

    def __init__(self):
        self.context = StageContext()

    def advance_stage(self, intent: str, turn_number: int, objection_count: int,
                      engagement_score: float = 0.5) -> ConversationStage:
        """
        Determine the appropriate conversation stage based on current context.
        Stage progression is not strictly linear — it responds to customer signals.
        """
        self.context.turn_number = turn_number
        self.context.objection_count = objection_count
        self.context.engagement_score = engagement_score

        # Hard decline → jump to soft close
        if intent in ("HARD_DECLINE",):
            self.context.current_stage = ConversationStage.STAGE_5_SOFT_CLOSE
            return self.context.current_stage

        # Soft decline → decision support
        if intent in ("SOFT_DECLINE",):
            self.context.current_stage = ConversationStage.STAGE_4_DECISION_SUPPORT
            return self.context.current_stage

        # Ready to book → decision support / soft close
        if intent == "READY_TO_BOOK":
            self.context.current_stage = ConversationStage.STAGE_4_DECISION_SUPPORT
            return self.context.current_stage

        # Turn-based progression with intent modifiers
        if turn_number == 1:
            self.context.current_stage = ConversationStage.STAGE_1_EDUCATE

        elif turn_number == 2:
            if intent in ("SKEPTICISM", "SECOND_OPINION_SEEKING"):
                self.context.current_stage = ConversationStage.STAGE_2_VALIDATE
            else:
                self.context.current_stage = ConversationStage.STAGE_2_VALIDATE

        elif turn_number == 3:
            if objection_count >= 2 or intent in ("COST_CONCERN", "LOGISTICS_BLOCKER", "SKEPTICISM"):
                self.context.current_stage = ConversationStage.STAGE_3_HANDLE_OBJECTIONS
            else:
                self.context.current_stage = ConversationStage.STAGE_3_HANDLE_OBJECTIONS

        elif turn_number == 4:
            if objection_count >= 3:
                self.context.current_stage = ConversationStage.STAGE_4_DECISION_SUPPORT
            else:
                self.context.current_stage = ConversationStage.STAGE_4_DECISION_SUPPORT

        else:
            self.context.current_stage = ConversationStage.STAGE_5_SOFT_CLOSE

        return self.context.current_stage

    def get_stage_guidance(self) -> Dict:
        """Return guidance dict for current stage"""
        return self.STAGE_GUIDANCE.get(self.context.current_stage, {})

    def get_stage_name(self) -> str:
        return self.context.current_stage.value

    def update_trust_score(self, delta: float):
        self.context.trust_score = max(0.0, min(1.0, self.context.trust_score + delta))

    def update_resistance(self, delta: int):
        self.context.resistance_level = max(0, min(5, self.context.resistance_level + delta))

    def mark_strategy_used(self, strategy: str):
        self.context.last_strategy = strategy
        if strategy not in self.context.strategies_used:
            self.context.strategies_used.append(strategy)

    def mark_topic_covered(self, topic: str):
        if topic not in self.context.topics_covered:
            self.context.topics_covered.append(topic)

    def get_context_summary(self) -> Dict:
        return {
            "stage": self.context.current_stage.value,
            "turn": self.context.turn_number,
            "objections": self.context.objection_count,
            "trust_score": round(self.context.trust_score, 2),
            "resistance_level": self.context.resistance_level,
            "last_strategy": self.context.last_strategy,
            "strategies_used": self.context.strategies_used,
            "topics_covered": self.context.topics_covered,
        }
