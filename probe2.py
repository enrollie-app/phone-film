"""One phone at a time, each Safari layout in turn with no restart between, and every reading pushed the moment it's taken."""
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import threading
import time

OUT = os.environ["OUT"]
FIRST = os.environ["U"]
RUNTIME = os.environ["RUNTIME"]
NAME = os.environ["NAME"]
PORT = 8899
HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = open(os.path.join(HERE, "probe.html"), "rb").read()
RESULTS = os.path.join(os.getcwd(), "results")
SAFARI = "com.apple.mobilesafari"
KEY = "PreferredCapsuleLayoutStyle"
VALUES = (None, 0, 1, 2, 3)
# The phone the job booted comes first, then one more at a time: the iPhone 14's size, the home-button size, the largest.
MORE = {
    "ios-27": [("iPhone-17e", "small"), ("iPhone-SE-3rd-generation", "se"), ("iPhone-18-Pro-Max", "promax")],
    "ios-26": [("iPhone-16e", "small"), ("iPhone-SE-3rd-generation", "se"), ("iPhone-17-Pro-Max", "promax")],
}[NAME]

latest = {}
changed = threading.Condition()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(PROBE)
        except BrokenPipeError:
            pass

    def do_POST(self):
        size = int(self.headers.get("content-length", 0))
        rows = json.loads(self.rfile.read(size))
        with changed:
            for row in rows:
                latest[row["label"]] = row
            changed.notify_all()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def run(*args, timeout=120):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("timed out:", args[:5], flush=True)
        return subprocess.CompletedProcess(args, 124, "", "timeout")


def push(message):
    run("git", "add", "-A", "results")
    run("git", "-c", "user.name=phone-film", "-c", "user.email=phone-film@users.noreply.github.com", "commit", "-qm", message)
    done = run("git", "push", "-qf", "origin", f"HEAD:refs/heads/results-{NAME}")
    if done.returncode != 0:
        print("push failed:", done.stderr.strip()[:200], flush=True)


def domain_of(udid):
    data = run("xcrun", "simctl", "get_app_container", udid, SAFARI, "data").stdout.strip()
    return os.path.join(data, "Library/Preferences/com.apple.mobilesafari")


def open_page(udid, label):
    with changed:
        latest.pop(label, None)
    run("xcrun", "simctl", "openurl", udid, f"http://127.0.0.1:{PORT}/probe.html?label={label}")
    with changed:
        return changed.wait_for(lambda: label in latest, timeout=40)


def take(udid, tag, value, domain):
    suffix = "none" if value is None else str(value)
    label = f"{tag}-v{suffix}"
    run("xcrun", "simctl", "terminate", udid, SAFARI)
    if value is None:
        run("xcrun", "simctl", "spawn", udid, "defaults", "delete", domain, KEY)
    else:
        run("xcrun", "simctl", "spawn", udid, "defaults", "write", domain, KEY, "-int", str(value))
    time.sleep(1)
    got = open_page(udid, label) or open_page(udid, label)
    # The bar slides in a moment after the page; the picture says which layout this setting is.
    time.sleep(1.5)
    picture = os.path.join(RESULTS, f"{label}.png")
    run("xcrun", "simctl", "io", udid, "screenshot", picture)
    if not got:
        print("no reading:", label, flush=True)
        with open(os.path.join(RESULTS, f"{label}.json"), "w") as out:
            json.dump({"label": label, "phone": tag, "value": value, "failed": True}, out)
    else:
        row = dict(latest[label], phone=tag, value=value)
        with open(os.path.join(RESULTS, f"{label}.json"), "w") as out:
            json.dump(row, out)
        print(label, "screen", row["screenW"], row["screenH"], "innerH", row["innerH"], "svh", row["svh"], "lvh", row["lvh"],
              "gap", round(row["lvh"] - row["svh"], 2), flush=True)
    push(label)


def measure_phone(udid, tag):
    open_page(udid, f"{tag}-first")
    time.sleep(2)
    domain = domain_of(udid)
    for value in VALUES:
        take(udid, tag, value, domain)


def main():
    os.makedirs(RESULTS, exist_ok=True)
    run("git", "checkout", "-q", "-B", f"results-{NAME}")
    server = Server(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    measure_phone(FIRST, "pro")
    run("xcrun", "simctl", "shutdown", FIRST)
    for kind, tag in MORE:
        made = run("xcrun", "simctl", "create", f"probe-{tag}", f"com.apple.CoreSimulator.SimDeviceType.{kind}",
                   f"com.apple.CoreSimulator.SimRuntime.{RUNTIME}")
        if made.returncode != 0:
            print("no such phone here:", kind, made.stderr.strip()[:140], flush=True)
            continue
        udid = made.stdout.strip()
        run("xcrun", "simctl", "boot", udid)
        run("xcrun", "simctl", "bootstatus", udid, "-b", timeout=300)
        time.sleep(3)
        measure_phone(udid, tag)
        run("xcrun", "simctl", "shutdown", udid)
    with open(os.path.join(RESULTS, "done.json"), "w") as out:
        json.dump({"done": True}, out)
    push("done")
    shutil.copytree(RESULTS, os.path.join(OUT, "results"), dirs_exist_ok=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
