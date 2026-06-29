"""
Watches agent-console for file saves, re-indexes the knowledge graph
incrementally on every change, and prints the real blast radius of the
edit (which functions/components got impacted). Leave the graph UI
(localhost:9749) open in a browser while this runs — it auto-polls
index-status, so the 3D view should update itself live as you code.
"""

import json
import os
import subprocess
import time

REPO = "/Users/akshaysharma/Documents/Claude/Projects/Akshay-bnb/agent-console"
PROJECT = "Users-akshaysharma-Documents-Claude-Projects-Akshay-bnb-agent-console"
WATCH_EXTS = (".ts", ".tsx", ".js", ".jsx")
IGNORE_DIRS = {"node_modules", ".next", ".git"}

ENV = dict(os.environ)
ENV["PATH"] = f"/Users/akshaysharma/.local/bin:{ENV.get('PATH', '')}"


def cmmcp(*args):
    out = subprocess.run(
        ["codebase-memory-mcp", "cli", *args],
        capture_output=True,
        text=True,
        env=ENV,
    )
    line = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "{}"
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {"raw": out.stdout, "stderr": out.stderr}


def snapshot_mtimes():
    snap = {}
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f.endswith(WATCH_EXTS):
                path = os.path.join(root, f)
                try:
                    snap[path] = os.path.getmtime(path)
                except FileNotFoundError:
                    pass
    return snap


def main():
    print(f"Watching {REPO} for changes. Ctrl+C to stop.")
    print("Keep http://localhost:9749 open in a browser to see it update live.\n")
    last = snapshot_mtimes()

    while True:
        time.sleep(1)
        now = snapshot_mtimes()
        changed = [p for p, t in now.items() if last.get(p) != t]
        if not changed:
            last = now
            continue

        for path in changed:
            rel = os.path.relpath(path, REPO)
            print(f"\033[33m[changed]\033[0m {rel}")

        result = cmmcp("index_repository", json.dumps({"repo_path": REPO}))
        print(
            f"\033[32m[reindexed]\033[0m nodes={result.get('nodes')} "
            f"edges={result.get('edges')}"
        )

        blast = cmmcp("detect_changes", json.dumps({"project": PROJECT}))
        impacted = blast.get("impacted_symbols", [])
        if impacted:
            print(f"\033[36m[blast radius]\033[0m {len(impacted)} symbols affected:")
            for sym in impacted[:10]:
                print(f"  - {sym['label']}: {sym['name']}  ({sym['file']})")
            if len(impacted) > 10:
                print(f"  ... and {len(impacted) - 10} more")
        print()

        last = now


if __name__ == "__main__":
    main()
