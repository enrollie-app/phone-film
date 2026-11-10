"""Measures what a web page can see of Safari's layout, on several iPhone sizes and each layout setting."""
import http.server
import json
import os
import plistlib
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
SAFARI = "com.apple.mobilesafari"
KEY = "PreferredCapsuleLayoutStyle"
SIZES = {
    "ios-27": ["iPhone-18-Pro-Max", "iPhone-17e", "iPhone-SE-3rd-generation"],
    "ios-26": ["iPhone-17-Pro-Max", "iPhone-16e", "iPhone-SE-3rd-generation"],
}[NAME]


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(PROBE)

    def do_POST(self):
        size = int(self.headers.get("content-length", 0))
        body = self.rfile.read(size)
        with open(f"{OUT}/probe.jsonl", "a") as out:
            for row in json.loads(body):
                out.write(json.dumps(row) + "\n")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def run(*args, timeout=180):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("timed out:", args[:5], flush=True)
        return subprocess.CompletedProcess(args, 124, "", "timeout")


def plist_path(udid):
    done = run("xcrun", "simctl", "get_app_container", udid, SAFARI, "data")
    return os.path.join(done.stdout.strip(), "Library/Preferences/com.apple.mobilesafari.plist")


def set_layout(udid, value):
    """Writes the setting to Safari's own preferences while the phone is off, so nothing caches the old value."""
    path = plist_path(udid)
    run("xcrun", "simctl", "shutdown", udid)
    data = {}
    if os.path.exists(path):
        with open(path, "rb") as source:
            data = plistlib.load(source)
    if value is None:
        data.pop(KEY, None)
    else:
        data[KEY] = value
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as target:
        plistlib.dump(data, target)
    run("xcrun", "simctl", "boot", udid)
    run("xcrun", "simctl", "bootstatus", udid, "-b", timeout=300)
    time.sleep(3)


def measure(udid, label):
    run("xcrun", "simctl", "terminate", udid, SAFARI)
    time.sleep(1)
    run("xcrun", "simctl", "openurl", udid, f"http://127.0.0.1:{PORT}/probe.html?label={label}")
    time.sleep(12)
    run("xcrun", "simctl", "io", udid, "screenshot", f"{OUT}/{label}.png")
    print("measured", label, flush=True)


def main():
    server = Server(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # Safari has to have run once for its preferences file to exist.
    run("xcrun", "simctl", "openurl", FIRST, f"http://127.0.0.1:{PORT}/probe.html?label=first")
    time.sleep(10)
    with open(plist_path(FIRST), "rb") as source:
        print("settings before:", sorted(plistlib.load(source).keys())[:60], flush=True)
    phones = [(FIRST, "pro")]
    for kind in SIZES:
        made = run("xcrun", "simctl", "create", f"probe-{kind}",
                   f"com.apple.CoreSimulator.SimDeviceType.{kind}",
                   f"com.apple.CoreSimulator.SimRuntime.{RUNTIME}")
        if made.returncode != 0:
            print("no such phone here:", kind, made.stderr.strip()[:120], flush=True)
            continue
        udid = made.stdout.strip()
        run("xcrun", "simctl", "boot", udid)
        run("xcrun", "simctl", "bootstatus", udid, "-b", timeout=300)
        phones.append((udid, kind.replace("iPhone-", "").replace("-3rd-generation", "").lower()))
        run("xcrun", "simctl", "openurl", udid, f"http://127.0.0.1:{PORT}/probe.html?label=first-{phones[-1][1]}")
        time.sleep(10)
    for udid, tag in phones:
        for value in (None, 0, 1, 2, 3):
            set_layout(udid, value)
            measure(udid, f"{tag}-v{'none' if value is None else value}")
    print("done", flush=True)


if __name__ == "__main__":
    main()
