"""
Vehicle Reanalysis Engine - Autonomous Service Orchestration Platform v1.0
Pre-follow-up re-analysis: pulls fresh telematics, computes delta vs. previous state,
and generates a tone directive for the conversation agent.

Delta Tone Modes:
  WORSENED  → "Since we last spoke, the condition has worsened…"
  STABLE    → "Condition hasn't worsened, but risk remains…"
  IMPROVED  → "Good news — hasn't worsened as quickly as expected…"
"""

import random
from datetime import datetime
from typing import Dict, Optional


class ReanalysisResult:
    """Structured result from vehicle re-analysis."""

    def __init__(self, vehicle_id: str, customer_id: str,
                 previous_state: Dict, current_state: Dict,
                 delta_summary: Dict, tone_mode: str,
                 updated_failure_prob: float, updated_rul_days: int,
                 days_elapsed: int):
        self.vehicle_id = vehicle_id
        self.customer_id = customer_id
        self.previous_state = previous_state
        self.current_state = current_state
        self.delta_summary = delta_summary
        self.tone_mode = tone_mode  # WORSENED | STABLE | IMPROVED
        self.updated_failure_prob = updated_failure_prob
        self.updated_rul_days = updated_rul_days
        self.days_elapsed = days_elapsed
        self.analyzed_at = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "vehicle_id": self.vehicle_id,
            "tone_mode": self.tone_mode,
            "updated_failure_prob": self.updated_failure_prob,
            "updated_rul_days": self.updated_rul_days,
            "days_elapsed": self.days_elapsed,
            "delta_summary": self.delta_summary,
            "analyzed_at": self.analyzed_at.isoformat(),
        }

    def get_opening_line(self, first_name: str, component: str) -> str:
        """Get the tone-appropriate opening line for the follow-up message."""
        if self.tone_mode == "WORSENED":
            prob_delta = self.delta_summary.get("failure_prob_change", 0)
            rul_delta = self.delta_summary.get("rul_change_days", 0)
            return (
                f"{first_name}, I've just pulled the latest data on your {component} "
                f"before reaching out — and I want to be upfront with you. "
                f"Since we last spoke {self.days_elapsed} day{'s' if self.days_elapsed != 1 else ''} ago, "
                f"the condition has worsened. "
                f"The failure probability has increased by {abs(prob_delta):.0f}% "
                f"and the estimated safe window has shortened by {abs(rul_delta)} days."
            )
        elif self.tone_mode == "IMPROVED":
            return (
                f"Good news, {first_name} — I've just pulled the latest data on your {component}. "
                f"Since we last spoke {self.days_elapsed} day{'s' if self.days_elapsed != 1 else ''} ago, "
                f"the condition hasn't worsened as quickly as our model initially projected. "
                f"That said, the risk is still present and I want to make sure you have "
                f"the full picture."
            )
        else:  # STABLE
            return (
                f"{first_name}, I've just pulled the latest data on your {component} "
                f"before reaching out. "
                f"Since we last spoke {self.days_elapsed} day{'s' if self.days_elapsed != 1 else ''} ago, "
                f"the condition hasn't worsened — which is the good news. "
                f"However, the risk remains at the same level, and I want to make sure "
                f"we address it before it does progress."
            )

    def get_data_update_line(self, component: str) -> str:
        """Get the updated data line for the follow-up message."""
        current = self.current_state
        prev = self.previous_state
        component_lower = component.lower()

        if "brake" in component_lower:
            curr_mm = current.get("brake_pad_mm", 0)
            prev_mm = prev.get("brake_pad_mm", 0)
            change = curr_mm - prev_mm
            return (
                f"Updated reading: {component} is now at {curr_mm:.2f}mm "
                f"(was {prev_mm:.2f}mm — change: {change:+.2f}mm). "
                f"Failure probability: {self.updated_failure_prob:.0f}% "
                f"within {self.updated_rul_days} days."
            )
        elif "battery" in component_lower:
            curr_v = current.get("battery_voltage_v", 0)
            prev_v = prev.get("battery_voltage_v", 0)
            change = curr_v - prev_v
            return (
                f"Updated reading: Battery is now at {curr_v:.2f}V "
                f"(was {prev_v:.2f}V — change: {change:+.2f}V). "
                f"Failure probability: {self.updated_failure_prob:.0f}% "
                f"within {self.updated_rul_days} days."
            )
        else:
            return (
                f"Updated failure probability: {self.updated_failure_prob:.0f}% "
                f"within {self.updated_rul_days} days "
                f"(was {self.previous_state.get('failure_prob', 0) * 100:.0f}% "
                f"{self.days_elapsed} days ago)."
            )


