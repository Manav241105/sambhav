"""

Scheduling Agent - Autonomous Service Orchestration Platform v1.0

Enterprise-grade autonomous scheduling. No human advisor needed.



Capabilities:

  ✅ Capacity Intelligence (technicians, bays, duration, priority queue)

  ✅ Slot Intelligence (suggest, hold, lock, release, alternatives)

  ✅ Booking Execution (new, reschedule, cancel, waitlist, priority escalation)

  ✅ Structured Confirmation (Booking ID, slot, technician, bay, duration, prep)

"""



import re

import uuid

import random

from datetime import datetime, timedelta, date as date_type

from typing import Dict, List, Optional, Tuple





# ── Service Duration Map (hours) ──────────────────────────────────────────────

SERVICE_DURATIONS = {

    "Brake Pads": 1.5,

    "Battery": 0.75,

    "Cooling System": 2.0,

    "Engine": 3.0,

    "Transmission": 4.0,

    "Tires": 1.0,

    "Oil Change": 0.5,

    "Full Service": 3.5,

    "default": 2.0,

}



# ── Technician Pool ───────────────────────────────────────────────────────────

TECHNICIANS = [

    {"id": "T001", "name": "Rajesh Kumar",    "specialization": ["Brake Pads", "Tires", "Oil Change"], "level": "SENIOR"},

    {"id": "T002", "name": "Amit Sharma",     "specialization": ["Battery", "Electrical"],              "level": "SENIOR"},

    {"id": "T003", "name": "Priya Nair",      "specialization": ["Cooling System", "Engine"],           "level": "LEAD"},

    {"id": "T004", "name": "Suresh Patel",    "specialization": ["Transmission", "Full Service"],       "level": "SENIOR"},

    {"id": "T005", "name": "Deepak Mehta",    "specialization": ["Brake Pads", "Battery", "Tires"],     "level": "JUNIOR"},

]



# ── Bay Pool ──────────────────────────────────────────────────────────────────

BAYS = [

    {"id": "BAY-1", "type": "STANDARD"},

    {"id": "BAY-2", "type": "STANDARD"},

    {"id": "BAY-3", "type": "HEAVY"},

    {"id": "BAY-4", "type": "EXPRESS"},

    {"id": "BAY-5", "type": "STANDARD"},

]



# ── Working Hours ─────────────────────────────────────────────────────────────

WORKING_HOURS_START = 8   # 8:00 AM

WORKING_HOURS_END = 18    # 6:00 PM





class SlotHold:

    """Temporary slot hold (15-minute expiry)."""

    HOLD_DURATION_MINUTES = 15



    def __init__(self, slot_time: datetime, technician_id: str,

                 bay_id: str, customer_id: str):

        self.hold_id = f"HOLD-{uuid.uuid4().hex[:8].upper()}"

        self.slot_time = slot_time

        self.technician_id = technician_id

        self.bay_id = bay_id

        self.customer_id = customer_id

        self.created_at = datetime.now()

        self.expires_at = self.created_at + timedelta(minutes=self.HOLD_DURATION_MINUTES)



    def is_expired(self) -> bool:

        return datetime.now() > self.expires_at



    def minutes_remaining(self) -> int:

        delta = self.expires_at - datetime.now()

        return max(0, int(delta.total_seconds() / 60))





# Dashboard state (v6.0)
try:
    from app_state import app_state as _app_state
except ImportError:
    _app_state = None


