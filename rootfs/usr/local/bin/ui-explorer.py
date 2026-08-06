#!/usr/bin/env python3
import sys

try:
    import pyatspi
except ImportError:
    print("pyatspi not found.")
    sys.exit(1)

def print_hierarchy(obj, indent=0, max_depth=20):
    if indent > max_depth:
        return
    try:
        name = obj.name
        role = obj.get_role_name()
        
        extents = ""
        try:
            comp = obj.queryComponent()
            bbox = comp.getExtents(pyatspi.XY_SCREEN)
            extents = f" BBox: ({bbox.x}, {bbox.y}, {bbox.width}, {bbox.height})"
        except:
            pass

        # Print EVERYTHING
        print("  " * indent + f"[{role}] Name: '{name}'{extents}")
        
        # If it's a known container role that might have the input, or if it's an entry
        if role in ["entry", "text", "combo box"]:
             print("  " * (indent+1) + f"!! POTENTIAL INPUT !! Role: {role}, Name: {name}")

        for i in range(obj.get_child_count()):
            child = obj.get_child_at_index(i)
            if child:
                print_hierarchy(child, indent + 1, max_depth)
    except:
        pass

def main():
    print("Searching for applications...")
    try:
        # pyatspi.Registry is the entry point
        desktop_count = pyatspi.Registry.getDesktopCount()
        for i in range(desktop_count):
            desktop = pyatspi.Registry.getDesktop(i)
            for j in range(desktop.get_child_count()):
                app = desktop.get_child_at_index(j)
                if app and "breitbandmessung" in app.name.lower():
                    print(f"Found: {app.name}")
                    print_hierarchy(app)
                    return
        print("Application 'Breitbandmessung' not found.")
    except Exception as e:
        print(f"Error accessing Accessibility Registry: {e}")
        print("Make sure the Accessibility Bus is running (at-spi2-core).")

if __name__ == "__main__":
    main()
