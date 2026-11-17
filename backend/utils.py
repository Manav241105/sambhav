"""
Utility Functions
Helper functions for JSON parsing, data conversion, and response cleaning
"""

import json
import re
import numpy as np
from typing import Dict, Any, Optional


class JSONParser:
    """Enhanced JSON parsing with robust error handling"""
    
    @staticmethod
    def clean_llm_response(response_text: str) -> str:
        """
        Clean LLM response to extract pure JSON
        Handles markdown code blocks, extra text, and formatting issues
        """
        if not response_text:
            return "{}"
        
        # Remove markdown code blocks
        if "```json" in response_text:
            parts = response_text.split("```json")
            if len(parts) > 1:
                response_text = parts[1].split("```")[0].strip()
        elif "```" in response_text:
            parts = response_text.split("```")
            if len(parts) > 1:
                response_text = parts[1].split("```")[0].strip()
        
        # Remove any leading/trailing whitespace
        response_text = response_text.strip()
        
        # Find the first { and last } to extract JSON object
        start_idx = response_text.find('{')
        if start_idx == -1:
            return "{}"
        
        # Count braces to find matching closing brace
        brace_count = 0
        end_idx = -1
        for i in range(start_idx, len(response_text)):
            if response_text[i] == '{':
                brace_count += 1
            elif response_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx+1]
        else:
            # Fallback: just use rfind
            end_idx = response_text.rfind('}')
            if end_idx > start_idx:
                response_text = response_text[start_idx:end_idx+1]
        
        return response_text
    
    @staticmethod
    def parse_json_safe(json_str: str, fallback: Dict = None) -> Dict:
        """
        Safely parse JSON with fallback
        
        Args:
            json_str: JSON string to parse
            fallback: Default dict to return on failure
            
        Returns:
            Parsed dict or fallback
        """
        if fallback is None:
            fallback = {}
        
        try:
            # Clean the response first
            cleaned = JSONParser.clean_llm_response(json_str)
            
            # Attempt to parse
            result = json.loads(cleaned)
            
            # Validate it's a dict
            if not isinstance(result, dict):
                print(f"   ⚠️  Parsed result is not a dict: {type(result)}")
                return fallback
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON decode error: {str(e)[:60]}")
            return fallback
        except Exception as e:
            print(f"   ⚠️  Parse error: {str(e)[:60]}")
            return fallback
    
    @staticmethod
    def extract_json_objects(text: str) -> list:
        """
        Extract all JSON objects from text
        Useful when response contains multiple JSON blocks
        """
        json_objects = []
        
        # Pattern to match JSON objects
        pattern = r'\{[^{}]*\}'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            try:
                obj = json.loads(match.group())
                json_objects.append(obj)
            except:
                continue
        
        return json_objects


class DataConverter:
    """Convert between different data types"""
    
    @staticmethod
    def convert_numpy_types(obj: Any) -> Any:
        """
        Recursively convert NumPy types to native Python types
        Essential for JSON serialization
        """
        if isinstance(obj, dict):
            return {k: DataConverter.convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DataConverter.convert_numpy_types(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(DataConverter.convert_numpy_types(item) for item in obj)
        elif isinstance(obj, (np.bool_, np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """Safely convert value to int"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_bool(value: Any, default: bool = False) -> bool:
        """Safely convert value to bool"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 't', 'y']
        try:
            return bool(value)
        except:
            return default


class ResponseValidator:
    """Validate agent responses"""
    
    @staticmethod
    def validate_data_analysis_output(output: Dict) -> bool:
        """Validate Data Analysis Agent output"""
        required_fields = [
            "health_score",
            "detected_anomalies",
            "service_demand_forecast",
            "confidence"
        ]
        
        return all(field in output for field in required_fields)
    
    @staticmethod
    def validate_diagnosis_output(output: Dict) -> bool:
        """Validate Diagnosis Agent output"""
        required_fields = [
            "failure_probability",
            "rul_days",
            "affected_component",
            "severity",
            "confidence"
        ]
        
        return all(field in output for field in required_fields)
    
    @staticmethod
    def validate_customer_engagement_output(output: Dict) -> bool:
        """Validate Customer Engagement Agent output"""
        required_fields = [
            "customer_response",
            "interaction_outcome",
            "engagement_quality"
        ]
        
        return all(field in output for field in required_fields)
    
    @staticmethod
    def validate_monitoring_decision(output: Dict) -> bool:
        """Validate Master Orchestrator monitoring decision"""
        required_fields = [
            "continue_execution",
            "recommendation",
            "confidence"
        ]
        
        return all(field in output for field in required_fields)


class DisplayFormatter:
    """Format output for console display"""
    
    @staticmethod
    def format_header(text: str, char: str = "=", width: int = 80) -> str:
        """Format section header"""
        return f"\n{char * width}\n{text}\n{char * width}\n"
    
    @staticmethod
    def format_subheader(text: str, width: int = 80) -> str:
        """Format subsection header"""
        return f"\n{text}\n{'-' * width}"
    
    @staticmethod
    def format_metric(label: str, value: Any, unit: str = "") -> str:
        """Format metric display"""
        return f"✓ {label}: {value}{unit}"
    
    @staticmethod
    def format_warning(message: str) -> str:
        """Format warning message"""
        return f"⚠️  {message}"
    
    @staticmethod
    def format_error(message: str) -> str:
        """Format error message"""
        return f"❌ {message}"
    
    @staticmethod
    def format_success(message: str) -> str:
        """Format success message"""
        return f"✅ {message}"