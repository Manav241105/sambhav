"""
Voice API - v4.3
FastAPI server for Twilio webhooks and WebSocket handling
Production-ready with error handling and logging
"""

from fastapi import FastAPI, WebSocket, Request, HTTPException, WebSocketDisconnect
from fastapi.responses import Response, PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.request_validator import RequestValidator
import asyncio
import os
from typing import Dict
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from voice_ai_agent import VoiceAIAgent
from omnichannel_orchestrator import OmnichannelOrchestrator
from models import MemoryStore
from communication_service import CommunicationService
from config import SystemConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Voice AI & Omnichannel API",
    description="Production-ready Voice AI with Twilio integration",
    version="4.3"
)

# Initialize components
memory_store = MemoryStore()
communication_service = CommunicationService()
omnichannel = OmnichannelOrchestrator(memory_store, communication_service)
voice_ai = VoiceAIAgent(memory_store)

# Twilio validator (for security)
# Use dummy token if missing to prevent crash in simulation mode
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
if not twilio_auth_token:
    logger.warning("⚠️ TWILIO_AUTH_TOKEN missing - Webhook validation will fail or be disabled")
    # Use dummy value for initialization, validation checks should handle None
    twilio_validator = RequestValidator("dummy_token_for_simulation")
else:
    twilio_validator = RequestValidator(twilio_auth_token)


# ============================================================================
# VOICE ENDPOINTS
# ============================================================================

@app.post("/voice/incoming")
async def handle_incoming_call(request: Request):
    """
    Handle incoming voice call from Twilio
    Returns TwiML to connect to WebSocket stream
    """
    
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    from_number = form_data.get("From")
    to_number = form_data.get("To")
    
    logger.info(f"Incoming call: {call_sid} from {from_number}")
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Initial greeting
    response.say(
        "Hello! Thank you for calling. Connecting you now.",
        voice='Polly.Joanna'
    )
    
    # Connect to WebSocket stream
    connect = Connect()
    stream = Stream(
        url=f"wss://{request.headers.get('host')}/voice/stream/{call_sid}"
    )
    connect.append(stream)
    response.append(connect)
    
    return Response(content=str(response), media_type="application/xml")


@app.post("/voice/twiml")
async def voice_twiml(request: Request):
    """
    Generate TwiML for outbound calls
    """
    
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    
    logger.info(f"Generating TwiML for call: {call_sid}")
    
    response = VoiceResponse()
    
    # Connect to WebSocket
    connect = Connect()
    stream = Stream(
        url=f"wss://{request.headers.get('host')}/voice/stream/{call_sid}"
    )
    connect.append(stream)
    response.append(connect)
    
    return Response(content=str(response), media_type="application/xml")


@app.websocket("/voice/stream/{call_sid}")
async def voice_stream(websocket: WebSocket, call_sid: str):
    """
    WebSocket endpoint for real-time audio streaming
    
    This is where the Voice AI magic happens!
    """
    
    await websocket.accept()
    logger.info(f"WebSocket connected: {call_sid}")
    
    try:
        # Handle the call stream
        await voice_ai.handle_call_stream(websocket, call_sid)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {call_sid}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        logger.info(f"WebSocket closed: {call_sid}")


@app.post("/voice/status")
async def voice_status(request: Request):
    """
    Receive call status updates from Twilio
    """
    
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    
    logger.info(f"Call status update: {call_sid} - {call_status}")
    
    # Update call state
    call_state = voice_ai.get_call_status(call_sid)
    if call_state:
        call_state['status'] = call_status
    
    return {"status": "ok"}


# ============================================================================
# SMS ENDPOINTS
# ============================================================================

@app.post("/sms/incoming")
async def handle_incoming_sms(request: Request):
    """
    Handle incoming SMS from Twilio
    Analyzes sentiment and may escalate to voice
    """
    
    form_data = await request.form()
    from_number = form_data.get("From")
    message_body = form_data.get("Body")
    message_sid = form_data.get("MessageSid")
    
    logger.info(f"Incoming SMS from {from_number}: {message_body}")
    
    # Process through omnichannel orchestrator
    result = omnichannel.process_incoming_message(
        customer_id=from_number,
        channel="SMS",
        message=message_body
    )
    
    sentiment = result['sentiment']
    should_escalate = result['should_escalate']
    
    logger.info(f"Sentiment: {sentiment.get('emotion')} - Escalate: {should_escalate}")
    
    # If should escalate to voice
    if should_escalate:
        # Initiate voice call
        customer_state = result['customer_state']
        
        # Create diagnosis from context (simplified)
        diagnosis = {
            "severity": "HIGH",
            "affected_component": "Communication",
            "failure_probability": 0.8
        }
        
        call_result = await voice_ai.initiate_call(
            from_number,
            diagnosis,
            customer_state.to_dict()
        )
        
        # Send SMS notification
        response_message = "I understand your frustration. I'm calling you now to help resolve this quickly."
    
    else:
        # Generate text response
        response_message = await _generate_sms_response(message_body, sentiment)
    
    # Send SMS response
    response = VoiceResponse()
    response.message(response_message)
    
    return Response(content=str(response), media_type="application/xml")


