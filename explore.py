"""Walks Safari's Add to Home Screen steps on the public page, keeping a picture and the on-screen labels at each step."""
import json
import os
import subprocess
import time

U = os.environ["U"]
OUT = os.environ["OUT"]
PAGE = "https://enrollie.app/"


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def tree():
    done = run("axe", "describe-ui", "--udid", U)
    try:
        return json.loads(done.stdout)
    except ValueError:
        print("describe-ui failed:", done.stdout[:300], done.stderr[:300], flush=True)
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
    print(f"--- {name}", flush=True)
    for node in walk(nodes):
        frame = node.get("frame") or {}
        if node.get("AXLabel") and node.get("type") != "StaticText":
            print(
                node.get("type"),
                repr(node.get("AXLabel"))[:60],
                int(frame.get("x", 0)),
                int(frame.get("y", 0)),
                int(frame.get("width", 0)),
                int(frame.get("height", 0)),
                flush=True,
            )


def find(*labels):
    for node in walk(tree()):
        if node.get("AXLabel") in labels:
            return node
    return None


def tap_xy(x, y):
    done = run("axe", "tap", "-x", str(x), "-y", str(y), "--tap-style", "physical", "--udid", U)
    print("tap", x, y, done.stdout.strip()[:80], done.stderr.strip()[:200], flush=True)


def press_xy(x, y, seconds=1.2):
    done = run("axe", "touch", "-x", str(x), "-y", str(y), "--down", "--up", "--delay", str(seconds), "--udid", U)
    print("press", x, y, done.stdout.strip()[:80], done.stderr.strip()[:200], flush=True)


def center(node):
    frame = node["frame"]
    return int(frame["x"] + frame["width"] / 2), int(frame["y"] + frame["height"] / 2)


def tap(*labels):
    node = find(*labels)
    if node is None:
        print("NOT FOUND", labels, flush=True)
        return False
    tap_xy(*center(node))
    return True


def open_page():
    run("xcrun", "simctl", "openurl", U, PAGE)
    time.sleep(9)


def try_for_share():
    """Each way a bar might reach Share. Returns True once Share has been tapped."""
    if tap("Share"):
        return True
    for label in ("More", "Page Menu", "Page menu", "Website Settings", "Page Settings", "Menu"):
        if find(label) is not None:
            tap(label)
            time.sleep(2.5)
            snap(f"20-after-{label.replace(' ', '-')}")
            if tap("Share"):
                return True
            open_page()

    pill = find("Address") or find("Address and Search")
    spots = [("pill-tap", tap_xy, center(pill) if pill else (201, 816))]
    spots.append(("pill-press", press_xy, center(pill) if pill else (201, 816)))
    tabs = find("Tabs")
    if tabs is not None:
        spots.append(("tabs-press", press_xy, center(tabs)))
    back = find("Back")
    if back is not None:
        spots.append(("back-press", press_xy, center(back)))
    for name, action, where in spots:
        action(*where)
        time.sleep(2.5)
        snap(f"21-{name}")
        if tap("Share"):
            return True
        open_page()
    return False


open_page()
snap("10-page")
if try_for_share():
    time.sleep(3)
    snap("30-sheet")
    if find("Add to Home Screen") is None:
        done = run("axe", "swipe", "--start-x", "300", "--start-y", "560", "--end-x", "300", "--end-y", "160", "--duration", "0.5", "--udid", U)
        print("swipe", done.stdout.strip()[:80], done.stderr.strip()[:200], flush=True)
        time.sleep(2.5)
        snap("31-sheet-up")
    if not tap("Add to Home Screen"):
        tap("More")
        time.sleep(2.5)
        snap("32-more-actions")
        tap("Add to Home Screen")
    time.sleep(3.5)
    snap("40-add")
    tap("Add")
    time.sleep(5)
    snap("50-after-add")
else:
    print("NO SHARE FOUND", flush=True)
