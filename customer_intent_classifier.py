"""
Customer Intent Classifier - Enterprise Conversation Intelligence v2.0
Classifies customer intent from their message using keyword + semantic pattern matching.

Intent Categories (14 total):
  LOGISTICS_BLOCKER             → Customer unavailable due to travel, schedule, location
  SKEPTICISM                    → Customer doubts the diagnosis or severity
  COST_CONCERN                  → Customer worried about price / affordability
  SECOND_OPINION_SEEKING        → Customer wants to verify with another mechanic
  INFO_GATHERING                → Customer asking questions to understand better
  READY_TO_BOOK                 → Customer showing positive booking signals
  SOFT_DECLINE                  → Customer hesitating, not fully refusing
  HARD_DECLINE                  → Customer explicitly refusing service
  PAST_SERVICE_FAILURE          → Customer referencing a past bad service experience [NEW]
  TRUST_DAMAGE_EVENT            → Customer expressing loss of trust [NEW]
  SERVICE_DELAY_TRAUMA          → Customer referencing past service delays [NEW]
  REPAIR_QUALITY_DOUBT          → Customer doubting repair quality from past [NEW]
  PRICE_SHOCK_HISTORY           → Customer referencing past overcharging [NEW]
  DEALERSHIP_AVOIDANCE_PATTERN  → Customer expressing intent to avoid dealership [NEW]
"""

from typing import Dict, List, Tuple