# ============================================================================
# WHATSAPP ENDPOINTS
# ============================================================================

@app.post("/whatsapp/incoming")
async def handle_incoming_whatsapp(request: Request):
    """
    Handle incoming WhatsApp message from Twilio
    """
    
    form_data = await request.form()
    from_number = form_data.get("From")  # Format: whatsapp:+1234567890
    message_body = form_data.get("Body")
    
    # Remove 'whatsapp:' prefix
    customer_id = from_number.replace("whatsapp:", "")
    
    logger.info(f"Incoming WhatsApp from {customer_id}: {message_body}")
    
    # Process through omnichannel
    result = omnichannel.process_incoming_message(
        customer_id=customer_id,
        channel="WHATSAPP",
        message=message_body
    )
    
    sentiment = result['sentiment']
    should_escalate = result['should_escalate']
    
    # If should escalate to voice
    if should_escalate:
        customer_state = result['customer_state']
        
        diagnosis = {
            "severity": "HIGH",
            "affected_component": "Communication"
        }
        
        # Initiate voice call
        await voice_ai.initiate_call(
            customer_id,
            diagnosis,
            customer_state.to_dict()
        )
        
        response_message = "I see you're frustrated. I'm calling you right now to help! 📞"
    
    else:
        response_message = await _generate_whatsapp_response(message_body, sentiment)
    
    # Send WhatsApp response
    response = VoiceResponse()
    response.message(response_message)
    
    return Response(content=str(response), media_type="application/xml")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _generate_sms_response(message: str, sentiment: Dict) -> str:
    """Generate appropriate SMS response based on sentiment"""
    
    emotion = sentiment.get('emotion', 'NEUTRAL')
    objection_type = sentiment.get('objection_type')
    
    if objection_type == 'price':
        return "I understand cost is a concern. Safety is priceless though. Can we discuss flexible payment options?"
    
    elif objection_type == 'not_interested':
        return "No problem! Just wanted to keep you informed about your vehicle's health. Stay safe!"
    
    elif emotion == 'FRUSTRATED':
        return "I'm sorry for the frustration. Let me help you right away. Calling you now."
    
    elif emotion == 'CONFUSED':
        return "Let me clarify! Your vehicle needs maintenance. I can explain everything in detail if you'd like."
    
    else:
        return "Thanks for your message! How can I help you today?"


async def _generate_whatsapp_response(message: str, sentiment: Dict) -> str:
    """Generate WhatsApp response with emojis"""
    
    emotion = sentiment.get('emotion', 'NEUTRAL')
    
    if emotion == 'FRUSTRATED':
        return "I'm so sorry you're frustrated 😔 Let me call you right now to fix this! 📞"
    
    elif emotion == 'HAPPY':
        return "Great to hear! 😊 How can I help you today?"
    
    elif emotion == 'CONFUSED':
        return "No worries! Let me explain 💡 What would you like to know?"
    
    else:
        return "Thanks for reaching out! 👋 How can I assist you?"


# ============================================================================
# HEALTH CHECK & INFO
# ============================================================================

@app.get("/")
async def root():
    """API info"""
    return {
        "service": "Voice AI & Omnichannel API",
        "version": "4.3",
        "status": "operational",
        "features": [
            "Real-time voice calls",
            "Sentiment analysis",
            "Omnichannel orchestration",
            "Automatic escalation"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "voice_ai": "operational",
        "omnichannel": "operational"
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    
    active_calls = len(voice_ai.active_calls)
    active_customers = len(omnichannel.customer_states)
    
    return {
        "active_calls": active_calls,
        "active_customers": active_customers,
        "memory_store_size": len(memory_store.customer_memories)
    }


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Voice AI API starting up...")
    logger.info("✅ Voice AI initialized")
    logger.info("✅ Omnichannel orchestrator ready")
    logger.info("🎙️  Ready to handle calls!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Voice AI API shutting down...")
    
    # Save memory store
    memory_store.save_to_file("memory_store_v43.json")
    logger.info("💾 Memory saved")


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "voice_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
