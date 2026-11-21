# Dynamic Agentic Predictive Maintenance System v3.0

A **truly autonomous** multi-agent AI system for vehicle predictive maintenance with **real-time replanning** and **customer interaction loops** using AutoGen 0.7.5 and Ollama.

## 🌟 NEW Features (v3.0)

### 🔄 **TRUE Dynamic Agentic Behavior**
- **Customer Interaction Loops**: System dynamically responds to customer feedback
- **Runtime Replanning**: Master Orchestrator creates new plans based on customer responses
- **Event-Driven Workflow**: Adapts to runtime conditions, not just pre-planned sequences
- **Multiple Replanning Cycles**: Up to 3 interaction rounds with adaptive strategies

### ✅ **Fixed Issues from v2.1**
- **✅ JSON Parsing Errors Resolved**: No more "Extra data" errors in monitoring
- **✅ Enhanced JSON Extraction**: Strict parsing with proper response cleaning
- **✅ Better Error Handling**: Graceful fallbacks throughout the system

### 🎯 **Core Features**
- **Master Orchestrator AI**: Autonomous planning, monitoring, and adaptive replanning
- **Specialist Agents**: Data Analysis, Diagnosis, and Customer Engagement
- **Robust JSON Parsing**: Enhanced error handling with fallback mechanisms
- **Rule-Based Decision Engine**: Deterministic priority assignment and escalation logic
- **Full Audit Trail**: Regulatory-grade traceability with SHA-256 hashing
- **Modular Architecture**: Clean separation of concerns for maintainability

## 📁 Project Structure

```
predictive-maintenance/
├── config.py                  # System configuration and model clients
├── models.py                  # Data models and state management
├── data_generator.py          # Synthetic data generation
├── rule_engine.py             # Decision rules and business logic
├── utils.py                   # Utility functions (JSON parsing, validation)
├── master_orchestrator.py     # Master AI orchestrator agent
├── specialist_agents.py       # Specialist AI agents (Data, Diagnosis, Customer)
├── orchestration_system.py    # Main workflow orchestration engine
├── main.py                    # Executable entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Ollama** installed and running
3. **Llama3:8b** model pulled in Ollama

```bash
# Install Ollama (if not installed)
curl https://ollama.ai/install.sh | sh

# Pull Llama3 model
ollama pull llama3:8b

# Start Ollama server
ollama serve
```

### Installation

```bash
# Clone/create project directory
mkdir predictive-maintenance
cd predictive-maintenance

# Install dependencies
pip install -r requirements.txt
```

### Running the System

```bash
python main.py
```

## 🏗️ Architecture

### Component Overview

#### 1. Configuration Layer (`config.py`)
- System-wide configuration
- Model client factory
- Threshold definitions

#### 2. Data Models (`models.py`)
- `ExecutionContext`: Tracks workflow state
- `WorkflowState`: Enum for workflow stages
- `AuditTrail`: Generates audit hashes

#### 3. Data Generation (`data_generator.py`)
- Synthetic vehicle data
- Telematics time series
- Maintenance history
- Customer profiles

#### 4. Rule Engine (`rule_engine.py`)
- Priority assignment (P0-P3)
- Escalation determination
- Service window calculation
- Risk assessment

#### 5. Utilities (`utils.py`)
- `JSONParser`: Robust LLM response parsing
- `DataConverter`: NumPy to Python type conversion
- `ResponseValidator`: Agent output validation
- `DisplayFormatter`: Console output formatting

#### 6. Master Orchestrator (`master_orchestrator.py`)
- Creates execution plans
- Monitors workflow progress
- Triggers adaptive replanning
- Makes go/no-go decisions

#### 7. Specialist Agents (`specialist_agents.py`)
- **Data Analysis Agent**: Telematics health assessment
- **Diagnosis Agent**: Failure prediction and RUL calculation
- **Customer Engagement Agent**: Service communication simulation

#### 8. Orchestration System (`orchestration_system.py`)
- Main workflow coordinator
- Agent execution management
- Work order generation
- Audit record creation

#### 9. Main Script (`main.py`)
- Entry point
- Scenario runner
- Results aggregation

## 🔄 Dynamic Workflow Example

### Scenario: Customer Initially Declines Service

```
1. Initial Contact
   ├── Data Analysis Agent: Detects brake wear
   ├── Diagnosis Agent: Predicts 85% failure probability
   └── Customer Engagement: Customer DECLINES (busy schedule)

2. Master Orchestrator Adapts
   ├── Trigger: Customer DECLINED
   ├── Creates adaptive plan: Follow-up with alternative options
   └── Replanning Count: 1

3. Follow-up Interaction
   ├── Customer Engagement (Round 2): Offer flexible scheduling
   ├── Customer Response: REQUESTED_RESCHEDULE
   └── Master Orchestrator: Adjust plan for scheduling flexibility

4. Final Interaction
   ├── Customer Engagement (Round 3): Confirm appointment options
   ├── Customer Response: ACCEPTED
   └── Work Order: Generated with scheduled date

