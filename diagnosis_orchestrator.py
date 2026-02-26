"""
Diagnosis Orchestrator - v1.0
Master agent that coordinates the full per-vehicle AI diagnosis pipeline.

Flow:
    1. DataAnalysisAgentV4  → evaluates raw telematics → health_score, anomalies
    2. DiagnosisAgentV4     → predicts failure + RUL + severity
    3. ManufacturingAgent   → DTC codes + NHTSA recall check
    4. SchedulingAgent      → suggests optimal service slot (if needed)

Each step feeds into the next. The final merged result is written into
app_state and pushed via WebSocket so the frontend refreshes automatically.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Optional

from specialist_agents import DataAnalysisAgentV4, DiagnosisAgentV4, AgentExecutor
from manufacturing_agent import ManufacturingAgent
from scheduling_agent import SchedulingAgent
from config import LlamaModelClient
from app_state import app_state, DashboardEvent


# ──────────────────────────────────────────────────────────────────────────────
# Fallback responses if LLM is unavailable
# ──────────────────────────────────────────────────────────────────────────────
_DATA_ANALYSIS_FALLBACK = {
    "health_score": 0.5,
    "detected_anomalies": ["Unable to analyse — LLM unavailable"],
    "service_demand_forecast": "MEDIUM",
    "confidence": 0.0,
    "data_coverage": 0.0,
    "data_quality_notes": "Fallback result",
    "critical_alerts": [],
    "trend_analysis": "No trend available",
}

_DIAGNOSIS_FALLBACK = {
    "failure_probability": 0.5,
    "rul_days": 30,
    "affected_component": "unknown",
    "severity": "MEDIUM",
    "recurring_defect": False,
    "confidence": 0.0,
    "diagnostic_reasoning": "Unable to diagnose — LLM unavailable",
    "recommended_action": "Schedule manual inspection",
    "failure_mode": "Unknown",
    "secondary_risks": [],
}


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────
class DiagnosisOrchestrator:
    """
    Coordinates the full AI diagnosis pipeline for a single vehicle.
    Safe to instantiate once and reuse across calls.
    """

    def __init__(self):
        self._model_client = None
        self._data_agent = None
        self._diag_agent = None
        self._mfg_agent = ManufacturingAgent()
        self._sched_agent = SchedulingAgent()

    # ── Lazy init of LLM agents ───────────────────────────────────────────────

    def _ensure_agents(self):
        """Create AutoGen agents on first use (keeps startup fast)."""
        if self._data_agent is None:
            try:
                self._model_client = LlamaModelClient.create_specialist_client()
                self._data_agent = DataAnalysisAgentV4.create(self._model_client)
                self._diag_agent = DiagnosisAgentV4.create(self._model_client)
            except Exception as e:
                print(f"⚠️  DiagnosisOrchestrator: could not create agents — {e}")
                self._data_agent = None
                self._diag_agent = None

    # ── Main pipeline ─────────────────────────────────────────────────────────

    async def run_diagnosis(self, vehicle_id: str) -> Dict:
        """
        Execute the full 4-step diagnosis pipeline for *vehicle_id*.
        Returns the merged diagnosis dict and writes it into app_state.
        """
        self._ensure_agents()

        vehicle = app_state.get_vehicle(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found in app_state")

        telematics = vehicle.get("telematics", {})
        telem_str = json.dumps(telematics, default=str)

        # ── Step 1: Data Analysis ─────────────────────────────────────────────
        print(f"\n🔬 [{vehicle_id}] Step 1 — Data Analysis Agent")
        data_report = await self._run_data_analysis(telem_str)

        # ── Step 2: Diagnosis ─────────────────────────────────────────────────
        print(f"🩺 [{vehicle_id}] Step 2 — Diagnosis Agent")
        diag_report = await self._run_diagnosis_agent(telem_str, data_report)

        # ── Step 3: Manufacturing check ───────────────────────────────────────
        print(f"🏭 [{vehicle_id}] Step 3 — Manufacturing Agent")
        mfg_report = self._mfg_agent.check_vehicle(vehicle_id)
        app_state.set_manufacturing(vehicle_id, mfg_report)

        # ── Step 4: Scheduling suggestion ─────────────────────────────────────
        print(f"📅 [{vehicle_id}] Step 4 — Scheduling Agent")
        schedule = self._suggest_schedule(vehicle_id, diag_report)

        # ── Merge & persist ───────────────────────────────────────────────────
        merged_diagnosis = {
            "status": "completed",
            "severity": diag_report.get("severity", "MEDIUM"),
            "predicted_component": diag_report.get("affected_component", "unknown"),
            "rul_days": diag_report.get("rul_days"),
            "confidence": diag_report.get("confidence", 0.0),
            "failure_probability": diag_report.get("failure_probability", 0.5),
            "diagnostic_reasoning": diag_report.get("diagnostic_reasoning", ""),
            "recommended_action": diag_report.get("recommended_action", ""),
            "failure_mode": diag_report.get("failure_mode", ""),
            "secondary_risks": diag_report.get("secondary_risks", []),
            "recurring_defect": diag_report.get("recurring_defect", False),
            "data_analysis": data_report,
            "manufacturing": {
                "dtc_codes": mfg_report.get("dtc_codes", []),
                "recalls": mfg_report.get("recalls", []),
                "has_critical_issue": mfg_report.get("has_critical_issue", False),
            },
            "suggested_schedule": schedule,
            "diagnosed_at": datetime.now().isoformat(),
        }

        # Update vehicle health_score from the AI result
        health_score = data_report.get("health_score", vehicle.get("health_score", 0.5))
        failure_prob = diag_report.get("failure_probability", vehicle.get("failure_probability", 0.5))

        # Derive priority from severity
        sev = merged_diagnosis["severity"].upper()
        priority_map = {"CRITICAL": "P0", "HIGH": "P1", "MEDIUM": "P2", "LOW": "P3"}
        new_priority = priority_map.get(sev, vehicle.get("priority", "P3"))

        # Persist into vehicle record (merge, don't overwrite)
        vehicle["diagnosis"] = merged_diagnosis
        vehicle["health_score"] = round(health_score, 2) if isinstance(health_score, (int, float)) else vehicle.get("health_score", 0.5)
        vehicle["failure_probability"] = round(failure_prob, 2) if isinstance(failure_prob, (int, float)) else vehicle.get("failure_probability", 0.5)
        vehicle["priority"] = new_priority
        app_state.upsert_vehicle(vehicle_id, vehicle)

        # Push a dedicated WS event
        app_state._broadcast(DashboardEvent.make(
            "DIAGNOSIS_UPDATED",
            {"vehicle_id": vehicle_id, "severity": sev},
        ))

        # Fire alert if critical/high
        if sev in ("CRITICAL", "HIGH"):
            app_state.fire_alert({
                "vehicle_id": vehicle_id,
                "priority": new_priority,
                "message": f"AI Diagnosis: {merged_diagnosis['predicted_component']} — {sev}",
                "component": merged_diagnosis["predicted_component"],
                "source": "diagnosis_orchestrator",
            })

        print(f"✅ [{vehicle_id}] Diagnosis complete — severity={sev}, RUL={merged_diagnosis['rul_days']}d")
        return merged_diagnosis

    # ── Step helpers ──────────────────────────────────────────────────────────

    async def _run_data_analysis(self, telem_str: str) -> Dict:
        """Step 1: Call DataAnalysisAgentV4."""
        if not self._data_agent:
            return _DATA_ANALYSIS_FALLBACK.copy()

        prompt = (
            f"Analyse the following vehicle telematics data and return your JSON assessment.\n\n"
            f"Telematics:\n{telem_str}"
        )
        return await AgentExecutor.execute_agent(
            self._data_agent, prompt, _DATA_ANALYSIS_FALLBACK.copy()
        )

    async def _run_diagnosis_agent(self, telem_str: str, data_report: Dict) -> Dict:
        """Step 2: Call DiagnosisAgentV4 with telematics + data report."""
        if not self._diag_agent:
            return _DIAGNOSIS_FALLBACK.copy()

        prompt = (
            f"Given the vehicle telematics and the data-analysis report below, "
            f"predict component failure, RUL, and severity.\n\n"
            f"Telematics:\n{telem_str}\n\n"
            f"Data Analysis Report:\n{json.dumps(data_report, default=str)}"
        )
        return await AgentExecutor.execute_agent(
            self._diag_agent, prompt, _DIAGNOSIS_FALLBACK.copy()
        )

    def _suggest_schedule(self, vehicle_id: str, diag_report: Dict) -> Optional[Dict]:
        """Step 4: Ask SchedulingAgent for the best service slot."""
        severity = diag_report.get("severity", "LOW").upper()
        if severity in ("LOW",) and diag_report.get("rul_days", 999) > 60:
            return None  # No urgency — skip scheduling

        component = diag_report.get("affected_component", "default")
        priority_map = {"CRITICAL": "P0", "HIGH": "P1", "MEDIUM": "P2", "LOW": "P3"}
        priority = priority_map.get(severity, "P3")

        try:
            slot = self._sched_agent.find_optimal_slot(
                component=component,
                priority=priority,
            )
            if slot:
                return {
                    "slot_display": slot.get("slot_display"),
                    "slot_time_iso": slot.get("slot_time", datetime.now()).isoformat()
                                     if hasattr(slot.get("slot_time", ""), "isoformat")
                                     else str(slot.get("slot_time", "")),
                    "technician": slot.get("technician", {}).get("name", "TBD"),
                    "bay": slot.get("bay", {}).get("id", "TBD") if isinstance(slot.get("bay"), dict) else str(slot.get("bay", "TBD")),
                }
        except Exception as e:
            print(f"⚠️  Scheduling suggestion failed: {e}")

        return None


# ──────────────────────────────────────────────────────────────────────────────
# Background loop — re-diagnoses every vehicle on a timer
# ──────────────────────────────────────────────────────────────────────────────
_orchestrator_instance: Optional[DiagnosisOrchestrator] = None


def get_orchestrator() -> DiagnosisOrchestrator:
    """Return the module-level singleton orchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DiagnosisOrchestrator()
    return _orchestrator_instance


async def background_diagnosis_loop(interval_minutes: int = 30):
    """
    Infinite loop that re-runs diagnosis for every vehicle.
    Call this as an asyncio.create_task from the server startup.
    """
    orchestrator = get_orchestrator()

    while True:
        await asyncio.sleep(interval_minutes * 60)
        print(f"\n🔁 Background diagnosis loop — re-scanning all vehicles")
        for vid in list(app_state.vehicles.keys()):
            try:
                await orchestrator.run_diagnosis(vid)
            except Exception as e:
                print(f"⚠️  Background diagnosis failed for {vid}: {e}")
        print("🔁 Background diagnosis loop — cycle complete\n")
