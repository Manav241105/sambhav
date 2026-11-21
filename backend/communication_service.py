"""
Communication Service - v4.1
Multi-channel communication with escalation and priority handling
"""

from typing import Dict, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from config import SystemConfig, CommunicationChannel
from core.settings import is_configured


class CommunicationResult:
    """Result of communication attempt"""
    
    def __init__(self, success: bool, message_id: Optional[str] = None,
                 error: Optional[str] = None, channel: str = "",
                 metadata: Dict = None):
        self.success = success
        self.message_id = message_id
        self.error = error
        self.channel = channel
        self.timestamp = datetime.now().isoformat()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "message_id": self.message_id,
            "error": self.error,
            "channel": self.channel,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class CommunicationProvider(ABC):
    """Abstract base class for communication providers"""
    
    @abstractmethod
    async def send_message(self, to: str, message: str, 
                          subject: Optional[str] = None,
                          priority: str = "NORMAL",
                          metadata: Dict = None) -> CommunicationResult:
        """Send message via this provider"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        pass


class EmailProvider(CommunicationProvider):
    """Email communication provider with priority support"""
    
    def __init__(self):
        self.config = SystemConfig.EMAIL_CONFIG
        self.smtp_server = self.config.get("smtp_server")
        self.smtp_port = self.config.get("smtp_port")
        self.from_email = self.config.get("from_email")
        self.password = self.config.get("password")
    
    async def send_message(self, to: str, message: str, 
                          subject: Optional[str] = None,
                          priority: str = "NORMAL",
                          metadata: Dict = None) -> CommunicationResult:
        """Send email with priority and escalation flags"""
        
        if not self.is_configured():
            return CommunicationResult(
                success=False,
                error="Email not configured",
                channel=CommunicationChannel.EMAIL
            )
        
        try:
            # Add priority indicator to subject
            priority_prefix = ""
            if priority in ["P0", "CRITICAL"]:
                priority_prefix = "🚨 URGENT - "
            elif priority in ["P1", "HIGH"]:
                priority_prefix = "⚠️ IMPORTANT - "
            
            full_subject = f"{priority_prefix}{subject or 'Vehicle Maintenance Notification'}"
            
            # Simulated email sending
            print(f"\n📧 EMAIL SENT")
            print(f"   To: {to}")
            print(f"   Priority: {priority}")
            print(f"   Subject: {full_subject}")
            print(f"   Message: {message[:100]}...")
            
            if metadata:
                cycle = metadata.get('cycle_number', 1)
                escalated = metadata.get('escalated', False)
                if cycle > 1:
                    print(f"   Cycle: {cycle}")
                if escalated:
                    print(f"   🚨 ESCALATED")
            
            # In production, use smtplib with priority headers:
            # import smtplib
            # from email.mime.text import MIMEText
            # 
            # msg = MIMEText(message)
            # msg['Subject'] = full_subject
            # msg['From'] = self.from_email
            # msg['To'] = to
            # msg['X-Priority'] = '1' if priority in ['P0', 'CRITICAL'] else '3'
            # msg['Importance'] = 'high' if priority in ['P0', 'P1'] else 'normal'
            # 
            # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            #     server.starttls()
            #     server.login(self.from_email, self.password)
            #     server.send_message(msg)
            
            message_id = f"email_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channel=CommunicationChannel.EMAIL,
                metadata=metadata
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                error=str(e),
                channel=CommunicationChannel.EMAIL
            )
    
    def is_configured(self) -> bool:
        """Check if email is configured"""
        return all(map(is_configured, (self.smtp_server, self.from_email, self.password)))


class WhatsAppProvider(CommunicationProvider):
    """WhatsApp communication provider with media support"""
    
    def __init__(self):
        self.config = SystemConfig.WHATSAPP_CONFIG
        self.api_key = self.config.get("api_key")
        self.from_number = self.config.get("from_number")
    
    async def send_message(self, to: str, message: str, 
                          subject: Optional[str] = None,
                          priority: str = "NORMAL",
                          metadata: Dict = None) -> CommunicationResult:
        """Send WhatsApp message with priority emojis"""
        
        if not self.is_configured():
            return CommunicationResult(
                success=False,
                error="WhatsApp not configured",
                channel=CommunicationChannel.WHATSAPP
            )
        
        try:
            # Add priority emoji to message
            priority_emoji = ""
            if priority in ["P0", "CRITICAL"]:
                priority_emoji = "🚨 URGENT: "
            elif priority in ["P1", "HIGH"]:
                priority_emoji = "⚠️ IMPORTANT: "
            
            full_message = f"{priority_emoji}{message}"
            
            # Simulated WhatsApp sending
            print(f"\n💬 WHATSAPP SENT")
            print(f"   To: {to}")
            print(f"   Priority: {priority}")
            print(f"   Message: {full_message[:100]}...")
            
            if metadata:
                cycle = metadata.get('cycle_number', 1)
                escalated = metadata.get('escalated', False)
                if cycle > 1:
                    print(f"   Cycle: {cycle}")
                if escalated:
                    print(f"   🚨 ESCALATED")
            
            # In production, use Twilio WhatsApp API:
            # from twilio.rest import Client
            # 
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     from_=f'whatsapp:{self.from_number}',
            #     body=full_message,
            #     to=f'whatsapp:{to}'
            # )
            
            message_id = f"whatsapp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channel=CommunicationChannel.WHATSAPP,
                metadata=metadata
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                error=str(e),
                channel=CommunicationChannel.WHATSAPP
            )
    
    def is_configured(self) -> bool:
        """Check if WhatsApp is configured"""
        return all(map(is_configured, (self.api_key, self.from_number)))


class SMSProvider(CommunicationProvider):
    """SMS communication provider with character optimization"""
    
    def __init__(self):
        self.config = SystemConfig.TWILIO_CONFIG
        self.account_sid = self.config.get("account_sid")
        self.auth_token = self.config.get("auth_token")
        self.from_number = self.config.get("from_number")
    
    async def send_message(self, to: str, message: str, 
                          subject: Optional[str] = None,
                          priority: str = "NORMAL",
                          metadata: Dict = None) -> CommunicationResult:
        """Send SMS with character limit awareness"""
        
        if not self.is_configured():
            return CommunicationResult(
                success=False,
                error="SMS/Twilio not configured",
                channel=CommunicationChannel.SMS
            )
        
        try:
            # Truncate to 160 characters for single SMS
            # Add priority prefix
            priority_prefix = ""
            if priority in ["P0", "CRITICAL"]:
                priority_prefix = "URGENT: "
            elif priority in ["P1", "HIGH"]:
                priority_prefix = "IMPORTANT: "
            
            max_len = 160 - len(priority_prefix)
            truncated_message = message[:max_len]
            if len(message) > max_len:
                truncated_message = message[:max_len-3] + "..."
            
            full_message = f"{priority_prefix}{truncated_message}"
            
            # Simulated SMS sending
            print(f"\n📱 SMS SENT")
            print(f"   To: {to}")
            print(f"   Priority: {priority}")
            print(f"   Message ({len(full_message)} chars): {full_message[:80]}...")
            
            if metadata:
                cycle = metadata.get('cycle_number', 1)
                if cycle > 1:
                    print(f"   Cycle: {cycle}")
            
            # In production, use Twilio:
            # from twilio.rest import Client
            # 
            # client = Client(self.account_sid, self.auth_token)
            # message = client.messages.create(
            #     body=full_message,
            #     from_=self.from_number,
            #     to=to
            # )
            
            message_id = f"sms_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channel=CommunicationChannel.SMS,
                metadata=metadata
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                error=str(e),
                channel=CommunicationChannel.SMS
            )
    
    def is_configured(self) -> bool:
        """Check if SMS is configured"""
        return all(map(is_configured, (self.account_sid, self.auth_token, self.from_number)))


class VoiceCallProvider(CommunicationProvider):
    """Voice call provider with TTS and priority handling"""
    
    def __init__(self):
        self.config = SystemConfig.TWILIO_CONFIG
        self.account_sid = self.config.get("account_sid")
        self.auth_token = self.config.get("auth_token")
        self.from_number = self.config.get("from_number")
    
    async def send_message(self, to: str, message: str, 
                          subject: Optional[str] = None,
                          priority: str = "NORMAL",
                          metadata: Dict = None) -> CommunicationResult:
        """Place voice call with TTS and urgency in tone"""
        
        if not self.is_configured():
            return CommunicationResult(
                success=False,
                error="Voice call not configured",
                channel=CommunicationChannel.VOICE_CALL
            )
        
        try:
            # Add urgency phrasing for critical calls
            if priority in ["P0", "CRITICAL"]:
                tts_message = f"This is an urgent safety alert. {message}"
                voice_speed = "slow"  # Slower for emphasis
            elif priority in ["P1", "HIGH"]:
                tts_message = f"This is an important message. {message}"
                voice_speed = "medium"
            else:
                tts_message = message
                voice_speed = "medium"
            
            # Simulated voice call
            print(f"\n📞 VOICE CALL PLACED")
            print(f"   To: {to}")
            print(f"   Priority: {priority}")
            print(f"   TTS Speed: {voice_speed}")
            print(f"   TTS Message: {tts_message[:100]}...")
            
            if metadata:
                cycle = metadata.get('cycle_number', 1)
                escalated = metadata.get('escalated', False)
                if cycle > 1:
                    print(f"   Cycle: {cycle}")
                if escalated:
                    print(f"   🚨 ESCALATED CALL")
            
            # In production, use Twilio Voice API with TTS:
            # from twilio.rest import Client
            # from twilio.twiml.voice_response import VoiceResponse
            # 
            # client = Client(self.account_sid, self.auth_token)
            # 
            # response = VoiceResponse()
            # response.say(
            #     tts_message, 
            #     voice='alice',
            #     language='en-US'
            # )
            # 
            # # For critical calls, repeat the message
            # if priority in ['P0', 'CRITICAL']:
            #     response.pause(length=1)
            #     response.say(tts_message, voice='alice')
            # 
            # call = client.calls.create(
            #     twiml=str(response),
            #     to=to,
            #     from_=self.from_number
            # )
            
            message_id = f"call_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channel=CommunicationChannel.VOICE_CALL,
                metadata=metadata
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                error=str(e),
                channel=CommunicationChannel.VOICE_CALL
            )
    
    def is_configured(self) -> bool:
        """Check if voice call is configured"""
        return all(map(is_configured, (self.account_sid, self.auth_token, self.from_number)))


class CommunicationService:
    """
    Unified communication service with priority and escalation support
    Routes messages to appropriate channel provider
    """
    
    def __init__(self):
        self.providers = {
            CommunicationChannel.EMAIL: EmailProvider(),
            CommunicationChannel.WHATSAPP: WhatsAppProvider(),
            CommunicationChannel.SMS: SMSProvider(),
            CommunicationChannel.VOICE_CALL: VoiceCallProvider()
        }
    
    async def send(self, channel: str, to: str, message: str,
                  subject: Optional[str] = None,
                  priority: str = "NORMAL",
                  metadata: Dict = None) -> CommunicationResult:
        """Send message via specified channel with priority"""
        
        if channel not in self.providers:
            return CommunicationResult(
                success=False,
                error=f"Unknown channel: {channel}",
                channel=channel
            )
        
        provider = self.providers[channel]
        
        if not provider.is_configured():
            # Fallback to simulation mode
            print(f"\n⚠️  {channel} not configured, using SIMULATION mode")
            return await self._simulate_send(channel, to, message, subject, priority, metadata)
        
        return await provider.send_message(to, message, subject, priority, metadata)
    
    async def _simulate_send(self, channel: str, to: str, message: str,
                            subject: Optional[str], priority: str,
                            metadata: Dict = None) -> CommunicationResult:
        """Simulate message sending with priority indicators"""
        
        channel_icons = {
            CommunicationChannel.EMAIL: "📧",
            CommunicationChannel.WHATSAPP: "💬",
            CommunicationChannel.SMS: "📱",
            CommunicationChannel.VOICE_CALL: "📞"
        }
        
        icon = channel_icons.get(channel, "📨")
        
        # Add priority indicator
        priority_icon = ""
        if priority in ["P0", "CRITICAL"]:
            priority_icon = "🚨 "
        elif priority in ["P1", "HIGH"]:
            priority_icon = "⚠️ "
        
        print(f"\n{priority_icon}{icon} SIMULATED {channel}")
        print(f"   To: {to}")
        print(f"   Priority: {priority}")
        if subject:
            print(f"   Subject: {subject}")
        print(f"   Message: {message[:150]}...")
        
        if metadata:
            cycle = metadata.get('cycle_number', 1)
            escalated = metadata.get('escalated', False)
            if cycle > 1:
                print(f"   Cycle: {cycle}")
            if escalated:
                print(f"   🚨 ESCALATED")
        
        message_id = f"sim_{channel.lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return CommunicationResult(
            success=True,
            message_id=message_id,
            channel=channel,
            metadata=metadata
        )
    
    def get_available_channels(self) -> list:
        """Get list of configured channels"""
        return [
            channel for channel, provider in self.providers.items()
            if provider.is_configured()
        ]
    
    def get_channel_status(self) -> Dict[str, bool]:
        """Get configuration status of all channels"""
        return {
            channel: provider.is_configured()
            for channel, provider in self.providers.items()
        }