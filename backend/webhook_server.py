"""
Webhook Server - v4.0
FastAPI server for receiving real-time customer responses
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import asyncio
from datetime import datetime

from config import LlamaModelClient
from event_system import EventBus, Event
from config import EventTypes
from customer_interpreter import CustomerResponseInterpreter

# Dashboard API layer (v6.0)
from api_server import api_router, ws_router, seed_all
from app_state import app_state


# Initialize FastAPI app
app = FastAPI(
    title="Predictive Maintenance Webhook Server",
    description="Receives customer responses from WhatsApp, SMS, Email",
    version="5.0"
)

# Mount dashboard REST + WebSocket routers
app.include_router(api_router)
app.include_router(ws_router)

# CORS — allow React dev server to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator (initialized on startup)
interpreter = None
event_bus = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on server startup"""
    global interpreter, event_bus
    
    print("\n" + "="*80)
    print("🚀 WEBHOOK SERVER STARTING")
    print("="*80 + "\n")
    
    # Create model client for interpreter
    interpreter_client = LlamaModelClient.create_customer_interpreter_client()
    
    # Create event bus
    event_bus = EventBus()
    
    # Create interpreter
    interpreter = CustomerResponseInterpreter(interpreter_client)
    
    # Seed dashboard with mock data so the frontend has something to show
    seed_all()
    print(f"✅ Dashboard seeded: {len(app_state.vehicles)} vehicles, "
          f"{len(app_state.bookings)} bookings, {len(app_state.conversations)} conversations")

    # Start background AI diagnosis loop (re-scans every 30 min)
    try:
        from diagnosis_orchestrator import background_diagnosis_loop
        asyncio.create_task(background_diagnosis_loop(interval_minutes=30))
        print("✅ Background diagnosis loop started (30-min interval)")
    except Exception as e:
        print(f"⚠️  Background diagnosis loop not started: {e}")

    print("✅ Webhook server ready to receive customer responses")
    print("="*80 + "\n")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Predictive Maintenance Webhook Server",
        "version": "4.0",
        "endpoints": {
            "whatsapp": "/webhook/whatsapp",
            "sms": "/webhook/sms",
            "email": "/webhook/email",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "interpreter_ready": interpreter is not None,
        "event_bus_ready": event_bus is not None
    }


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    tenant_id: Optional[str] = Form(None)
):
    """
    Handle incoming WhatsApp messages from Twilio
    
    Twilio WhatsApp webhook format:
    - From: whatsapp:+1234567890
    - Body: Message text
    - MessageSid: Unique message ID
    """
    
    print(f"\n📱 WHATSAPP WEBHOOK RECEIVED")
    print(f"   From: {From}")
    print(f"   Message: {Body[:100]}...")
    
    try:
        # Extract tenant_id from message or database lookup
        # In production, you'd lookup by phone number
        if not tenant_id:
            # Try to extract from message
            import re
            match = re.search(r'VEH\d{3}', Body)
            tenant_id = match.group(0) if match else "UNKNOWN"
        
        if tenant_id == "UNKNOWN":
            return JSONResponse(
                status_code=400,
                content={"error": "Could not identify vehicle/tenant"}
            )
        
        # Interpret customer response
        interpretation = await interpreter.interpret(
            raw_message=Body,
            channel="WHATSAPP",
            context={"from": From, "message_sid": MessageSid}
        )
        
        print(f"   Interpreted: {interpretation.get('customer_response')}")
        print(f"   Sentiment: {interpretation.get('sentiment')}")
        print(f"   Confidence: {interpretation.get('confidence', 0.0):.2f}")
        
        # Publish event to event bus
        event = Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={
                "interpretation": interpretation,
                "channel": "WHATSAPP",
                "from": From,
                "message_sid": MessageSid
            },
            priority="HIGH"
        )
        
        await event_bus.publish(event)
        
        print(f"   ✅ Event published for tenant {tenant_id}")
        
        # Return TwiML response (optional - for auto-reply)
        return JSONResponse(content={
            "status": "processed",
            "tenant_id": tenant_id,
            "interpretation": interpretation.get('customer_response'),
            "event_published": True
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/sms")
async def sms_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    tenant_id: Optional[str] = Form(None)
):
    """
    Handle incoming SMS messages from Twilio
    
    Twilio SMS webhook format:
    - From: +1234567890
    - Body: Message text
    - MessageSid: Unique message ID
    """
    
    print(f"\n📱 SMS WEBHOOK RECEIVED")
    print(f"   From: {From}")
    print(f"   Message: {Body[:100]}...")
    
    try:
        # Extract tenant_id
        if not tenant_id:
            import re
            match = re.search(r'VEH\d{3}', Body)
            tenant_id = match.group(0) if match else "UNKNOWN"
        
        if tenant_id == "UNKNOWN":
            return JSONResponse(
                status_code=400,
                content={"error": "Could not identify vehicle/tenant"}
            )
        
        # Interpret response
        interpretation = await interpreter.interpret(
            raw_message=Body,
            channel="SMS",
            context={"from": From, "message_sid": MessageSid}
        )
        
        print(f"   Interpreted: {interpretation.get('customer_response')}")
        
        # Publish event
        event = Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={
                "interpretation": interpretation,
                "channel": "SMS",
                "from": From
            },
            priority="HIGH"
        )
        
        await event_bus.publish(event)
        
        print(f"   ✅ Event published for tenant {tenant_id}")
        
        return JSONResponse(content={
            "status": "processed",
            "tenant_id": tenant_id,
            "interpretation": interpretation.get('customer_response')
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/email")
async def email_webhook(request: Request):
    """
    Handle incoming email responses
    
    This would integrate with services like:
    - SendGrid Inbound Parse
    - Mailgun Routes
    - AWS SES
    
    Expected JSON format:
    {
        "from": "customer@example.com",
        "subject": "Re: Maintenance for VEH001",
        "body": "Yes, I can bring it in tomorrow",
        "tenant_id": "VEH001"
    }
    """
    
    print(f"\n📧 EMAIL WEBHOOK RECEIVED")
    
    try:
        data = await request.json()
        
        from_email = data.get('from', '')
        subject = data.get('subject', '')
        body = data.get('body', '')
        tenant_id = data.get('tenant_id')
        
        print(f"   From: {from_email}")
        print(f"   Subject: {subject}")
        
        # Extract tenant_id from subject if not provided
        if not tenant_id:
            import re
            match = re.search(r'VEH\d{3}', subject + ' ' + body)
            tenant_id = match.group(0) if match else "UNKNOWN"
        
        if tenant_id == "UNKNOWN":
            return JSONResponse(
                status_code=400,
                content={"error": "Could not identify vehicle/tenant"}
            )
        
        # Interpret response
        interpretation = await interpreter.interpret(
            raw_message=body,
            channel="EMAIL",
            context={"from": from_email, "subject": subject}
        )
        
        print(f"   Interpreted: {interpretation.get('customer_response')}")
        
        # Publish event
        event = Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={
                "interpretation": interpretation,
                "channel": "EMAIL",
                "from": from_email
            },
            priority="MEDIUM"
        )
        
        await event_bus.publish(event)
        
        print(f"   ✅ Event published for tenant {tenant_id}")
        
        return JSONResponse(content={
            "status": "processed",
            "tenant_id": tenant_id,
            "interpretation": interpretation.get('customer_response')
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/simulate-response")
async def simulate_customer_response(
    tenant_id: str = Form(...),
    message: str = Form(...),
    channel: str = Form("WHATSAPP")
):
    """
    Test endpoint to simulate customer responses
    Useful for testing without real Twilio integration
    """
    
    print(f"\n🧪 TEST: Simulating customer response")
    print(f"   Tenant: {tenant_id}")
    print(f"   Channel: {channel}")
    print(f"   Message: {message}")
    
    try:
        # Interpret response
        interpretation = await interpreter.interpret(
            raw_message=message,
            channel=channel,
            context={"test": True}
        )
        
        # Publish event
        event = Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={
                "interpretation": interpretation,
                "channel": channel,
                "test": True
            },
            priority="MEDIUM"
        )
        
        await event_bus.publish(event)
        
        return JSONResponse(content={
            "status": "test_processed",
            "interpretation": interpretation,
            "event_published": True
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("🌐 STARTING WEBHOOK SERVER")
    print("="*80)
    print("\nEndpoints:")
    print("  - WhatsApp: http://localhost:8001/webhook/whatsapp")
    print("  - SMS:      http://localhost:8001/webhook/sms")
    print("  - Email:    http://localhost:8001/webhook/email")
    print("  - Test:     http://localhost:8001/test/simulate-response")
    print("  - Health:   http://localhost:8001/health")
    print("\nStarting server...\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )