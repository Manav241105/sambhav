"""
Sentiment Analyzer - v4.3
Real-time sentiment analysis with emotion detection and objection handling
"""

from typing import Dict, List, Optional
import re


class SentimentAnalyzer:
    """
    Analyzes customer sentiment in real-time
    
    Features:
    - Emotion detection (Happy, Frustrated, Confused, Urgent)
    - Objection detection (price, cancel, not interested)
    - Urgency scoring
    - Recommended actions
    """
    
    # Emotion patterns
    EMOTION_PATTERNS = {
        "FRUSTRATED": {
            "keywords": ["frustrated", "annoyed", "upset", "angry", "mad", "irritated", 
                        "fed up", "sick of", "terrible", "awful", "horrible"],
            "weight": 1.0
        },
        "CONFUSED": {
            "keywords": ["confused", "don't understand", "what", "huh", "unclear",
                        "explain", "how", "why", "don't get it"],
            "weight": 0.8
        },
        "URGENT": {
            "keywords": ["urgent", "emergency", "asap", "now", "immediately", "critical",
                        "right away", "quickly", "hurry", "fast"],
            "weight": 1.2
        },
        "HAPPY": {
            "keywords": ["great", "thanks", "perfect", "excellent", "awesome", "good",
                        "wonderful", "appreciate", "love", "fantastic"],
            "weight": 0.9
        },
        "WORRIED": {
            "keywords": ["worried", "concerned", "nervous", "scared", "afraid",
                        "anxious", "unsafe", "dangerous"],
            "weight": 1.1
        }
    }
    
    # Objection patterns
    OBJECTION_PATTERNS = {
        "price": {
            "keywords": ["expensive", "cost", "afford", "cheap", "price", "money",
                        "too much", "overpriced", "budget"],
            "severity": "HIGH"
        },
        "cancel": {
            "keywords": ["cancel", "stop", "unsubscribe", "don't call", "remove",
                        "opt out", "leave me alone"],
            "severity": "CRITICAL"
        },
        "not_interested": {
            "keywords": ["not interested", "no thanks", "don't need", "don't want",
                        "not now", "maybe later", "not for me"],
            "severity": "MEDIUM"
        },
        "time": {
            "keywords": ["no time", "busy", "later", "not now", "call back",
                        "bad time", "in a meeting"],
            "severity": "LOW"
        },
        "trust": {
            "keywords": ["scam", "fraud", "don't trust", "suspicious", "fake",
                        "not real", "lie", "lying"],
            "severity": "CRITICAL"
        }
    }
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze text for sentiment, emotion, and objections
        
        Args:
            text: Customer text to analyze
            
        Returns:
            {
                "emotion": "FRUSTRATED",
                "score": 0.85,
                "urgency": "HIGH",
                "objection_detected": true,
                "objection_type": "price",
                "objection_severity": "HIGH",
                "recommended_action": "escalate_to_voice",
                "confidence": 0.90
            }
        """
        
        text_lower = text.lower()
        
        # Detect emotion
        emotion, emotion_score = self._detect_emotion(text_lower)
        
        # Detect objections
        objection_result = self._detect_objection(text_lower)
        
        # Calculate urgency
        urgency = self._calculate_urgency(emotion, emotion_score, objection_result)
        
        # Determine recommended action
        action = self._recommend_action(emotion, urgency, objection_result)
        
        return {
            "emotion": emotion,
            "score": emotion_score,
            "urgency": urgency,
            "objection_detected": objection_result['detected'],
            "objection_type": objection_result.get('type'),
            "objection_severity": objection_result.get('severity'),
            "recommended_action": action,
            "confidence": self._calculate_confidence(text_lower),
            "raw_text": text
        }
    
    def _detect_emotion(self, text: str) -> tuple:
        """
        Detect primary emotion in text
        
        Returns:
            (emotion, score)
        """
        
        emotion_scores = {}
        
        for emotion, config in self.EMOTION_PATTERNS.items():
            score = 0.0
            keywords = config['keywords']
            weight = config['weight']
            
            for keyword in keywords:
                if keyword in text:
                    # Count occurrences
                    count = text.count(keyword)
                    score += count * weight
            
            if score > 0:
                emotion_scores[emotion] = score
        
        if not emotion_scores:
            return "NEUTRAL", 0.5
        
        # Get emotion with highest score
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[primary_emotion]
        
        # Normalize score to 0-1
        normalized_score = min(1.0, max_score / 3.0)
        
        return primary_emotion, normalized_score
    
    def _detect_objection(self, text: str) -> Dict:
        """
        Detect objections in text
        
        Returns:
            {
                "detected": true,
                "type": "price",
                "severity": "HIGH",
                "keywords_found": ["expensive", "cost"]
            }
        """
        
        for objection_type, config in self.OBJECTION_PATTERNS.items():
            keywords_found = []
            
            for keyword in config['keywords']:
                if keyword in text:
                    keywords_found.append(keyword)
            
            if keywords_found:
                return {
                    "detected": True,
                    "type": objection_type,
                    "severity": config['severity'],
                    "keywords_found": keywords_found
                }
        
        return {"detected": False}
    
    def _calculate_urgency(self, emotion: str, emotion_score: float,
                          objection_result: Dict) -> str:
        """
        Calculate urgency level
        
        Returns:
            "CRITICAL", "HIGH", "MEDIUM", or "LOW"
        """
        
        urgency_score = 0.0
        
        # Emotion-based urgency
        if emotion == "URGENT":
            urgency_score += 1.0
        elif emotion == "FRUSTRATED":
            urgency_score += 0.8
        elif emotion == "WORRIED":
            urgency_score += 0.9
        
        # Add emotion score
        urgency_score += emotion_score * 0.5
        
        # Objection severity
        if objection_result.get('detected'):
            severity = objection_result.get('severity')
            if severity == "CRITICAL":
                urgency_score += 1.0
            elif severity == "HIGH":
                urgency_score += 0.7
            elif severity == "MEDIUM":
                urgency_score += 0.4
        
        # Map to urgency level
        if urgency_score >= 1.5:
            return "CRITICAL"
        elif urgency_score >= 1.0:
            return "HIGH"
        elif urgency_score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _recommend_action(self, emotion: str, urgency: str,
                         objection_result: Dict) -> str:
        """
        Recommend action based on analysis
        
        Returns:
            Action recommendation
        """
        
        # Critical objections
        if objection_result.get('severity') == "CRITICAL":
            if objection_result.get('type') == "cancel":
                return "immediate_supervisor_escalation"
            elif objection_result.get('type') == "trust":
                return "provide_credentials_and_reassure"
        
        # High frustration → escalate to voice
        if emotion == "FRUSTRATED" and urgency in ["HIGH", "CRITICAL"]:
            return "escalate_to_voice"
        
        # Urgent matters
        if emotion == "URGENT" or urgency == "CRITICAL":
            return "prioritize_immediate_response"
        
        # Price objections
        if objection_result.get('type') == "price":
            return "switch_to_value_persona"
        
        # Not interested
        if objection_result.get('type') == "not_interested":
            return "gentle_value_proposition"
        
        # Confused
        if emotion == "CONFUSED":
            return "provide_clear_explanation"
        
        # Happy/positive
        if emotion == "HAPPY":
            return "continue_standard_approach"
        
        # Default
        return "continue_conversation"
    
    def _calculate_confidence(self, text: str) -> float:
        """
        Calculate confidence in sentiment analysis
        
        Based on text length and keyword matches
        """
        
        # Longer text = higher confidence
        word_count = len(text.split())
        
        if word_count < 3:
            return 0.5
        elif word_count < 10:
            return 0.7
        elif word_count < 20:
            return 0.85
        else:
            return 0.95
    
    def should_escalate_to_voice(self, sentiment_history: List[Dict]) -> bool:
        """
        Determine if conversation should escalate to voice
        
        Args:
            sentiment_history: List of recent sentiment analyses
            
        Returns:
            True if should escalate to voice call
        """
        
        if not sentiment_history:
            return False
        
        # Check last 3 messages
        recent = sentiment_history[-3:]
        
        # Count frustrated messages
        frustrated_count = sum(
            1 for s in recent 
            if s.get('emotion') == 'FRUSTRATED'
        )
        
        # Escalate if 2+ frustrated messages
        if frustrated_count >= 2:
            return True
        
        # Escalate if any critical urgency
        if any(s.get('urgency') == 'CRITICAL' for s in recent):
            return True
        
        # Escalate if critical objection
        if any(
            s.get('objection_severity') == 'CRITICAL' 
            for s in recent
        ):
            return True
        
        return False
    
    def get_persona_recommendation(self, sentiment: Dict) -> str:
        """
        Recommend conversation persona based on sentiment
        
        Returns:
            "standard", "persuasion", "empathetic", "technical"
        """
        
        if sentiment.get('objection_detected'):
            objection_type = sentiment.get('objection_type')
            
            if objection_type in ['price', 'not_interested']:
                return "persuasion"
            elif objection_type == 'cancel':
                return "empathetic"
        
        if sentiment.get('emotion') == 'CONFUSED':
            return "technical"
        
        if sentiment.get('emotion') in ['FRUSTRATED', 'WORRIED']:
            return "empathetic"
        
        return "standard"
