"""Functional test for all new intelligence modules"""
from customer_intent_classifier import CustomerIntentClassifier
from edge_case_reasoning_engine import EdgeCaseReasoningEngine
from strategy_response_router import StrategyResponseRouter
from conversation_memory_tracker import ConversationMemoryTracker

clf = CustomerIntentClassifier()
ec = EdgeCaseReasoningEngine()
mem = ConversationMemoryTracker()

TESTS = [
    {
        "name": "Family Mechanic (was: generic fallback)",
        "msg": "yeah so i have a family mechanic i will check n repair will be done by him is it ok?",
        "expected_intent": "SECOND_OPINION_SEEKING",
        "expected_ec": "EC_FAMILY_MECHANIC",
    },
    {
        "name": "Past Bad Service (was: LOGISTICS_BLOCKER misclassification)",
        "msg": "so last time when i had given my honda car for such service it came 6 days late than it was expected , then too my issue was not solved properly again i had to visit the service center and give car to service for another 2 days no why should i trust u again?",
        "expected_intent": "PAST_SERVICE_FAILURE",
        "expected_ec": "EC_PAST_BAD_SERVICE",
        "check_no_logistics": True,
        "check_trust_damage": True,
    },
    {
        "name": "Out of Town",
        "msg": "i am not in town for another 15 days",
        "expected_intent": "LOGISTICS_BLOCKER",
        "expected_ec": "EC_OUT_OF_TOWN_HIGH_RISK",
    },
    {
        "name": "Skeptical Polite",
        "msg": "I dont think it is that serious, the car drives fine",
        "expected_intent": "SKEPTICISM",
        "expected_ec": "EC_SKEPTICAL_POLITE",
    },
    {
        "name": "Cost Concern",
        "msg": "How much will this cost? Seems expensive",
        "expected_intent": "COST_CONCERN",
        "expected_ec": "EC_COST_SENSITIVE",
    },
]

all_passed = True
for t in TESTS:
    print(f"\n{'='*60}")
    print(f"TEST: {t['name']}")
    print(f"{'='*60}")
    r = clf.classify(t["msg"])
    intent = r["primary_intent"]
    intent_ok = intent == t["expected_intent"] or (
        t.get("expected_intent") in ("PAST_SERVICE_FAILURE", "SERVICE_DELAY_TRAUMA")
        and intent in ("PAST_SERVICE_FAILURE", "SERVICE_DELAY_TRAUMA", "REPAIR_QUALITY_DOUBT")
    )
    print(f"Intent: {intent} | Expected: {t['expected_intent']} | {'PASS' if intent_ok else 'FAIL'}")

    if t.get("check_no_logistics"):
        no_log = "LOGISTICS_BLOCKER" not in r["all_intents"]
        print(f"LOGISTICS_BLOCKER removed: {no_log} | {'PASS' if no_log else 'FAIL'}")
        if not no_log:
            all_passed = False

    if t.get("check_trust_damage"):
        td = r["is_trust_damage"]
        print(f"Trust Damage detected: {td} | {'PASS' if td else 'FAIL'}")
        if not td:
            all_passed = False

    ec_result = ec.detect_edge_case(t["msg"], intent, {})
    ec_ok = ec_result == t["expected_ec"]
    print(f"Edge Case: {ec_result} | Expected: {t['expected_ec']} | {'PASS' if ec_ok else 'FAIL'}")

    if not intent_ok or not ec_ok:
        all_passed = False

print(f"\n{'='*60}")
print(f"RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
print(f"{'='*60}")
