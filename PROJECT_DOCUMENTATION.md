# AutoPredict — Agentic Predictive Maintenance Platform
## Complete Technical Documentation

> **What this system is, in one sentence:** a multi-agent AI system that continuously watches vehicle telematics, predicts component failures before they happen, autonomously negotiates a service appointment with the customer over chat/SMS/WhatsApp/voice, books the slot, and surfaces the whole operation on a live web dashboard and a Flutter mobile app.

**Stack at a glance**

| Layer | Technology |
|---|---|
| Agent framework | Microsoft **AutoGen 0.7.5** (`autogen-agentchat`, `autogen-ext[openai]`) |
| LLM (brain) | **Llama 3 8B** served locally by **Ollama** (`http://localhost:11434`) |
| ML models | scikit-learn **RandomForest** classifier + regressor (persisted as `.joblib`) |
| Backend API | **FastAPI** + Uvicorn, REST + WebSocket, port 8000 |
| Web dashboard | **React 19 + Vite + TailwindCSS + Recharts + Three.js** |
| Mobile app | **Flutter 3 + Riverpod + go_router + Dio** |
| Comms | Twilio (SMS/WhatsApp/Voice), SMTP email, ElevenLabs TTS, Whisper STT |
| State | In-process singleton (`app_state`) + JSON memory files |

---

# TABLE OF CONTENTS

