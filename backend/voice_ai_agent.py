"""
Voice AI Agent - v4.3
Real-time voice conversation with Twilio, Whisper, Groq, and ElevenLabs
Ultra-low latency (<300ms) with sentiment-aware responses
"""

import asyncio
import json
import base64
from typing import Dict, Optional, List
from datetime import datetime
import os

try:
    from twilio.rest import Client
    from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
    import websockets
    import requests  # For Hugging Face API
    from groq import AsyncGroq
    from elevenlabs import AsyncElevenLabs
    VOICE_AI_AVAILABLE = True
except ImportError:
    VOICE_AI_AVAILABLE = False
    print("⚠️  Voice AI libraries not available. Install: pip install twilio openai groq elevenlabs websockets")

from models import MemoryStore
from sentiment_analyzer import SentimentAnalyzer
from config import SystemConfig


class VoiceAIAgent:
    """
    Real-time voice conversation agent with agentic AI integration
    
    Features:
    - Twilio WebSocket streaming
    - Hugging Face Whisper STT (Inference API)
    - Groq Llama-3 LLM (ultra-low latency)
    - ElevenLabs TTS turbo-v2.5
    - Sentiment-aware responses
    - Objection handling
    """
    
    SYSTEM_MESSAGE = """You are a helpful vehicle maintenance assistant on a phone call.

CRITICAL RULES:
1. Keep responses under 25 words
2. Use conversational fillers: "uh-huh", "I see", "got it"
3. Mirror the customer's emotional state
4. Be empathetic and understanding
5. Speak naturally, like a human

RESPONSE FORMAT:
- Short, conversational sentences
- Use contractions (I'm, you're, it's)
- Ask one question at a time
- Acknowledge emotions

Example good responses:
- "I see, that sounds frustrating. Let me help you with that."
- "Uh-huh, got it. So your brakes are making noise?"
- "I understand. Safety is important. Let's get this fixed."

Example bad responses:
- Long technical explanations
- Multiple questions at once
- Robotic formal language
"""
    
    PERSUASION_PERSONA = """You are a VALUE-FOCUSED vehicle maintenance assistant.

When customer objects (price, not interested, cancel):
1. Acknowledge their concern empathetically
2. Emphasize SAFETY and VALUE
3. Offer flexible options
4. Keep it under 25 words

Example responses:
- "I totally get it. But brake failure could cost way more - and it's dangerous."
- "Fair point. How about we start with just the critical safety items?"
- "I hear you. What if we could break this into smaller payments?"
"""
    
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        
        # Robustly checking availability
        global VOICE_AI_AVAILABLE
        
        # Check environment variables
        self.twilio_sid = os.getenv("TWILIO_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.groq_key = os.getenv("GROQ_KEY")
        self.eleven_key = os.getenv("ELEVENLABS_KEY")
        
        # If essential keys are missing, disable Voice AI
        if not (self.twilio_sid and self.twilio_token and self.groq_key and self.eleven_key):
             print("   ⚠️  Voice AI keys missing in .env - failing over to simulation mode")
             VOICE_AI_AVAILABLE = False
        
        if not VOICE_AI_AVAILABLE:
            print("   ⚠️  Voice AI not available - using simulation mode")
            return
        
        try:
            # Initialize clients
            self.twilio_client = Client(self.twilio_sid, self.twilio_token)
            
            # Hugging Face STT Configuration
            self.hf_api_url = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
            self.hf_headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_KEY')}"}
            
            self.groq_client = AsyncGroq(api_key=self.groq_key)
            self.elevenlabs_client = AsyncElevenLabs(api_key=self.eleven_key)
            
        except Exception as e:
            print(f"   ⚠️  Voice AI initialization error: {str(e)}")
            VOICE_AI_AVAILABLE = False
            return
        
        # Components
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # State
        self.active_calls = {}  # call_sid -> call_state
        self.current_persona = "standard"
    
    async def initiate_call(self, customer_phone: str, diagnosis: Dict, 
                           customer_state: Dict) -> Dict:
        """
        Initiate outbound call to customer
        
        Args:
            customer_phone: Customer phone number
            diagnosis: Vehicle diagnosis information
            customer_state: Customer conversation state
            
        Returns:
            Call result with status
        """
        
        if not VOICE_AI_AVAILABLE:
            return self._simulate_call(customer_phone, diagnosis)
        
        try:
            # Create call
            call = self.twilio_client.calls.create(
                to=customer_phone,
                from_=os.getenv("TWILIO_PHONE"),
                url=f"{SystemConfig.VOICE_AI_CONFIG['webhook_base_url']}/voice/twiml",
                status_callback=f"{SystemConfig.VOICE_AI_CONFIG['webhook_base_url']}/voice/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed']
            )
            
            # Store call state
            self.active_calls[call.sid] = {
                "customer_phone": customer_phone,
                "diagnosis": diagnosis,
                "customer_state": customer_state,
                "started_at": datetime.now(),
                "conversation_history": [],
                "sentiment_history": []
            }
            
            print(f"   ✅ Voice call initiated: {call.sid}")
            
            return {
                "success": True,
                "call_sid": call.sid,
                "status": "initiated",
                "channel": "VOICE"
            }
            
        except Exception as e:
            print(f"   ❌ Call initiation failed: {str(e)[:60]}")
            return {
                "success": False,
                "error": str(e),
                "channel": "VOICE"
            }
    
    async def handle_call_stream(self, websocket, call_sid: str):
        """
        Handle real-time audio streaming via WebSocket
        
        This is the main conversation loop
        """
        
        call_state = self.active_calls.get(call_sid)
        if not call_state:
            print(f"   ⚠️  Unknown call: {call_sid}")
            return
        
        print(f"   🎙️  Starting voice stream for {call_sid}")
        
        # Audio buffer
        audio_buffer = bytearray()
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['event'] == 'connected':
                    print(f"   ✅ WebSocket connected: {call_sid}")
                
                elif data['event'] == 'start':
                    print(f"   🎬 Stream started: {call_sid}")
                    # Send initial greeting
                    await self._send_greeting(websocket, call_state)
                
                elif data['event'] == 'media':
                    # Receive audio chunk
                    payload = data['media']['payload']
                    audio_chunk = base64.b64decode(payload)
                    audio_buffer.extend(audio_chunk)
                    
                    # Process when we have enough audio (e.g., 1 second)
                    if len(audio_buffer) >= 8000:  # 8kHz * 1 second
                        await self._process_audio_chunk(
                            websocket, call_sid, bytes(audio_buffer)
                        )
                        audio_buffer.clear()
                
                elif data['event'] == 'stop':
                    print(f"   🛑 Stream stopped: {call_sid}")
                    break
        
        except Exception as e:
            print(f"   ❌ Stream error: {str(e)[:60]}")
        
        finally:
            # Cleanup
            if call_sid in self.active_calls:
                await self._end_call(call_sid)
    
    async def _send_greeting(self, websocket, call_state: Dict):
        """Send initial greeting based on diagnosis"""
        
        diagnosis = call_state['diagnosis']
        component = diagnosis.get('affected_component', 'vehicle')
        severity = diagnosis.get('severity', 'MEDIUM')
        
        if severity == 'CRITICAL':
            greeting = f"Hi, this is about your {component}. We detected a critical safety issue. Do you have a moment?"
        else:
            greeting = f"Hi, this is about your {component} maintenance. Got a quick minute?"
        
        await self._speak(websocket, greeting)
    
    async def _process_audio_chunk(self, websocket, call_sid: str, audio_data: bytes):
        """
        Process audio chunk through STT → LLM → TTS pipeline
        
        This is where the magic happens!
        """
        
        call_state = self.active_calls[call_sid]
        
        try:
            # 1. Speech-to-Text (Whisper) - ~100ms
            text = await self._transcribe_audio(audio_data)
            
            if not text or len(text.strip()) < 3:
                return  # Ignore silence or noise
            
            print(f"   👤 Customer: {text}")
            
            # 2. Sentiment Analysis - ~10ms
            sentiment = self.sentiment_analyzer.analyze(text)
            
            # Store in history
            call_state['conversation_history'].append({
                "speaker": "customer",
                "text": text,
                "sentiment": sentiment,
                "timestamp": datetime.now()
            })
            
            # 3. Check for objections
            if sentiment.get('objection_detected'):
                self._switch_persona("persuasion")
            
            # 4. Generate response (Groq Llama-3) - ~50-100ms
            response_text = await self._generate_response(text, sentiment, call_state)
            
            print(f"   🤖 Agent: {response_text}")
            
            # Store response
            call_state['conversation_history'].append({
                "speaker": "agent",
                "text": response_text,
                "timestamp": datetime.now()
            })
            
            # 5. Text-to-Speech (ElevenLabs) - ~100ms
            await self._speak(websocket, response_text)
            
        except Exception as e:
            print(f"   ❌ Processing error: {str(e)[:60]}")
            # Fallback response
            await self._speak(websocket, "I'm sorry, could you repeat that?")
    
    async def _transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio using Hugging Face Inference API (Whisper)
        
        Returns:
            Transcribed text
        """
        
        try:
            # Hugging Face Inference API call
            # Note: We run this synchronously in a thread executor to avoid blocking the async loop
            # since 'requests' is synchronous.
            
            def query_hf_api(data):
                response = requests.post(
                    self.hf_api_url, 
                    headers=self.hf_headers, 
                    data=data
                )
                return response.json()
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, query_hf_api, audio_data)
            
            # Hugging Face returns a dict with 'text' key for ASR models
            if isinstance(result, dict) and 'text' in result:
                return result['text']
            elif isinstance(result, dict) and 'error' in result:
                print(f"   ⚠️  Hugging Face API error: {result['error']}")
                return ""
            else:
                 # Fallback for some model outputs structure
                return str(result)
            
        except Exception as e:
            print(f"   ⚠️  STT error: {str(e)[:40]}")
            return ""
    
    async def _generate_response(self, customer_text: str, sentiment: Dict,
                                call_state: Dict) -> str:
        """
        Generate response using Groq Llama-3
        
        Ultra-low latency LLM inference
        """
        
        # Build context from conversation history
        conversation_context = self._build_conversation_context(call_state)
        
        # Select system message based on persona
        system_message = (
            self.PERSUASION_PERSONA if self.current_persona == "persuasion"
            else self.SYSTEM_MESSAGE
        )
        
        # Build prompt
        messages = [
            {"role": "system", "content": system_message},
            {"role": "system", "content": f"Customer emotion: {sentiment.get('emotion', 'NEUTRAL')}"},
            {"role": "system", "content": f"Diagnosis: {call_state['diagnosis']}"},
            {"role": "system", "content": f"Context: {conversation_context}"},
            {"role": "user", "content": customer_text}
        ]
        
        try:
            # Groq API call (ultra-fast!)
            response = await self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages,
                max_tokens=50,  # Keep responses short
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Ensure under 25 words
            words = response_text.split()
            if len(words) > 25:
                response_text = ' '.join(words[:25]) + "..."
            
            return response_text
            
        except Exception as e:
            print(f"   ⚠️  LLM error: {str(e)[:40]}")
            return "I understand. Let me help you with that."
    
    async def _speak(self, websocket, text: str):
        """
        Convert text to speech and stream to Twilio
        
        Uses ElevenLabs turbo-v2.5 for low latency
        """
        
        try:
            # Generate audio with ElevenLabs
            audio_stream = await self.elevenlabs_client.text_to_speech.convert_as_stream(
                voice_id=SystemConfig.VOICE_AI_CONFIG['tts_voice_id'],
                text=text,
                model_id="eleven_turbo_v2_5",
                output_format="ulaw_8000"  # Twilio format
            )
            
            # Stream audio chunks to Twilio
            async for audio_chunk in audio_stream:
                # Encode to base64
                payload = base64.b64encode(audio_chunk).decode('utf-8')
                
                # Send to Twilio
                await websocket.send(json.dumps({
                    "event": "media",
                    "streamSid": websocket.stream_sid,
                    "media": {
                        "payload": payload
                    }
                }))
            
        except Exception as e:
            print(f"   ⚠️  TTS error: {str(e)[:40]}")
    
    def _build_conversation_context(self, call_state: Dict) -> str:
        """Build context from conversation history"""
        
        history = call_state['conversation_history'][-3:]  # Last 3 exchanges
        
        context_parts = []
        for msg in history:
            speaker = "Customer" if msg['speaker'] == 'customer' else "You"
            context_parts.append(f"{speaker}: {msg['text']}")
        
        return " | ".join(context_parts) if context_parts else "New conversation"
    
    def _switch_persona(self, persona: str):
        """Switch conversation persona"""
        
        if persona != self.current_persona:
            print(f"   🔄 Switching persona: {self.current_persona} → {persona}")
            self.current_persona = persona
    
    async def _end_call(self, call_sid: str):
        """Clean up after call ends"""
        
        call_state = self.active_calls.get(call_sid)
        if not call_state:
            return
        
        # Calculate duration
        duration = (datetime.now() - call_state['started_at']).total_seconds()
        
        print(f"   📞 Call ended: {call_sid} ({duration:.1f}s)")
        
        # Store in memory
        # (Would integrate with memory_store here)
        
        # Cleanup
        del self.active_calls[call_sid]
    
    def _simulate_call(self, customer_phone: str, diagnosis: Dict) -> Dict:
        """Simulate call when APIs not available"""
        
        print(f"   🎭 Simulating voice call to {customer_phone}")
        print(f"   📋 Diagnosis: {diagnosis.get('affected_component')} - {diagnosis.get('severity')}")
        
        return {
            "success": True,
            "call_sid": f"SIM{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "simulated",
            "channel": "VOICE",
            "simulated": True
        }
    
    def get_call_status(self, call_sid: str) -> Optional[Dict]:
        """Get status of active call"""
        return self.active_calls.get(call_sid)
