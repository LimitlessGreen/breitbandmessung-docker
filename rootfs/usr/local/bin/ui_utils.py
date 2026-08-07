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

    def automate(self, app):
        # Navigation
        btn = self.find(app, "Akzeptieren", "button")
        if btn: btn.queryAction().doAction(0); time.sleep(2)
        
        if self.find(app, "Nutzerangaben vervollständigen", "button"):
            return False, "Setup missing"

        menu = self.wait(app, "Messkampagne", "menu item")
        if menu: menu.queryAction().doAction(0); time.sleep(2)

        start = self.wait(app, "Messung durchführen", "button")
        if not start: return (True, "Running") if self.find(app, "Die Downloadmessung wird durchgeführt.", "static") else (False, "No Start Button")
        start.queryAction().doAction(0); time.sleep(3)

        # Checkboxes
        cbs = []
        def find_cbs(o):
            if o.get_role_name() == "check box": cbs.append(o)
            for i in range(o.get_child_count()): find_cbs(o.get_child_at_index(i))
        find_cbs(app)
        for cb in cbs: cb.queryAction().doAction(0)

        go = self.wait(app, "Messung starten", "button")
        if go: go.queryAction().doAction(0); time.sleep(3)

        dlg = self.find(app, "Standortfreigabe", "dialog")
        if dlg:
            no = self.find(dlg, "Nein", "button")
            if no: no.queryAction().doAction(0); time.sleep(2)

        return (True, "Started") if self.wait(app, "Die Downloadmessung wird durchgeführt.", "static") else (False, "Confirm failed")