class CustomerIntentClassifier:
    """
    Classifies customer intent from their reply message.
    Uses layered keyword + phrase matching with confidence scoring.
    Trust damage intents take priority over LOGISTICS_BLOCKER (critical fix).
    """

    INTENT_PATTERNS: Dict[str, List[Tuple[List[str], float]]] = {
        "LOGISTICS_BLOCKER": [
            (["out of town", "not in town", "travelling", "traveling", "travel", "trip", "away",
              "out of city", "out of country", "vacation", "holiday", "station", "posted",
              "transfer", "another city", "not here", "not around", "not available",
              "busy schedule", "work trip", "business trip", "conference", "15 days", "few weeks",
              "next month", "when i'm back", "when i return", "back in", "come back"], 1.0),
            (["busy", "schedule", "time", "can't make it", "cannot make it", "not free",
              "tied up", "occupied", "commitments", "prior engagement"], 0.6),
        ],
        "SKEPTICISM": [
            (["don't think", "dont think", "not that serious", "not serious", "really?",
              "seriously?", "are you sure", "how do you know", "doubt it", "not convinced",
              "seems fine", "drives fine", "no problem", "no issue", "feels okay",
              "i don't feel", "i dont feel", "nothing wrong", "seems okay", "looks fine",
              "not sure i believe", "hard to believe", "sounds exaggerated",
              "just trying to sell", "upselling", "upsell", "scam", "money grab"], 1.0),
            (["really", "seriously", "actually", "hmm", "interesting", "not sure",
              "uncertain", "skeptical", "doubt", "question"], 0.5),
        ],
        "COST_CONCERN": [
            (["expensive", "cost", "price", "afford", "money", "budget", "cheap",
              "how much", "quote", "estimate", "bill", "charge", "fee", "payment",
              "can't afford", "cannot afford", "too much", "pricey", "costly",
              "financial", "broke", "tight budget", "low on cash", "installment",
              "emi", "payment plan", "finance option"], 1.0),
            (["worth it", "value", "reasonable", "fair price", "competitive"], 0.5),
        ],
        "SECOND_OPINION_SEEKING": [
            (["family mechanic", "my mechanic", "local mechanic", "trusted mechanic",
              "second opinion", "another garage", "another workshop", "check elsewhere",
              "verify", "confirm", "get it checked", "show someone else",
              "my guy", "regular mechanic", "neighborhood mechanic",
              "want to check", "let me check", "will check", "done by him",
              "repair will be done by him", "he will fix", "he will repair"], 1.0),
            (["another place", "somewhere else", "different shop", "other service center"], 0.7),
        ],
        "INFO_GATHERING": [
            (["what exactly", "what is", "what does", "how does", "why is", "explain",
              "tell me more", "what happens", "what are the symptoms", "what should i look for",
              "how serious", "how bad", "what if i wait", "consequences", "what will happen",
              "how long", "how soon", "what are my options", "can you explain",
              "i want to understand", "help me understand", "clarify"], 1.0),
            (["?", "what", "how", "why", "when", "where", "which", "who"], 0.3),
        ],
        "READY_TO_BOOK": [
            (["yes", "okay", "ok", "sure", "fine", "book it", "schedule", "let's do it",
              "go ahead", "sounds good", "alright", "agreed", "i'll come",
              "when can i", "book me", "make an appointment", "fix it",
              "let's schedule", "i'm ready", "i agree", "confirmed",
              "please book", "yes please", "absolutely", "definitely"], 1.0),
            (["when is available", "earliest slot", "next available", "this week",
              "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday"], 0.7),
        ],
        "SOFT_DECLINE": [
            (["maybe later", "not right now", "let me think", "i'll think about it",
              "need to think", "give me time", "not sure yet", "undecided",
              "will let you know", "i'll get back", "check my schedule",
              "not today", "some other time", "next week", "next month",
              "let me discuss", "talk to my wife", "talk to my husband",
              "talk to family", "consult", "need to check"], 1.0),
            (["maybe", "perhaps", "possibly", "might", "could", "would consider"], 0.5),
        ],
        "HARD_DECLINE": [
            (["no thanks", "not interested", "don't want", "dont want", "cancel",
              "stop calling", "remove me", "unsubscribe", "leave me alone",
              "not going to", "won't be", "will not", "definitely not",
              "absolutely not", "never", "no way", "forget it", "drop it",
              "not happening", "stop contacting"], 1.0),
            (["no", "nope", "nah"], 0.6),
        ],
        # ── NEW: Trust Damage Intent Classes ──────────────────────────────────
        "PAST_SERVICE_FAILURE": [
            (["last time", "previously", "before", "last service", "past experience",
              "came late", "came 6 days", "6 days late", "6 day", "delayed",
              "not on time", "not fixed", "not solved", "issue not resolved",
              "same issue", "had to come back", "came back again", "visited again",
              "second visit", "poor service", "bad experience", "disappointed",
              "let down", "why should i trust", "trust you again", "trust again",
              "another 2 days", "2 days more", "had to give again"], 1.0),
            (["again", "before", "last", "previous", "already", "returned"], 0.4),
        ],
        "TRUST_DAMAGE_EVENT": [
            (["don't trust", "dont trust", "can't trust", "cannot trust",
              "lost trust", "no confidence", "not reliable", "unreliable",
              "broken promise", "lied", "mislead", "deceived", "cheated",
              "overcharged", "charged extra", "hidden charges", "surprise bill"], 1.0),
        ],
        "SERVICE_DELAY_TRAUMA": [
            (["came late", "6 days late", "6 day", "delayed", "not on time",
              "took longer", "took too long", "waited", "waiting", "days late",
              "week late", "overdue", "promised date", "expected date",
              "said it would be ready", "not ready on time", "than expected",
              "than it was expected"], 1.0),
            (["late", "delay", "slow", "waiting", "waited"], 0.5),
        ],
        "REPAIR_QUALITY_DOUBT": [
            (["not fixed", "not solved", "issue not resolved", "same problem",
              "same issue", "came back", "had to return", "returned again",
              "still broken", "still not working", "didn't fix", "didnt fix",
              "repair failed", "poor quality", "bad repair", "shoddy work",
              "not done properly", "not done right", "issue was not solved",
              "again i had to visit"], 1.0),
        ],
        "PRICE_SHOCK_HISTORY": [
            (["overcharged", "charged too much", "surprise bill", "hidden charges",
              "extra charges", "unexpected cost", "more than quoted", "more than expected",
              "price shock", "bill shock", "expensive last time", "cost more than",
              "paid too much", "ripped off", "robbery"], 1.0),
        ],
        "DEALERSHIP_AVOIDANCE_PATTERN": [
            (["never coming back", "won't come back", "avoid", "stay away",
              "go elsewhere", "another service center", "different dealership",
              "not your service center", "not coming to you", "find someone else",
              "not using your service", "done with you", "last time i use"], 1.0),
        ],
    }

    # Trust damage intents that override LOGISTICS_BLOCKER
    TRUST_DAMAGE_INTENTS = {
        "PAST_SERVICE_FAILURE", "TRUST_DAMAGE_EVENT", "SERVICE_DELAY_TRAUMA",
        "REPAIR_QUALITY_DOUBT", "PRICE_SHOCK_HISTORY", "DEALERSHIP_AVOIDANCE_PATTERN"
    }

    def classify(self, user_reply: str, conversation_history: List[str] = None) -> Dict:
        """
        Classify customer intent from their reply.
        Returns primary intent, confidence, and all detected intents.
        Trust damage intents take priority over LOGISTICS_BLOCKER.
        """
        lower_reply = user_reply.lower().strip()
        conversation_history = conversation_history or []

        scores: Dict[str, float] = {}

        for intent, pattern_groups in self.INTENT_PATTERNS.items():
            score = 0.0
            for keywords, weight in pattern_groups:
                for keyword in keywords:
                    if keyword in lower_reply:
                        score += weight
                        break  # Only count each group once
            if score > 0:
                scores[intent] = min(score, 1.0)

        # CRITICAL FIX: Trust damage intents override LOGISTICS_BLOCKER
        # "last time my car came 6 days late" was being classified as LOGISTICS_BLOCKER
        if any(t in scores for t in self.TRUST_DAMAGE_INTENTS):
            scores.pop("LOGISTICS_BLOCKER", None)

        # Resolve conflicts: HARD_DECLINE beats SOFT_DECLINE
        if "HARD_DECLINE" in scores and "SOFT_DECLINE" in scores:
            del scores["SOFT_DECLINE"]

        # READY_TO_BOOK requires no conflicting negative signals
        if "READY_TO_BOOK" in scores:
            if any(neg in scores for neg in ["HARD_DECLINE", "SOFT_DECLINE", "SKEPTICISM"]):
                if scores.get("READY_TO_BOOK", 0) < 0.8:
                    del scores["READY_TO_BOOK"]

        if not scores:
            primary_intent = "INFO_GATHERING"
            confidence = 0.4
        else:
            primary_intent = max(scores, key=lambda k: scores[k])
            confidence = scores[primary_intent]

        return {
            "primary_intent": primary_intent,
            "confidence": round(confidence, 2),
            "all_intents": scores,
            "is_logistics": "LOGISTICS_BLOCKER" in scores,
            "is_skeptical": "SKEPTICISM" in scores,
            "is_cost_concern": "COST_CONCERN" in scores,
            "is_second_opinion": "SECOND_OPINION_SEEKING" in scores,
            "is_ready": "READY_TO_BOOK" in scores,
            "is_declining": "HARD_DECLINE" in scores or "SOFT_DECLINE" in scores,
            "is_trust_damage": any(t in scores for t in self.TRUST_DAMAGE_INTENTS),
        }

    def get_objection_count(self, conversation_history: List[str]) -> int:
        """Count total objections raised across conversation history"""
        objection_intents = {
            "SKEPTICISM", "COST_CONCERN", "LOGISTICS_BLOCKER",
            "SECOND_OPINION_SEEKING", "SOFT_DECLINE", "HARD_DECLINE",
        } | self.TRUST_DAMAGE_INTENTS
        count = 0
        for msg in conversation_history:
            if msg.startswith("Customer:"):
                result = self.classify(msg.replace("Customer:", "").strip())
                if result["primary_intent"] in objection_intents:
                    count += 1
        return count