class BookingConfirmation:

    """Structured booking confirmation returned to the conversation agent."""



    def __init__(self, booking_id: str, slot_time: datetime,

                 technician: Dict, bay: Dict, service_component: str,

                 service_duration_hours: float, customer_id: str,

                 vehicle_id: str, priority: str, status: str = "CONFIRMED"):

        self.booking_id = booking_id

        self.slot_time = slot_time

        self.technician = technician

        self.bay = bay

        self.service_component = service_component

        self.service_duration_hours = service_duration_hours

        self.customer_id = customer_id

        self.vehicle_id = vehicle_id

        self.priority = priority

        self.status = status

        self.created_at = datetime.now()

        self.prep_instructions = self._build_prep_instructions(service_component)



    def _build_prep_instructions(self, component: str) -> str:

        lower = component.lower()

        if "brake" in lower:

            return (

                "Please arrive 10 minutes early. "

                "Avoid hard braking on the way to the service center. "

                "The service will take approximately 1.5 hours."

            )

        elif "battery" in lower:

            return (

                "Please bring your vehicle registration documents. "

                "The service will take approximately 45 minutes. "

                "Your vehicle will be ready same day."

            )

        elif "cool" in lower or "engine" in lower:

            return (

                "Please ensure the engine is cool before arrival (do not drive more than 15 minutes). "

                "The service will take 2–3 hours. A waiting area is available."

            )

        return (

            "Please arrive 5 minutes before your appointment. "

            "Bring your vehicle registration. "

            f"Estimated service time: {self.service_duration_hours:.1f} hours."

        )



    def to_dict(self) -> Dict:

        return {

            "booking_id": self.booking_id,

            "slot_time": self.slot_time.strftime("%A, %d %B %Y at %I:%M %p"),

            "slot_time_iso": self.slot_time.isoformat(),

            "technician_name": self.technician["name"],

            "technician_level": self.technician["level"],

            "bay": self.bay["id"],

            "service_component": self.service_component,

            "service_duration_hours": self.service_duration_hours,

            "customer_id": self.customer_id,

            "vehicle_id": self.vehicle_id,

            "priority": self.priority,

            "status": self.status,

            "prep_instructions": self.prep_instructions,

            "created_at": self.created_at.isoformat(),

        }



    def to_customer_message(self, first_name: str, vehicle_desc: str) -> str:

        """Generate a natural confirmation message for the customer."""

        slot_str = self.slot_time.strftime("%A, %d %B at %I:%M %p")

        return (

            f"✅ **Booking Confirmed!**\n\n"

            f"Here are your details, {first_name}:\n\n"

            f"📋 **Booking ID:** {self.booking_id}\n"

            f"📅 **Date & Time:** {slot_str}\n"

            f"🔧 **Service:** {self.service_component} for {vehicle_desc}\n"

            f"👨‍🔧 **Technician:** {self.technician['name']} ({self.technician['level']})\n"

            f"🏎️ **Bay:** {self.bay['id']}\n"

            f"⏱️ **Estimated Duration:** {self.service_duration_hours:.1f} hours\n\n"

            f"📝 **Prep Instructions:** {self.prep_instructions}\n\n"

            f"You'll receive an SMS confirmation shortly. "

            f"If you need to reschedule, just let me know — I can handle that for you instantly."

        )