class VehicleReanalysisEngine:
    """
    Pre-follow-up vehicle re-analysis engine.

    Before each follow-up contact:
    1. Pull latest telematics (simulated or from temporal engine)
    2. Compare with previous state
    3. Compute delta (worsened / stable / improved)
    4. Generate tone directive for conversation agent
    """

    # Degradation rates per day (realistic simulation)
    DEGRADATION_RATES = {
        "brake_pad_mm": -0.05,       # Brake pads wear ~0.05mm/day under normal use
        "battery_voltage_v": -0.01,  # Battery degrades ~0.01V/day
        "coolant_temp_c": 0.2,       # Coolant temp rises ~0.2°C/day if issue present
    }

    def __init__(self):
        self._previous_states: Dict[str, Dict] = {}   # vehicle_id → previous telematics
        self._reanalysis_history: Dict[str, list] = {}  # vehicle_id → [ReanalysisResult]

    def store_baseline(self, vehicle_id: str, telematics: Dict, diagnosis: Dict):
        """Store baseline state for future delta comparison."""
        self._previous_states[vehicle_id] = {
            **telematics,
            "failure_prob": diagnosis.get("failure_probability", 0.5),
            "rul_days": diagnosis.get("rul_days", 30),
            "stored_at": datetime.now().isoformat()
        }

    def reanalyze(self, vehicle_id: str, customer_id: str,
                  days_elapsed: int,
                  temporal_simulator=None,
                  scenario: str = "warning") -> ReanalysisResult:
        """
        Perform re-analysis for a vehicle after a delay period.

        Args:
            vehicle_id: Vehicle identifier
            customer_id: Customer identifier
            days_elapsed: Days since last contact
            temporal_simulator: Optional existing TemporalSimulator instance
            scenario: Vehicle scenario for simulation

        Returns:
            ReanalysisResult with delta and tone directive
        """
        previous = self._previous_states.get(vehicle_id, {})

        # ── Pull fresh telematics ─────────────────────────────────────────────
        if temporal_simulator:
            # Use existing temporal simulator for realistic degradation
            current_telematics = temporal_simulator.simulate_time_passage(
                vehicle_id, days_elapsed, scenario
            )
        else:
            # Simulate degradation independently
            current_telematics = self._simulate_degradation(previous, days_elapsed)

        # ── Compute delta ─────────────────────────────────────────────────────
        delta_summary = self._compute_delta(previous, current_telematics, days_elapsed)

        # ── Determine tone mode ───────────────────────────────────────────────
        tone_mode = self._determine_tone_mode(delta_summary)

        # ── Update failure probability and RUL ────────────────────────────────
        prev_failure_prob = previous.get("failure_prob", 0.5) * 100
        prev_rul = previous.get("rul_days", 30)

        if tone_mode == "WORSENED":
            # Increase failure prob, decrease RUL
            prob_increase = random.uniform(5, 15)
            rul_decrease = random.randint(2, 7)
            updated_failure_prob = min(95, prev_failure_prob + prob_increase)
            updated_rul = max(1, prev_rul - rul_decrease)
        elif tone_mode == "IMPROVED":
            # Slight improvement
            prob_decrease = random.uniform(2, 8)
            rul_increase = random.randint(1, 3)
            updated_failure_prob = max(10, prev_failure_prob - prob_decrease)
            updated_rul = prev_rul + rul_increase
        else:  # STABLE
            # Minor fluctuation
            updated_failure_prob = prev_failure_prob + random.uniform(-3, 5)
            updated_rul = max(1, prev_rul - random.randint(0, 2))

        delta_summary["failure_prob_change"] = updated_failure_prob - prev_failure_prob
        delta_summary["rul_change_days"] = updated_rul - prev_rul

        result = ReanalysisResult(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            previous_state=previous,
            current_state=current_telematics,
            delta_summary=delta_summary,
            tone_mode=tone_mode,
            updated_failure_prob=updated_failure_prob,
            updated_rul_days=updated_rul,
            days_elapsed=days_elapsed
        )

        # Store result in history
        if vehicle_id not in self._reanalysis_history:
            self._reanalysis_history[vehicle_id] = []
        self._reanalysis_history[vehicle_id].append(result)

        # Update baseline for next comparison
        self._previous_states[vehicle_id] = {
            **current_telematics,
            "failure_prob": updated_failure_prob / 100,
            "rul_days": updated_rul,
            "stored_at": datetime.now().isoformat()
        }

        print(f"\n   🔬 [REANALYSIS] Vehicle: {vehicle_id}")
        print(f"   📊 Tone Mode: {tone_mode}")
        print(f"   📈 Failure Prob: {prev_failure_prob:.0f}% → {updated_failure_prob:.0f}%")
        print(f"   ⏱️  RUL: {prev_rul} → {updated_rul} days")

        return result

    def _simulate_degradation(self, previous: Dict, days_elapsed: int) -> Dict:
        """Simulate component degradation over elapsed days."""
        current = dict(previous)

        for metric, rate in self.DEGRADATION_RATES.items():
            if metric in current:
                # Add some randomness (±30% of rate)
                actual_rate = rate * (1 + random.uniform(-0.3, 0.3))
                current[metric] = current[metric] + (actual_rate * days_elapsed)

        return current

    def _compute_delta(self, previous: Dict, current: Dict,
                       days_elapsed: int) -> Dict:
        """Compute delta between previous and current telematics."""
        delta = {"days_elapsed": days_elapsed}

        # Brake pad delta
        if "brake_pad_mm" in previous and "brake_pad_mm" in current:
            prev_mm = previous["brake_pad_mm"]
            curr_mm = current.get("brake_pad_mm", prev_mm)
            delta["brake_pad_change_mm"] = curr_mm - prev_mm
            delta["brake_pad_worsened"] = curr_mm < prev_mm

        # Battery delta
        if "battery_voltage_v" in previous and "battery_voltage_v" in current:
            prev_v = previous["battery_voltage_v"]
            curr_v = current.get("battery_voltage_v", prev_v)
            delta["battery_change_v"] = curr_v - prev_v
            delta["battery_worsened"] = curr_v < prev_v

        # Coolant delta
        if "coolant_temp_c" in previous and "coolant_temp_c" in current:
            prev_c = previous["coolant_temp_c"]
            curr_c = current.get("coolant_temp_c", prev_c)
            delta["coolant_change_c"] = curr_c - prev_c
            delta["coolant_worsened"] = curr_c > prev_c

        return delta

    def _determine_tone_mode(self, delta: Dict) -> str:
        """Determine tone mode based on delta analysis."""
        worsened_count = sum([
            delta.get("brake_pad_worsened", False),
            delta.get("battery_worsened", False),
            delta.get("coolant_worsened", False),
        ])

        if worsened_count >= 2:
            return "WORSENED"
        elif worsened_count == 1:
            # Check severity of worsening
            brake_change = abs(delta.get("brake_pad_change_mm", 0))
            battery_change = abs(delta.get("battery_change_v", 0))
            if brake_change > 0.3 or battery_change > 0.1:
                return "WORSENED"
            return "STABLE"
        else:
            # No worsening — check if actually improved
            brake_improved = delta.get("brake_pad_change_mm", 0) > 0
            battery_improved = delta.get("battery_change_v", 0) > 0
            if brake_improved or battery_improved:
                return "IMPROVED"
            return "STABLE"

    def get_reanalysis_history(self, vehicle_id: str) -> list:
        """Get all reanalysis results for a vehicle."""
        return self._reanalysis_history.get(vehicle_id, [])

    def has_baseline(self, vehicle_id: str) -> bool:
        """Check if a baseline exists for this vehicle."""
        return vehicle_id in self._previous_states
