"""One take of the iPhone alert video: make Enrollie's alerts stay on screen (Banner Style, Persistent), English or Spanish.
Off camera first: the film page (web/app, served on this runner at localhost:8080) goes on the Home Screen as Enrollie and
its alerts are allowed. On camera: Home Screen, Settings, Notifications, Enrollie, Banner Style, Persistent, Home. Then a
test alert arrives and stays. Every step prints its time, so the cut can find it; a picture confirms each step."""
import json
import os
import subprocess
import sys
import time

U = os.environ["U"]
OUT = os.environ["OUT"]
SPANISH = os.environ.get("FILM_LANG") == "es"
PAGE = "http://localhost:8080/app/"
SHARE = ("Compartir",) if SPANISH else ("Share",)
ADD = ("Agregar", "Añadir") if SPANISH else ("Add",)
ADD_HOME = ("Agregar a inicio", "Agregar a pantalla de inicio", "Añadir a pantalla de inicio") if SPANISH else ("Add to Home Screen",)
CONTINUE = ("Continuar", "Continue")
ALLOW = ("Permitir",) if SPANISH else ("Allow",)
SETTINGS = ("Configuración", "Ajustes") if SPANISH else ("Settings",)
NOTIFICATIONS = ("Notificaciones",) if SPANISH else ("Notifications",)
STYLE = ("Estilo de tiras", "Estilo de tira", "Estilo de las tiras", "Estilo de avisos", "Estilo") if SPANISH else ("Banner Style",)
PERSISTENT = ("Persistente", "Persistentes", "Permanente", "Permanentes") if SPANISH else ("Persistent",)
TITLE = "Alerta de prueba" if SPANISH else "Test alert"
ADD_XY = (362, 100) if SPANISH else (370, 100)
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
    return os.path.getsize(path) if os.path.exists(path) else 0


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


def dump(name):
    nodes = tree()
    with open(f"{OUT}/{name}.json", "w") as out:
        json.dump(nodes, out)
    for node in walk(nodes):
        frame = node.get("frame") or {}
        label = node.get("AXLabel")
        if label:
            print("  ", node.get("type"), repr(label)[:60], repr(node.get("AXValue"))[:30], int(frame.get("x", 0)),
                  int(frame.get("y", 0)), int(frame.get("width", 0)), int(frame.get("height", 0)), flush=True)
    return nodes


def find(*names, nodes=None, loose=False):
    """Exact label first; with loose, a label that starts with or holds one of the names."""
    nodes = list(walk(nodes if nodes is not None else tree()))
    for node in nodes:
        if node.get("AXLabel") in names:
            return node
    if loose:
        wanted = [n.lower() for n in names]
        for node in nodes:
            label = (node.get("AXLabel") or "").lower()
            if label and any(label.startswith(w) for w in wanted):
                return node
        for node in nodes:
            label = (node.get("AXLabel") or "").lower()
            if label and any(w in label for w in wanted):
                return node
    return None


def tap_xy(x, y):
    for _ in range(4):
        mark(f"tap {x} {y}")
        done = run("axe", "tap", "-x", str(x), "-y", str(y), "--tap-style", "physical", "--udid", U)
        if "completed" in done.stdout:
            return
        mark(f"tap again: {done.stdout.strip()[:40]} {done.stderr.strip()[:100]}")
        time.sleep(2)
    sys.exit("tap kept failing")


def center(node):
    frame = node["frame"]
    return int(frame["x"] + frame["width"] / 2), int(frame["y"] + frame["height"] / 2)


def tap(node, what):
    mark(f"step {what}")
    tap_xy(*center(node))


def home():
    mark("home button")
    done = run("axe", "button", "home", "--udid", U)
    if "rror" in (done.stdout + done.stderr):
        mark(f"home said {done.stdout.strip()[:60]} {done.stderr.strip()[:120]}")


def swipe(y1, y2, x1=200, x2=200, duration="0.4"):
    run("axe", "swipe", "--start-x", str(x1), "--start-y", str(y1), "--end-x", str(x2), "--end-y", str(y2),
        "--duration", duration, "--udid", U)


def wait_for(names, what, tries=6, pause=1.5, loose=False, scroll=False):
    for i in range(tries):
        node = find(*names, loose=loose)
        if node is not None:
            return node
        if scroll and i >= 1:
            mark(f"scroll for {what}")
            swipe(640, 340)
        time.sleep(pause)
    dump(f"missing-{what}")
    shot(f"missing-{what}")
    sys.exit(f"never found {what}")


