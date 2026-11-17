"""
Conversation Memory Tracker - Enterprise Conversation Intelligence v2.0
Tracks full per-session conversation state for trend-aware, non-repetitive responses.

Memory Tags:
  LAST_STRATEGY_USED        → Prevents consecutive strategy repetition
  LAST_OBJECTION_TYPE       → Tracks most recent objection for targeted response
  CUSTOMER_TRUST_TREND      → rising / falling / stable
  CUSTOMER_RESISTANCE_TREND → escalating / de-escalating / stable
  CUSTOMER_DECISION_VELOCITY → fast / slow / stalled
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Deque
from collections import deque


@dataclass
class ConversationMemory:
    # Strategy tracking
    last_strategy_used: Optional[str] = None
    strategies_used: List[str] = field(default_factory=list)
    strategy_turn_map: Dict[str, int] = field(default_factory=dict)  # strategy → turn used

    # Objection tracking
    last_objection_type: Optional[str] = None
    objections_raised: List[str] = field(default_factory=list)
    objection_count: int = 0

    # Trust tracking
    trust_score: float = 0.5
    trust_history: Deque[float] = field(default_factory=lambda: deque(maxlen=5))
    trust_trend: str = "stable"  # rising / falling / stable

    # Resistance tracking
    resistance_level: int = 0
    resistance_history: Deque[int] = field(default_factory=lambda: deque(maxlen=5))
    resistance_trend: str = "stable"  # escalating / de-escalating / stable

    # Decision velocity
    positive_signals: int = 0
    negative_signals: int = 0
    decision_velocity: str = "slow"  # fast / slow / stalled

    # Intent history
    intents_seen: List[str] = field(default_factory=list)
    last_intent: Optional[str] = None

    # Topics covered (to enforce novelty)
    topics_covered: List[str] = field(default_factory=list)
    data_points_shared: List[str] = field(default_factory=list)

    # Edge case flags
    trust_damage_detected: bool = False
    past_service_failure_mentioned: bool = False
    family_mechanic_mentioned: bool = False
    cost_concern_raised: bool = False
    logistics_blocker_active: bool = False
    second_opinion_requested: bool = False

    # Turn counter
    turn_number: int = 0


class ConversationMemoryTracker:
    """
    Maintains full conversation state across all turns.
    Provides trend analysis and novelty enforcement.
    """

    def __init__(self):
        self.memory = ConversationMemory()

    def update(self, intent: str, strategy: str, trust_delta: float,
               resistance_delta: int, turn_number: int) -> None:
        """Update all memory tags after each turn"""
        self.memory.turn_number = turn_number

        # Strategy tracking
        self.memory.last_strategy_used = strategy
        if strategy not in self.memory.strategies_used:
            self.memory.strategies_used.append(strategy)
        self.memory.strategy_turn_map[strategy] = turn_number

        # Intent tracking
        self.memory.last_intent = intent
        if intent not in self.memory.intents_seen:
            self.memory.intents_seen.append(intent)

        # Objection tracking
        objection_intents = {
            "SKEPTICISM", "COST_CONCERN", "LOGISTICS_BLOCKER",
            "SECOND_OPINION_SEEKING", "SOFT_DECLINE", "HARD_DECLINE",
            "PAST_SERVICE_FAILURE", "TRUST_DAMAGE_EVENT",
            "SERVICE_DELAY_TRAUMA", "REPAIR_QUALITY_DOUBT",
            "PRICE_SHOCK_HISTORY", "DEALERSHIP_AVOIDANCE_PATTERN"
        }
        if intent in objection_intents:
            self.memory.last_objection_type = intent
            if intent not in self.memory.objections_raised:
                self.memory.objections_raised.append(intent)
            self.memory.objection_count += 1

        # Trust trend
        old_trust = self.memory.trust_score
        self.memory.trust_score = max(0.0, min(1.0, old_trust + trust_delta))
        self.memory.trust_history.append(self.memory.trust_score)
        self.memory.trust_trend = self._compute_trend(list(self.memory.trust_history))

        # Resistance trend
        old_resistance = self.memory.resistance_level
        self.memory.resistance_level = max(0, min(5, old_resistance + resistance_delta))
        self.memory.resistance_history.append(self.memory.resistance_level)
        self.memory.resistance_trend = self._compute_trend(
            list(self.memory.resistance_history), higher_is_worse=True
        )

        # Decision velocity
        if trust_delta > 0:
            self.memory.positive_signals += 1
        elif trust_delta < 0:
            self.memory.negative_signals += 1

        total = self.memory.positive_signals + self.memory.negative_signals
        if total == 0:
            self.memory.decision_velocity = "slow"
        elif self.memory.positive_signals / max(total, 1) > 0.6:
            self.memory.decision_velocity = "fast"
        elif self.memory.negative_signals / max(total, 1) > 0.6:
            self.memory.decision_velocity = "stalled"
        else:
            self.memory.decision_velocity = "slow"

        # Edge case flags
        if intent in ("PAST_SERVICE_FAILURE", "TRUST_DAMAGE_EVENT",
                      "SERVICE_DELAY_TRAUMA", "REPAIR_QUALITY_DOUBT",
                      "DEALERSHIP_AVOIDANCE_PATTERN"):
            self.memory.trust_damage_detected = True
            self.memory.past_service_failure_mentioned = True

        if intent == "SECOND_OPINION_SEEKING":
            self.memory.family_mechanic_mentioned = True
            self.memory.second_opinion_requested = True

        if intent in ("COST_CONCERN", "PRICE_SHOCK_HISTORY"):
            self.memory.cost_concern_raised = True

        if intent == "LOGISTICS_BLOCKER":
            self.memory.logistics_blocker_active = True

    def mark_topic_covered(self, topic: str) -> None:
        if topic not in self.memory.topics_covered:
            self.memory.topics_covered.append(topic)

    def mark_data_shared(self, data_point: str) -> None:
        if data_point not in self.memory.data_points_shared:
            self.memory.data_points_shared.append(data_point)

    def is_topic_covered(self, topic: str) -> bool:
        return topic in self.memory.topics_covered

    def is_data_shared(self, data_point: str) -> bool:
        return data_point in self.memory.data_points_shared

    def get_unused_strategies(self, candidates: List[str]) -> List[str]:
        return [s for s in candidates if s not in self.memory.strategies_used]

    def needs_trust_recovery(self) -> bool:
        return (
            self.memory.trust_damage_detected or
            self.memory.trust_score < 0.35 or
            self.memory.trust_trend == "falling" and self.memory.trust_score < 0.5
        )

    def needs_generic_prevention(self) -> bool:
        """Returns True if generic fallback must be blocked"""
        return (
            self.memory.objection_count >= 2 or
            self.memory.trust_score < 0.6 or
            self.memory.resistance_level > 2
        )

    def get_summary(self) -> Dict:
        return {
            "turn": self.memory.turn_number,
            "last_strategy": self.memory.last_strategy_used,
            "last_intent": self.memory.last_intent,
            "last_objection": self.memory.last_objection_type,
            "trust_score": round(self.memory.trust_score, 2),
            "trust_trend": self.memory.trust_trend,
            "resistance_level": self.memory.resistance_level,
            "resistance_trend": self.memory.resistance_trend,
            "decision_velocity": self.memory.decision_velocity,
            "objection_count": self.memory.objection_count,
            "trust_damage": self.memory.trust_damage_detected,
            "strategies_used": self.memory.strategies_used,
            "topics_covered": self.memory.topics_covered,
        }

    @staticmethod
    def _compute_trend(history: List[float], higher_is_worse: bool = False) -> str:
        if len(history) < 2:
            return "stable"
        recent = history[-1]
        earlier = history[0]
        delta = recent - earlier
        if abs(delta) < 0.05:
            return "stable"
        if delta > 0:
            return "falling" if higher_is_worse else "rising"
        return "escalating" if higher_is_worse else "falling"