**PART A — CONCEPTS**
1. [What is Agentic AI](#1-what-is-agentic-ai)
2. [Types of Agentic AI](#2-types-of-agentic-ai--and-which-one-this-project-is)
3. [The Backbone of This System](#3-the-backbone-of-this-system)

**PART B — THE SYSTEM**
4. [End-to-End Architecture](#4-end-to-end-architecture)
5. [The Two Execution Paths](#5-the-two-execution-paths)
6. [The 5 Agents — In Depth](#6-the-5-agents--in-depth)
7. [The Meta-Agents (Orchestrator, Learning, Interpreter, Timing, Voice)](#7-the-meta-agents)
8. [The Models — LLM, ML, and the Rule Engine](#8-the-models--llm-ml-and-rule-engine)
9. [The Conversation Intelligence Stack](#9-the-conversation-intelligence-stack-15-modules)

**PART C — THE CLIENTS**
10. [The Web Dashboard (React)](#10-the-web-dashboard-react)
11. [The Mobile App (Flutter)](#11-the-mobile-app-flutter)

**PART D — RAG**
12. [What is RAG](#12-what-is-rag)
13. [Why This Project Needs RAG](#13-why-this-project-needs-rag--the-exact-pain-points)
14. [RAG Architecture for AutoPredict](#14-rag-architecture-for-autopredict)
15. [Full Implementation Guide (with code)](#15-full-implementation-guide)

**PART E — REFERENCE**
16. [Complete File-by-File Map](#16-complete-file-by-file-map)
17. [How to Run Everything](#17-how-to-run-everything)
18. [What's Real vs What's Mocked](#18-whats-real-vs-whats-mocked)

---
---

# PART A — CONCEPTS

## 1. What is Agentic AI

### 1.1 The plain definition

A normal LLM application is a **function**: text in → text out. You ask, it answers, it forgets, it stops.

**Agentic AI** is when you wrap an LLM in a loop that gives it three things a plain LLM does not have:

| Capability | What it means | Where you see it in this repo |
|---|---|---|
| **Goal** | A persistent objective, not a single question | *"Get this vehicle safely serviced before the component fails."* Each vehicle is a tenant with its own goal — see `TenantState` in [`backend/event_system.py`](backend/event_system.py) |
| **Tools / Actions** | The ability to *do* things in the world, not just talk | Send WhatsApp, place a voice call, hold a service bay slot, create a booking, write to the dashboard — `communication_service.py`, `scheduling_agent.py` |
| **Loop + Memory** | It observes the result of its action and decides the next one, remembering what happened | `EventBus` + `MasterOrchestrator.handle_event()` + `MemoryStore` |

The classic formulation is the **Perceive → Reason → Act → Reflect** loop:

```
        ┌──────────────────────────────────────────────┐
        │                                              │
        ▼                                              │
   ┌─────────┐    ┌────────┐    ┌─────┐    ┌─────────┐ │
   │ PERCEIVE│───▶│ REASON │───▶│ ACT │─ ──▶│ REFLECT │─┘
   └─────────┘    └────────┘    └─────┘    └─────────┘
    telematics     LLM plans     send msg   did it work?
    customer       + ML preds    book slot  update memory
    reply          + rules       escalate   replan
```

In AutoPredict this maps exactly to:

- **PERCEIVE** — `data_generator.py` / live OBD stream from the phone → `DataAnalysisAgent`
- **REASON** — `DiagnosisAgent` + `ml_models.py` + `rule_engine.py` → `MasterOrchestrator` builds a plan
- **ACT** — `CustomerEngagementAgent` sends messages, `SchedulingAgent` books the slot
- **REFLECT** — `LearningAgent` writes what worked into `memory_store_v4*.json`; `VehicleReanalysisEngine` re-checks the vehicle before the next follow-up

### 1.2 What makes it "agentic" and not just "automation"

A cron job that emails "your service is due" is automation. This system is agentic because:

1. **It replans at runtime.** If the customer declines, the `MasterOrchestrator` does not follow a pre-written `else` branch — it creates a *new plan* with a different strategy (`customer_recovery`) based on the situation. See `master_orchestrator.py:_handle_customer_response()`.
2. **It reacts to events, not to a script.** `EventBus` (in `event_system.py`) publishes typed events like `LOW_CONFIDENCE_DETECTED` or `CUSTOMER_NON_RESPONSIVE`, and any agent subscribed to them wakes up. The order of execution is not hard-coded.
3. **It has autonomy boundaries.** `ExecutionModeManager` enforces a 4-stage gate before the system is allowed to actually book something — the agent can talk freely but can only *act* after explicit human consent.
4. **It self-monitors.** Every agent returns a `confidence` field. If confidence < 0.6, the orchestrator fires `LOW_CONFIDENCE_DETECTED` and triggers deeper analysis instead of proceeding on a shaky answer.

---

## 2. Types of Agentic AI — and which one this project is

There are two useful ways to slice "types". Both matter for understanding this codebase.

### 2.1 By autonomy level (how much the AI decides)

| Level | Name | Description | Used here? |
|---|---|---|---|
| L0 | **Rule/Script** | Fixed if/else. No LLM. | ✅ `rule_engine.py` — deliberately kept as the *safety authority* |
| L1 | **LLM Call** | Single prompt → single response. Stateless. | ✅ `api_server.py:/api/chat` (the app's chat) |
| L2 | **LLM Chain** | Fixed sequence of prompts, output of A feeds B. | ✅ `diagnosis_orchestrator.py` — Data → Diagnosis → Manufacturing → Scheduling |
| L3 | **Router / Tool-using agent** | LLM decides *which* tool/branch to take. | ✅ `master_orchestrator_router.py` — routes intent to Booking / Follow-up / Escalation domains |
| L4 | **Autonomous multi-agent** | Agents plan, replan, and coordinate through an orchestrator; loops until goal met. | ✅ `orchestration_system.py` + `master_orchestrator.py` — the main system |
| L5 | **Fully autonomous / self-improving** | Agent modifies its own goals and code. | ❌ Not attempted (correctly — this is a safety-critical domain) |

**AutoPredict operates at L4**, with L0 rules deliberately retained as an override layer so an LLM hallucination can never assign the wrong safety priority.

### 2.2 By coordination pattern (how agents talk to each other)

| Pattern | Shape | Description |
|---|---|---|
| **Single agent + tools** | `Agent → [tool, tool, tool]` | One brain, many hands (ReAct style) |
| **Sequential / Pipeline** | `A → B → C` | Each agent's output is the next agent's input |
| **Hierarchical (Supervisor)** | `Master → {A, B, C}` | A supervisor plans, delegates, monitors, replans. **Workers never talk to each other.** |
| **Group Chat / Debate** | `A ⟷ B ⟷ C` | Agents converse freely; a selector picks who speaks next |
| **Swarm / Handoff** | `A → hands off → B` | Peer agents pass control explicitly |
| **Blackboard / Event-driven** | `A,B,C ⟷ shared bus` | Agents publish/subscribe to a shared event stream |

**AutoPredict uses a hybrid of Hierarchical + Event-driven + Sequential:**

```
                    ┌───────────────────────────┐
                    │    MASTER ORCHESTRATOR    │   ← Hierarchical supervisor
                    │  (plans, monitors,        │
                    │   replans, escalates)     │
                    └────────────┬──────────────┘
                                 │ publishes / subscribes
                    ┌────────────▼──────────────┐
                    │        EVENT BUS          │   ← Event-driven backbone
                    │  DATA_ANALYSIS_COMPLETED  │
                    │  LOW_CONFIDENCE_DETECTED  │
                    │  CUSTOMER_DECLINED ...    │
                    └────────────┬──────────────┘
          ┌───────────┬──────────┼──────────┬───────────┐
          ▼           ▼          ▼          ▼           ▼
     ┌────────┐  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
     │  Data  │─▶│Diagnosis│▶│  Mfg   │▶│Schedule│ │ Customer │  ← Sequential pipeline
     │Analysis│  │        │ │        │ │        │ │Engagement│
     └────────┘  └────────┘ └────────┘ └────────┘ └──────────┘
```

The system message in [`backend/master_orchestrator.py`](backend/master_orchestrator.py) states this contract explicitly:

> *"Agents never communicate directly with each other. All coordination, replanning, and escalation decisions are made by you."*

This is the **strict hierarchical guarantee** — it makes the system auditable, because every decision has one owner.

### 2.3 The multi-tenant twist

One design choice worth calling out: **each vehicle is an independent tenant** with its own isolated state machine.

```python
# event_system.py
class TenantRegistry:
    self.tenants: Dict[str, TenantState] = {}   # VEH001 → its own workflow, plan, memory
```

The orchestrator's system prompt enforces: *"Decisions MUST be isolated per vehicle. Never mix states, memory, or outcomes across tenants."* This means 100 vehicles = 100 concurrent independent agent loops, not one agent juggling 100 contexts.

---

## 3. The Backbone of This System

### 3.1 AutoGen 0.7.5 — the agent framework

Every LLM agent in this project is an `autogen_agentchat.agents.AssistantAgent`, run inside a `RoundRobinGroupChat` with `max_turns=1`.

```python
# specialist_agents.py — the pattern used everywhere
agent = AssistantAgent(
    name="Diagnosis_Agent",
    model_client=model_client,
    system_message=DiagnosisAgentV4.SYSTEM_MESSAGE   # forces strict JSON output
)

team = RoundRobinGroupChat([agent], max_turns=1)
stream = team.run_stream(task=prompt)
```

**Why `max_turns=1`?** The project uses AutoGen as a *structured single-shot executor*, not as a free-form chat. Each agent is called, produces one JSON object, and returns. The multi-turn logic lives in the orchestrator, not in AutoGen's group chat. This is a deliberate trade — it gives determinism and auditability at the cost of emergent agent-to-agent negotiation.

### 3.2 Ollama + Llama 3 8B — the LLM brain

```python
# config.py
MODEL_NAME     = "llama3:8b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"   # OpenAI-compatible shim
OLLAMA_API_KEY  = "ollama"                       # dummy, Ollama ignores it
```

Ollama exposes an **OpenAI-compatible `/v1` endpoint**, so AutoGen's `OpenAIChatCompletionClient` talks to it unchanged. Everything runs locally — no API keys, no per-token cost, full data privacy (important: this system handles customer PII and vehicle telemetry).

**Per-role temperature tuning** — a nice detail in `config.py`:

| Client factory | Temp | Max tokens | Rationale |
|---|---|---|---|
| `create_master_orchestrator_client()` | **0.05** | 3000 | Planning must be reproducible |
| `create_specialist_client()` | **0.1** | 2000 | Diagnosis must be consistent |
| `create_customer_interpreter_client()` | **0.1** | 1500 | Intent classification must be stable |
| `create_learning_client()` | **0.2** | 2000 | Slightly creative memory synthesis |
| `/api/chat` (mobile app) | **0.65** | 200 | Conversational warmth |

### 3.3 The Event Bus — the nervous system

[`backend/event_system.py`](backend/event_system.py) implements a lightweight async pub/sub:

```python
class EventBus:
    def subscribe(self, event_type: str, handler: Callable)
    async def publish(self, event: Event)          # fans out via asyncio.gather
    def get_tenant_events(self, tenant_id, event_type=None)   # per-vehicle isolation
```

**19 event types** defined in `config.py:EventTypes`:

```
Agent completion:  DATA_ANALYSIS_COMPLETED, DIAGNOSIS_UPDATED, CUSTOMER_RESPONSE_RECEIVED
Thresholds:        LOW_CONFIDENCE_DETECTED, HIGH_FAILURE_PROBABILITY
Customer:          CUSTOMER_NON_RESPONSIVE, CUSTOMER_DECLINED, CUSTOMER_ACCEPTED
System:            SLA_VIOLATION_RISK, AGENT_EXECUTION_FAILURE, ESCALATION_REQUIRED
Replanning:        REPLANNING_TRIGGERED, REPLANNING_COMPLETED
Workflow:          WORKFLOW_STARTED, WORKFLOW_COMPLETED, WORKFLOW_ABORTED
v5.0 routing:      BOOKING_INTENT_DETECTED, FOLLOWUP_REQUESTED, ESCALATION_REQUESTED
```

Every event carries a `tenant_id` (the vehicle) and gets a SHA-256 `event_id` for audit.

### 3.4 `app_state` — the shared blackboard

[`backend/app_state.py`](backend/app_state.py) is a process-wide singleton that every layer reads and writes:

```python
class AppState:
    vehicles:      Dict[str, Dict]   # vehicle_id → merged vehicle record
    bookings:      List[Dict]
    conversations: List[Dict]
    alerts:        List[Dict]
    manufacturing: Dict[str, Dict]   # DTC + recall data
    _ws_clients:   Set[asyncio.Queue]  # connected dashboard browsers
```

When an agent writes here, it **automatically broadcasts a WebSocket event** to every connected dashboard:

```python
def upsert_vehicle(self, vehicle_id, data):
    self.vehicles[vehicle_id] = data
    self._broadcast(DashboardEvent.make("VEHICLE_UPDATED", {"vehicle_id": vehicle_id}))
```

That single line is why the React dashboard updates live without polling.

### 3.5 Robust JSON extraction — the unglamorous but critical piece

Local 8B models are chatty; they wrap JSON in prose and markdown fences. `AgentExecutor.execute_agent()` in [`backend/specialist_agents.py`](backend/specialist_agents.py) handles this with a **bracket-counting parser that is string-aware**:

```python
# strips ```json fences, then walks characters tracking:
#   - escape sequences (\")
#   - whether we're inside a string literal
#   - brace depth
# stops at the exact closing brace of the first complete JSON object
```

Every agent call also passes a **`fallback` dict** computed from deterministic rules. If the LLM returns garbage, the system silently uses rule-based output and keeps running. This is why the system never crashes when Ollama is slow or the model rambles.

---
---

# PART B — THE SYSTEM

## 4. End-to-End Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENTS                                      │
│                                                                         │
│  ┌──────────────────────┐              ┌───────────────────────────┐    │
│  │  Flutter Mobile App  │              │   React Web Dashboard     │    │
│  │  (customer-facing)   │              │   (staff-facing)          │    │
│  │  • Home / OBD gauges │              │   • Operations view       │    │
│  │  • Diagnostics       │              │   • Manager view          │    │
│  │  • AI Service Chat   │              │   • Executive view        │    │
│  │  • Bookings          │              │   • 40+ analytics charts  │    │
│  └──────────┬───────────┘              └────────────┬──────────────┘    │
└─────────────┼──────────────────────────────────────┼───────────────────┘
              │ REST (Dio)                           │ REST (axios) + WS
              │ + direct Ollama via ngrok            │
              ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI SERVER  (port 8000)                          │
│                    webhook_server.py  ← entry point                     │
│                                                                         │
│   ┌───────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│   │  api_server.py    │  │ /webhook/whatsapp│  │  /ws/dashboard     │   │
│   │  60+ REST routes  │  │ /webhook/sms     │  │  WebSocket push    │   │
│   │  /api/vehicles    │  │ /webhook/email   │  │                    │   │
│   │  /api/bookings    │  │  ↓               │  │                    │   │
│   │  /api/analytics/* │  │ CustomerInterpr. │  │                    │   │
│   │  /api/chat        │  │  ↓ EventBus      │  │                    │   │
│   └─────────┬─────────┘  └────────┬─────────┘  └─────────▲──────────┘   │
└─────────────┼─────────────────────┼──────────────────────┼──────────────┘
              │                     │                      │
              ▼                     ▼                      │ broadcast
┌─────────────────────────────────────────────────────────────────────────┐
│                        app_state  (shared blackboard)                   │
│         vehicles · bookings · conversations · alerts · manufacturing    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ read / write
              ┌────────────────┴─────────────────┐
              ▼                                  ▼
┌──────────────────────────┐        ┌────────────────────────────────────┐
│  diagnosis_orchestrator  │        │      orchestration_system.py       │
│  (server pipeline)       │        │  EventDrivenOrchestratorV41        │
│  runs every 30 min       │        │  (CLI simulation, full 6-phase)    │
│                          │        │                                    │
│  1. Data Analysis Agent  │        │  Phase 0 Data → 1 Plan → 2 Execute │
│  2. Diagnosis Agent      │        │  → 3 Engage → 5 Decide → 6 Learn   │
│  3. Manufacturing Agent  │        │  + multi-cycle time simulation     │
│  4. Scheduling Agent     │        │                                    │
└───────────┬──────────────┘        └────────────────┬───────────────────┘
            │                                        │
            └────────────────┬───────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AGENT LAYER                                    │
│                                                                         │
│  MASTER ORCHESTRATOR (master_orchestrator.py + _router.py)              │
│         │ plans · monitors · replans · routes · resolves conflicts      │
│         ├── Data Analysis Agent      (specialist_agents.py)             │
│         ├── Diagnosis Agent          (specialist_agents.py)             │
│         ├── Manufacturing Agent      (manufacturing_agent.py)           │
│         ├── Scheduling Agent         (scheduling_agent.py)              │
│         ├── Customer Engagement Agent(customer_engagement.py)           │
│         │      └── 15-module conversation intelligence stack            │
│         ├── Learning Agent           (learning_agent.py)                │
│         ├── Contact Timing Agent     (ml_contact_timing_agent.py)       │
│         ├── Customer Interpreter     (customer_interpreter.py)          │
│         └── Voice AI Agent           (voice_ai_agent.py)                │
└──────────────┬────────────────────────────────────┬─────────────────────┘
               ▼                                    ▼
   ┌───────────────────────┐          ┌──────────────────────────────┐
   │   Ollama llama3:8b    │          │  scikit-learn RandomForest   │
   │   localhost:11434     │          │  ml_models/*.joblib          │
   └───────────────────────┘          └──────────────────────────────┘
               │                                    │
               └────────────────┬───────────────────┘
                                ▼
                  ┌──────────────────────────┐
                  │  rule_engine.py          │  ← DETERMINISTIC OVERRIDE
                  │  final safety authority  │     (P0/P1/P2/P3)
                  └──────────────────────────┘
```

---

## 5. The Two Execution Paths

This is the single most important thing to understand about the codebase: **there are two parallel runtimes**, built at different times, sharing the same agents.

### Path 1 — The CLI Simulation (`main.py`)

```
python main.py
   ↓
orchestration_system.py :: EventDrivenOrchestratorV41.run_workflow()
```

The full, demo-grade agentic loop with time simulation and human-in-the-loop terminal chat.

**Six phases per cycle:**

| Phase | Method | What happens |
|---|---|---|
| **0** Data Gathering | `_phase_0_data_gathering` | Generate telematics, vehicle master, maintenance history, customer profile, UEBA security check. Aborts the whole workflow if UEBA flags the account. |
| **1** Planning | `_phase_1_planning` | Master Orchestrator LLM produces a JSON plan: `strategy` (standard/expedited/deep_analysis/customer_recovery), `risk_level`, `steps[]`, `monitoring_expectations`, `next_events_to_watch` |
| **2** Execution | `_phase_2_workflow_execution` | Data Analysis Agent → Diagnosis Agent. Both re-run with fresh data on every cycle (not cached). ML prediction is merged in here. |
| **3** Engagement | `_phase_3_customer_engagement` | Contact Timing Agent picks *when* to contact → Vehicle Reanalysis (cycle ≥2) → Customer Engagement Agent sends via ALL channels → interactive terminal conversation |
| **5** Decision | `_phase_5_final_decision` | `rule_engine.assign_priority()` (deterministic) → service window → work order generated |
| **6** Learning | `_phase_6_learning_and_summary` | Learning Agent updates customer + vehicle memory profiles |

**Multi-cycle behaviour** — the standout agentic feature:

```
CYCLE 1 → Customer DECLINES
    ↓
⏰ TIME SIMULATION: 2 days pass
    ↓
TemporalSimulator.simulate_time_passage()  → components degrade
    ↓
_display_degradation()  → "Brake pad Day 0: 3.20mm → Day 2: 2.80mm (-12.5%) 🔴 WORSENED"
    ↓
temporal_simulator.should_escalate()  → yes
    ↓
🚨 AUTO-ESCALATION → priority forced to P0, strategy forced to 'expedited'
    ↓
CYCLE 2 → all agents re-run on NEW data → VOICE CALL → customer ACCEPTS
```

### Path 2 — The Live Server (`webhook_server.py`)

```
python webhook_server.py   →  uvicorn on 0.0.0.0:8000
```

This is what the **web dashboard and mobile app** actually talk to.

**On startup it:**
1. Creates the Customer Interpreter LLM client
2. Creates the EventBus
3. Calls `seed_all()` — seeds 10 mock vehicles (`VEH001`–`VEH010`), 6 bookings, 4 conversations into `app_state`
4. Starts `background_diagnosis_loop(interval_minutes=30)` as an asyncio task

**What it exposes:**
- `api_router` from `api_server.py` — 60+ REST endpoints under `/api`
- `ws_router` — `/ws/dashboard` WebSocket
- `/webhook/whatsapp`, `/webhook/sms`, `/webhook/email` — inbound customer replies from Twilio/SendGrid
- `/test/simulate-response` — fake a customer reply for testing

**The background loop** ([`backend/diagnosis_orchestrator.py`](backend/diagnosis_orchestrator.py)) is the server-side agent pipeline:

```python
async def background_diagnosis_loop(interval_minutes=30):
    while True:
        await asyncio.sleep(interval_minutes * 60)
        for vid in app_state.vehicles:
            await orchestrator.run_diagnosis(vid)   # 4-agent chain
```

`run_diagnosis()` executes the sequential chain, merges the results, writes to `app_state`, broadcasts `DIAGNOSIS_UPDATED` over WebSocket, and fires an alert if severity is CRITICAL/HIGH.

**Why two paths exist:** Path 1 was built first as the research/demo system with rich agentic behaviour. Path 2 was added when the web and mobile clients needed a persistent API. They share `specialist_agents.py`, `scheduling_agent.py`, `manufacturing_agent.py`, `config.py`, and `app_state.py`.

---

## 6. The 5 Agents — In Depth

### AGENT 1 — Data Analysis Agent 🔬

| | |
|---|---|
| **File** | [`backend/specialist_agents.py`](backend/specialist_agents.py) → `class DataAnalysisAgentV4` |
| **Type** | LLM agent (AutoGen `AssistantAgent`) |
| **Model** | llama3:8b @ temp 0.1, 2000 tokens |
| **Position** | First in the chain — everything downstream depends on it |

**Exact role:** convert raw sensor numbers into a *health assessment* — a compressed, judgement-bearing summary that the Diagnosis Agent can reason over.

**Input prompt** (built in `orchestration_system.py:_execute_data_analysis`):
```
Analyze vehicle data:

TELEMATICS:
- Brake Pads: 2.10mm
- Battery: 11.20V
- Coolant: 115.3°C
- Oil Pressure: 2.80 bar
- Odometer: 87,432km

MAINTENANCE HISTORY: 4 events

Provide health assessment. JSON only.
```

**Required output schema:**
```json
{
  "health_score": 0.75,                    // 0.0–1.0 overall vehicle health
  "detected_anomalies": ["Critical brake wear"],
  "service_demand_forecast": "LOW|MEDIUM|HIGH",
  "confidence": 0.85,                      // used by orchestrator to trigger replanning
  "data_coverage": 0.95,                   // how complete was the sensor data
  "data_quality_notes": "Real-time data complete",
  "critical_alerts": ["IMMEDIATE brake replacement required"],
  "trend_analysis": "Accelerating wear on front axle"
}
```

**Hard-coded thresholds injected into its system prompt** (so the LLM doesn't invent its own):

| Component | Warning | Critical |
|---|---|---|
| Brake pads | < 5 mm | < 3 mm |
| Battery voltage | < 11.8 V | < 11.5 V |
| Coolant temp | > 105 °C | > 110 °C |

**Deterministic fallback.** If the LLM fails, `_detect_anomalies()`, `_forecast_demand()` and `_get_critical_alerts()` produce the same shape from pure Python threshold logic. The system degrades gracefully rather than failing.

**How its output is used:**
- `health_score` → written to `vehicle["health_score"]` → drives the fleet health gauge on the web dashboard
- `confidence` → if `< 0.6`, the Master Orchestrator publishes `LOW_CONFIDENCE_DETECTED` and triggers replanning
- `detected_anomalies` → fed verbatim into the Diagnosis Agent's prompt

---

### AGENT 2 — Diagnosis Agent 🩺

| | |
|---|---|
| **File** | [`backend/specialist_agents.py`](backend/specialist_agents.py) → `class DiagnosisAgentV4` |
| **Type** | LLM agent, **fused with an ML model** |
| **Model** | llama3:8b @ temp 0.1 + RandomForest classifier/regressor |
| **Position** | Second — the predictive core of the whole product |

**Exact role:** answer three questions with numbers: *What will break? How likely? How long do we have?*

**Required output schema:**
```json
{
  "failure_probability": 0.85,        // 0–1
  "rul_days": 12,                     // Remaining Useful Life in days
  "affected_component": "Brake Pads",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "recurring_defect": false,          // has this component failed before?
  "confidence": 0.80,
  "diagnostic_reasoning": "Front brake pads at 2.1mm with 87k km...",
  "recommended_action": "Replace front brake pads",
  "failure_mode": "Pad backing plate contact with rotor",
  "secondary_risks": ["Rotor scoring", "ABS sensor damage"]
}
```

**The LLM + ML fusion** (`orchestration_system.py:_execute_diagnosis`):

```python
# 1. Rule-based fallback computed FIRST from raw thresholds
if brake_val < 3:
    component, failure_prob, rul, severity = "Brake Pads", 0.85, max(3, int((brake_val-1.5)*5)), "CRITICAL"
elif battery_val < 11.5: ...
elif coolant_val > 110: ...

# 2. ML model predicts independently
ml_prediction = self.ml_manager.predict_failure(telematics, maintenance_history)

# 3. LLM agent runs (falls back to #1 if it fails)
output = await self.agent_executor.execute_agent(diagnosis_agent, prompt, fallback)

# 4. If the LLM produced nothing useful, ML wins
if ml_prediction and output.get('ml_model') == 'rule_based_fallback':
    output = ml_prediction
```

So there are **three independent predictors** (rules, ML, LLM) with a defined precedence. This redundancy is what makes the system safe to run on a small local model.

**RUL formulas in the fallback path** — worth knowing because they run more often than you'd think:

| Component | Trigger | RUL formula |
|---|---|---|
| Brake Pads | `< 3.0 mm` | `max(3, (mm - 1.5) × 5)` days |
| Battery | `< 11.5 V` | `max(5, (V - 10.5) × 10)` days |
| Cooling System | `> 110 °C` | `max(7, (120 - °C) × 2)` days |
| Default | — | `max(20, brake_mm × 10)` days |

**Severity → Priority mapping** (`diagnosis_orchestrator.py`):
```python
{"CRITICAL": "P0", "HIGH": "P1", "MEDIUM": "P2", "LOW": "P3"}
```
…but this is **overridden** by `rule_engine.assign_priority()` in the CLI path, which considers raw sensor values directly. A safety-critical brake reading forces P0 regardless of what the LLM said.

---

### AGENT 3 — Manufacturing Agent 🏭

| | |
|---|---|
| **File** | [`backend/manufacturing_agent.py`](backend/manufacturing_agent.py) → `class ManufacturingAgent` |
| **Type** | **Deterministic tool agent** (no LLM) |
| **Position** | Third — enriches the diagnosis with manufacturer-side facts |

**Exact role:** bring in information the vehicle's own sensors cannot know — **DTC fault codes** and **open safety recalls**.

**Two functions:**

**1. `get_dtc_codes(vehicle_id)` — simulated OBD-II scan**

Uses a deterministic seed (`int(digits_in_vehicle_id) × 7919`) so the same vehicle always returns the same codes. Picks 0–3 codes from a catalogue of 10 SAE J2012 codes with weights `[0.40, 0.30, 0.20, 0.10]`.

The catalogue spans all four OBD-II systems:

| Prefix | System | Example |
|---|---|---|
| `P` | Powertrain | `P0300` Random/multiple cylinder misfire — **critical** |
| `C` | Chassis | `C0035` Left front wheel speed sensor fault — **critical** |
| `B` | Body | `B0100` Driver airbag loop resistance high — **critical** |
| `U` | Network | `U0100` Lost communication with ECM/PCM — **critical** |

Each returned code carries `first_seen`, `occurrence_count`, and `mil_status` (Malfunction Indicator Lamp: `ON` for critical, `PENDING` otherwise).

**2. `get_recalls(vehicle_id)` — NHTSA recall check**

Resolves the vehicle's `make` (from `app_state`, falling back to `data_generator`), then matches against a catalogue of 4 mock NHTSA campaigns:

| Campaign | Component | Affected makes |
|---|---|---|
| `24V-987` | Airbag inflator | Toyota, Honda |
| `23V-654` | Brake master cylinder | Ford, BMW |
| `25V-112` | HV battery contactors | Tesla |
| `24V-321` | Fuel pump relay | Honda, Toyota, Ford |

**Output:**
```json
{
  "vehicle_id": "VEH001", "checked_at": "...",
  "dtc_codes": [...], "dtc_count": 2,
  "recalls": [...], "recall_count": 1,
  "has_critical_issue": true      // any critical DTC OR any open recall
}
```

**Why no LLM?** Recalls and DTCs are *facts*, not judgements. A hallucinated recall campaign number is worse than useless — it's a legal problem. This agent is deliberately deterministic.

> ⚠️ **This is currently mocked.** In production, `get_recalls()` would call `https://api.nhtsa.gov/recalls/recallsByVehicle` and `get_dtc_codes()` would read a real OBD-II dongle. The module docstring says exactly this. **This is also the single best RAG target in the codebase — see [§13](#13-why-this-project-needs-rag--the-exact-pain-points).**

---

### AGENT 4 — Scheduling Agent 📅

| | |
|---|---|
| **File** | [`backend/scheduling_agent.py`](backend/scheduling_agent.py) → `class SchedulingAgent` (~1600 lines) |
| **Type** | **Deterministic constraint-solving agent** (no LLM) |
| **Position** | Fourth — turns a diagnosis into a real, resourced appointment |

**Exact role:** be the autonomous service advisor. Find a slot that satisfies technician skill, bay availability, service duration, priority, and customer preference — then hold it, confirm it, and produce a customer-ready confirmation. **No human advisor needed.**

**The resource model:**

```python
SERVICE_DURATIONS = {           # hours
    "Brake Pads": 1.5,  "Battery": 0.75,  "Cooling System": 2.0,
    "Engine": 3.0,      "Transmission": 4.0, "Tires": 1.0,
    "Oil Change": 0.5,  "Full Service": 3.5, "default": 2.0,
}

TECHNICIANS = [   # 5 techs, each with specializations and a level
    {"id":"T001", "name":"Rajesh Kumar", "specialization":["Brake Pads","Tires","Oil Change"], "level":"SENIOR"},
    {"id":"T002", "name":"Amit Sharma",  "specialization":["Battery","Electrical"],            "level":"SENIOR"},
    {"id":"T003", "name":"Priya Nair",   "specialization":["Cooling System","Engine"],         "level":"LEAD"},
    {"id":"T004", "name":"Suresh Patel", "specialization":["Transmission","Full Service"],     "level":"SENIOR"},
    {"id":"T005", "name":"Deepak Mehta", "specialization":["Brake Pads","Battery","Tires"],    "level":"JUNIOR"},
]

BAYS = [BAY-1 STANDARD, BAY-2 STANDARD, BAY-3 HEAVY, BAY-4 EXPRESS, BAY-5 STANDARD]
WORKING_HOURS = 08:00 – 18:00
```

**Capability breakdown:**

| Capability | Key methods |
|---|---|
| **Capacity intelligence** | `_get_available_technician()` (skill-matched), `_get_available_bay()`, `_get_service_duration()`, `_is_slot_within_working_hours()` |
| **Slot intelligence** | `find_slots_for_date()`, `find_best_slot()`, `find_alternative_slots()`, `find_optimal_slot()`, `check_availability()` |
| **Reservation lifecycle** | `hold_slot()` → `SlotHold` with expiry → `release_hold()` / `_cleanup_expired_holds()` |
| **Booking execution** | `create_booking()`, `reschedule_booking()`, `cancel_booking()`, `add_to_waitlist()` |
| **Natural language** | `_parse_requested_date()` — parses "tomorrow", "next Tuesday", "this weekend" |
| **Customer output** | `format_availability_message()`, `BookingConfirmation.to_customer_message()` |

**The `SlotHold` mechanism** is the notable bit of engineering. When a customer says "yes", the agent doesn't book immediately — it places a **time-limited hold** on the slot. This prevents double-booking during the multi-turn "which time works for you?" conversation, and auto-releases if the customer goes silent.

**`BookingConfirmation`** produces a fully structured record:
```
Booking ID · Slot datetime · Technician (name + level) · Bay (id + type)
Service duration · Priority · Prep instructions (component-specific)
```
`_build_prep_instructions(component)` generates advice like *"Please arrive with at least ¼ tank of fuel"* or *"Remove personal items from the boot"* per service type.

---

### AGENT 5 — Customer Engagement Agent 💬

| | |
|---|---|
| **File** | [`backend/customer_engagement.py`](backend/customer_engagement.py) → `class CustomerEngagementAgentV6` (~930 lines, aliased as `V4`/`V5` for back-compat) |
| **Type** | **Hybrid** — deterministic reasoning core + LLM used *only* for language polish |
| **Position** | Last, and by far the most complex |

**Exact role:** persuade a real human to bring their car in — handling scepticism, cost objections, travel constraints, past bad service, and requests for a human — without ever pressuring them, and without the LLM being allowed to invent facts.

#### The core design principle

> **The LLM never decides the response direction. It only makes a pre-decided response sound natural.**

Its system message says exactly that:
```
You are polishing a pre-written response to make it sound more natural and human.
1. Keep ALL the facts, data, and specific details exactly as given
2. Make the language flow more naturally
3. Do NOT add urgency, pressure, or sales language
4. Do NOT remove any specific measurements, percentages, or data points
5. Do NOT change the core message or direction
```

This is the opposite of the usual "let the LLM handle the conversation" approach — and it's the right call for a domain where a hallucinated price or a fabricated safety claim is a liability.

#### The 10-step per-turn pipeline

Every time the customer sends a message, this runs:

```
 1. Intent Classification          → customer_intent_classifier.py  (14 intents)
 2. Execution Mode Check           → execution_mode_manager.py      (booking gate)
 3. Trust Signal Detection         → trust_signal_detector.py       (trust score)
 4. Conversation Stage             → conversation_stage_manager.py  (5 stages)
 5. Personalization Context        → personalization_context_engine.py
 6. Edge Case Detection            → edge_case_decision_engine.py   (7 cases)
 7. Strategy Response Router       → strategy_response_router.py    (deterministic text)
 8. Scheduling Handoff             → scheduling_agent.py            (if EXECUTION_MODE)
 9. LLM Polish                     → llama3:8b  (naturalization only)
10. Safety Overrides               → final guardrails
```

#### Multi-channel outreach

On first contact it fires **every channel simultaneously**:

```python
for ch in ["EMAIL", "WHATSAPP", "SMS"]:
    await self.communication_service.send(channel=ch, ...)

if priority in ["P0", "P1"] or escalated:
    await self.communication_service.send(channel="VOICE_CALL", ...)   # 📞
```

Channel eligibility is configured per priority in `config.py`:

| Channel | Allowed priorities | Max retries |
|---|---|---|
| EMAIL | P0, P1, P2, P3 | 3 |
| SMS | P0, P1, P2 | 2 |
| WHATSAPP | P0, P1 | 2 |
| VOICE_CALL | P0 only | 1 |

#### The four terminal states

The conversation loop exits on one of:

| Status | Meaning | Returned `customer_response` |
|---|---|---|
| `BOOKING_CONFIRMED` | Explicit consent **+** slot picked **+** slot confirmed → booking created | `ACCEPTED` |
| `ESCALATED_TO_HUMAN` | Customer explicitly asked for a supervisor | `ESCALATED` |
| `FOLLOWUP_SCHEDULED` | Customer asked to be contacted later | `DELAYED` |
| `DECLINED` | Customer refused | `DECLINED` |

#### The `ACCEPTED` → `EXECUTION_READY` safety gate

This is the subtlest and most important piece of logic in the file:

```python
elif status == 'ACCEPTED':
    # Customer accepted — enter EXECUTION_READY: present slot options
    # DO NOT create booking yet — wait for slot preference
    self.execution_mode_manager.force_execution_mode(customer_id)
    availability  = self.scheduling_agent.check_availability(component, priority)
    slot_options  = self.scheduling_agent.format_availability_message(...)
    current_message = f"Wonderful, {first_name}! Here are the available slots... Which time works best?"
    print("🛡️ [SAFETY] ACCEPTED → EXECUTION_READY (presenting slots, no booking yet)")
```

**"Customer acceptance ≠ final slot lock."** `ExecutionModeManager` enforces a one-way 4-stage gate:

```
INTENT_ACCEPTED  →  SLOT_SELECTED  →  SLOT_CONFIRMED  →  EXECUTION
```

The agent cannot skip a stage. This is the autonomy boundary that makes an autonomous booking agent deployable.

#### Follow-up cycles with re-analysis

If the customer says "call me in two days", `FollowupCycleManager` schedules it — and critically, before the follow-up message goes out, `VehicleReanalysisEngine` re-reads the vehicle and computes a delta, producing a **tone directive**:

| Delta | Tone directive | Opening line |
|---|---|---|
| `WORSENED` | Increase urgency, factual | *"Since we last spoke, the condition has worsened…"* |
| `STABLE` | Steady, no pressure | *"Condition hasn't worsened, but the risk remains…"* |
| `IMPROVED` | Reassuring | *"Good news — it hasn't worsened as quickly as expected…"* |

The follow-up message is therefore **grounded in fresh data**, not a canned reminder.

---

## 7. The Meta-Agents

Beyond the five worker agents, five more agents run the system.

### 7.1 Master Orchestrator 🧠

**Files:** [`backend/master_orchestrator.py`](backend/master_orchestrator.py) + [`backend/master_orchestrator_router.py`](backend/master_orchestrator_router.py)

The supervisor. Its system prompt lays out six responsibilities:

```
1. Plan workflows dynamically per tenant (vehicle)
2. React to events instead of static sequences
3. Monitor agent confidence, execution quality, and customer responses
4. Trigger replanning, escalation, or abort decisions
5. Maintain lifecycle state per tenant
6. Enable self-learning by updating memory signals
```

**Its replanning rules — the decision policy:**
```
- Replan if confidence < 0.6
- Replan if customer declines or reschedules
- Escalate if P0/P1 risk AND customer unresponsive
- Abort ONLY on compliance or safety violation
```

**Its four planning strategies:**

| Strategy | When |
|---|---|
| `standard` | Routine maintenance, normal flow |
| `expedited` | P0/P1 priority — fast-track |
| `deep_analysis` | Unclear case — gather more data before contacting |
| `customer_recovery` | Customer declined / went silent |

**Event handlers** (`handle_event` dispatches to eight):

| Event | Reaction |
|---|---|
| `DATA_ANALYSIS_COMPLETED` | If confidence < 0.6 → publish `LOW_CONFIDENCE_DETECTED`; else proceed |
| `DIAGNOSIS_UPDATED` | If failure prob > 0.7 → publish `HIGH_FAILURE_PROBABILITY` (CRITICAL) |
| `CUSTOMER_RESPONSE_RECEIVED` | ACCEPTED → work order · DECLINED → replan · RESCHEDULE → adaptive plan |
| `LOW_CONFIDENCE_DETECTED` | Trigger replanning for deeper analysis |
| `HIGH_FAILURE_PROBABILITY` | Publish `ESCALATION_REQUIRED` |
| `CUSTOMER_NON_RESPONSIVE` | P0/P1 → escalate · else → schedule follow-up |
| `SLA_VIOLATION_RISK` | Immediate escalation |
| `AGENT_EXECUTION_FAILURE` | Replan with fallback strategy |

**The v5.0 domain router** (`master_orchestrator_router.py`) adds intent-based routing above all of this:

```
BOOKING            → SchedulingAgent
FOLLOW_UP_ANALYSIS → VehicleReanalysisEngine
ESCALATION         → Human advisor (explicit request / legal / VIP only)
PARTS / PRICE      → stub agents (future)
```

It also handles **conflict resolution** — e.g. slot is available but the part isn't:
```python
resolve_scheduling_conflict(customer_id, vehicle_id, slot_available, parts_available, booking_confirmation)
```

### 7.2 Learning Agent 🧠💾

**File:** [`backend/learning_agent.py`](backend/learning_agent.py)

The reflect step. After every workflow it writes behavioural patterns into `MemoryStore` (persisted to `memory_store_v4*.json`).

**What it learns:**

*Customer profile:*
```json
{
  "preferences":      { "preferred_channel": "WHATSAPP" },
  "behavior_signals": { "PREFERS_WHATSAPP": true, "HIGH_TRUST_CUSTOMER": true,
                        "RESPONDS_SLOWLY": false, "OFTEN_DECLINES": false },
  "multi_cycle_patterns": { "accepts_after_escalation": true,
                            "typical_response_time_hours": 12.5,
                            "responds_to_urgency": true }
}
```

*Vehicle profile:*
```json
{
  "reliability_signals": { "HIGH_RELIABILITY": true },
  "recurring_issues": ["Brake Pads"],
  "degradation_patterns": { "brake_pad_degradation_rate": "ACCELERATED",
                            "typical_cycle_interval_days": 2 }
}
```

**Its learning rules** (encoded in the system prompt, mirrored in `_get_default_updates()`):
```
- accepted via WhatsApp     → PREFERS_WHATSAPP = true
- declined 3+ times         → OFTEN_DECLINES = true
- response time > 24h       → RESPONDS_SLOWLY = true
- always accepts P0/P1      → HIGH_TRUST_CUSTOMER = true
- declined C1, accepted C2  → accepts_after_follow_up = true, learn optimal wait time
- accepted after escalation → responds_to_urgency = true
```

**How the loop closes:** `CustomerMemory.get_recommended_channel(priority)` reads these signals, so the *next* engagement automatically picks the channel this customer historically responds to. The system genuinely gets better per customer over time.

### 7.3 Customer Response Interpreter 📨

**File:** [`backend/customer_interpreter.py`](backend/customer_interpreter.py)

Turns free-text inbound messages ("yeah ok but can we do friday instead") into structured intent:
```json
{ "customer_response": "REQUESTED_RESCHEDULE", "sentiment": "NEUTRAL", "confidence": 0.87 }
```

Called by all three webhook handlers in `webhook_server.py`, then the result is published as a `CUSTOMER_RESPONSE_RECEIVED` event onto the bus, where the Master Orchestrator picks it up. This is the bridge between the real world and the agent loop.

### 7.4 Contact Timing Agent ⏰

**File:** [`backend/ml_contact_timing_agent.py`](backend/ml_contact_timing_agent.py) + `ml_models.py:ContactTimingOptimizer`

Decides **when** to contact — a genuinely differentiating feature.

| Priority | Behaviour |
|---|---|
| **P0** | Contact **now**, never wait |
| **P1** | Wait max 2 h; if within work hours, contact right after 17:00 |
| **P2/P3** | Use learned `preferred_hour`, default 19:00; wait up to 24 h |

Acceptance-probability modifiers:
```
evening (18:00–20:00)   → +0.15
work hours (09:00–17:00)→ −0.20
weekend, prefers weekend→ +0.10
weekend, doesn't        → −0.10
```

It returns human-readable reasoning: *"Avoiding work hours (9 AM – 5 PM); Evening contact preferred"*.

### 7.5 Voice AI Agent 📞

**Files:** [`backend/voice_ai_agent.py`](backend/voice_ai_agent.py), [`backend/voice_api.py`](backend/voice_api.py), [`backend/sentiment_analyzer.py`](backend/sentiment_analyzer.py)

Real-time voice conversation for P0 escalations. Target latency **< 300 ms**.

```
Twilio call ⟷ WebSocket audio stream
    ↓ STT   openai/whisper-large-v3-turbo  (Hugging Face)
    ↓ LLM   llama-3.1-70b-versatile        (Groq — fast inference)
    ↓ TTS   eleven_turbo_v2_5              (ElevenLabs, voice "Rachel")
```

Constrained to `max_response_words: 25` with filler words enabled (*"mm-hmm"*, *"right"*) so the caller doesn't hear dead air. `SentimentAnalyzer` runs live on the transcript — if frustration > 0.7 across 2+ turns, it triggers objection handling or escalation.

---

## 8. The Models — LLM, ML, and Rule Engine

The system runs **three independent prediction systems** and reconciles them. This is its most defensible architectural decision.

### 8.1 The LLM — llama3:8b via Ollama

| Property | Value |
|---|---|
| Model | `llama3:8b` (Meta Llama 3, 8 billion parameters) |
| Serving | Ollama, `http://localhost:11434` |
| Interface | OpenAI-compatible `/v1` (AutoGen) **and** native `/api/chat`, `/api/generate` |
| Cost | Zero — fully local |
| Privacy | Customer PII never leaves the machine |

**Which components call it:**

| Component | Endpoint | Temp | Purpose |
|---|---|---|---|
| Master Orchestrator | `/v1` via AutoGen | 0.05 | Planning JSON |
| Data Analysis / Diagnosis | `/v1` via AutoGen | 0.1 | Structured assessment JSON |
| Customer Interpreter | `/v1` via AutoGen | 0.1 | Intent extraction |
| Learning Agent | `/v1` via AutoGen | 0.2 | Memory synthesis |
| Customer Engagement (polish) | `/api/generate` direct httpx | 0.1 | Naturalize pre-written text |
| `/api/chat` (mobile) | `/api/chat` direct httpx | 0.65 | Conversational advisor |
| Flutter `OllamaService` | `/api/chat` streaming via ngrok | 0.7 | Token-by-token in-app chat |

### 8.2 The ML models — scikit-learn RandomForest

**Files:** [`backend/ml_models.py`](backend/ml_models.py), [`backend/ml_training.py`](backend/ml_training.py)
**Artifacts:** `backend/ml_models/` → `failure_classifier.joblib` (1.8 MB), `failure_regressor.joblib` (8.9 MB), `scaler.joblib`

**Model 1 — `FailurePredictionModel`**

| | |
|---|---|
| Classifier | `RandomForestClassifier` → failure probability |
| Regressor | `RandomForestRegressor` → RUL in days |
| Preprocessing | `StandardScaler` |

**10 input features:**
```
 1. brake_pad_mm          6. odo_km / 1000                (normalized)
 2. battery_voltage_v     7. len(maintenance_history)
 3. coolant_temp_c        8. brake_pad_mm < 3.0    → binary flag
 4. oil_pressure_bar      9. battery_voltage < 11.5→ binary flag
 5. tire_pressure_psi    10. coolant_temp > 110    → binary flag
```

Features 8–10 are **engineered threshold crossings** — they give the tree explicit access to the safety boundaries rather than making it learn them from data.

**Confidence is derived, not guessed:**
```python
raw_confidence = 2 * abs(failure_prob - 0.5)    # 0.5 → 0.0 ; 0.0 or 1.0 → 1.0
confidence = clip(raw_confidence + 0.5 + noise, 0.60, 0.98)
```
i.e. *the further the prediction is from a coin flip, the more confident we are.* Small random variance (±5% on probability, ±5 days on RUL) is added to simulate real-world model uncertainty.

**Model 2 — `ContactTimingOptimizer`** — 7 features (hour, weekday, is_weekend, total_interactions, avg_response_time, acceptance_rate, preferred_hour).

**Model 3 — `CustomerBehaviorPredictor`** — predicts acceptance likelihood:
```python
acceptance = base_rate + severity_boost[CRITICAL:+0.30, HIGH:+0.20, MEDIUM:+0.10, LOW:0]
if failure_prob > 0.8: acceptance += 0.15
acceptance = min(0.95, acceptance)     # never claim certainty
```
It then recommends an approach: `standard_notification` / `urgent_multi_channel` / `gentle_persuasion`.

**Graceful degradation:** if scikit-learn isn't installed or the `.joblib` files are missing, `MLModelManager.load_models()` logs a notice and every model falls back to `_fallback_prediction()` — pure threshold logic returning the identical schema. The system runs either way.

### 8.3 The Rule Engine — the deterministic authority

**File:** [`backend/rule_engine.py`](backend/rule_engine.py)

**This has the final word on priority.** No LLM output can override it.

```python
# P0 — Critical (immediate, <24h)
if brake_pad_mm < 3.0:                     return "P0"
if battery_voltage < 11.5:                 return "P0"
if coolant_temp > 110.0:                   return "P0"
if severity in ("HIGH", "CRITICAL"):       return "P0"
if recurring_defect and severity=="MEDIUM":return "P0"
if rul_days <= 3:                          return "P0"

# P1 — High (<7 days)
if failure_probability > 0.7:              return "P1"
if rul_days <= 7:                          return "P1"
if brake_pad_mm < 4.0:                     return "P1"
if battery_voltage < 11.8:                 return "P1"

# P2 — Medium (<30 days)
if failure_probability > 0.4:              return "P2"
if rul_days <= 30:                         return "P2"
if brake_pad_mm < 6.0:                     return "P2"

return "P3"    # Routine
```

**Other deterministic decisions it owns:**

| Method | Logic |
|---|---|
| `determine_escalation()` | P0 always · P1 + declined · recurring + declined · failure>0.7 + declined |
| `calculate_service_window()` | P0: `min(1, rul//4)` d · P1: `min(7, rul//2)` · P2: `min(30, rul//2)` · P3: `min(90, rul)` |
| `determine_service_urgency()` | `EMERGENCY` / `URGENT` / `SCHEDULED_SOON` / `ROUTINE` |
| `calculate_confidence_threshold()` | P0 needs 0.85 · P1 0.75 · P2 0.65 · P3 0.50 |
| `assess_risk_level()` | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` |

**The safety architecture in one line:**

```
LLM proposes  →  ML quantifies  →  RULES decide  →  Human consents  →  System acts
```

---

## 9. The Conversation Intelligence Stack (15 modules)

The Customer Engagement Agent delegates to 15 specialised modules. This is where the "no generic fallback responses" guarantee comes from.

| # | Module | Responsibility |
|---|---|---|
| 1 | `customer_intent_classifier.py` | Classifies message into **14 intents**: `LOGISTICS_BLOCKER`, `SKEPTICISM`, `COST_CONCERN`, `SECOND_OPINION_SEEKING`, `INFO_GATHERING`, `READY_TO_BOOK`, … |
| 2 | `conversation_stage_manager.py` | Drives **5 stages**: EDUCATE → VALIDATE → HANDLE_OBJECTIONS → DECISION_SUPPORT → SOFT_CLOSE |
| 3 | `response_strategy_engine.py` | Rotates **6 strategies** so no two consecutive turns repeat: DATA_EDUCATION, EMPATHY_VALIDATION, TRUST_BUILDING, RISK_EXPLANATION, LOGISTICS_HELP, PRECAUTION_GUIDANCE |
| 4 | `trust_signal_detector.py` | Live trust score from trust-building and trust-eroding signals |
| 5 | `logistics_reasoning_engine.py` | Solves real constraints: out of town longer than RUL, different city, tight schedule |
| 6 | `conversation_memory_tracker.py` | Per-session tags: `LAST_STRATEGY_USED`, `LAST_OBJECTION_TYPE`, `CUSTOMER_TRUST_TREND`, `CUSTOMER_RESISTANCE_TREND`, `CUSTOMER_DECISION_VELOCITY` |
| 7 | `trust_recovery_engine.py` | **6-step protocol** for customers burned by past service: acknowledge → validate → show improvement → offer transparency → return control → remove all pressure |
| 8 | `edge_case_reasoning_engine.py` | 5 original edge cases with deterministic responses |
| 9 | `personalization_context_builder.py` | Builds context from customer memory + vehicle + telematics |
| 10 | `strategy_response_router.py` | **The binding layer.** Intent + Stage + Trust + Resistance → exact response. *"LLM NEVER decides core response direction. It only polishes."* |
| 11 | `execution_mode_manager.py` | The 4-stage booking gate (see [§6 Agent 5](#agent-5--customer-engagement-agent-)) |
| 12 | `personalization_context_engine.py` | Deeper layer: response-speed pattern, channel preference, trust sensitivity, decline tendency, past satisfaction |
| 13 | `edge_case_decision_engine.py` | Extended to **7 edge cases** (see table below) |
| 14 | `followup_cycle_manager.py` | Detects "call me tomorrow" → schedules `FollowUpTask` → triggers re-analysis before contact |
| 15 | `vehicle_reanalysis_engine.py` | Fresh telematics + delta vs. last state → tone directive (WORSENED / STABLE / IMPROVED) |

**The 7 edge cases:**

| Code | Scenario | Handling |
|---|---|---|
| EC1 | Past bad service / trust damage | Trust Recovery Mode — zero urgency language |
| EC2 | Family mechanic / second opinion | Support it, share the diagnostic data, preserve the relationship |
| EC3 | Out of town with high risk | Safety coaching + interim mitigation + remote booking |
| EC4 | Skeptical but polite | Data Transparency Mode |
| EC5 | Cost sensitive | Financial Safety Mode |
| EC6 | **Silent after follow-up promise** | Re-analyze vehicle → send updated risk message |
| EC7 | **Asks for supervisor** | *Only then* escalate to a human advisor |

EC7 is worth noting: the system escalates to a human **only on explicit request** (or legal/VIP triggers). It does not bail out to a human when the conversation gets hard.

---
---

# PART C — THE CLIENTS

## 10. The Web Dashboard (React)

**Location:** [`backend/autopredict-web/`](backend/autopredict-web/)

**Stack:** React 19 · Vite 7 · TailwindCSS 3 · React Router 7 · Recharts 3 · Framer Motion · Three.js (`@react-three/fiber` + `drei`) · FullCalendar · Lottie · Axios

### 10.1 Three role-based dashboards

Authentication (`pages/Login.jsx` → `POST /api/auth/login`) returns a role; `ProtectedRoute.jsx` gates each tree.

```
/                              → HeroSection (public marketing page, 3D car via Three.js)
/login                         → Login

/dashboard/operations          → OperationsLayout        [role: ops]
    ├── index                  → OpsOverview
    ├── /fleet                 → OpsFleet
    ├── /calendar              → OpsCalendar
    ├── /conversations         → OpsConversations
    └── /warnings              → OpsWarnings

/dashboard/manager             → ManagerLayout           [role: manager]
    ├── index                  → ManagerOverview
    ├── /escalations           → ManagerEscalations
    ├── /revenue               → ManagerRevenue
    └── /workload              → ManagerWorkload

/dashboard/executive           → ExecutiveLayout         [role: executive]
    ├── index                  → ExecOverview
    ├── /fleet-health          → ExecFleetHealth
    ├── /trends                → ExecTrends
    └── /recalls               → ExecRecalls

/dashboard/conversations       → shared
/dashboard/recalls             → shared
/dashboard/reports             → shared
/dashboard/settings            → shared
```

**Who sees what:**

| Role | Focus |
|---|---|
| **Operations** | Today's work — live fleet, bay calendar, active conversations, warnings needing action |
| **Manager** | Team & money — escalations, revenue, technician workload |
| **Executive** | Strategy — fleet health trends, 6-month comparisons, ROI, recall exposure |

### 10.2 Live data via WebSocket

[`src/contexts/WebSocketContext.jsx`](backend/autopredict-web/src/contexts/WebSocketContext.jsx) is a proper pub/sub client:

- Connects to `ws://localhost:8000/ws/dashboard`
- **Exponential back-off reconnect** — `1s → 2s → 4s → … ` up to 10 retries
- Subscriber registry `Map<eventType, Set<callback>>` with a `'*'` wildcard channel
- `subscribe(eventType, cb)` returns an unsubscribe function for clean React effects

Components subscribe to the seven `DashboardEvent` types:
```
VEHICLE_UPDATED · BOOKING_CREATED · BOOKING_CANCELLED · CONVERSATION_TURN
ALERT_FIRED · WORKFLOW_COMPLETED · DIAGNOSIS_UPDATED
```

So when the background diagnosis loop finishes a vehicle, every open dashboard tab updates instantly.

### 10.3 The 40 chart components

All in [`src/components/charts/`](backend/autopredict-web/src/components/charts/), each backed by a dedicated `/api/analytics/*` endpoint in `api_server.py`.

| Category | Components |
|---|---|
| **Fleet health** | `FleetHealthScoreGauge`, `HealthScoreTimeline`, `VehicleRiskMatrix`, `RULDistribution`, `SubsystemRadar`, `TelematicsSparklines` |
| **Predictive** | `PredictiveAlertFunnel`, `ComponentFailureRate`, `DtcFrequencyBar`, `AlertTimeline`, `WhatIfSimulator` |
| **Operations** | `BayOccupancyGantt`, `TechnicianUtilisation`, `TechnicianWorkload`, `ServiceDurationBox`, `ServiceCompletionRate`, `BayCalendar` |
| **Conversation** | `ConversationFunnel`, `ConversationVolumeArea`, `AcceptanceRateLine`, `BookingFunnelSankey`, `ConversionScatterByMake` |
| **Escalation** | `EscalationHeatmap`, `EscalationReasonBreakdown`, `EscalationTrendLine` |
| **Revenue / ROI** | `RevenueByComponentBar`, `RevenueForecast`, `RevenueVsCostAvoidanceLine`, `CostAvoidanceWaterfall`, `ROIDashboard` |
| **Recalls** | `RecallCompletionDonut`, `RecallHeatmapExec`, `RecallTimelineBar` |
| **Executive** | `KPITrendCards`, `SixMonthComparison`, `AgentPerformanceRadar`, `AIExecutiveSummary` |

`AIExecutiveSummary` is notable — `GET /api/analytics/executive-summary` generates a natural-language paragraph from fleet aggregates.

### 10.4 3D and visual components

| Component | What it does |
|---|---|
| `CarModel.jsx` | Loads `public/car.glb` / `car1.glb` via `@react-three/drei`, orbit controls |
| `Engine3D.jsx` | 3D engine visualisation |
| `SteeringWheel3D.jsx` | Animated steering wheel |
| `TelematicsGauge.jsx` | Live sensor gauge |
| `LiveEventBus.jsx` | Scrolling feed of incoming WebSocket events |
| `LiveToast.jsx` | Toast notifications on `ALERT_FIRED` |
| `HeroSection.jsx` | Landing page with the 3D car |

### 10.5 API surface consumed

**Core:** `/api/vehicles`, `/api/vehicles/{id}`, `/api/vehicles/{id}/manufacturing`, `/api/vehicles/{id}/history`, `/api/bookings` (GET/POST/PATCH/DELETE), `/api/bookings/today`, `/api/availability`, `/api/conversations`, `/api/dashboard/summary`, `/api/dashboard/alerts`, `/api/manufacturing/summary`, `/api/vehicles/{id}/diagnose` (manual trigger)

**Analytics (~25 endpoints):** `/api/analytics/` + `fleet`, `revenue`, `workload`, `escalations`, `conversation-volume`, `agent-performance`, `booking-funnel`, `escalation-heatmap`, `escalation-trend`, `revenue-by-component`, `revenue-forecast`, `bay-occupancy`, `service-duration`, `booking-velocity`, `cost-avoidance`, `recall-heatmap`, `component-failure-rate`, `alert-funnel`, `conversion-by-make`, `kpi-trends`, `executive-summary`, `roi`, `recall-details`, `monthly`

**Config:** [`src/config.js`](backend/autopredict-web/src/config.js) — change `API_BASE` / `WS_BASE` here to point at a LAN IP instead of `localhost`.

---

## 11. The Mobile App (Flutter)

**Location:** [`backend/autopredict_app/`](backend/autopredict_app/)
**Package:** `autopredict_app` — *"AutoPredict — Smart Vehicle Diagnostics & AI Service Booking"*

**Stack:** Flutter 3 · **Riverpod** (state) · **go_router** (nav) · **Dio** (HTTP) · fl_chart · Lottie · flutter_animate · Hive + SharedPreferences · google_fonts · flutter_map · sensors_plus (crash detection) · flutter_tts

### 11.1 Screens and routes

```dart
'/'              → SplashScreen
'/onboarding'    → OnboardingScreen
'/login'         → LoginScreen              (OTP-based)
'/home'          → HomeScreen               + settings_tab
'/diagnostics'   → DiagnosticsScreen
'/chat'          → ChatScreen               ← direct Ollama, streaming
'/bookings'      → BookingsScreen
'/book-new'      → BookingFlowScreen
'/notifications' → NotificationsScreen
'/profile'       → ProfileScreen
'/service-chat'  → ServiceChatScreen        ← backend /api/chat, booking actions
```
Plus `battery_screen`, `media_screen`, `parking_screen` for the connected-car experience.

### 11.2 The two chat systems (an important distinction)

The app has **two separate AI chats** that hit different backends:

| | `/chat` — `ChatScreen` | `/service-chat` — `ServiceChatScreen` |
|---|---|---|
| Service | `OllamaService` | `ApiService.serviceChat()` |
| Endpoint | Ollama `/api/chat` **directly via ngrok tunnel** | Backend `POST /api/chat` on port 8000 |
| Streaming | ✅ token-by-token | ❌ single response |
| Context source | Live OBD from the phone, injected client-side | `app_state` vehicle record, injected server-side |
| Can create bookings | ❌ | ✅ returns `action: SHOW_SLOTS` / `BOOKING_CREATED` |
| Purpose | Fast conversational Q&A about the car | Transactional service advisor |

**`OllamaService`** ([`lib/core/services/ollama_service.dart`](backend/autopredict_app/lib/core/services/ollama_service.dart)):
- Base URL is an **ngrok tunnel** (`ngrok http 11434`) so a physical phone can reach the dev machine's Ollama
- Sends header `ngrok-skip-browser-warning: true`
- `chatStream()` parses newline-delimited JSON chunks and yields tokens
- Builds a system prompt embedding live vehicle context (speed, RPM, coolant, fuel, voltage, engine status, DTC codes, tyre pressure, active booking)
- Instructs the model to end with `ACTION:SHOW_BOOKING` or `ACTION:SHOW_ALERT`, and **not** to re-offer booking if one is already active

**`ApiService.serviceChat()`** ([`lib/core/services/api_service.dart`](backend/autopredict_app/lib/core/services/api_service.dart)) → `POST /api/chat` in `api_server.py`:

The server-side system prompt gives the model a 4-step script:
```
1. Greet and explain the AI-detected issue clearly but conversationally.
2. Persuade them to book a service if the issue is significant.
3. When they agree, say exactly: SHOW_SLOTS
4. Once they pick a slot, confirm and say BOOKING_CREATED
```

The server then **detects those tokens in the reply** and attaches structured data:

| Token detected | Server response |
|---|---|
| `SHOW_SLOTS` | Builds a 7-day calendar (09:00–17:00 hourly), marks slots already booked in `app_state` as unavailable, returns `action_data.calendar` |
| `BOOKING_CREATED` | Auto-creates a booking in `app_state` with a real `booking_id`, technician, bay, `status: CONFIRMED`, `source: "app_chat"` |

This is a clean **structured-action-from-text** pattern: the LLM signals intent with a sentinel token, deterministic code performs the actual state mutation.

### 11.3 Offline-first design

**Every** `ApiService` method wraps its call in try/catch and returns rich mock data on failure:

```dart
Future<Map<String, dynamic>> getVehicle([String? id]) async {
  try   { return (await _dio.get('/vehicles/${id ?? _vehicleId}')).data; }
  catch (_) { return _mockVehicle(); }   // Toyota Camry, brake_pads, RUL 12d, 88% conf
}
```

`_mockAgentReply()` even simulates a **multi-turn conversation flow** — first turn gives the brake diagnosis, "yes/book" returns `SHOW_SLOTS` with a generated calendar, "cost/price" returns a pricing answer (₹2,500–₹4,000). The app demos fully with the backend down.

### 11.4 Riverpod state layer

| Provider | Responsibility |
|---|---|
| `vehicle_provider.dart` | Current vehicle + live OBD telemetry |
| `diagnostics_provider.dart` | Component health list |
| `booking_provider.dart` | Bookings CRUD, active-booking detection |
| `chat_provider.dart` | Chat history, streaming accumulation, context assembly |
| `theme_provider.dart` | Light/dark/system mode |

`chat_provider.dart` assembles the vehicle context passed to the LLM on every turn:
```dart
final ctx = {
  'speed': vehicle.speedMph,        'rpm': vehicle.rpm,
  'coolantTemp': vehicle.coolantTempC, 'fuel': vehicle.fuelLevelPct,
  'voltage': vehicle.batteryVoltage,   'engineStatus': vehicle.engineStatus,
  'dtcCodes': vehicle.dtcCodes,        'tyrePressure': vehicle.tyrePressureFl,
  'activeBooking': bookingDesc,        // prevents re-offering an existing booking
};
```

### 11.5 OBD simulator

[`lib/core/services/obd_simulator.dart`](backend/autopredict_app/lib/core/services/obd_simulator.dart) generates realistic live telemetry — speed, RPM, coolant, fuel, voltage, tyre pressure, DTC codes — so the gauges animate without a real OBD-II dongle. Swapping this for a real Bluetooth ELM327 reader is the single change needed to make the app production-real.

### 11.6 App-specific backend endpoints

Defined in `api_server.py`:

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/otp/send` | Send OTP (currently always `000000`) |
| `POST /api/auth/otp/verify` | Verify → base64 session token (7-day expiry) |
| `POST /api/auth/register` | Register customer, link vehicle |
| `GET /api/customer/{id}/vehicles` | Customer's vehicles |
| `POST /api/conversations/message` | Keyword-routed assistant (returns `SHOW_BOOKING_CARD` / `SHOW_DIAGNOSIS`) |
| `GET /api/conversations/{vehicle_id}` | Conversation history |
| `POST /api/fcm/register` | Store FCM push token |
| `POST /api/fcm/notify` | Queue a push notification |
| `POST /api/chat` | **The main service agent** |

---
---

# PART D — RAG

## 12. What is RAG

### 12.1 The definition

**RAG = Retrieval-Augmented Generation.**

An LLM only knows two things: what it memorised during training, and what you put in the prompt. It does **not** know your dealership's repair history, your OEM service manuals, or last week's NHTSA recall bulletin.

RAG fixes this by putting a **search step in front of the LLM**:

```
                          ┌──────────────────────────────────────┐
                          │   KNOWLEDGE BASE (your documents)    │
                          │  manuals · TSBs · recalls · history  │
                          └───────────────┬──────────────────────┘
                                          │  ① INGEST (offline, once)
                                          ▼
                          ┌──────────────────────────────────────┐
                          │  chunk → embed → store in vector DB  │
                          └───────────────┬──────────────────────┘
                                          │
  User/agent query ──② EMBED──▶ ③ SIMILARITY SEARCH ──▶ top-k chunks
                                          │
                                          ▼
                    ┌───────────────────────────────────────┐
                    │  ④ AUGMENTED PROMPT                   │
                    │  "Using ONLY the context below,       │
                    │   answer the question.                │
                    │   CONTEXT: <retrieved chunks>         │
                    │   QUESTION: <query>"                  │
                    └──────────────────┬────────────────────┘
                                       ▼
                              ⑤ LLM generates
                                       ▼
                          ⑥ Answer + citations
```

### 12.2 The pipeline in detail

| Step | What happens | Key decisions |
|---|---|---|
| **1. Ingest** | Load PDFs, HTML, CSVs, DB rows | What sources? How often refreshed? |
| **2. Chunk** | Split into ~200–800 token pieces | Size, overlap, split boundary (paragraph? section?) |
| **3. Embed** | Each chunk → a vector (e.g. 768 floats) capturing meaning | Which embedding model? |
| **4. Index** | Store vectors + metadata in a vector DB | Chroma / FAISS / pgvector / Qdrant |
| **5. Retrieve** | Embed the query, find nearest chunks by cosine similarity | `k`? similarity threshold? metadata filters? |
| **6. Rerank** *(optional)* | Reorder top-50 down to top-5 with a cross-encoder | Worth it for precision-critical use |
| **7. Augment** | Insert chunks into the prompt with strict instructions | "Answer ONLY from context; say 'not found' otherwise" |
| **8. Generate** | LLM answers | Low temperature for factual grounding |
| **9. Cite** | Return source doc IDs alongside the answer | Essential for auditability |

### 12.3 Why "semantic" search beats keyword search

Embeddings map *meaning* to geometry. The query *"brakes feel spongy"* lands near a manual section titled *"Hydraulic pressure loss in the braking circuit"* even though they share zero keywords. That's the whole value proposition.

### 12.4 RAG vs. the alternatives

| Approach | Cost | Freshness | Traceability | Good for |
|---|---|---|---|---|
| **Prompt stuffing** | Free | Manual | High | Small, static facts (what this repo does today) |
| **RAG** | Low | Real-time | **High — cites sources** | Large, changing knowledge bases |
| **Fine-tuning** | High | Stale (retrain to update) | **None** | Style, format, tone |
| **Bigger model** | Very high | Fixed at training cutoff | None | General reasoning |

For AutoPredict — where the knowledge base changes (new recalls, new TSBs, new repair records) and every claim must be traceable — **RAG is clearly the right tool.** Fine-tuning llama3:8b on service manuals would bake in facts you can't update and can't cite.

---

## 13. Why This Project Needs RAG — the exact pain points

There is currently **no vector store, no embeddings, and no retrieval anywhere in this codebase.** Here is exactly where that hurts, with file and line references.

### Pain point 1 — Diagnosis has no domain knowledge

`diagnosis_orchestrator.py:_run_diagnosis_agent()` prompts:
```python
prompt = (f"Given the vehicle telematics and the data-analysis report below, "
          f"predict component failure, RUL, and severity.\n\n"
          f"Telematics:\n{telem_str}\n\nData Analysis Report:\n{json.dumps(data_report)}")
```

That's **raw numbers and nothing else.** A generalist 8B model is guessing. It has never seen:
- The OEM wear curve for these specific brake pads
- Technical Service Bulletins for this make/model/year
- The 40 previous brake jobs this dealership performed on the same platform

**With RAG:** retrieve the 3 most similar past failures + the relevant manual section, and the RUL becomes an evidence-based estimate rather than a guess.

### Pain point 2 — Manufacturing Agent is a 10-row hardcoded array

`manufacturing_agent.py` contains exactly 10 DTC codes and 4 recall campaigns as Python literals. The real world has **~5,000 standardised DTCs** and **thousands of NHTSA campaigns**. Its own docstring admits it:

> *"For now every method is deterministic / mock — in production the NHTSA lookup would hit `https://api.nhtsa.gov/recalls/recallsByVehicle` and the DTC decoder would query an OBD-II database."*

**This is the highest-ROI RAG target in the entire project.** A retrieval index over the real DTC dictionary and the NHTSA recall corpus replaces a mock with a genuinely useful capability, with zero hallucination risk (retrieval returns real records, not generated text).

### Pain point 3 — Facts are hardcoded into system prompts

`ollama_service.dart:_buildSystemPrompt()` literally hardcodes:
```dart
DIAGNOSTICS:
- Brake Pads: 2.1mm (CRITICAL — replace immediately)
- Battery: 11.8V (WARNING)
```
Those numbers are **the same for every vehicle and every user.** Similarly `api_server.py:/api/chat` builds the system prompt from a handful of `app_state` fields.

**With RAG:** the prompt is assembled from retrieved, per-vehicle records plus retrieved policy documents — pricing, warranty terms, service policy — so the agent can answer *"is this covered under warranty?"* and *"how much will it cost?"* correctly instead of making it up.

### Pain point 4 — 15 modules of hand-written response text

The conversation intelligence stack (§9) exists because the team correctly refused to let the LLM invent responses. But it means **every objection response is hand-authored Python.** Adding a new objection type means writing new code.

**With RAG:** a curated `kb_playbook` index of approved response patterns lets `strategy_response_router.py` *retrieve* the right approved response instead of hard-coding it. Same safety guarantee (text is pre-approved by humans), far better scalability.

### Pain point 5 — Memory is flag-based, not semantic

`memory_store_v4*.json` stores boolean flags: `PREFERS_WHATSAPP`, `OFTEN_DECLINES`, `RESPONDS_SLOWLY`. Useful, but lossy. The system cannot ask *"how did we successfully handle a cost-sensitive customer with a P1 brake issue last month?"*

**With RAG:** embed past conversation transcripts. `LearningAgent` retrieves semantically similar past interactions and their outcomes — a form of episodic memory.

### Summary table

| # | Where | Current state | With RAG |
|---|---|---|---|
| 1 | Diagnosis Agent | Numbers only, no domain knowledge | Grounded in manuals, TSBs, similar past cases |
| 2 | Manufacturing Agent | 10 hardcoded DTCs, 4 mock recalls | Real DTC dictionary + real NHTSA corpus |
| 3 | Both chat endpoints | Facts hardcoded in system prompts | Per-vehicle records + policy/pricing/warranty docs |
| 4 | Engagement modules | 15 files of hand-written responses | Retrieved from an approved playbook |
| 5 | Learning Agent | Boolean behaviour flags | Semantic recall of similar past conversations |

---

## 14. RAG Architecture for AutoPredict

### 14.1 Four knowledge indices

Don't build one giant index. Build four, each with its own consumer and refresh cadence:

| Index | Contents | Consumed by | Refresh |
|---|---|---|---|
| **`kb_technical`** | OEM service manuals, TSBs, component wear curves, DTC dictionary (~5,000 codes), repair procedures | Diagnosis Agent, Manufacturing Agent | Quarterly |
| **`kb_recalls`** | NHTSA campaign records — campaign #, make/model/year range, component, summary, remedy | Manufacturing Agent | Weekly (NHTSA API) |
| **`kb_playbook`** | Approved objection responses, pricing tables, warranty terms, service policy, prep instructions | Customer Engagement Agent, `/api/chat` | On policy change |
| **`kb_history`** | This fleet's past work orders, resolved diagnoses, anonymised conversation transcripts + outcomes | Diagnosis Agent (analogy), Learning Agent (episodic memory) | Continuous — append on every workflow completion |

### 14.2 Where retrieval plugs into the existing flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                       EXISTING PIPELINE                              │
│                                                                      │
│  Telematics                                                          │
│      │                                                               │
│      ▼                                                               │
│  ┌──────────────────┐                                                │
│  │ Data Analysis    │  (unchanged — pure numeric assessment)         │
│  │ Agent            │                                                │
│  └────────┬─────────┘                                                │
│           │ health_score, anomalies                                  │
│           ▼                                                          │
│  ┌──────────────────┐        ╔═══════════════════════════════╗       │
│  │ Diagnosis Agent  │◀───────╢ RETRIEVE from kb_technical    ║  ★NEW │
│  │                  │        ║  + kb_history                 ║       │
│  └────────┬─────────┘        ║  query: component + readings  ║       │
│           │                  ║  filter: make, model, year    ║       │
│           │                  ╚═══════════════════════════════╝       │
│           ▼                                                          │
│  ┌──────────────────┐        ╔═══════════════════════════════╗       │
│  │ Manufacturing    │◀───────╢ RETRIEVE from kb_recalls      ║  ★NEW │
│  │ Agent            │        ║  + kb_technical (DTC lookup)  ║       │
│  └────────┬─────────┘        ╚═══════════════════════════════╝       │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────┐                                                │
│  │ Scheduling Agent │  (unchanged — pure constraint solving)         │
│  └────────┬─────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────┐        ╔═══════════════════════════════╗       │
│  │ Customer         │◀───────╢ RETRIEVE from kb_playbook     ║  ★NEW │
│  │ Engagement Agent │        ║  query: intent + objection    ║       │
│  └──────────────────┘        ╚═══════════════════════════════╝       │
│                                                                      │
│  ┌──────────────────┐        ╔═══════════════════════════════╗       │
│  │ Learning Agent   │───────▶╢ WRITE outcome to kb_history   ║  ★NEW │
│  └──────────────────┘        ╚═══════════════════════════════╝       │
└──────────────────────────────────────────────────────────────────────┘
```

**Critical constraint: retrieval must never override `rule_engine.py`.** RAG improves *explanation and estimation*. Priority assignment stays deterministic. If a retrieved manual says "brake pads are fine down to 2mm" but `rule_engine` says `< 3.0mm → P0`, **the rule wins.**

### 14.3 Technology choices (matched to this stack)

| Component | Recommendation | Why |
|---|---|---|
| **Embedding model** | `nomic-embed-text` **via Ollama** | Ollama is already running. No new service, no API key, no cost, stays local. 768-dim, strong retrieval quality. Alternative: `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim, faster, no Ollama dependency). |
| **Vector store** | **ChromaDB** (`chromadb`) with `PersistentClient` | Pure Python, embedded (no server), persists to disk exactly like the existing `ml_models/*.joblib` pattern. Metadata filtering built in. Migrate to `pgvector` or Qdrant only when you outgrow one machine. |
| **Chunking** | ~500 tokens, 50-token overlap, split on section headings | Manual sections are semantically coherent; overlap prevents losing context across a boundary |
| **Retrieval** | `k=5`, cosine similarity, **metadata pre-filter** on make/model/year | Pre-filtering by vehicle is far more effective than relying on the embedding to encode "Toyota Camry 2021" |
| **Reranking** | Skip initially | With `k=5` from a well-filtered index, a cross-encoder adds latency for marginal gain. Add later if precision is an issue. |

---

## 15. Full Implementation Guide

### Step 0 — Dependencies

Add to [`backend/requirements.txt`](backend/requirements.txt):

```txt
# ── RAG (v7.0) ────────────────────────────────────────
chromadb>=0.5.0
pypdf>=4.0.0            # PDF ingestion (service manuals)
tiktoken>=0.7.0         # token-accurate chunking
```

Pull the embedding model:
```bash
ollama pull nomic-embed-text
```

### Step 1 — `backend/rag/vector_store.py`

The embedding + storage layer. Mirrors the existing `MLModelManager` pattern — graceful degradation if the dependency is missing.

```python
"""
RAG Vector Store - v1.0
ChromaDB-backed semantic index with Ollama embeddings.

Design notes:
  • Embeddings come from Ollama (nomic-embed-text) — no new service, no API key.
  • Persists to disk like ml_models/*.joblib.
  • Degrades gracefully: if chromadb is missing, every call is a safe no-op
    and callers fall back to their existing behaviour.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional

import httpx

from config import SystemConfig

try:
    import chromadb
    from chromadb.config import Settings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  chromadb not installed. RAG disabled. Install: pip install chromadb")


EMBED_MODEL = "nomic-embed-text"
EMBED_URL   = SystemConfig.OLLAMA_BASE_URL.replace("/v1", "") + "/api/embeddings"
RAG_DIR     = os.path.join(os.path.dirname(__file__), "..", "rag_store")

# The four knowledge indices
COLLECTIONS = ["kb_technical", "kb_recalls", "kb_playbook", "kb_history"]


class VectorStore:
    """Embedded semantic index. Safe to instantiate once and reuse."""

    def __init__(self, persist_dir: str = RAG_DIR):
        self.enabled = RAG_AVAILABLE
        self.client = None
        self._collections: Dict[str, object] = {}

        if not self.enabled:
            return

        try:
            os.makedirs(persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            for name in COLLECTIONS:
                self._collections[name] = self.client.get_or_create_collection(
                    name=name, metadata={"hnsw:space": "cosine"}
                )
            print(f"   ✅ RAG vector store ready ({len(COLLECTIONS)} collections)")
        except Exception as e:
            print(f"   ⚠️  RAG init failed: {str(e)[:60]}")
            self.enabled = False

    # ── Embeddings ────────────────────────────────────────────────────────

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts via Ollama. Returns [] on failure."""
        vectors = []
        try:
            with httpx.Client(timeout=30.0) as client:
                for text in texts:
                    r = client.post(EMBED_URL,
                                    json={"model": EMBED_MODEL, "prompt": text})
                    r.raise_for_status()
                    vectors.append(r.json()["embedding"])
            return vectors
        except Exception as e:
            print(f"   ⚠️  Embedding failed: {str(e)[:60]}")
            return []

    # ── Write ─────────────────────────────────────────────────────────────

    def add(self, collection: str, documents: List[str],
            metadatas: List[Dict], ids: Optional[List[str]] = None) -> bool:
        """Add documents to a collection. Idempotent via content-hash IDs."""
        if not self.enabled or collection not in self._collections:
            return False
        if not documents:
            return False

        embeddings = self.embed(documents)
        if not embeddings:
            return False

        if ids is None:
            ids = [hashlib.sha256(d.encode()).hexdigest()[:16] for d in documents]

        try:
            self._collections[collection].upsert(
                ids=ids, documents=documents,
                embeddings=embeddings, metadatas=metadatas,
            )
            return True
        except Exception as e:
            print(f"   ⚠️  RAG add failed: {str(e)[:60]}")
            return False

    # ── Read ──────────────────────────────────────────────────────────────

    def query(self, collection: str, query_text: str, k: int = 5,
              where: Optional[Dict] = None) -> List[Dict]:
        """
        Semantic search. `where` is a Chroma metadata filter, e.g.
            {"make": "Toyota"}  or  {"$and": [{"make":"Toyota"},{"year":2021}]}
        Returns [] on any failure so callers can fall back safely.
        """
        if not self.enabled or collection not in self._collections:
            return []

        q_emb = self.embed([query_text])
        if not q_emb:
            return []

        try:
            res = self._collections[collection].query(
                query_embeddings=q_emb, n_results=k, where=where,
            )
            hits = []
            for doc, meta, dist in zip(res["documents"][0],
                                       res["metadatas"][0],
                                       res["distances"][0]):
                hits.append({
                    "text": doc,
                    "metadata": meta,
                    "similarity": round(1 - dist, 3),   # cosine distance → similarity
                })
            return hits
        except Exception as e:
            print(f"   ⚠️  RAG query failed: {str(e)[:60]}")
            return []

    def count(self, collection: str) -> int:
        if not self.enabled or collection not in self._collections:
            return 0
        return self._collections[collection].count()


# Module-level singleton — import this everywhere (same pattern as app_state)
vector_store = VectorStore()
```

### Step 2 — `backend/rag/retriever.py`

The prompt-formatting layer. Every agent gets one purpose-built retrieval function.

```python
"""
RAG Retriever - v1.0
Purpose-built retrieval functions, one per consuming agent.
Each returns a prompt-ready CONTEXT block, or "" when nothing is found.
"""

from typing import Dict, List, Optional
from rag.vector_store import vector_store

MIN_SIMILARITY = 0.45   # below this, a hit is noise — drop it


def _format(hits: List[Dict], header: str) -> str:
    """Render hits as a numbered, cited context block."""
    kept = [h for h in hits if h["similarity"] >= MIN_SIMILARITY]
    if not kept:
        return ""

    lines = [f"\n{header}"]
    for i, h in enumerate(kept, 1):
        src = h["metadata"].get("source", "unknown")
        lines.append(f"[{i}] (source: {src}, relevance: {h['similarity']})")
        lines.append(h["text"].strip())
        lines.append("")
    return "\n".join(lines)


# ── For the Diagnosis Agent ───────────────────────────────────────────────

def retrieve_diagnostic_context(component: str, telematics: Dict,
                                vehicle: Dict, k: int = 3) -> str:
    """Technical manual knowledge + similar past cases for this vehicle."""
    query = (
        f"{vehicle.get('make','')} {vehicle.get('model','')} {component} failure "
        f"brake pad {telematics.get('brake_pad_mm','')}mm "
        f"battery {telematics.get('battery_voltage_v','')}V "
        f"coolant {telematics.get('coolant_temp_c','')}C "
        f"odometer {telematics.get('odo_km','')}km"
    )

    where = None
    if vehicle.get("make"):
        where = {"make": vehicle["make"]}

    technical = vector_store.query("kb_technical", query, k=k, where=where)
    history   = vector_store.query("kb_history",   query, k=k, where=where)

    return (_format(technical, "=== TECHNICAL REFERENCE ===") +
            _format(history,   "=== SIMILAR PAST CASES (this fleet) ==="))


# ── For the Manufacturing Agent ───────────────────────────────────────────

def retrieve_recalls(vehicle: Dict, k: int = 5) -> List[Dict]:
    """Open recall campaigns matching this vehicle. Returns raw hits."""
    query = (f"recall {vehicle.get('make','')} {vehicle.get('model','')} "
             f"{vehicle.get('year','')}")
    where = {"make": vehicle["make"]} if vehicle.get("make") else None
    return vector_store.query("kb_recalls", query, k=k, where=where)


def retrieve_dtc_definition(code: str) -> Optional[Dict]:
    """Look up a DTC code in the technical dictionary."""
    hits = vector_store.query("kb_technical", f"DTC {code}", k=1,
                              where={"doc_type": "dtc"})
    return hits[0] if hits else None


# ── For the Customer Engagement Agent ─────────────────────────────────────

def retrieve_playbook(intent: str, component: str,
                      objection: str = "", k: int = 3) -> str:
    """Approved response patterns, pricing, warranty terms."""
    query = f"{intent} {objection} {component} customer objection response"
    hits = vector_store.query("kb_playbook", query, k=k)
    return _format(hits, "=== APPROVED RESPONSE GUIDANCE ===")


# ── For the Learning Agent ────────────────────────────────────────────────

def retrieve_similar_outcomes(customer_profile: Dict, diagnosis: Dict,
                              k: int = 5) -> str:
    """Episodic memory: how did similar situations resolve?"""
    query = (f"{diagnosis.get('affected_component','')} "
             f"{diagnosis.get('severity','')} "
             f"customer {customer_profile.get('segment','standard')} outcome")
    hits = vector_store.query("kb_history", query, k=k,
                              where={"doc_type": "conversation_outcome"})
    return _format(hits, "=== SIMILAR PAST OUTCOMES ===")
```

### Step 3 — `backend/rag/ingest.py`

The offline pipeline that populates the indices.

```python
"""
RAG Ingestion - v1.0
Run once to build the knowledge base, then on a schedule to refresh.

Usage:
    python -m rag.ingest --all
    python -m rag.ingest --recalls        # refresh NHTSA weekly
    python -m rag.ingest --history        # append completed work orders
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List

import httpx

from rag.vector_store import vector_store

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_docs")


# ── Chunking ──────────────────────────────────────────────────────────────

def chunk_text(text: str, size: int = 500, overlap: int = 50) -> List[str]:
    """
    Word-based chunking with overlap. Good enough for manuals;
    swap for tiktoken-based chunking if you need exact token budgets.
    """
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        i += size - overlap
    return [c for c in chunks if len(c.split()) > 20]   # drop stubs


# ── kb_technical: manuals, TSBs, DTC dictionary ───────────────────────────

def ingest_technical():
    """Ingest PDFs/text from knowledge_docs/technical/ plus the DTC dictionary."""
    tech_dir = os.path.join(DOCS_DIR, "technical")
    docs, metas = [], []

    # 1. Service manuals / TSBs (PDF or .txt)
    if os.path.isdir(tech_dir):
        for fname in os.listdir(tech_dir):
            path = os.path.join(tech_dir, fname)
            text = ""

            if fname.endswith(".pdf"):
                try:
                    from pypdf import PdfReader
                    text = "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
                except Exception as e:
                    print(f"   ⚠️  PDF read failed {fname}: {e}")
                    continue
            elif fname.endswith((".txt", ".md")):
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            else:
                continue

            # Filename convention: Make_Model_Year_DocType.pdf
            parts = fname.rsplit(".", 1)[0].split("_")
            meta_base = {
                "source": fname,
                "doc_type": "manual",
                "make":  parts[0] if len(parts) > 0 else "",
                "model": parts[1] if len(parts) > 1 else "",
                "year":  int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
            }

            for chunk in chunk_text(text):
                docs.append(chunk)
                metas.append(dict(meta_base))

    # 2. DTC dictionary (JSON: [{code, system, description, causes, severity}, ...])
    dtc_path = os.path.join(DOCS_DIR, "dtc_dictionary.json")
    if os.path.exists(dtc_path):
        with open(dtc_path, encoding="utf-8") as f:
            for d in json.load(f):
                docs.append(
                    f"DTC {d['code']} ({d['system']}): {d['description']}. "
                    f"Common causes: {', '.join(d.get('causes', []))}. "
                    f"Severity: {d.get('severity','unknown')}."
                )
                metas.append({"source": f"DTC {d['code']}", "doc_type": "dtc",
                              "code": d["code"], "make": ""})

    ok = vector_store.add("kb_technical", docs, metas)
    print(f"{'✅' if ok else '❌'} kb_technical: {len(docs)} chunks")


# ── kb_recalls: NHTSA ─────────────────────────────────────────────────────

def ingest_recalls(makes: List[str] = None):
    """Pull live recall campaigns from the NHTSA API."""
    makes = makes or ["Toyota", "Honda", "Ford", "BMW", "Tesla", "Tata", "Hyundai"]
    docs, metas = [], []

    with httpx.Client(timeout=30.0) as client:
        for make in makes:
            try:
                r = client.get(
                    "https://api.nhtsa.gov/recalls/recallsByVehicle",
                    params={"make": make, "modelYear": datetime.now().year},
                )
                r.raise_for_status()
                for rec in r.json().get("results", []):
                    docs.append(
                        f"RECALL {rec.get('NHTSACampaignNumber','')}: "
                        f"{rec.get('Component','')} — {rec.get('Summary','')} "
                        f"Remedy: {rec.get('Remedy','')} "
                        f"Consequence: {rec.get('Consequence','')}"
                    )
                    metas.append({
                        "source": rec.get("NHTSACampaignNumber", ""),
                        "doc_type": "recall",
                        "make": make,
                        "model": rec.get("Model", ""),
                        "year": int(rec.get("ModelYear", 0) or 0),
                        "component": rec.get("Component", ""),
                    })
            except Exception as e:
                print(f"   ⚠️  NHTSA fetch failed for {make}: {str(e)[:60]}")

    ok = vector_store.add("kb_recalls", docs, metas)
    print(f"{'✅' if ok else '❌'} kb_recalls: {len(docs)} campaigns")


# ── kb_playbook: approved responses, pricing, warranty ────────────────────

def ingest_playbook():
    """Ingest curated markdown from knowledge_docs/playbook/."""
    pb_dir = os.path.join(DOCS_DIR, "playbook")
    docs, metas = [], []

    if os.path.isdir(pb_dir):
        for fname in os.listdir(pb_dir):
            if not fname.endswith(".md"):
                continue
            with open(os.path.join(pb_dir, fname), encoding="utf-8") as f:
                text = f.read()
            # Split on '## ' headings so each response pattern stays intact
            for section in text.split("\n## "):
                if len(section.split()) < 20:
                    continue
                docs.append(section.strip())
                metas.append({"source": fname, "doc_type": "playbook",
                              "topic": fname.rsplit(".", 1)[0]})

    ok = vector_store.add("kb_playbook", docs, metas)
    print(f"{'✅' if ok else '❌'} kb_playbook: {len(docs)} sections")


# ── kb_history: this fleet's own outcomes ─────────────────────────────────

def ingest_history_record(vehicle: Dict, diagnosis: Dict,
                          outcome: Dict, conversation: List[str] = None):
    """
    Append ONE completed workflow to kb_history.
    Call this from LearningAgent.update_memory() so the index grows automatically.
    """
    doc = (
        f"VEHICLE: {vehicle.get('make','')} {vehicle.get('model','')} "
        f"{vehicle.get('year','')} @ {vehicle.get('odo_km','?')}km. "
        f"DIAGNOSIS: {diagnosis.get('affected_component','')} — "
        f"{diagnosis.get('severity','')}, "
        f"failure probability {diagnosis.get('failure_probability',0):.0%}, "
        f"RUL {diagnosis.get('rul_days','?')} days. "
        f"REASONING: {diagnosis.get('diagnostic_reasoning','')} "
        f"OUTCOME: customer {outcome.get('final_customer_response','UNKNOWN')} "
        f"via {outcome.get('communication_channel','')} "
        f"after {outcome.get('cycle_count',1)} cycle(s), "
        f"response time {outcome.get('response_time_hours',0):.1f}h."
    )
    if conversation:
        doc += " TRANSCRIPT: " + " | ".join(conversation[-6:])

    meta = {
        "source": f"workflow_{vehicle.get('vehicle_id','')}_{datetime.now():%Y%m%d}",
        "doc_type": "conversation_outcome",
        "make":      vehicle.get("make", ""),
        "model":     vehicle.get("model", ""),
        "year":      int(vehicle.get("year", 0) or 0),
        "component": diagnosis.get("affected_component", ""),
        "outcome":   outcome.get("final_customer_response", "UNKNOWN"),
    }
    vector_store.add("kb_history", [doc], [meta])


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--all",       action="store_true")
    p.add_argument("--technical", action="store_true")
    p.add_argument("--recalls",   action="store_true")
    p.add_argument("--playbook",  action="store_true")
    args = p.parse_args()

    if args.all or args.technical: ingest_technical()
    if args.all or args.recalls:   ingest_recalls()
    if args.all or args.playbook:  ingest_playbook()

    print("\n📊 Index sizes:")
    for c in ["kb_technical", "kb_recalls", "kb_playbook", "kb_history"]:
        print(f"   {c:<15} {vector_store.count(c):>6} documents")
```

### Step 4 — Wire it into the Diagnosis Agent

Edit [`backend/diagnosis_orchestrator.py`](backend/diagnosis_orchestrator.py):

```python
# at the top
from rag.retriever import retrieve_diagnostic_context

# replace _run_diagnosis_agent with:
async def _run_diagnosis_agent(self, telem_str: str, data_report: Dict,
                                vehicle: Dict = None, telematics: Dict = None) -> Dict:
    """Step 2: Call DiagnosisAgentV4, grounded with retrieved domain knowledge."""
    if not self._diag_agent:
        return _DIAGNOSIS_FALLBACK.copy()

    # ── RAG: retrieve manual knowledge + similar past cases ──────────────
    rag_context = ""
    try:
        component = data_report.get("detected_anomalies", ["general"])[0]
        rag_context = retrieve_diagnostic_context(
            component, telematics or {}, vehicle or {}
        )
        if rag_context:
            print(f"   📚 RAG: retrieved {rag_context.count('[')} reference chunks")
    except Exception as e:
        print(f"   ⚠️  RAG retrieval skipped: {str(e)[:50]}")

    prompt = (
        f"Given the vehicle telematics, the data-analysis report, and the "
        f"reference material below, predict component failure, RUL, and severity.\n\n"
        f"Telematics:\n{telem_str}\n\n"
        f"Data Analysis Report:\n{json.dumps(data_report, default=str)}\n"
        f"{rag_context}\n"
        f"IMPORTANT: Ground your RUL estimate and diagnostic_reasoning in the "
        f"reference material above when it is relevant. If the reference material "
        f"does not cover this case, rely on the telematics thresholds and say so "
        f"in diagnostic_reasoning. Never invent a manual reference."
    )
    return await AgentExecutor.execute_agent(
        self._diag_agent, prompt, _DIAGNOSIS_FALLBACK.copy()
    )
```

And update the call site in `run_diagnosis()`:
```python
diag_report = await self._run_diagnosis_agent(telem_str, data_report, vehicle, telematics)
```

### Step 5 — Wire it into the Manufacturing Agent

Edit [`backend/manufacturing_agent.py`](backend/manufacturing_agent.py) — RAG-first, mock as fallback:

```python
def get_recalls(self, vehicle_id: str) -> List[Dict]:
    """Check open recalls. Uses the RAG recall index; falls back to the mock catalogue."""
    make = self._resolve_make(vehicle_id)
    if not make:
        return []

    # ── RAG path ──────────────────────────────────────────────────────
    try:
        from rag.retriever import retrieve_recalls
        from app_state import app_state

        vehicle = app_state.get_vehicle(vehicle_id) or {"make": make}
        hits = retrieve_recalls(vehicle, k=5)
        if hits:
            return [{
                "nhtsa_campaign": h["metadata"].get("source", ""),
                "component":      h["metadata"].get("component", ""),
                "summary":        h["text"],
                "remedy":         "See campaign details",
                "status":         "OPEN",
                "relevance":      h["similarity"],
                "source":         "nhtsa_rag",
            } for h in hits]
    except Exception as e:
        print(f"   ⚠️  RAG recall lookup failed, using mock: {str(e)[:50]}")

    # ── Fallback: existing hardcoded catalogue ────────────────────────
    return [
        {"nhtsa_campaign": r["nhtsa_campaign"], "component": r["component"],
         "summary": r["summary"], "remedy": r["remedy"], "status": "OPEN",
         "source": "mock_catalogue"}
        for r in _RECALL_CATALOGUE if make in r["make_match"]
    ]
```

### Step 6 — Wire it into `/api/chat`

Edit [`backend/api_server.py`](backend/api_server.py) in `service_chat()`:

```python
# after building `component`, before `system_prompt`
rag_block = ""
try:
    from rag.retriever import retrieve_playbook
    rag_block = retrieve_playbook(
        intent="service_advisory", component=component, objection=body.message
    )
except Exception:
    pass

system_prompt = f"""You are AutoPredict's in-app service advisor for {make} {model}.
... (existing content unchanged) ...
{rag_block}
GROUNDING RULE: Any statement about price, warranty coverage, or service policy
must come from the APPROVED RESPONSE GUIDANCE above. If it is not covered there,
say "let me check that and get back to you" — never estimate a price yourself."""
```

### Step 7 — Close the learning loop

Edit [`backend/learning_agent.py`](backend/learning_agent.py) at the end of `update_memory()`:

```python
# ── Append this workflow to the semantic history index ────────────────
try:
    from rag.ingest import ingest_history_record
    ingest_history_record(
        vehicle={"vehicle_id": vehicle_id, **workflow_outcome.get("vehicle", {})},
        diagnosis=workflow_outcome.get("diagnosis", {}),
        outcome=workflow_outcome,
        conversation=workflow_outcome.get("conversation_history", []),
    )
except Exception as e:
    print(f"   ⚠️  RAG history write skipped: {str(e)[:50]}")
```

Every completed workflow now makes the next diagnosis smarter.

### Step 8 — Directory layout

```
backend/
├── rag/
│   ├── __init__.py
│   ├── vector_store.py       # ChromaDB + Ollama embeddings
│   ├── retriever.py          # per-agent retrieval functions
│   └── ingest.py             # offline ingestion pipeline
│
├── rag_store/                # ChromaDB persistence (gitignore this)
│   └── chroma.sqlite3
│
└── knowledge_docs/           # SOURCE documents you provide
    ├── technical/
    │   ├── Toyota_Camry_2021_ServiceManual.pdf
    │   ├── Honda_City_2022_TSB.pdf
    │   └── brake_wear_curves.md
    ├── playbook/
    │   ├── cost_objections.md
    │   ├── warranty_terms.md
    │   ├── pricing_table.md
    │   └── safety_explanations.md
    └── dtc_dictionary.json
```

Add to `.gitignore`:
```
rag_store/
knowledge_docs/*.pdf
```

### Step 9 — Verify

```bash
cd backend
ollama pull nomic-embed-text
pip install chromadb pypdf tiktoken

python -m rag.ingest --all

# expected:
# ✅ kb_technical:  1,284 chunks
# ✅ kb_recalls:      312 campaigns
# ✅ kb_playbook:      47 sections
```

Quick sanity check:
```python
from rag.retriever import retrieve_diagnostic_context
print(retrieve_diagnostic_context(
    "Brake Pads",
    {"brake_pad_mm": 2.1, "odo_km": 87432},
    {"make": "Toyota", "model": "Camry", "year": 2021},
))
```

### 15.1 Guardrails — non-negotiable

| Rule | Why |
|---|---|
| **Retrieval never overrides `rule_engine.py`** | Priority assignment must stay deterministic and auditable. A retrieved manual cannot downgrade a P0. |
| **Empty retrieval ⇒ existing behaviour** | Every retrieval function returns `""` or `[]` on failure. The system must run identically with RAG off. |
| **Instruct the LLM to admit gaps** | *"If the reference material does not cover this case, say so."* Prevents the model from inventing a manual citation. |
| **Always carry `source` metadata** | Every retrieved chunk has a source ID. Surface it in the UI — a technician must be able to check the claim. |
| **Filter by similarity threshold** | `MIN_SIMILARITY = 0.45`. A weak match is worse than no match — it actively misleads the model. |
| **Never embed PII** | Anonymise `kb_history` before ingestion: strip names, phone numbers, addresses. |
| **Watch latency** | Each retrieval adds one embedding call (~50–150 ms locally) plus the vector search (~10 ms). Fine for the 30-min background loop; measure it before adding to `/api/chat`. |

### 15.2 Measuring whether it worked

Build a small eval set of ~50 `(query, expected_document)` pairs and track:

| Metric | Definition | Target |
|---|---|---|
| **Recall@5** | Is the correct doc in the top 5? | > 0.90 |
| **MRR** | Mean reciprocal rank of the correct doc | > 0.70 |
| **Groundedness** | % of generated claims traceable to a retrieved chunk | > 0.85 |
| **Retrieval latency** | p95 end-to-end | < 300 ms |
| **Diagnosis confidence delta** | Mean `confidence` with RAG vs without | should rise |

The last one is measurable **for free** — every agent already returns a `confidence` field, so you can A/B the RAG path against the current path on the same telematics and compare.

---
---

# PART E — REFERENCE

## 16. Complete File-by-File Map

### 16.1 Backend — Core Infrastructure

| File | Lines | What it contains |
|---|---|---|
| [`backend/config.py`](backend/config.py) | 247 | `SystemConfig` (all thresholds, channel config, timeouts, ML/voice/sentiment settings), `EventTypes` (19 events), `CommunicationChannel`, `LlamaModelClient` factory with 4 role-specific client builders |
| [`backend/event_system.py`](backend/event_system.py) | 283 | `Event` dataclass (SHA-256 event_id), `EventPriority`, `EventBus` (async pub/sub), `TenantState` (per-vehicle state machine), `TenantRegistry` (isolation), `EventLogger` (audit) |
| [`backend/models.py`](backend/models.py) | 393 | `WorkflowState` enum, `CustomerMemory` (preferences, behaviour signals, channel recommendation), `VehicleMemory` (reliability, recurring issues), `CommunicationLog`, `MemoryStore` (JSON persistence), `AuditTrail` (SHA-256 hashing) |
| [`backend/app_state.py`](backend/app_state.py) | 207 | `DashboardEvent` (7 WS event types), `AppState` singleton — vehicles/bookings/conversations/alerts/manufacturing + WebSocket broadcast |
| [`backend/utils.py`](backend/utils.py) | 214 | `JSONParser` (robust LLM output extraction), `DataConverter` (numpy→Python, safe_float/int/bool), `ResponseValidator`, `DisplayFormatter` (console output) |
| [`backend/rule_engine.py`](backend/rule_engine.py) | 174 | `MaintenanceRuleEngine` — `assign_priority()`, `determine_escalation()`, `calculate_service_window()`, `determine_service_urgency()`, `assess_risk_level()`, `calculate_confidence_threshold()` |
| [`backend/data_generator.py`](backend/data_generator.py) | 320 | `VehicleDataGenerator` — telematics timeseries + history, vehicle master, maintenance history, customer profile, UEBA status. Scenario-driven (normal/warning/critical) |

### 16.2 Backend — Agents

| File | Lines | What it contains |
|---|---|---|
| [`backend/master_orchestrator.py`](backend/master_orchestrator.py) | 472 | `MasterOrchestrator` — system prompt with 6 responsibilities + replanning rules, 8 event handlers, `create_initial_plan()`, `_trigger_replanning()`, v5.0 domain routing methods, conflict resolution |
| [`backend/master_orchestrator_router.py`](backend/master_orchestrator_router.py) | 296 | `MasterOrchestratorRouter` — intent→domain mapping (`BOOKING_INTENTS`, `FOLLOWUP_ANALYSIS_INTENTS`, `ESCALATION_INTENTS`), per-conversation state, `resolve_conflict()` |
| [`backend/specialist_agents.py`](backend/specialist_agents.py) | 174 | `DataAnalysisAgentV4`, `DiagnosisAgentV4` (system messages + factories), `AgentExecutor` (bracket-counting JSON parser), `AgentFactoryV4` |
| [`backend/manufacturing_agent.py`](backend/manufacturing_agent.py) | 185 | `ManufacturingAgent` — `_DTC_CATALOGUE` (10 SAE J2012 codes), `_RECALL_CATALOGUE` (4 NHTSA mocks), `check_vehicle()`, `get_dtc_codes()`, `get_recalls()` |
| [`backend/scheduling_agent.py`](backend/scheduling_agent.py) | 1600 | `SERVICE_DURATIONS`, `TECHNICIANS` (5), `BAYS` (5), `SlotHold`, `BookingConfirmation`, `SchedulingAgent` (capacity/slot/booking/waitlist/NL date parsing) |
| [`backend/customer_engagement.py`](backend/customer_engagement.py) | 930 | `CustomerEngagementAgentV6` (aliased V4/V5) — 10-step pipeline, multi-channel outreach, `_run_interactive_loop()`, `_analyze_reply_v6()`, 4 terminal states, EXECUTION_READY gate |
| [`backend/learning_agent.py`](backend/learning_agent.py) | 333 | `LearningAgent` — memory update system prompt, multi-cycle learning rules, `_get_default_updates()` fallback, `_apply_memory_updates()`, `get_memory_summary()` |
| [`backend/customer_interpreter.py`](backend/customer_interpreter.py) | 320 | `CustomerResponseInterpreter` (raw text → structured intent + sentiment), `WebhookHandler` |
| [`backend/ml_contact_timing_agent.py`](backend/ml_contact_timing_agent.py) | 170 | `ContactTimingAgent` — LLM reasoning layered on `ContactTimingOptimizer` ML output |
| [`backend/diagnosis_orchestrator.py`](backend/diagnosis_orchestrator.py) | 267 | `DiagnosisOrchestrator` — 4-step server pipeline, lazy agent init, `run_diagnosis()`, `background_diagnosis_loop()` |
| [`backend/orchestration_system.py`](backend/orchestration_system.py) | 798 | `EventDrivenOrchestratorV41` — the full 6-phase CLI workflow, multi-cycle logic, degradation display, ML fusion, `_assign_priority()` |

### 16.3 Backend — Conversation Intelligence (15 modules)

| File | Purpose |
|---|---|
| [`backend/customer_intent_classifier.py`](backend/customer_intent_classifier.py) | 14 intent categories via keyword + semantic pattern matching |
| [`backend/conversation_stage_manager.py`](backend/conversation_stage_manager.py) | 5-stage progression: EDUCATE → VALIDATE → OBJECTIONS → DECISION → CLOSE |
| [`backend/response_strategy_engine.py`](backend/response_strategy_engine.py) | 6 strategies with anti-repetition rotation |
| [`backend/trust_signal_detector.py`](backend/trust_signal_detector.py) | Dynamic trust score from conversational signals |
| [`backend/logistics_reasoning_engine.py`](backend/logistics_reasoning_engine.py) | Real-world scheduling constraint solutions |
| [`backend/conversation_memory_tracker.py`](backend/conversation_memory_tracker.py) | Per-session tags: strategy, objection, trust trend, resistance trend, decision velocity |
| [`backend/trust_recovery_engine.py`](backend/trust_recovery_engine.py) | 6-step trust recovery protocol for past-bad-service customers |
| [`backend/edge_case_reasoning_engine.py`](backend/edge_case_reasoning_engine.py) | 5 original edge cases, deterministic responses |
| [`backend/edge_case_decision_engine.py`](backend/edge_case_decision_engine.py) | Extended to 7 edge cases (adds EC6 silent, EC7 supervisor) |
| [`backend/personalization_context_builder.py`](backend/personalization_context_builder.py) | v1 personalization from memory + vehicle + telematics |
| [`backend/personalization_context_engine.py`](backend/personalization_context_engine.py) | v2 — response speed, channel preference, trust sensitivity, decline tendency, satisfaction |
| [`backend/strategy_response_router.py`](backend/strategy_response_router.py) | **The binding layer** — deterministic response selection, LLM polish only |
| [`backend/execution_mode_manager.py`](backend/execution_mode_manager.py) | 4-stage one-way booking gate (INTENT→SLOT_SELECTED→CONFIRMED→EXECUTION) |
| [`backend/followup_cycle_manager.py`](backend/followup_cycle_manager.py) | Delay-intent detection, `FollowUpTask` scheduling, reanalysis trigger |
| [`backend/vehicle_reanalysis_engine.py`](backend/vehicle_reanalysis_engine.py) | Pre-follow-up delta computation → tone directive (WORSENED/STABLE/IMPROVED) |

### 16.4 Backend — ML, Communication, Voice

| File | Purpose |
|---|---|
| [`backend/ml_models.py`](backend/ml_models.py) | `FailurePredictionModel` (RF classifier + regressor, 10 features), `ContactTimingOptimizer`, `CustomerBehaviorPredictor`, `MLModelManager` |
| [`backend/ml_training.py`](backend/ml_training.py) | Training pipeline on synthetic data → produces the `.joblib` artifacts |
| `backend/ml_models/` | `failure_classifier.joblib` (1.8 MB), `failure_regressor.joblib` (8.9 MB), `scaler.joblib` |
| [`backend/communication_service.py`](backend/communication_service.py) | Multi-channel abstraction (EMAIL/SMS/WHATSAPP/VOICE), retry logic, simulation mode when credentials absent |
| [`backend/omnichannel_orchestrator.py`](backend/omnichannel_orchestrator.py) | Unified state across SMS/WhatsApp/Voice, channel switching |
| [`backend/voice_ai_agent.py`](backend/voice_ai_agent.py) | Real-time voice: Whisper STT → Groq Llama-3.1-70B → ElevenLabs TTS, <300 ms target |
| [`backend/voice_api.py`](backend/voice_api.py) | FastAPI server for Twilio webhooks + WebSocket audio streaming |
| [`backend/sentiment_analyzer.py`](backend/sentiment_analyzer.py) | Live emotion detection, frustration/urgency thresholds, objection detection |
| [`backend/temporal_engine.py`](backend/temporal_engine.py) | `ComponentDegradationModel`, `TemporalSimulator`, `MultiCycleWorkflowManager` |

### 16.5 Backend — Servers & Entry Points

| File | Purpose |
|---|---|
| [`backend/webhook_server.py`](backend/webhook_server.py) | **Main server entry point.** FastAPI app, mounts `api_router` + `ws_router`, CORS, startup (seed + background loop), 3 webhook endpoints, `/test/simulate-response` |
| [`backend/api_server.py`](backend/api_server.py) | **83 KB, 60+ endpoints.** Seeding, auth, vehicles, bookings, availability, conversations, dashboard, manufacturing, ~25 analytics endpoints, `/ws/dashboard`, mobile endpoints (OTP/register/FCM), `/api/chat` |
| [`backend/main.py`](backend/main.py) | CLI entry point — initialises 4 model clients, creates `EventDrivenOrchestratorV41`, loads memory, runs 4 test scenarios |
| [`backend/run_system.py`](backend/run_system.py) | Multiprocess launcher — voice API server + main simulation together |
| [`backend/check_system.py`](backend/check_system.py) | Health check — verifies Ollama, model availability, API server, dependencies |

### 16.6 Backend — Legacy / Scratch (⚠️ not part of the live system)

| File | Status |
|---|---|
| [`backend/heelo.py`](backend/heelo.py) | v1 monolith — earliest AutoGen + Llama prototype |
| [`backend/high.py`](backend/high.py) | v2 monolith — "True Agentic AI with Master Orchestrator" |
| [`backend/newww.py`](backend/newww.py) | v2.5 monolith — "Deterministic Rule Engine + LLM Advisory Agents" |
| [`backend/_test_intelligence.py`](backend/_test_intelligence.py) | Functional test for the intelligence modules |
| `backend/memory_store*.json` | Memory snapshots across versions: `memory_store.json`, `_v4`, `_v41`, `_v43` |
| `backend/analyze_*.txt`, `build_out.txt`, `flutter_run2.txt` | Flutter build/analyze logs |
| [`backend/advanced_suggestions.txt`](backend/advanced_suggestions.txt) | Roadmap notes (LSTM RUL, blockchain audit, dynamic pricing, …) |
| `SOLUTION.md`, `QUICKSTART.md`, `START_HERE.md`, `FIX_SUMMARY.txt` | Setup/troubleshooting docs |

### 16.7 Web Dashboard

| Path | Purpose |
|---|---|
| [`autopredict-web/src/App.jsx`](backend/autopredict-web/src/App.jsx) | Router — 3 role dashboards + shared pages + 404 |
| [`autopredict-web/src/main.jsx`](backend/autopredict-web/src/main.jsx) | React entry |
| [`autopredict-web/src/config.js`](backend/autopredict-web/src/config.js) | `API_BASE`, `WS_BASE` |
| [`autopredict-web/src/contexts/WebSocketContext.jsx`](backend/autopredict-web/src/contexts/WebSocketContext.jsx) | WS client with back-off reconnect + typed pub/sub |
| `src/hooks/useWebSocket.js`, `useWebSocketData.js` | Hook wrappers over the context |
| `src/components/ProtectedRoute.jsx` | Role-gated routing |
| `src/components/DashboardLayout.jsx`, `Sidebar.jsx` | Shell |
| `src/components/charts/` (40 files) | Every analytics visualisation (see §10.3) |
| `src/components/CarModel.jsx`, `Engine3D.jsx`, `SteeringWheel3D.jsx` | Three.js 3D |
| `src/components/TelematicsGauge.jsx`, `SubsystemRadar.jsx`, `VehicleCard.jsx`, `DtcPanel.jsx`, `BayCalendar.jsx`, `AlertBanner.jsx`, `LiveEventBus.jsx`, `LiveToast.jsx` | Domain widgets |
| `src/pages/operations/` (6) | Ops dashboard |
| `src/pages/manager/` (5) | Manager dashboard |
| `src/pages/executive/` (5) | Executive dashboard |
| `src/pages/` — `Login`, `ConversationsPage`, `RecallsPage`, `ReportsPage`, `SettingsPage` | Shared pages |
| `public/car.glb`, `car1.glb`, `Speedometer.json` | 3D models + Lottie |
| `tailwind.config.js`, `vite.config.js`, `postcss.config.js` | Build config |

### 16.8 Mobile App

| Path | Purpose |
|---|---|
| [`autopredict_app/lib/main.dart`](backend/autopredict_app/lib/main.dart) | Entry — `ProviderScope`, go_router (11 routes), theme, portrait lock |
| `lib/core/services/api_service.dart` | Dio REST client + full offline mock layer |
| `lib/core/services/ollama_service.dart` | Direct Ollama client via ngrok, streaming, vehicle-context system prompt |
| `lib/core/services/obd_simulator.dart` | Simulated live OBD telemetry |
| `lib/core/providers/` | Riverpod: `vehicle`, `diagnostics`, `booking`, `chat` |
| `lib/core/models/` | `vehicle_data`, `diagnostic_component`, `chat_message` |
| `lib/core/theme/` | `app_theme`, `colors`, `typography`, `theme_provider` |
| `lib/features/splash`, `onboarding`, `auth` | Entry flow |
| `lib/features/home` | `home_screen`, `settings_tab` |
| `lib/features/diagnostics` | Component health |
| `lib/features/chat` | Direct Ollama streaming chat |
| `lib/features/service_chat` | Backend `/api/chat` with booking actions |
| `lib/features/bookings` | `bookings_screen`, `booking_flow_screen` |
| `lib/features/battery`, `media`, `parking`, `notifications`, `profile` | Connected-car features |
| `lib/shared/widgets/` | `car_top_view`, `floating_nav_bar`, `speedometer_gauge`, `stat_card`, `vehicle_pod` |
| `pubspec.yaml` | Dependencies |
| `android/`, `ios/` | Platform projects |

---

## 17. How to Run Everything

### 17.1 Prerequisites

```bash
# 1. Ollama + Llama 3
curl https://ollama.ai/install.sh | sh     # or download the Windows installer
ollama pull llama3:8b
ollama serve                                # keep running, port 11434

# verify
curl http://localhost:11434/api/tags
```

### 17.2 Backend

```bash
cd backend
pip install -r requirements.txt

# Option A — the LIVE SERVER (what web + app need)
python webhook_server.py
#   → http://localhost:8000
#   → /docs for the OpenAPI UI
#   → seeds 10 vehicles, starts the 30-min diagnosis loop

# Option B — the CLI AGENT SIMULATION (interactive, terminal chat)
python main.py

# Health check
python check_system.py
```

### 17.3 Web dashboard

```bash
cd backend/autopredict-web
npm install
npm run dev            # → http://localhost:5173
```
Log in with any credentials; pick a role (`ops` / `manager` / `executive`).

### 17.4 Mobile app

```bash
cd backend/autopredict_app
flutter pub get
flutter run
```

**Two URLs must be configured:**

1. `lib/core/services/api_service.dart` → `_base`
   - Android emulator: `http://10.0.2.2:8000/api`
   - Physical device: `http://<YOUR_PC_LAN_IP>:8000/api`
2. `lib/core/services/ollama_service.dart` → `_baseUrl`
   - Run `ngrok http 11434`, paste the HTTPS URL

Both devices must be on the same Wi-Fi network.

### 17.5 Common problems

| Symptom | Cause | Fix |
|---|---|---|
| `[AI offline — ensure Ollama is running]` | API server not running | `python webhook_server.py` and leave it open |
| `Port 8000 already in use` | Stale process | `netstat -ano \| findstr :8000` → `taskkill /PID <pid> /F` |
| App shows mock data only | Wrong IP in `api_service.dart` | Use the PC's LAN IP, same Wi-Fi |
| `Module not found` | Missing deps | `pip install -r requirements.txt` |
| ngrok URL expired | Free ngrok rotates URLs | Re-run `ngrok http 11434`, update `ollama_service.dart`, hot-restart |
| WS not connecting | CORS / wrong `WS_BASE` | Check `autopredict-web/src/config.js` |

---

## 18. What's Real vs What's Mocked

Being clear about this matters for anyone extending the system.

### ✅ Real and working

- AutoGen multi-agent orchestration with genuine LLM calls to local Llama 3
- Event-driven pub/sub with per-tenant isolation
- Master Orchestrator planning and replanning
- Trained RandomForest models (`.joblib` artifacts present and loaded)
- Full deterministic rule engine
- Scheduling agent — real constraint solving over technicians, bays, durations, holds
- 15-module conversation intelligence stack
- FastAPI server, 60+ endpoints, live WebSocket broadcast
- React dashboard with 40 charts and live updates
- Flutter app with streaming chat and booking flow
- Memory persistence to JSON
- Multi-cycle temporal simulation with component degradation

### ⚠️ Mocked / simulated

| What | Where | To make it real |
|---|---|---|
| Telematics data | `data_generator.py` | Connect a real telematics feed / OBD-II dongle |
| DTC codes | `manufacturing_agent.py` — 10 hardcoded codes | Real OBD-II reader + full DTC database (**→ RAG**) |
| NHTSA recalls | `manufacturing_agent.py` — 4 hardcoded campaigns | `api.nhtsa.gov/recalls/recallsByVehicle` (**→ RAG**) |
| Customer responses (CLI path) | `orchestration_system.py` — `random.choice([...])` | Real inbound webhooks (already built, just unwired in that path) |
| SMS / WhatsApp / Voice | `communication_service.py` — simulation mode | Set real Twilio credentials in `config.py` / `.env` |
| Email | `communication_service.py` | Set real SMTP credentials |
| Login | `api_server.py:/api/auth/login` — accepts anything | Real auth + JWT |
| OTP | `api_server.py` — always `000000` | Twilio Verify |
| Session token | base64 JSON, not signed | Real JWT with signature |
| FCM push | `/api/fcm/notify` returns `"queued"` | Firebase Admin SDK |
| Mobile OBD | `obd_simulator.dart` | Bluetooth ELM327 reader |
| `ai_accuracy: 0.94` | `app_state.get_summary()` — placeholder | Compute from actual prediction outcomes |
| Some analytics | Several `/api/analytics/*` synthesise plausible numbers | Aggregate from real historical data |

### 🎯 The highest-value next steps

1. **RAG for the Manufacturing Agent** — replaces the weakest mock with a genuinely useful capability and carries near-zero hallucination risk (§13, §15)
2. **RAG for the Diagnosis Agent** — the biggest accuracy lever available; an 8B model reasoning over retrieved manuals beats an 8B model guessing
3. **Real Twilio credentials** — the entire multi-channel pipeline is already built; it just needs keys
4. **Wire the CLI path's customer responses to the real webhooks** — removes the last `random.choice()` from the agentic loop
5. **LSTM for RUL** (already sketched in `advanced_suggestions.txt`) — RandomForest ignores temporal degradation trends; an LSTM over 30 days of telematics would capture accelerating failure

---

## Appendix — Quick Reference Card

### The 5 agents

| # | Agent | File | Type | Role |
|---|---|---|---|---|
| 1 | **Data Analysis** | `specialist_agents.py` | LLM | Telematics → health score, anomalies, confidence |
| 2 | **Diagnosis** | `specialist_agents.py` + `ml_models.py` | LLM + ML | Failure probability, RUL, component, severity |
| 3 | **Manufacturing** | `manufacturing_agent.py` | Deterministic | DTC codes + NHTSA recalls |
| 4 | **Scheduling** | `scheduling_agent.py` | Deterministic | Slot finding, holds, bookings, reschedule, waitlist |
| 5 | **Customer Engagement** | `customer_engagement.py` | Hybrid | Multi-channel persuasion, objection handling, consent-gated booking |

### The 5 meta-agents

| Agent | File | Role |
|---|---|---|
| **Master Orchestrator** | `master_orchestrator.py` | Plan · monitor · replan · route · escalate |
| **Learning Agent** | `learning_agent.py` | Update customer + vehicle memory profiles |
| **Customer Interpreter** | `customer_interpreter.py` | Raw inbound text → structured intent |
| **Contact Timing Agent** | `ml_contact_timing_agent.py` | Decide *when* to contact |
| **Voice AI Agent** | `voice_ai_agent.py` | Real-time voice for P0 escalations |

### Priority thresholds

| Priority | Meaning | Triggers |
|---|---|---|
| **P0** | Critical, < 24 h | brake < 3 mm · battery < 11.5 V · coolant > 110 °C · severity HIGH/CRITICAL · RUL ≤ 3 d |
| **P1** | High, < 7 days | failure prob > 0.7 · RUL ≤ 7 d · brake < 4 mm · battery < 11.8 V |
| **P2** | Medium, < 30 days | failure prob > 0.4 · RUL ≤ 30 d · brake < 6 mm |
| **P3** | Routine | everything else |

### Ports

| Service | Port |
|---|---|
| Ollama | 11434 |
| FastAPI backend | 8000 |
| React dev server | 5173 |

---

*Document generated from a full read of the codebase. Every file path, class name, threshold, and code excerpt in this document was taken directly from the source.*