# Off camera: the film page on the Home Screen, as Enrollie.
run("xcrun", "simctl", "openurl", U, PAGE)
time.sleep(10)
for _ in range(4):
    if tree():
        break
    time.sleep(3)
mark("page ready")
shot("10-page")
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
    dump("missing-menu")
    sys.exit("menu never opened")
tap_xy(*center(share))
time.sleep(6)
swipe(560, 160, 300, 300, "0.5")
time.sleep(3)
row = find(*ADD_HOME, loose=True)
shot("20-sheet")
tap_xy(*(center(row) if row is not None else (155, 637)))
time.sleep(5)
if os.environ.get("NAME") == "ios-26":
    time.sleep(3)
    tap_xy(201, 829)
    time.sleep(4)
nodes = tree()
popup = find(*CONTINUE, nodes=nodes)
if popup is not None:
    tap_xy(*center(popup))
    time.sleep(3)
    nodes = tree()
add = next((n for n in walk(nodes) if n.get("AXLabel") in ADD and n.get("type") == "Button"), None)
tap_xy(*(center(add) if add is not None else ADD_XY))
time.sleep(6)
shot("30-home")

# Open it from the Home Screen and allow its alerts.
icon = find("Enrollie")
if icon is None:
    swipe(400, 400, 360, 40)
    time.sleep(2)
    icon = wait_for(("Enrollie",), "icon")
tap(icon, "open Enrollie")
time.sleep(6)
dump("40-app")
# The page's buttons (web content has no labels here): Allow alerts, Send a test alert, Send one now, in points.
ALLOW_PAGE, SEND_PAGE, NOW_PAGE = (201, 277), (201, 341), (201, 405)
button = find("Allow alerts", loose=True)
tap_xy(*(center(button) if button is not None else ALLOW_PAGE))
time.sleep(3)
allow = find(*ALLOW)
if allow is None:
    shot("40-no-prompt")
    tap_xy(*ALLOW_PAGE)
    time.sleep(3)
allow = wait_for(ALLOW, "allow")
tap(allow, "allow alerts")
time.sleep(3)
shot("41-allowed")
home()
time.sleep(2)
home()
time.sleep(3)

# On camera.
mark("FILM home screen")
shot("50-home")
dump("50-home")
time.sleep(2)
tap(wait_for(SETTINGS, "settings"), "FILM settings")
time.sleep(3.5)
shot("51-settings")
tap(wait_for(NOTIFICATIONS, "notifications", scroll=True), "FILM notifications")
time.sleep(3)
shot("52-notifications")
dump("52-notifications")
tap(wait_for(("Enrollie",), "enrollie row", tries=8, scroll=True), "FILM enrollie row")
time.sleep(3)
shot("53-enrollie")
dump("53-enrollie")
tap(wait_for(STYLE, "banner style", tries=8, loose=True, scroll=True), "FILM banner style")
time.sleep(3)
shot("54-style")
dump("54-style")
tap(wait_for(PERSISTENT, "persistent", loose=True), "FILM persistent")
time.sleep(3)
shot("55-persistent")
home()
mark("FILM home after")
time.sleep(3)
shot("56-home")

# Off camera: ask the film page for a test alert, then the Home Screen, where it arrives and stays.
icon = find("Enrollie")
if icon is None:
    swipe(400, 400, 360, 40)
    time.sleep(2)
    icon = wait_for(("Enrollie",), "icon again")
tap(icon, "open Enrollie again")
time.sleep(5)
send = find("Send a test alert", loose=True)
tap_xy(*(center(send) if send is not None else SEND_PAGE))
home()
mark("FILM waiting for the alert")
seen = False
for i in range(8):
    time.sleep(1.5)
    if find(TITLE, loose=True) is not None:
        seen = True
        mark("FILM alert on screen")
        break
if not seen:
    mark("no alert from the worker's wait; asking for one now with the app open")
    icon = find("Enrollie")
    if icon is not None:
        tap(icon, "open Enrollie for now")
        time.sleep(4)
        now = find("Send one now", loose=True)
        tap_xy(*(center(now) if now is not None else NOW_PAGE))
        for i in range(8):
            time.sleep(1.5)
            if find(TITLE, loose=True) is not None:
                seen = True
                mark("FILM alert on screen (app open)")
                break
        home()
shot("60-alert")
dump("60-alert")
time.sleep(10)
shot("61-alert-10s")
print("still there after 10 s:", find(TITLE, loose=True) is not None, flush=True)
time.sleep(6)
mark("done")
sys.exit(0 if seen else 3)
