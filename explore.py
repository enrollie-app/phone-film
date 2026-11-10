"""Walks Safari's Add to Home Screen steps once, keeping a picture and the on-screen labels at each step."""
import json
import os
import subprocess
import time

U = os.environ["U"]
OUT = os.environ["OUT"]


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def tree():
    done = run("axe", "describe-ui", "--udid", U)
    try:
        return json.loads(done.stdout)
    except ValueError:
        print("describe-ui failed:", done.stdout[:300], done.stderr[:300])
        return []


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get("children") or [])


def snap(name):
    run("xcrun", "simctl", "io", U, "screenshot", f"{OUT}/{name}.png")
    nodes = tree()
    with open(f"{OUT}/{name}.json", "w") as out:
        json.dump(nodes, out)
    print(f"--- {name}")
    for node in walk(nodes):
        if node.get("AXLabel"):
            print(node.get("type"), repr(node.get("AXLabel")), node.get("frame"))


def find(*labels):
    for node in walk(tree()):
        if node.get("AXLabel") in labels:
            return node
    return None


def tap_xy(x, y):
    done = run("axe", "tap", "-x", str(x), "-y", str(y), "--tap-style", "physical", "--udid", U)
    print("tap", x, y, done.stdout.strip()[:120], done.stderr.strip()[:200])


def tap(*labels):
    node = find(*labels)
    if node is None:
        print("NOT FOUND", labels)
        return False
    frame = node["frame"]
    tap_xy(int(frame["x"] + frame["width"] / 2), int(frame["y"] + frame["height"] / 2))
    return True


time.sleep(12)
snap("01-page")
if not tap("Share"):
    tap("More", "Page Menu", "Menu", "More options", "Page menu")
    time.sleep(2.5)
    snap("02-menu")
    tap("Share")
time.sleep(3)
snap("03-sheet")
if find("Add to Home Screen") is None:
    done = run("axe", "swipe", "--start-x", "300", "--start-y", "560", "--end-x", "300", "--end-y", "160", "--duration", "0.5", "--udid", U)
    print("swipe", done.stdout.strip()[:120], done.stderr.strip()[:200])
    time.sleep(2.5)
    snap("04-sheet-up")
if not tap("Add to Home Screen"):
    tap("More")
    time.sleep(2.5)
    snap("04b-more-actions")
    tap("Add to Home Screen")
time.sleep(3.5)
snap("05-add")
tap("Add")
time.sleep(5)
snap("06-after-add")
