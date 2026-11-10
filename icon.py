"""Opens the live install page in Compact on one phone, for the drawn first-step icon (6165 task 29) and pushes a picture of each the moment it's taken."""
import os
import subprocess
import time

U = os.environ["U"]
NAME = os.environ["NAME"]
RESULTS = os.path.join(os.getcwd(), "results")
SAFARI = "com.apple.mobilesafari"
KEY = "PreferredCapsuleLayoutStyle"
PAGE = "https://enrollie.app/"
LAYOUTS = (("compact", 0),)


def run(*args, timeout=120):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("timed out:", args[:5], flush=True)
        return subprocess.CompletedProcess(args, 124, "", "timeout")


def push(message):
    run("git", "add", "-A", "results")
    run("git", "-c", "user.name=phone-film", "-c", "user.email=phone-film@users.noreply.github.com", "commit", "-qm", message)
    done = run("git", "push", "-qf", "origin", f"HEAD:refs/heads/icon-{NAME}")
    if done.returncode != 0:
        print("push failed:", done.stderr.strip()[:200], flush=True)


def main():
    os.makedirs(RESULTS, exist_ok=True)
    run("git", "checkout", "-q", "-B", f"icon-{NAME}")
    data = run("xcrun", "simctl", "get_app_container", U, SAFARI, "data").stdout.strip()
    domain = os.path.join(data, "Library/Preferences/com.apple.mobilesafari")
    run("xcrun", "simctl", "openurl", U, PAGE)
    time.sleep(12)
    for name, value in LAYOUTS:
        run("xcrun", "simctl", "terminate", U, SAFARI)
        run("xcrun", "simctl", "spawn", U, "defaults", "write", domain, KEY, "-int", str(value))
        time.sleep(1)
        run("xcrun", "simctl", "openurl", U, PAGE)
        time.sleep(10)
        run("xcrun", "simctl", "io", U, "screenshot", os.path.join(RESULTS, f"{name}.png"))
        print("pictured", name, flush=True)
        push(name)
    with open(os.path.join(RESULTS, "done.txt"), "w") as out:
        out.write("done\n")
    push("done")


if __name__ == "__main__":
    main()
