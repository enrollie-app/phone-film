"""One clean take of iOS 27's Add to Home Screen steps, at a calm pace."""
import json
import os
import subprocess
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
    run("xcrun", "simctl", "io", U, "screenshot", f"{OUT}/{name}.png")
    mark(f"shot {name}")


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


def labels(name):
    nodes = tree()
    with open(f"{OUT}/{name}.json", "w") as out:
        json.dump(nodes, out)
    for node in walk(nodes):
        frame = node.get("frame") or {}
        if node.get("AXLabel") and node.get("type") != "StaticText":
            print(node.get("type"), repr(node.get("AXLabel"))[:50], int(frame.get("x", 0)), int(frame.get("y", 0)), int(frame.get("width", 0)), int(frame.get("height", 0)), flush=True)
    return nodes


def tap_xy(x, y):
    mark(f"tap {x} {y}")
    done = run("axe", "tap", "-x", str(x), "-y", str(y), "--tap-style", "physical", "--udid", U)
    mark(f"tapped {done.stdout.strip()[:40]} {done.stderr.strip()[:100]}")


run("xcrun", "simctl", "openurl", U, PAGE)
time.sleep(12)
shot("10-page")
time.sleep(1.5)
tap_xy(114, 816)  # the menu button in the address bar
time.sleep(3.2)
shot("20-menu")
time.sleep(0.8)
tap_xy(207, 351)  # Share
time.sleep(6.5)
shot("30-sheet")
time.sleep(0.8)
mark("swipe")
run("axe", "swipe", "--start-x", "300", "--start-y", "560", "--end-x", "300", "--end-y", "160", "--duration", "0.5", "--udid", U)
mark("swiped")
time.sleep(3.5)
shot("31-sheet-up")
time.sleep(0.8)
tap_xy(155, 637)  # Add to Home Screen
time.sleep(5)
shot("40-add")
nodes = labels("40-add")
add = None
for node in walk(nodes):
    if node.get("AXLabel") == "Add" and node.get("type") == "Button":
        add = node
time.sleep(0.8)
if add is not None:
    frame = add["frame"]
    tap_xy(int(frame["x"] + frame["width"] / 2), int(frame["y"] + frame["height"] / 2))
else:
    tap_xy(370, 100)
time.sleep(6)
shot("50-home")
labels("50-home")