class SchedulingAgent:

    """

    Enterprise-grade autonomous scheduling agent.

    Handles the full booking lifecycle without any human advisor involvement.

    """



    def __init__(self):

        self._holds: Dict[str, SlotHold] = {}           # hold_id → SlotHold

        self._bookings: Dict[str, BookingConfirmation] = {}  # booking_id → Confirmation

        self._waitlist: List[Dict] = []

        # Simulate some pre-booked slots to create realistic availability

        self._booked_slots: List[Tuple[datetime, str]] = []  # (slot_time, technician_id)

        self._initialize_sample_bookings()



    def _initialize_sample_bookings(self):

        """Pre-populate some bookings to simulate real capacity."""

        now = datetime.now()

        # Simulate 40% capacity already booked

        for days_ahead in range(7):

            for hour in [9, 11, 14, 16]:

                if random.random() < 0.4:

                    slot = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)

                    tech = random.choice(TECHNICIANS)

                    self._booked_slots.append((slot, tech["id"]))



    # ── Capacity Intelligence ─────────────────────────────────────────────────



    def _get_available_technician(self, slot_time: datetime,

                                  component: str) -> Optional[Dict]:

        """Find an available technician for the given slot and component."""

        # Clean expired holds

        self._cleanup_expired_holds()



        # Get technicians already booked at this slot

        booked_tech_ids = {

            tech_id for (s, tech_id) in self._booked_slots

            if abs((s - slot_time).total_seconds()) < 3600

        }

        # Also check active holds

        held_tech_ids = {

            hold.technician_id for hold in self._holds.values()

            if not hold.is_expired() and

            abs((hold.slot_time - slot_time).total_seconds()) < 3600

        }

        unavailable = booked_tech_ids | held_tech_ids



        # Prefer specialized technicians

        specialized = [

            t for t in TECHNICIANS

            if t["id"] not in unavailable and

            any(component.lower() in s.lower() for s in t["specialization"])

        ]

        if specialized:

            return specialized[0]



        # Fall back to any available technician

        available = [t for t in TECHNICIANS if t["id"] not in unavailable]

        return available[0] if available else None



    def _get_available_bay(self, slot_time: datetime) -> Optional[Dict]:

        """Find an available bay for the given slot."""

        held_bay_ids = {

            hold.bay_id for hold in self._holds.values()

            if not hold.is_expired() and

            abs((hold.slot_time - slot_time).total_seconds()) < 3600

        }

        available = [b for b in BAYS if b["id"] not in held_bay_ids]

        return available[0] if available else None



    def _is_slot_within_working_hours(self, slot_time: datetime) -> bool:

        """Check if slot is within working hours."""

        return WORKING_HOURS_START <= slot_time.hour < WORKING_HOURS_END



    def _get_service_duration(self, component: str) -> float:

        """Get service duration for a component."""

        for key, duration in SERVICE_DURATIONS.items():

            if key.lower() in component.lower():

                return duration

        return SERVICE_DURATIONS["default"]



    # ── Slot Intelligence ─────────────────────────────────────────────────────



    def _parse_requested_date(self, date_str: str) -> Optional[datetime]:

        """

        Parse a natural date string into a datetime object.

        Handles: '21 feb', '21st feb', 'feb 21', '21/02', 'monday',

                 'tomorrow', 'today', 'next week', weekday names.

        Returns midnight datetime for the matched date, or None.

        """

        if not date_str:

            return None

        lower = date_str.lower().strip()

        now = datetime.now()



        # Relative dates

        if "today" in lower:

            return now.replace(hour=0, minute=0, second=0, microsecond=0)

        if "tomorrow" in lower:

            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        if "next week" in lower:

            return (now + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

        if "weekend" in lower:

            days_to_sat = (5 - now.weekday()) % 7 or 7

            return (now + timedelta(days=days_to_sat)).replace(hour=0, minute=0, second=0, microsecond=0)



        # Weekday names

        weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,

                    "friday": 4, "saturday": 5, "sunday": 6}

        for name, wd in weekdays.items():

            if name in lower:

                days_ahead = (wd - now.weekday()) % 7 or 7

                return (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)



        # Month names

        month_map = {

            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,

            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12

        }

        # "21 feb" or "21st feb" or "feb 21"

        for abbr, month_num in month_map.items():

            m = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s*' + abbr, lower)

            if not m:

                m = re.search(abbr + r'\s*(\d{1,2})', lower)

            if m:

                day_num = int(m.group(1))

                year = now.year if month_num >= now.month else now.year + 1

                try:

                    return datetime(year, month_num, day_num, 0, 0, 0)

                except ValueError:

                    pass



        # "21/02" or "21-02"

        m = re.search(r'(\d{1,2})[/-](\d{1,2})', lower)

        if m:

            day_num, month_num = int(m.group(1)), int(m.group(2))

            year = now.year

            try:

                return datetime(year, month_num, day_num, 0, 0, 0)

            except ValueError:

                pass



        return None



    def find_slots_for_date(self, component: str, priority: str,

                            target_date: datetime,

                            time_preference: Optional[str] = None) -> List[Dict]:

        """

        Find all available slots on a SPECIFIC date, optionally filtered by

        time-of-day preference (morning/afternoon/evening).

        Returns list of slot dicts (may be empty if no slots found).

        """

        slots = []

        for hour in [8, 9, 10, 11, 14, 15, 16, 17]:

            slot_time = target_date.replace(

                hour=hour, minute=0, second=0, microsecond=0

            )

            if slot_time <= datetime.now():

                continue

            if not self._is_slot_within_working_hours(slot_time):

                continue



            # Apply time-of-day filter

            if time_preference:

                tp = time_preference.lower()

                if "morning" in tp and not (8 <= hour <= 12):

                    continue

                if "afternoon" in tp and not (12 <= hour <= 17):

                    continue

                if "evening" in tp and not (hour >= 16):

                    continue



            tech = self._get_available_technician(slot_time, component)

            bay = self._get_available_bay(slot_time)

            if tech and bay:

                slots.append({

                    "slot_time": slot_time,

                    "technician": tech,

                    "bay": bay,

                    "days_from_now": (target_date.date() - datetime.now().date()).days,

                    "slot_display": slot_time.strftime("%A, %d %b at %I:%M %p"),

                })

        return slots



    def find_best_slot(self, component: str, priority: str,

                       preferred_time: Optional[str] = None,

                       requested_date: Optional[str] = None,

                       days_ahead: int = 14) -> Optional[Dict]:

        """

        Find the best available slot.

        If requested_date is given → search ONLY on that date.

        Otherwise → search next days_ahead days.

        Returns slot info dict or None if no slots available.

        """

        now = datetime.now()



        # ── Specific date requested ───────────────────────────────────────────

        if requested_date:

            target_dt = self._parse_requested_date(requested_date)

            if target_dt:

                slots = self.find_slots_for_date(component, priority, target_dt, preferred_time)

                if slots:

                    return slots[0]

                # No slots on that date — fall through to nearest alternative

                return None



        # ── Open-window search ────────────────────────────────────────────────

        start_day = 0 if priority in ["P0", "P1"] else 1

        candidate_slots = []

        for day_offset in range(start_day, days_ahead + 1):

            target_date_dt = now + timedelta(days=day_offset)

            if target_date_dt.weekday() >= 5 and priority not in ["P0", "P1"]:

                continue

            for hour in [9, 10, 11, 14, 15, 16]:

                slot_time = target_date_dt.replace(

                    hour=hour, minute=0, second=0, microsecond=0

                )

                if slot_time <= now:

                    continue

                if not self._is_slot_within_working_hours(slot_time):

                    continue

                tech = self._get_available_technician(slot_time, component)

                bay = self._get_available_bay(slot_time)

                if tech and bay:

                    candidate_slots.append({

                        "slot_time": slot_time,

                        "technician": tech,

                        "bay": bay,

                        "days_from_now": day_offset,

                        "slot_display": slot_time.strftime("%A, %d %b at %I:%M %p"),

                    })



        if not candidate_slots:

            return None



        # Match time preference

        if preferred_time:

            pref = preferred_time.lower()

            for slot in candidate_slots:

                h = slot["slot_time"].hour

                if "morning" in pref and 8 <= h <= 12:

                    return slot

                if "afternoon" in pref and 12 <= h <= 17:

                    return slot

                if "evening" in pref and h >= 16:

                    return slot



        return candidate_slots[0]





    def find_alternative_slots(self, component: str, priority: str,

                               count: int = 3) -> List[Dict]:

        """Find multiple alternative slots."""

        now = datetime.now()

        alternatives = []



        for day_offset in range(1, 14):

            if len(alternatives) >= count:

                break

            target_date = now + timedelta(days=day_offset)

            if target_date.weekday() >= 5:

                continue



            for hour in [9, 11, 14, 16]:

                if len(alternatives) >= count:

                    break

                slot_time = target_date.replace(

                    hour=hour, minute=0, second=0, microsecond=0

                )

                tech = self._get_available_technician(slot_time, component)

                bay = self._get_available_bay(slot_time)

                if tech and bay:

                    alternatives.append({

                        "slot_time": slot_time,

                        "technician": tech,

                        "bay": bay,

                        "slot_display": slot_time.strftime("%A, %d %b at %I:%M %p"),

                    })



        return alternatives



    def hold_slot(self, slot_time: datetime, technician: Dict,

                  bay: Dict, customer_id: str) -> SlotHold:

        """Temporarily hold a slot for 15 minutes."""

        hold = SlotHold(slot_time, technician["id"], bay["id"], customer_id)

        self._holds[hold.hold_id] = hold

        print(f"   🔒 [SCHEDULING] Slot held: {hold.hold_id} "

              f"(expires in {hold.HOLD_DURATION_MINUTES} min)")

        return hold



    def release_hold(self, hold_id: str):

        """Release a slot hold."""

        if hold_id in self._holds:

            del self._holds[hold_id]

            print(f"   🔓 [SCHEDULING] Hold released: {hold_id}")



    def _cleanup_expired_holds(self):

        """Remove expired holds."""

        expired = [hid for hid, h in self._holds.items() if h.is_expired()]

        for hid in expired:

            del self._holds[hid]



    # ── Booking Execution ─────────────────────────────────────────────────────



    def create_booking(self, customer_id: str, vehicle_id: str,

                       component: str, priority: str,

                       preferred_time: Optional[str] = None,

                       hold_id: Optional[str] = None) -> Dict:

        """

        Create a new booking. Returns structured result.



        Result:

          { "success": bool, "confirmation": BookingConfirmation | None,

            "alternatives": list, "message": str }

        """

        # Use held slot if available

        if hold_id and hold_id in self._holds:

            hold = self._holds[hold_id]

            if not hold.is_expired():

                slot_time = hold.slot_time

                tech = next((t for t in TECHNICIANS if t["id"] == hold.technician_id), TECHNICIANS[0])

                bay = next((b for b in BAYS if b["id"] == hold.bay_id), BAYS[0])

                del self._holds[hold_id]

            else:

                # Hold expired — find new slot

                slot_info = self.find_best_slot(component, priority, preferred_time)

                if not slot_info:

                    return self._no_slot_result(component, priority)

                slot_time = slot_info["slot_time"]

                tech = slot_info["technician"]

                bay = slot_info["bay"]

        else:

            slot_info = self.find_best_slot(component, priority, preferred_time)

            if not slot_info:

                return self._no_slot_result(component, priority)

            slot_time = slot_info["slot_time"]

            tech = slot_info["technician"]

            bay = slot_info["bay"]



        duration = self._get_service_duration(component)

        booking_id = f"BK{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"



        confirmation = BookingConfirmation(

            booking_id=booking_id,

            slot_time=slot_time,

            technician=tech,

            bay=bay,

            service_component=component,

            service_duration_hours=duration,

            customer_id=customer_id,

            vehicle_id=vehicle_id,

            priority=priority,

            status="CONFIRMED"

        )



        self._bookings[booking_id] = confirmation

        # Mark slot as booked

        self._booked_slots.append((slot_time, tech["id"]))



        # ── Push to app_state for dashboard API (v6.0) ────────────────────

        if _app_state is not None:

            try:

                _app_state.add_booking(confirmation.to_dict())

            except Exception as _e:

                print(f"   ⚠️  app_state booking write failed: {_e}")



        print(f"\n   ✅ [SCHEDULING] Booking confirmed: {booking_id}")

        print(f"   📅 Slot: {slot_time.strftime('%A, %d %b at %I:%M %p')}")

        print(f"   👨‍🔧 Technician: {tech['name']} ({tech['level']})")

        print(f"   🏎️  Bay: {bay['id']}")

        print(f"   ⏱️  Duration: {duration:.1f}h")



        return {

            "success": True,

            "confirmation": confirmation,

            "alternatives": [],

            "message": "Booking confirmed"

        }



    def reschedule_booking(self, booking_id: str, new_preferred_time: Optional[str] = None) -> Dict:

        """Reschedule an existing booking."""

        if booking_id not in self._bookings:

            return {"success": False, "message": "Booking not found", "confirmation": None}



        old = self._bookings[booking_id]

        # Remove old slot

        self._booked_slots = [

            (s, t) for (s, t) in self._booked_slots

            if not (s == old.slot_time and t == old.technician["id"])

        ]



        # Find new slot

        slot_info = self.find_best_slot(

            old.service_component, old.priority, new_preferred_time

        )

        if not slot_info:

            return self._no_slot_result(old.service_component, old.priority)



        new_booking_id = f"BK{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        new_confirmation = BookingConfirmation(

            booking_id=new_booking_id,

            slot_time=slot_info["slot_time"],

            technician=slot_info["technician"],

            bay=slot_info["bay"],

            service_component=old.service_component,

            service_duration_hours=old.service_duration_hours,

            customer_id=old.customer_id,

            vehicle_id=old.vehicle_id,

            priority=old.priority,

            status="CONFIRMED"

        )



        del self._bookings[booking_id]

        self._bookings[new_booking_id] = new_confirmation

        self._booked_slots.append((slot_info["slot_time"], slot_info["technician"]["id"]))



        print(f"\n   🔄 [SCHEDULING] Rescheduled: {booking_id} → {new_booking_id}")

        return {"success": True, "confirmation": new_confirmation, "message": "Rescheduled"}



    def cancel_booking(self, booking_id: str) -> Dict:

        """Cancel a booking."""

        if booking_id not in self._bookings:

            return {"success": False, "message": "Booking not found"}



        booking = self._bookings[booking_id]

        self._booked_slots = [

            (s, t) for (s, t) in self._booked_slots

            if not (s == booking.slot_time and t == booking.technician["id"])

        ]

        del self._bookings[booking_id]

        print(f"\n   ❌ [SCHEDULING] Cancelled: {booking_id}")

        return {"success": True, "message": "Booking cancelled"}



    def add_to_waitlist(self, customer_id: str, vehicle_id: str,

                        component: str, priority: str) -> Dict:

        """Add customer to waitlist."""

        waitlist_id = f"WL{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        entry = {

            "waitlist_id": waitlist_id,

            "customer_id": customer_id,

            "vehicle_id": vehicle_id,

            "component": component,

            "priority": priority,

            "added_at": datetime.now().isoformat(),

            "position": len(self._waitlist) + 1

        }

        self._waitlist.append(entry)

        print(f"\n   📋 [SCHEDULING] Added to waitlist: {waitlist_id} (position {entry['position']})")

        return entry



    def _no_slot_result(self, component: str, priority: str) -> Dict:

        """Return result when no slots are available."""

        alternatives = self.find_alternative_slots(component, priority)

        return {

            "success": False,

            "confirmation": None,

            "alternatives": alternatives,

            "message": "No immediate slots available — alternatives provided"

        }



    # ── Availability Check ────────────────────────────────────────────────────



    def check_availability(self, component: str, priority: str,

                           preferred_time: Optional[str] = None,

                           requested_date: Optional[str] = None) -> Dict:

        """

        Check slot availability and return structured response for conversation agent.

        If requested_date is given, ONLY that date is searched.

        """

        # Parse time preference from requested_date if it contains one

        # e.g. "morning on 21 feb" — split into date and time pref

        time_pref = preferred_time

        date_key = requested_date

        if requested_date:

            req_lower = requested_date.lower()

            for tp in ["morning", "afternoon", "evening"]:

                if tp in req_lower:

                    time_pref = tp

                    # Strip the time word so date parsing works properly

                    date_key = req_lower.replace(tp, "").replace("on", "").strip()

                    break



        if date_key:

            # Search ONLY on the specific requested date

            target_dt = self._parse_requested_date(date_key)
            if target_dt is None:
                # Date is invalid (e.g. 29 Feb in non-leap year)
                nearest = self.find_alternative_slots(component, priority, count=3)
                return {
                    "available": False,
                    "best_slot": None,
                    "alternatives": [
                        {"slot_display": a["slot_display"], "slot_time": a["slot_time"]}
                        for a in nearest
                    ],
                    "requested_date": date_key,
                    "date_found": False,
                    "message": f"Date '{date_key}' is invalid or unavailable"
                }

            if target_dt is None:

                # Date doesn't exist (e.g. 29 Feb in non-leap year) or couldn't be parsed

                # Return nearest alternatives with clear "no slots on X" message

                nearest = self.find_alternative_slots(component, priority, count=3)

                return {

                    "available": False,

                    "best_slot": None,

                    "alternatives": [

                        {"slot_display": a["slot_display"], "slot_time": a["slot_time"]}

                        for a in nearest

                    ],

                    "requested_date": date_key,

                    "date_found": False,

                    "message": f"Date '{date_key}' is invalid or doesn't exist"

                }

            if target_dt:

                slots = self.find_slots_for_date(component, priority, target_dt, time_pref)

                if slots:

                    best = slots[0]

                    alts = slots[1:3]  # Up to 2 alternatives on same day

                    return {

                        "available": True,

                        "best_slot": {

                            "slot_display": best["slot_time"].strftime("%A, %d %B at %I:%M %p"),

                            "slot_time": best["slot_time"],

                            "technician": best["technician"]["name"],

                            "technician_level": best["technician"]["level"],

                            "bay": best["bay"]["id"],

                            "days_from_now": best["days_from_now"],

                        },

                        "alternatives": [

                            {"slot_display": a["slot_display"], "slot_time": a["slot_time"]}

                            for a in alts

                        ],

                        "requested_date": date_key,

                        "date_found": True,

                        "message": f"Slots found for {date_key}"

                    }

                else:

                    # No slots on that date — find nearest alternatives

                    nearest = self.find_alternative_slots(component, priority, count=3)

                    return {

                        "available": False,

                        "best_slot": None,

                        "alternatives": [

                            {"slot_display": a["slot_display"], "slot_time": a["slot_time"]}

                            for a in nearest

                        ],

                        "requested_date": date_key,

                        "date_found": False,

                        "message": f"No slots on {date_key} — nearest alternatives shown"

                    }



        # No specific date — open-window search

        best = self.find_best_slot(component, priority, time_pref)

        alternatives = self.find_alternative_slots(component, priority, count=3)



        if best:

            return {

                "available": True,

                "best_slot": {

                    "slot_display": best["slot_time"].strftime("%A, %d %B at %I:%M %p"),

                    "slot_time": best["slot_time"],

                    "technician": best["technician"]["name"],

                    "technician_level": best["technician"].get("level", "SENIOR"),

                    "bay": best["bay"]["id"],

                    "days_from_now": best["days_from_now"],

                },

                "alternatives": [

                    {"slot_display": a["slot_display"], "slot_time": a["slot_time"]}

                    for a in alternatives

                ],

                "requested_date": None,

                "date_found": True,

                "message": "Slots available"

            }

        return {

            "available": False,

            "best_slot": None,

            "alternatives": [

                {"slot_display": a["slot_display"], "slot_time": a["slot_time"]}

                for a in alternatives

            ],

            "requested_date": None,

            "date_found": False,

            "message": "No immediate slots — alternatives available"

        }





    def format_availability_message(self, availability: Dict,

                                    first_name: str, component: str,

                                    requested_date: Optional[str] = None) -> str:

        """Format availability check result into a natural customer message."""

        req_date = availability.get("requested_date") or requested_date

        date_found = availability.get("date_found", True)

        date_label = f" on **{req_date}**" if req_date else ""



        if availability["available"]:

            best = availability["best_slot"]

            alts = availability["alternatives"][:2]

            alt_text = ""

            if alts:

                alt_displays = [a["slot_display"] for a in alts]

                day_ctx = " on that day" if (req_date and date_found) else ""

                alt_text = (

                    f"\n\nOther options{day_ctx}:\n"

                    + "\n".join(f"• {d}" for d in alt_displays)

                )

            tech_level = best.get("technician_level", "SENIOR")

            return (

                f"Here are the available slots{date_label} for your {component} service:\n\n"

                f"📅 **Best slot:** {best['slot_display']}\n"

                f"👨‍🔧 **Technician:** {best['technician']} ({tech_level})\n"

                f"🏎️ **Bay:** {best['bay']}"

                f"{alt_text}\n\n"

                f"Which slot works for you? Just confirm and I'll lock it in."

            )

        else:

            alts = availability["alternatives"]

            alt_text = "\n".join(f"• {a['slot_display']}" for a in alts)

            if req_date and not date_found:

                return (

                    f"Sorry, {first_name} — there are no available slots on **{req_date}** "

                    f"for your {component} service.\n\n"

                    f"Nearest availability:\n{alt_text}\n\n"

                    f"Would you like to book one of these instead?"

                )

            return (

                f"The immediate slots are filling up, {first_name}, but I have these "

                f"upcoming options for your {component} service:\n\n{alt_text}\n\n"

                f"Which of these works best for you?"

            )





    def get_booking(self, booking_id: str) -> Optional[BookingConfirmation]:

        """Get a booking by ID."""

        return self._bookings.get(booking_id)



    def get_customer_bookings(self, customer_id: str) -> List[BookingConfirmation]:

        """Get all bookings for a customer."""

        return [b for b in self._bookings.values() if b.customer_id == customer_id]

