#!/usr/bin/env python3
import sys, time, os, logging, random
from datetime import datetime, timedelta
from campaign import Campaign
from ui_utils import UI, set_clip, get_clip

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_simulation(cp):
    logging.info("--- Solver Test Mode ---")
    cp.state["active"] = True
    now = datetime.now().replace(second=0, microsecond=0)
    limit = 100000
    while cp.state["total"] < cp.RULES["TOTAL"] and limit > 0:
        limit -= 1
        ok, msg = cp.can_run(now)
        if ok:
            ts = now.timestamp() + random.randint(0, 45)
            cp.record(ts)
            logging.info(f"Test {cp.state['total']:02d} @ {datetime.fromtimestamp(ts)}")
            now = datetime.fromtimestamp(ts) + timedelta(minutes=1)
        else:
            if "Window" in msg:
                s_h, s_m = map(int, cp.prefs["START"].split(':'))
                if now.hour >= s_h:
                    now = now.replace(hour=s_h, minute=s_m) + timedelta(days=1)
                else:
                    now = now.replace(hour=s_h, minute=s_m)
            elif "Day" in msg:
                now = now.replace(hour=0, minute=0) + timedelta(days=1)
            elif "Wait" in msg:
                now += timedelta(minutes=5)
            elif "Expired" in msg:
                logging.error("Campaign expired during simulation!")
                break
            else:
                now += timedelta(minutes=10)
    logging.info(f"--- End Simulation ({cp.state['total']}/{cp.RULES['TOTAL']}) ---")

def main():
    cp = Campaign()
    if "--test-solver" in sys.argv: return run_simulation(cp)

    logging.info("Automation Service Active.")
    ui = UI()
    
    while True:
        # Trigger Check
        if get_clip().strip() in ["START", "RUN"] or os.path.exists("/START"):
            cp.state["active"] = True
            cp.save()
            if os.path.exists("/START"): os.remove("/START")
            set_clip("CAMPAIGN ACTIVE")

        if cp.state["active"]:
            now = datetime.now()
            allowed, msg = cp.can_run(now)
            if allowed:
                set_clip("STARTING...")
                try:
                    app = ui.get_app()
                    if app:
                        success, info = ui.automate(app)
                        if success:
                            cp.record(now.timestamp() + random.randint(0, 45))
                            set_clip(f"TEST {cp.state['total']}/30 OK")
                        else: set_clip(f"ERROR: {info}")
                    else: set_clip("ERROR: App not found")
                except Exception as e:
                    logging.exception("Failed")
                    set_clip(f"FATAL: {e}")
            else:
                set_clip(f"IDLE: {msg} ({cp.state['total']}/30)")
        
        time.sleep(20)

if __name__ == "__main__":
    main()
