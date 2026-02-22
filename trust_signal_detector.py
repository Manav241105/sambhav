"""
Trust Signal Detector - Enterprise Conversation Intelligence
Detects trust signals and trust-eroding signals in customer messages.
Tracks dynamic trust score across the conversation.
"""

from typing import Dict, List, Tuple


class TrustSignalDetector:
    """
    Detects trust-building opportunities and trust-eroding signals.
    Provides guidance on how to respond to each trust signal.
    """

    # Trust-building signals (customer is opening up / engaging positively)
    TRUST_POSITIVE_SIGNALS: List[Tuple[List[str], float, str]] = [
        (["thank you", "thanks", "appreciate", "helpful", "good point", "makes sense",
          "i see", "i understand", "that makes sense", "fair enough", "good to know"],
         0.1, "ACKNOWLEDGMENT"),
        (["question", "tell me more", "explain", "how does", "what exactly",
          "i want to understand", "help me understand"],
         0.05, "CURIOSITY"),
        (["okay", "alright", "fine", "sure", "sounds reasonable"],
         0.05, "SOFT_AGREEMENT"),
    ]

    # Trust-eroding signals (customer is becoming defensive / suspicious)
    TRUST_NEGATIVE_SIGNALS: List[Tuple[List[str], float, str]] = [
        (["upselling", "upsell", "scam", "money grab", "just want money", "trying to sell",
          "rip off", "overcharging", "not trustworthy", "don't trust"],
         -0.3, "DISTRUST_ACCUSATION"),
        (["already told you", "you keep saying", "same thing", "repeating yourself",
          "you said that already", "heard this before"],
         -0.2, "REPETITION_FRUSTRATION"),
        (["leave me alone", "stop calling", "annoying", "harassment", "bothering me"],
         -0.4, "ANNOYANCE"),
        (["not interested", "definitely not", "absolutely not", "no way"],
         -0.15, "STRONG_REFUSAL"),
    ]

    # Trust-building response guidance per signal type
    TRUST_RESPONSE_GUIDANCE: Dict[str, str] = {
        "DISTRUST_ACCUSATION": (
            "Customer suspects upselling. CRITICAL: Do NOT be defensive. "
            "Acknowledge their concern directly. Offer to share the raw diagnostic data. "
            "Invite them to have any mechanic verify the findings. "
            "Express that their safety — not a sale — is the priority."
        ),
        "REPETITION_FRUSTRATION": (
            "Customer is frustrated by repetition. CRITICAL: Introduce completely NEW information. "
            "Apologize briefly for repeating. Pivot to a different angle or new data point. "
            "Ask what specific information would be most helpful to them."
        ),
        "ANNOYANCE": (
            "Customer is feeling pressured. CRITICAL: Back off immediately. "
            "Apologize for any inconvenience. Offer to stop contact if they prefer. "
            "Leave safety information and exit gracefully."
        ),
        "STRONG_REFUSAL": (
            "Customer is firmly declining. Respect their decision. "
            "Provide brief safety precautions. Leave door open for future contact. "
            "Exit with warmth and professionalism."
        ),
        "ACKNOWLEDGMENT": (
            "Customer is engaging positively. Build on this momentum. "
            "Provide the next most relevant piece of information. "
            "Ask a gentle question to keep dialogue flowing."
        ),
        "CURIOSITY": (
            "Customer is curious and asking questions. This is excellent engagement. "
            "Answer their question thoroughly with specific data. "
            "This is a trust-building moment — be transparent and detailed."
        ),
        "SOFT_AGREEMENT": (
            "Customer is showing mild agreement. Don't rush to close. "
            "Provide one more piece of value before gently suggesting next steps."
        ),
    }

    def analyze(self, user_reply: str) -> Dict:
        """
        Analyze customer message for trust signals.
        Returns trust delta, detected signals, and response guidance.
        """
        lower_reply = user_reply.lower()
        detected_positive = []
        detected_negative = []
        trust_delta = 0.0
        guidance_list = []

        for keywords, delta, signal_type in self.TRUST_POSITIVE_SIGNALS:
            if any(kw in lower_reply for kw in keywords):
                detected_positive.append(signal_type)
                trust_delta += delta
                if signal_type in self.TRUST_RESPONSE_GUIDANCE:
                    guidance_list.append(self.TRUST_RESPONSE_GUIDANCE[signal_type])

        for keywords, delta, signal_type in self.TRUST_NEGATIVE_SIGNALS:
            if any(kw in lower_reply for kw in keywords):
                detected_negative.append(signal_type)
                trust_delta += delta  # delta is negative
                if signal_type in self.TRUST_RESPONSE_GUIDANCE:
                    guidance_list.append(self.TRUST_RESPONSE_GUIDANCE[signal_type])

        # Primary signal (most impactful)
        primary_signal = None
        if detected_negative:
            primary_signal = detected_negative[0]
        elif detected_positive:
            primary_signal = detected_positive[0]

        return {
            "trust_delta": round(trust_delta, 2),
            "positive_signals": detected_positive,
            "negative_signals": detected_negative,
            "primary_signal": primary_signal,
            "has_trust_issue": len(detected_negative) > 0,
            "is_engaging": len(detected_positive) > 0,
            "guidance": guidance_list[0] if guidance_list else None,
        }
