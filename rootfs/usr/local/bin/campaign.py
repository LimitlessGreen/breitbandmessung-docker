import os
import json
import random
import logging
from datetime import datetime

class Campaign:
    """Combines Config, State, and Compliance Logic into one lean class."""
    
    # BNetzA Rules
    RULES = {
        "TOTAL": 30, "PER_DAY": 10, "MAX_DAYS": 14,
        "GAP_MINS": 5, "LONG_GAP_AFTER": 5, "LONG_GAP_HOURS": 3, "GAP_DAYS": 1
    }

    def __init__(self, state_file="/config/campaign_state.json"):
        self.state_file = state_file
        self.prefs = {
            "START": os.environ.get("TIME_START", "08:00"),
            "END": os.environ.get("TIME_END", "22:00"),
            "DAYS": [d.strip().lower()[:3] for d in os.environ.get("PREFERRED_DAYS", "").split(',') if d],
            "TIMES": os.environ.get("PREFERRED_TIMES", ""),
            "JITTER": int(os.environ.get("JITTER_MAX_MINS", "7"))
        }
        self.load()

    def load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f: 
                    self.state = json.load(f)
                # Migration for old keys
                if "total_count" in self.state: self.state["total"] = self.state.pop("total_count")
                if "daily_count" in self.state: self.state["daily"] = self.state.pop("daily_count")
                if "last_test_ts" in self.state: self.state["last_ts"] = self.state.pop("last_test_ts")
                if "last_test_day" in self.state: self.state["last_day"] = self.state.pop("last_test_day")
                return
            except: pass
        self.state = {"start_date": None, "total": 0, "daily": 0, "last_ts": 0, "last_day": None, "active": False}

    def save(self):
        if "test-solver" in " ".join(os.sys.argv): return
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f: json.dump(self.state, f, indent=2)

    def _to_min(self, t_str):
        h, m = map(int, t_str.split(':'))
        return h * 60 + m

    def can_run(self, now):
        if not self.state["active"]: return False, "Inactive"
        if self.state["total"] >= self.RULES["TOTAL"]: return False, "Finished"
        
        today = now.strftime("%Y-%m-%d")
        if self.state["start_date"]:
            start = datetime.strptime(self.state["start_date"], "%Y-%m-%d")
            if (now - start).days > self.RULES["MAX_DAYS"]: return False, "Expired"

        # Day/Time Checks
        curr_min = now.hour * 60 + now.minute
        start_min = self._to_min(self.prefs["START"])
        end_min = self._to_min(self.prefs["END"])
        if not (start_min <= curr_min <= end_min):
            return False, f"Outside Window ({self.prefs['START']}-{self.prefs['END']})"
        
        if self.prefs["DAYS"] and now.strftime("%a").lower() not in self.prefs["DAYS"]:
            return False, "Wrong Day"

        # Efficiency Check: Is it even possible to reach the daily goal (10) today?
        # A test takes ~1min + MIN 5min gap = 6min per test cycle.
        remaining_tests = self.RULES["PER_DAY"] - self.state["daily"]
        if remaining_tests > 0:
            # We need (remaining-1) gaps of at least 5 mins
            min_time_needed = remaining_tests + (remaining_tests - 1) * self.RULES["GAP_MINS"]
            if curr_min + min_time_needed > end_min:
                return False, "Insufficient time for daily goal"

        # Interval Checks
        elapsed = (now.timestamp() - self.state["last_ts"]) / 60
        jitter = random.randint(0, self.prefs["JITTER"])
        
        if self.state["last_day"] == today:
            if self.state["daily"] >= self.RULES["PER_DAY"]: return False, "Daily Limit"
            req = (self.RULES["LONG_GAP_HOURS"] * 60 if self.state["daily"] == self.RULES["LONG_GAP_AFTER"] else self.RULES["GAP_MINS"]) + jitter
            if elapsed < req: return False, f"Wait {int(req-elapsed)}m"
        elif self.state["last_day"]:
            last = datetime.strptime(self.state["last_day"], "%Y-%m-%d")
            if (now - last).days < (self.RULES["GAP_DAYS"] + 1): return False, "Gap Day required"

        return True, "Ready"

    def record(self, ts):
        day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        if not self.state["start_date"]: self.state["start_date"] = day
        if self.state["last_day"] != day: self.state["daily"] = 0
        self.state["total"] += 1
        self.state["daily"] += 1
        self.state["last_ts"], self.state["last_day"] = ts, day
        self.save()