RESULT: 3 interaction rounds, 2 replanning events, successful resolution
```

## 🏗️ Architecture

### Enhanced Workflow Phases

#### Phase 0: Data Gathering
- Generate vehicle data
- Generate telematics
- Generate maintenance history
- Generate customer profile
- UEBA security check

#### Phase 1: Initial Planning
- Master Orchestrator analyzes vehicle condition
- Creates initial execution plan
- Determines strategy (standard/expedited/deep_analysis)

#### Phase 2: Initial Workflow
- Execute Data Analysis Agent
- Execute Diagnosis Agent
- Master monitors after each step
- Customer Engagement **deferred** to Phase 3

#### Phase 3: **🔄 Dynamic Customer Interaction Loop** (NEW!)
```
LOOP (up to 3 rounds):
  ├── Customer Engagement: Send service notification
  ├── Simulate Customer Response (ACCEPTED/DECLINED/RESCHEDULE)
  │
  ├── IF response != ACCEPTED:
  │   ├── Master Orchestrator: Create adaptive plan
  │   ├── Execute adaptive actions (follow-up, reschedule, escalate)
  │   ├── Monitor execution
  │   └── Check if customer changed response
  │
  └── IF ACCEPTED or max rounds: Exit loop
```

#### Phase 4: Final Decision
- Priority assignment
- Escalation determination
- Work order generation

#### Phase 5: Summary & Audit
- Execution summary
- Workflow event log
- Audit hash generation

## 🎯 Key Improvements from v2.1

### 1. **✅ FIXED: JSON Parsing Errors**
**Problem**: "Extra data: line X column Y (char Z)" errors
**Solution**: 
- Strict JSON extraction (first `{` to last `}` only)
- Remove ALL text before/after JSON
- No markdown code blocks allowed
- Proper error handling with fallbacks

### 2. **🔄 TRUE Dynamic Agentic Behavior**
**Problem**: Linear workflow, single customer contact, no runtime adaptation
**Solution**:
- Customer Interaction Loop (up to 3 rounds)
- Master Orchestrator creates adaptive plans based on responses
- Event-driven replanning (not pre-planned)
- Multiple replanning cycles per workflow

### 3. **📧 Realistic Customer Interaction**
- Initial contact simulation
- Response-based replanning (DECLINED → follow-up strategy)
- Follow-up engagement with alternative options
- Customer can change response over multiple rounds

### 4. **🧠 Enhanced Master Orchestrator**
- `create_customer_response_plan()`: NEW method for adaptive planning
- Monitors after EACH agent execution
- Creates context-aware adaptive plans
- Handles complex customer interaction scenarios

### 5. **📊 Workflow Event Tracking**
- All major events logged (planning, responses, replanning)
- Audit trail includes replanning count
- Better visibility into dynamic behavior

## 🔧 Configuration

Key configuration in `config.py`:

```python
# Model Settings
MODEL_NAME = "llama3:8b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Workflow Settings
MAX_REPLANNING_ATTEMPTS = 2
LOW_CONFIDENCE_THRESHOLD = 0.5
MAX_WORKFLOW_STEPS = 10

# Critical Thresholds
CRITICAL_BRAKE_PAD_MM = 3.0
CRITICAL_BATTERY_VOLTAGE = 11.5
CRITICAL_COOLANT_TEMP = 110.0
```

## 📊 Output Example

```
================================================================================
🤖 AGENTIC PREDICTIVE MAINTENANCE CYCLE
Vehicle ID: VEH001 | Scenario: CRITICAL
================================================================================

📊 STEP 0: Data Gathering
--------------------------------------------------------------------------------
✓ Vehicle: Tata Nexon EV (2023)
✓ Customer: Rajesh Kumar
✓ Odometer: 87,432 km
✓ Brake Pad: 2.1 mm
✓ Battery: 11.2 V
✓ Coolant: 115.3°C

🧠 MASTER ORCHESTRATOR: Initial Planning
--------------------------------------------------------------------------------
   ✅ Master Orchestrator created initial plan
✓ Strategy: EXPEDITED
✓ Risk Level: CRITICAL
✓ Steps Planned: 3
✓ Estimated Duration: 3 min
✓ Reasoning: Critical conditions detected, immediate analysis required

... [workflow execution]

🎯 FINAL DECISION & ACTION
================================================================================

📋 MAINTENANCE RECOMMENDATION:
   Component: Brake Pads
   Priority: P0
   Failure Probability: 85.0%
   RUL: 2 days
   Customer Response: ACCEPTED
   Escalation: YES

📄 WORK ORDER: WO20260118001
   Scheduled: 2026-01-19
   Service Type: Brake Pads Maintenance
   Status: SCHEDULED

📊 EXECUTION SUMMARY
================================================================================
✓ Total Steps: 3
✓ Agents Invoked: 3
✓ Replanning Count: 0
✓ Avg Confidence: 0.87
✓ Duration: 45.3s
✓ Final State: completed

🔒 AUDIT HASH: a3f8d9e2b1c6f7a4
✓ Regulatory Compliance: VERIFIED

================================================================================
✅ AGENTIC MAINTENANCE CYCLE COMPLETED
================================================================================
```

## 🐛 Troubleshooting

### Issue: "Monitoring JSON error: Extra data"
**Fixed in v2.1**: Enhanced JSON parsing with proper response cleaning

### Issue: Ollama connection failed
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
pkill ollama
ollama serve
```

### Issue: Model not found
```bash
# List available models
ollama list

# Pull llama3:8b if missing
ollama pull llama3:8b
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📧 Contact

For issues or questions, please open a GitHub issue.

## 🙏 Acknowledgments

- AutoGen Framework by Microsoft
- Ollama for local LLM inference
- Llama 3 model by Meta