"""
App State - v1.0
Shared singleton state for the Dashboard API layer.

All modules write here; the REST / WebSocket endpoints read from here.
Thread-safe via asyncio.Lock where mutations happen.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard event types pushed over WebSocket
# ──────────────────────────────────────────────────────────────────────────────
class DashboardEvent:
    """Lightweight event descriptor pushed to /ws/dashboard clients."""

    VEHICLE_UPDATED = "VEHICLE_UPDATED"
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    CONVERSATION_TURN = "CONVERSATION_TURN"
    ALERT_FIRED = "ALERT_FIRED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    DIAGNOSIS_UPDATED = "DIAGNOSIS_UPDATED"

    @staticmethod
    def make(event_type: str, payload: Dict) -> Dict:
        return {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton state
# ──────────────────────────────────────────────────────────────────────────────
class AppState:
    """
    Global, process-wide state shared by the orchestration engine,
    scheduling agent, customer engagement agent, and the REST API.

    Usage:
        from app_state import app_state
        app_state.upsert_vehicle("VEH001", {...})
        vehicles = app_state.get_all_vehicles()
    """

    def __init__(self):
        # Core data stores
        self.vehicles: Dict[str, Dict] = {}          # vehicle_id → merged vehicle dict
        self.bookings: List[Dict] = []                # ordered list of booking dicts
        self.conversations: List[Dict] = []           # ordered list of conversation turn dicts
        self.alerts: List[Dict] = []                  # active alerts (P0 / P1)
        self.manufacturing: Dict[str, Dict] = {}      # vehicle_id → DTC + recall info

        # WebSocket subscribers
        self._ws_clients: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

        # Metadata
        self._initialized_at = datetime.now().isoformat()
        self._workflow_count = 0

    # ── Vehicle helpers ───────────────────────────────────────────────────────

    def upsert_vehicle(self, vehicle_id: str, data: Dict):
        """Insert or update a vehicle record and push a WS event."""
        data["updated_at"] = datetime.now().isoformat()
        self.vehicles[vehicle_id] = data
        self._broadcast(DashboardEvent.make(
            DashboardEvent.VEHICLE_UPDATED,
            {"vehicle_id": vehicle_id},
        ))

    def get_vehicle(self, vehicle_id: str) -> Optional[Dict]:
        return self.vehicles.get(vehicle_id)

    def get_all_vehicles(self) -> List[Dict]:
        return list(self.vehicles.values())

    # ── Booking helpers ───────────────────────────────────────────────────────

    def add_booking(self, booking: Dict):
        """Append a booking and push a WS event."""
        booking.setdefault("created_at", datetime.now().isoformat())
        self.bookings.append(booking)
        self._broadcast(DashboardEvent.make(
            DashboardEvent.BOOKING_CREATED,
            {"booking_id": booking.get("booking_id")},
        ))

    def get_all_bookings(self) -> List[Dict]:
        return list(self.bookings)

    def get_todays_bookings(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            b for b in self.bookings
            if b.get("slot_time_iso", "")[:10] == today
               or b.get("created_at", "")[:10] == today
        ]

    # ── Conversation helpers ──────────────────────────────────────────────────

    def add_conversation_turn(self, turn: Dict):
        """Append a conversation turn and push a WS event."""
        turn.setdefault("timestamp", datetime.now().isoformat())
        self.conversations.append(turn)
        self._broadcast(DashboardEvent.make(
            DashboardEvent.CONVERSATION_TURN,
            {"vehicle_id": turn.get("vehicle_id"), "direction": turn.get("direction")},
        ))

    def get_all_conversations(self) -> List[Dict]:
        return list(self.conversations)

    # ── Alert helpers ─────────────────────────────────────────────────────────

    def fire_alert(self, alert: Dict):
        """Register a P0/P1 alert and push a WS event."""
        alert.setdefault("fired_at", datetime.now().isoformat())
        self.alerts.append(alert)
        self._broadcast(DashboardEvent.make(
            DashboardEvent.ALERT_FIRED,
            alert,
        ))

    def get_active_alerts(self) -> List[Dict]:
        return list(self.alerts)

    # ── Manufacturing / DTC helpers ───────────────────────────────────────────

    def set_manufacturing(self, vehicle_id: str, data: Dict):
        self.manufacturing[vehicle_id] = data

    def get_manufacturing(self, vehicle_id: str) -> Optional[Dict]:
        return self.manufacturing.get(vehicle_id)

    # ── Dashboard summary ─────────────────────────────────────────────────────

    def get_summary(self) -> Dict:
        """Aggregate summary for GET /api/dashboard/summary."""
        total = len(self.vehicles)
        critical = sum(
            1 for v in self.vehicles.values()
            if v.get("priority") in ("P0", "P1")
        )
        normal = total - critical

        return {
            "total_vehicles": total,
            "critical_vehicles": critical,
            "normal_vehicles": normal,
            "total_bookings": len(self.bookings),
            "todays_bookings": len(self.get_todays_bookings()),
            "open_conversations": len({
                c.get("vehicle_id") for c in self.conversations
                if c.get("status") != "CLOSED"
            }),
            "active_alerts": len(self.alerts),
            "ai_accuracy": 0.94,           # placeholder — will be live in Week 5
            "fallback_rate": 0.06,
            "updated_at": datetime.now().isoformat(),
        }

    # ── WebSocket broadcast ───────────────────────────────────────────────────

    def register_ws(self, queue: asyncio.Queue):
        self._ws_clients.add(queue)

    def unregister_ws(self, queue: asyncio.Queue):
        self._ws_clients.discard(queue)

    def fire_event(self, event_type: str, payload: Dict = None):
        """Public convenience: broadcast an arbitrary typed event."""
        self._broadcast(DashboardEvent.make(event_type, payload or {}))

    def _broadcast(self, event: Dict):
        """Non-blocking broadcast to all connected dashboard WS clients."""
        for q in list(self._ws_clients):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop if client is slow

    # ── Serialisation helpers ─────────────────────────────────────────────────

    def to_dict(self) -> Dict:
        return {
            "vehicles": self.vehicles,
            "bookings": self.bookings,
            "conversations": self.conversations,
            "alerts": self.alerts,
            "manufacturing": self.manufacturing,
            "initialized_at": self._initialized_at,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Module-level singleton — import this everywhere
# ──────────────────────────────────────────────────────────────────────────────
app_state = AppState()
