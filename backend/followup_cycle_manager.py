"""
Follow-Up Cycle Manager - Autonomous Service Orchestration Platform v1.0
Handles customer delay requests: "Call me tomorrow", "Follow up in 2 days", etc.

Workflow:
  1. Detect delay intent from customer message
  2. Create FollowUpTask with incremented cycle number
  3. Before follow-up contact: trigger VehicleReanalysisEngine
  4. Pass reanalysis delta to conversation agent for tone-aware messaging
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


# ── Delay Intent Keywords ─────────────────────────────────────────────────────
DELAY_KEYWORDS = [
    "call me tomorrow", "call tomorrow", "tomorrow",
    "follow up", "follow-up", "followup",
    "remind me", "reminder",
    "next week", "next month",
    "in a few days", "in a couple of days",
    "give me time", "need time", "need some time",
    "let me think", "i'll think about it", "think about it",
    "not now", "later", "some other time",
    "busy right now", "busy today", "busy this week",
    "call me in", "contact me in", "reach me in",
    "check back", "try again", "try later",
]

# ── Day Extraction Patterns ───────────────────────────────────────────────────
DAY_PATTERNS = [
    (r'\b(\d+)\s*day', lambda m: int(m.group(1))),
    (r'\btomorrow\b', lambda m: 1),
    (r'\bnext week\b', lambda m: 7),
    (r'\bnext month\b', lambda m: 30),
    (r'\bin a few days\b', lambda m: 3),
    (r'\bin a couple of days\b', lambda m: 2),
    (r'\bin (\d+)\s*week', lambda m: int(m.group(1)) * 7),
]


class FollowUpTask:
    """Represents a scheduled follow-up contact task."""

    def __init__(self, customer_id: str, vehicle_id: str,
                 followup_date: datetime, reason: str,
                 cycle_number: int, original_diagnosis: Dict):
        self.task_id = f"FU-{uuid.uuid4().hex[:8].upper()}"
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.followup_date = followup_date
        self.reason = reason
        self.cycle_number = cycle_number
        self.original_diagnosis = original_diagnosis
        self.status = "PENDING"   # PENDING | TRIGGERED | COMPLETED | CANCELLED
        self.created_at = datetime.now()
        self.reanalysis_result: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "followup_date": self.followup_date.isoformat(),
            "reason": self.reason,
            "cycle_number": self.cycle_number,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "days_until_followup": max(0, (self.followup_date - datetime.now()).days),
        }

    def days_until(self) -> int:
        return max(0, (self.followup_date - datetime.now()).days)


class FollowupCycleManager:
    """
    Manages follow-up cycles when customers request delays.

    Key behaviors:
    - Detects delay intent from customer message
    - Creates FollowUpTask with incremented cycle number
    - Triggers vehicle re-analysis before each follow-up contact
    - Returns tone directive based on condition delta
    """

    def __init__(self):
        self._tasks: Dict[str, List[FollowUpTask]] = {}   # customer_id → [tasks]
        self._cycle_counts: Dict[str, int] = {}            # customer_id → cycle count

    # ── Delay Detection ───────────────────────────────────────────────────────

    def detect_delay_intent(self, user_reply: str) -> Dict:
        """
        Detect if customer is requesting a follow-up delay.

        Returns:
            {
              "is_delay": bool,
              "days_requested": int,
              "followup_date": datetime,
              "reason": str,
              "confidence": float
            }
        """
        lower = user_reply.lower().strip()

        # Check for delay keywords
        matched_keywords = [kw for kw in DELAY_KEYWORDS if kw in lower]
        if not matched_keywords:
            return {"is_delay": False, "days_requested": 0,
                    "followup_date": None, "reason": "", "confidence": 0.0}

        # Extract number of days
        days = self._extract_days(lower)
        followup_date = datetime.now() + timedelta(days=days)

        # Determine reason
        reason = self._extract_reason(lower, matched_keywords[0])

        confidence = 0.9 if len(matched_keywords) > 1 else 0.75

        return {
            "is_delay": True,
            "days_requested": days,
            "followup_date": followup_date,
            "reason": reason,
            "confidence": confidence,
            "matched_keywords": matched_keywords
        }

    def _extract_days(self, lower: str) -> int:
        """Extract number of days from customer message."""
        for pattern, extractor in DAY_PATTERNS:
            match = re.search(pattern, lower)
            if match:
                try:
                    return extractor(match)
                except Exception:
                    continue
        # Default: 1 day if no specific time mentioned
        return 1

    def _extract_reason(self, lower: str, matched_keyword: str) -> str:
        """Extract human-readable reason for delay."""
        if "busy" in lower:
            return "Customer is currently busy"
        if "think" in lower:
            return "Customer wants time to consider"
        if "tomorrow" in lower:
            return "Customer requested next-day follow-up"
        if "next week" in lower:
            return "Customer requested follow-up next week"
        if "time" in lower:
            return "Customer needs more time"
        return f"Customer requested delay: '{matched_keyword}'"

    # ── Task Management ───────────────────────────────────────────────────────

    def create_followup_task(self, customer_id: str, vehicle_id: str,
                             delay_info: Dict,
                             original_diagnosis: Dict) -> FollowUpTask:
        """Create a new follow-up task with incremented cycle number."""
        # Increment cycle counter
        self._cycle_counts[customer_id] = self._cycle_counts.get(customer_id, 0) + 1
        cycle_number = self._cycle_counts[customer_id]

        task = FollowUpTask(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            followup_date=delay_info["followup_date"],
            reason=delay_info["reason"],
            cycle_number=cycle_number,
            original_diagnosis=original_diagnosis
        )

        if customer_id not in self._tasks:
            self._tasks[customer_id] = []
        self._tasks[customer_id].append(task)

        print(f"\n   📅 [FOLLOWUP] Task created: {task.task_id}")
        print(f"   📅 Follow-up date: {task.followup_date.strftime('%A, %d %B %Y')}")
        print(f"   🔄 Cycle number: {cycle_number}")
        print(f"   📝 Reason: {task.reason}")

        return task

    def get_pending_tasks(self, customer_id: str) -> List[FollowUpTask]:
        """Get all pending follow-up tasks for a customer."""
        tasks = self._tasks.get(customer_id, [])
        return [t for t in tasks if t.status == "PENDING"]

    def get_due_tasks(self, customer_id: str) -> List[FollowUpTask]:
        """Get tasks that are due for follow-up (date has passed)."""
        tasks = self._tasks.get(customer_id, [])
        now = datetime.now()
        return [
            t for t in tasks
            if t.status == "PENDING" and t.followup_date <= now
        ]

    def mark_task_triggered(self, task_id: str, customer_id: str):
        """Mark a task as triggered (follow-up contact initiated)."""
        for task in self._tasks.get(customer_id, []):
            if task.task_id == task_id:
                task.status = "TRIGGERED"
                break

    def mark_task_completed(self, task_id: str, customer_id: str):
        """Mark a task as completed."""
        for task in self._tasks.get(customer_id, []):
            if task.task_id == task_id:
                task.status = "COMPLETED"
                break

    def get_cycle_count(self, customer_id: str) -> int:
        """Get the current follow-up cycle count for a customer."""
        return self._cycle_counts.get(customer_id, 0)

    # ── Acknowledgment Message ────────────────────────────────────────────────

    def build_delay_acknowledgment(self, first_name: str, delay_info: Dict,
                                   component: str, failure_prob: float,
                                   rul_days: int) -> str:
        """
        Build a natural acknowledgment message when customer requests a delay.
        Confirms the follow-up without pressure, but includes a safety note.
        """
        days = delay_info["days_requested"]
        followup_date = delay_info["followup_date"]
        date_str = followup_date.strftime("%A, %d %B")

        if days == 1:
            timing_str = "tomorrow"
        elif days <= 3:
            timing_str = f"in {days} days"
        elif days == 7:
            timing_str = "next week"
        else:
            timing_str = f"on {date_str}"

        # Safety note calibrated to risk
        if failure_prob > 70:
            safety_note = (
                f"One thing to keep in mind: the failure risk is currently at "
                f"{failure_prob:.0f}% within {rul_days} days, so please drive "
                f"cautiously in the meantime — avoid hard braking and keep extra "
                f"following distance."
            )
        elif failure_prob > 40:
            safety_note = (
                f"The {component} is still flagged at {failure_prob:.0f}% risk "
                f"within {rul_days} days, so please drive gently in the meantime."
            )
        else:
            safety_note = (
                f"The {component} is being monitored — please let me know if you "
                f"notice any changes in how the vehicle drives."
            )

        return (
            f"Absolutely, {first_name} — no problem at all. "
            f"I'll follow up with you {timing_str}. "
            f"I'll also pull the latest vehicle data before I reach out, "
            f"so you'll have the most current picture. "
            f"\n\n{safety_note}"
        )
