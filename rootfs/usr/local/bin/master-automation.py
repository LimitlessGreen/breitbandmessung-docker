#!/usr/bin/env python3
import sys, time, os, logging, random, copy
from datetime import datetime, timedelta
from campaign import Campaign
from ui_utils import UI, set_clip, get_clip

# Try to load Rich for pretty tables
try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    HAS_RICH = True
except Exception:
    HAS_RICH = False

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def print_schedule_table(cp, title="Predicted Schedule"):
    if not HAS_RICH:
        logging.info("Rich not installed, skipping table.")
        return

    # Work on a deep copy of the campaign to not mess up the real state
    sim_cp = copy.deepcopy(cp)
    sim_cp.state["active"] = True
    
    # Simulation logic should start from 'now' or 'last test + gap'
    now = datetime.now().replace(second=0, microsecond=0)
    if sim_cp.state["last_ts"] > 0:
        last_dt = datetime.fromtimestamp(sim_cp.state["last_ts"])
        if now < last_dt + timedelta(minutes=5):
            now = last_dt + timedelta(minutes=5)

    console = Console()
    table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Test #", justify="right", style="dim")
    table.add_column("Day", justify="left")
    table.add_column("Predicted Time", justify="center", style="green")
    table.add_column("Status", justify="left")

    limit = 50
    while sim_cp.state["total"] < sim_cp.RULES["TOTAL"] and limit > 0:
        limit -= 1
        ok, msg = sim_cp.can_run(now)
        if ok:
            ts = now.timestamp() + 22 # Predict with average jitter
            sim_cp.record(ts)
            table.add_row(
                f"{sim_cp.state['total']:02d}/{sim_cp.RULES['TOTAL']}",
                now.strftime("%a, %Y-%m-%d"),
                now.strftime("%H:%M"),
                "[bold blue]Planned[/bold blue]"
            )
            now = datetime.fromtimestamp(ts) + timedelta(minutes=6) # 1min test + 5min gap
        else:
            if "Window" in msg or "Goal" in msg:
                s_h, s_m = map(int, sim_cp.prefs["START"].split(':'))
                next_day = (now + timedelta(days=1)).replace(hour=s_h, minute=s_m, second=0)
                now = next_day
            elif "Day" in msg or "Gap Day" in msg:
                now = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            elif "Wait" in msg:
                now += timedelta(minutes=5)
            elif "Expired" in msg: break
            else: now += timedelta(minutes=15)

    console.print(table)
    if sim_cp.state["total"] < sim_cp.RULES["TOTAL"]:
        console.print(f"[bold red]Warning:[/bold red] Only {sim_cp.state['total']}/{sim_cp.RULES['TOTAL']} tests possible in simulation!")

def run_simulation(cp):
    logging.info("--- Solver Test Mode ---")
    print_schedule_table(cp, title="Full Campaign Simulation")
    logging.info("--- End Simulation ---")

def main():
    cp = Campaign()
    if "--test-solver" in sys.argv: return run_simulation(cp)

    logging.info("Automation Service Active.")
    print_schedule_table(cp, title="Current Campaign Prediction")
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
