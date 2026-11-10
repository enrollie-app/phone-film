"""One clean take of iOS 27's Add to Home Screen steps, English or Spanish.
The phone is left alone while each animation runs, so the recording stays smooth, then one picture confirms the step."""
import json
import os
import subprocess
import sys
import time

U = os.environ["U"]
OUT = os.environ["OUT"]
SPANISH = os.environ.get("FILM_LANG") == "es"
PAGE = "https://enrollie.app/"
SHARE = ("Compartir",) if SPANISH else ("Share",)
ADD = ("Agregar", "Añadir") if SPANISH else ("Add",)
CONTINUE = ("Continuar", "Continue")
ADD_XY = (362, 100) if SPANISH else (370, 100)
# Share sits behind ••• on iOS 26 and behind ≡ on iOS 27.
MENU_XY = (344, 816) if os.environ.get("NAME") == "ios-26" else (114, 816)
START = time.time()


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def mark(what):
    print(f"{time.time() - START:7.2f} {what}", flush=True)


def shot(name):
    path = f"{OUT}/{name}.png"
    run("xcrun", "simctl", "io", U, "screenshot", path)
    mark(f"shot {name}")
    return os.path.getsize(path)


def tree():
    done = run("axe", "describe-ui", "--udid", U)
    try:
        return json.loads(done.stdout)
    except ValueError:
        return []


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get("children") or [])


def find(*names):
    for node in walk(tree()):
        if node.get("AXLabel") in names:
            return node
    return None


def tap_xy(x, y):
    for _ in range(4):
        mark(f"tap {x} {y}")
        done = run("axe", "tap", "-x", str(x), "-y", str(y), "--tap-style", "physical", "--udid", U)
        mark(f"tapped {done.stdout.strip()[:40]} {done.stderr.strip()[:100]}")
        if "completed" in done.stdout:
            return
        time.sleep(2)
    sys.exit("tap kept failing")


def center(node):
    frame = node["frame"]
    return int(frame["x"] + frame["width"] / 2), int(frame["y"] + frame["height"] / 2)


def settled(before, name, wait):
    """Leaves the phone alone for the animation, then checks the screen changed."""
    time.sleep(wait)
    size = shot(name)
    tries = 0
    while abs(size - before) <= before * 0.04:
        tries += 1
        if tries > 3:
            sys.exit(f"screen never changed at {name}")
        time.sleep(8)
        size = shot(f"{name}-{tries}")
    return size


run("xcrun", "simctl", "openurl", U, PAGE)
time.sleep(14)
for _ in range(4):
    if tree():
        break
    time.sleep(3)
mark("ready")
shot("10-page")
time.sleep(1.5)

# The menu button, then Share from the menu that opens.
share = None
for _ in range(4):
    tap_xy(*MENU_XY)
    time.sleep(2.5)
    for _ in range(5):
        share = find(*SHARE)
        if share is not None:
            break
        time.sleep(1.2)
    if share is not None:
        break
    mark("menu did not open, again")
if share is None:
    sys.exit("menu never opened")
mark("menu open")
time.sleep(1.2)
before = shot("21-menu")
tap_xy(*center(share))
settled(before, "30-sheet", 18)
time.sleep(1.5)
before = shot("31-sheet")
time.sleep(0.8)
mark("swipe")
run("axe", "swipe", "--start-x", "300", "--start-y", "560", "--end-x", "300", "--end-y", "160", "--duration", "0.5", "--udid", U)
mark("swiped")
time.sleep(5)
before = shot("32-sheet-up")
time.sleep(0.8)
tap_xy(155, 637)  # Add to Home Screen
settled(before, "40-add", 22)
nodes = tree()
popup = next((n for n in walk(nodes) if n.get("AXLabel") in CONTINUE), None)
if popup is not None:
    mark("keyboard popup")
    tap_xy(*center(popup))
    time.sleep(3)
    nodes = tree()
with open(f"{OUT}/41-add.json", "w") as out:
    json.dump(nodes, out)
for node in walk(nodes):
    frame = node.get("frame") or {}
    if node.get("AXLabel") and node.get("type") != "StaticText":
        print(node.get("type"), repr(node.get("AXLabel"))[:50], int(frame.get("x", 0)), int(frame.get("y", 0)), int(frame.get("width", 0)), int(frame.get("height", 0)), flush=True)
time.sleep(1.5)
before = shot("41-add")
time.sleep(1.0)
add = next((n for n in walk(nodes) if n.get("AXLabel") in ADD and n.get("type") == "Button"), None)
if add is not None:
    tap_xy(*center(add))
else:
    tap_xy(*ADD_XY)
settled(before, "50-home", 10)
time.sleep(8)
shot("51-home")
mark("done")
