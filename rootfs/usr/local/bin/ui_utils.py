import time
import subprocess
import logging

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def set_clip(text):
    logging.info(f"Clipboard: {text}")
    subprocess.run(f"echo '{text}' | xclip -selection clipboard", shell=True)

def get_clip():
    return run_cmd("xclip -o -selection clipboard 2>/dev/null")

class UI:
    """Simplified UI Automation helper."""
    def __init__(self):
        import pyatspi
        self.pyatspi = pyatspi

    def find(self, obj, name=None, role=None):
        try:
            if (not name or obj.name == name) and (not role or obj.get_role_name() == role): return obj
            for i in range(obj.get_child_count()):
                res = self.find(obj.get_child_at_index(i), name, role)
                if res: return res
        except: pass
        return None

    def wait(self, root, name=None, role=None, timeout=30):
        for _ in range(timeout):
            el = self.find(root, name, role)
            if el: return el
            time.sleep(1)
        return None

    def get_app(self):
        reg = self.pyatspi.Registry
        for i in range(reg.getDesktopCount()):
            d = reg.getDesktop(i)
            for j in range(d.get_child_count()):
                c = d.get_child_at_index(j)
                if c and "breitbandmessung" in c.name.lower(): return c
        return None

    def find_all(self, obj, role, results):
        try:
            if obj.get_role_name() == role: results.append(obj)
            for i in range(obj.get_child_count()): self.find_all(obj.get_child_at_index(i), role, results)
        except: pass

    def automate(self, app):
        # 0. Check if already running (Fast path)
        status_msg = "Die Downloadmessung wird durchgeführt."
        if self.find(app, status_msg, "static"):
            return True, "Already Running"

        # 1. Basic TOS
        tos = self.find(app, "Akzeptieren", "button")
        if tos: tos.queryAction().doAction(0); time.sleep(2)
        
        if self.find(app, "Nutzerangaben vervollständigen", "button"):
            return False, "Setup missing"

        # 2. Requirements Screen check (maybe we are already there?)
        go = self.find(app, "Messung starten", "button")
        if not go:
            # 3. Campaign Screen check
            start = self.find(app, "Messung durchführen", "button")
            if not start:
                # 4. We are likely on the wrong tab. Navigate back.
                logging.info("Main button missing. Navigating to 'Messkampagne' tab...")
                menu = self.find(app, "Messkampagne", "menu item")
                if menu:
                    menu.queryAction().doAction(0)
                    time.sleep(2)
                    start = self.wait(app, "Messung durchführen", "button")

            if start:
                start.queryAction().doAction(0)
                time.sleep(2)
                go = self.wait(app, "Messung starten", "button")

        # 5. Requirements Checkboxes (only if 'Messung starten' is visible)
        if go:
            cbs = []
            self.find_all(app, "check box", cbs)
            for cb in cbs:
                try:
                    # Check if already checked if possible, otherwise just click
                    cb.queryAction().doAction(0)
                except: pass
            
            go.queryAction().doAction(0)
            time.sleep(2)

        # 6. Location Dialog
        dlg = self.find(app, "Standortfreigabe", "dialog")
        if dlg:
            no = self.find(dlg, "Nein", "button")
            if no: no.queryAction().doAction(0); time.sleep(2)

        # 7. Final Verification
        if self.wait(app, status_msg, "static", timeout=5):
            return True, "Started"
        
        return False, "Failed to confirm start"
