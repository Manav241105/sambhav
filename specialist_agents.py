"""
Specialist Agents - v4.0
Enhanced agents with detailed outputs and strict JSON parsing
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
import asyncio
import json


class DataAnalysisAgentV4:
    """Advanced Data Analysis Agent with comprehensive telematics evaluation"""
    
    SYSTEM_MESSAGE = """You are an advanced Data Analysis AI.

CRITICAL: Respond with ONLY valid JSON. Start with { end with }. No markdown, no explanations.

OUTPUT (JSON ONLY):
{
  "health_score": 0.75,
  "detected_anomalies": ["Specific issues found"],
  "service_demand_forecast": "LOW|MEDIUM|HIGH",
  "confidence": 0.85,
  "data_coverage": 0.95,
  "data_quality_notes": "Brief assessment",
  "critical_alerts": ["Safety concerns"],
  "trend_analysis": "Brief trend"
}

THRESHOLDS:
- Brake pads: <3mm critical, <5mm warning
- Battery: <11.5V critical, <11.8V warning
- Coolant: >110°C critical, >105°C warning

Start with { end with }. Nothing else."""
    
    @staticmethod
    def create(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Data_Analysis_Agent",
            model_client=model_client,
            system_message=DataAnalysisAgentV4.SYSTEM_MESSAGE
        )


class DiagnosisAgentV4:
    """Advanced Diagnosis Agent with predictive failure analysis"""
    
    SYSTEM_MESSAGE = """You are an advanced Diagnostic AI.

CRITICAL: Respond with ONLY valid JSON. Start with { end with }. No markdown, no explanations.

OUTPUT (JSON ONLY):
{
  "failure_probability": 0.65,
  "rul_days": 25,
  "affected_component": "Specific component name",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "recurring_defect": false,
  "confidence": 0.80,
  "diagnostic_reasoning": "Brief technical explanation",
  "recommended_action": "Specific maintenance action",
  "failure_mode": "How failure would occur",
  "secondary_risks": ["Related components at risk"]
}

SEVERITY:
- CRITICAL: Immediate safety risk
- HIGH: Urgent attention needed
- MEDIUM: Service recommended soon
- LOW: Routine maintenance

Start with { end with }. Nothing else."""
    
    @staticmethod
    def create(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Diagnosis_Agent",
            model_client=model_client,
            system_message=DiagnosisAgentV4.SYSTEM_MESSAGE
        )


class AgentExecutor:
    """Helper class to execute agents with proper JSON parsing"""
    
    @staticmethod
    async def execute_agent(agent: AssistantAgent, prompt: str, 
                           fallback: dict) -> dict:
        """Execute agent and parse JSON response with robust extraction"""
        
        try:
            team = RoundRobinGroupChat([agent], max_turns=1)
            stream = team.run_stream(task=prompt)
            
            # Collect ONLY the last message content (agent reply, not task prompt)
            last_content = ""
            async for message in stream:
                if hasattr(message, 'content') and message.content:
                    last_content = str(message.content)
            
            response_text = last_content.strip()
            
            if not response_text:
                raise ValueError("Empty response from agent")
            
            # Remove markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Find the start of JSON
            start_idx = response_text.find('{')
            
            if start_idx == -1:
                raise ValueError("No JSON object found in response")
            
            # Use bracket counting to find the exact end of the JSON object
            # Properly handles strings containing braces
            bracket_count = 0
            in_string = False
            escape_next = False
            end_idx = start_idx
            
            for i in range(start_idx, len(response_text)):
                char = response_text[i]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"':
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_idx = i
                            break
            
            # Extract only the JSON object (strips any trailing text)
            json_str = response_text[start_idx:end_idx+1]
            
            result = json.loads(json_str)
            return result
            
        except json.JSONDecodeError as e:
            print(f"      ⚠️  JSON parsing error: {str(e)[:60]}")
        except Exception as e:
            print(f"      ⚠️  Agent execution error: {str(e)[:60]}")
        
        return fallback


class AgentFactoryV4:
    """Factory for creating all specialist agents"""
    
    @staticmethod
    def create_all_agents(model_client) -> dict:
        return {
            "Data_Analysis_Agent": DataAnalysisAgentV4.create(model_client),
            "Diagnosis_Agent": DiagnosisAgentV4.create(model_client)
        }