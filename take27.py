"""One clean take of iOS 27's Add to Home Screen steps. Each step is confirmed on screen before the next one starts."""
import json
import os
import subprocess
import sys
import time

U = os.environ["U"]
OUT = os.environ["OUT"]
PAGE = "https://enrollie.app/"
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


def changes(before, name, seconds=16):
    """Waits until the screen looks different from the picture size given."""
    end = time.time() + seconds
    n = 0
    while time.time() < end:
        time.sleep(1)
        n += 1
        size = shot(f"{name}-{n}")
        if abs(size - before) > before * 0.04:
            return size
    sys.exit(f"screen never changed at {name}")


run("xcrun", "simctl", "openurl", U, PAGE)
time.sleep(12)
for _ in range(3):
    if find("Page Menu") is not None:
        break
    time.sleep(3)
mark("ready")
time.sleep(1.5)

# The menu button, then Share from the menu that opens.
share = None
for _ in range(4):
    tap_xy(114, 816)
    for _ in range(5):
        time.sleep(1.2)
        share = find("Share")
        if share is not None:
            break
    if share is not None:
        break
    mark("menu did not open, again")
if share is None:
    sys.exit("menu never opened")
mark("menu open")
shot("20-menu")
time.sleep(1.2)
before = shot("21-before-share")
tap_xy(*center(share))
changes(before, "30-sheet")
time.sleep(2.5)
before = shot("31-sheet")
time.sleep(0.8)
mark("swipe")
run("axe", "swipe", "--start-x", "300", "--start-y", "560", "--end-x", "300", "--end-y", "160", "--duration", "0.5", "--udid", U)
mark("swiped")
time.sleep(3)
before = shot("32-sheet-up")
time.sleep(0.8)
tap_xy(155, 637)  # Add to Home Screen
changes(before, "40-add")
time.sleep(2.5)
before = shot("41-add")
nodes = tree()
with open(f"{OUT}/41-add.json", "w") as out:
    json.dump(nodes, out)
for node in walk(nodes):
    frame = node.get("frame") or {}
    if node.get("AXLabel") and node.get("type") != "StaticText":
        print(node.get("type"), repr(node.get("AXLabel"))[:50], int(frame.get("x", 0)), int(frame.get("y", 0)), int(frame.get("width", 0)), int(frame.get("height", 0)), flush=True)
time.sleep(0.8)
add = next((n for n in walk(nodes) if n.get("AXLabel") == "Add" and n.get("type") == "Button"), None)
if add is not None:
    tap_xy(*center(add))
else:
    tap_xy(370, 100)
changes(before, "50-home")
time.sleep(5)
shot("51-home")
mark("done")
