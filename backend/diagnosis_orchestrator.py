"""
Diagnosis Orchestrator - v2.0
Runs the LLM agent steps for one vehicle and returns a merged report.

Flow:
    1. DataAnalysisAgentV4  -> health assessment from the vehicle context
    2. DiagnosisAgentV4     -> failure component, RUL, severity
    3. ManufacturingAgent   -> DTC codes (simulated) + recalls (mock catalogue)
    4. SchedulingAgent      -> tentative slot suggestion

This module no longer reads or writes application state; `services.diagnosis`
loads the evidence from the database, calls `analyse()`, applies the rule
engine and persists the prediction.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from config import LlamaModelClient
from manufacturing_agent import ManufacturingAgent
from scheduling_agent import SchedulingAgent
from specialist_agents import AgentExecutor, DataAnalysisAgentV4, DiagnosisAgentV4

log = logging.getLogger(__name__)

# Fallback responses if the LLM is unavailable. `fallback: True` lets callers
# know the result did not come from the model.
_DATA_ANALYSIS_FALLBACK = {
    "health_score": None,
    "detected_anomalies": [],
    "service_demand_forecast": "UNKNOWN",
    "confidence": 0.0,
    "data_coverage": 0.0,
    "data_quality_notes": "LLM unavailable; no analysis",
    "critical_alerts": [],
    "trend_analysis": "",
    "fallback": True,
}

_DIAGNOSIS_FALLBACK = {
    "failure_probability": None,
    "rul_days": None,
    "affected_component": None,
    "severity": None,
    "recurring_defect": False,
    "confidence": 0.0,
    "diagnostic_reasoning": "",
    "recommended_action": "",
    "failure_mode": "",
    "secondary_risks": [],
    "fallback": True,
}


class DiagnosisOrchestrator:
    """Coordinates the LLM diagnosis steps. Safe to reuse across calls."""

    def __init__(self):
        self._model_client = None
        self._data_agent = None
        self._diag_agent = None
        self._mfg_agent = ManufacturingAgent()
        self._sched_agent = SchedulingAgent()

    def _ensure_agents(self) -> None:
        """Create AutoGen agents on first use (keeps startup fast)."""
        if self._data_agent is None:
            try:
                self._model_client = LlamaModelClient.create_specialist_client()
                self._data_agent = DataAnalysisAgentV4.create(self._model_client)
                self._diag_agent = DiagnosisAgentV4.create(self._model_client)
            except Exception as exc:
                log.warning("DiagnosisOrchestrator: could not create agents: %s", exc)
                self._data_agent = self._diag_agent = None

    async def analyse(self, context: dict, vehicle_code: str, make: str) -> dict:
        """Run steps 1-4 on `context` (vehicle, readings, history, baseline)."""
        self._ensure_agents()
        context_str = json.dumps(context, default=str)

        log.info("[%s] step 1: data analysis", vehicle_code)
        data_report = await self._run_data_analysis(context_str)
        log.info("[%s] step 2: diagnosis", vehicle_code)
        diag_report = await self._run_diagnosis_agent(context_str, data_report)
        log.info("[%s] step 3: manufacturing check", vehicle_code)
        mfg_report = self._mfg_agent.check_vehicle(vehicle_code, make=make)
        log.info("[%s] step 4: scheduling suggestion", vehicle_code)
        schedule = self._suggest_schedule(diag_report)

        return {
            "fallback": bool(data_report.get("fallback") or diag_report.get("fallback")),
            "severity": diag_report.get("severity"),
            "predicted_component": _normalise_component(diag_report.get("affected_component")),
            "rul_days": diag_report.get("rul_days"),
            "confidence": diag_report.get("confidence", 0.0),
            "failure_probability": diag_report.get("failure_probability"),
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
            "diagnosed_at": datetime.now().astimezone().isoformat(),
        }

    async def _run_data_analysis(self, context_str: str) -> dict:
        if not self._data_agent:
            return dict(_DATA_ANALYSIS_FALLBACK)
        prompt = (
            "Analyse the following vehicle context and return your JSON assessment. "
            "`telematics` may be null when the car has no reading source; then rely on "
            "service history, km driven, reported symptoms and the baseline estimate.\n\n"
            f"Context:\n{context_str}"
        )
        return await AgentExecutor.execute_agent(self._data_agent, prompt, dict(_DATA_ANALYSIS_FALLBACK))

    async def _run_diagnosis_agent(self, context_str: str, data_report: dict) -> dict:
        if not self._diag_agent:
            return dict(_DIAGNOSIS_FALLBACK)
        prompt = (
            "Given the vehicle context and the data-analysis report below, predict the component most "
            "likely to fail, its remaining useful life in days, and severity. Use one of these component "
            "names: brake_pads, battery, engine_oil, coolant_system, tires, air_filter.\n\n"
            f"Context:\n{context_str}\n\nData Analysis Report:\n{json.dumps(data_report, default=str)}"
        )
        return await AgentExecutor.execute_agent(self._diag_agent, prompt, dict(_DIAGNOSIS_FALLBACK))

    def _suggest_schedule(self, diag_report: dict) -> dict | None:
        """Tentative slot from the in-memory scheduler (DB-backed in Phase 1)."""
        severity = str(diag_report.get("severity") or "LOW").upper()
        rul = diag_report.get("rul_days")
        if severity == "LOW" and (not isinstance(rul, int) or rul > 60):
            return None
        priority = {"CRITICAL": "P0", "HIGH": "P1", "MEDIUM": "P2", "LOW": "P3"}.get(severity, "P3")
        try:
            slot = self._sched_agent.find_optimal_slot(component=diag_report.get("affected_component") or "default", priority=priority)
        except Exception as exc:
            log.warning("Scheduling suggestion failed: %s", exc)
            return None
        if not slot:
            return None
        when = slot.get("slot_time")
        return {
            "tentative": True,
            "slot_display": slot.get("slot_display"),
            "slot_time_iso": when.isoformat() if hasattr(when, "isoformat") else str(when or ""),
            "technician": (slot.get("technician") or {}).get("name", "TBD"),
            "bay": (slot.get("bay") or {}).get("id", "TBD") if isinstance(slot.get("bay"), dict) else str(slot.get("bay", "TBD")),
        }


def _normalise_component(raw) -> str | None:
    """Map free-text LLM component names onto the canonical part names."""
    if not raw or not isinstance(raw, str):
        return None
    text = raw.lower()
    for key, words in {
        "brake_pads": ("brake",),
        "battery": ("battery",),
        "engine_oil": ("oil",),
        "coolant_system": ("coolant", "cooling", "radiator"),
        "tires": ("tire", "tyre"),
        "air_filter": ("air filter", "air_filter"),
    }.items():
        if any(w in text for w in words):
            return key
    return None


_orchestrator_instance: DiagnosisOrchestrator | None = None


def get_orchestrator() -> DiagnosisOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DiagnosisOrchestrator()
    return _orchestrator_instance
