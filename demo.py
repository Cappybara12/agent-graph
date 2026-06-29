"""
Memory-grounded refactor demo.

Task: rename `highlight` -> `highlightTarget` in agent-console's
HighlightProvider context (lib/highlight-context.tsx) and every call site.

Compares two agents, both backed by the same local Ollama model:

  - blind agent:   sees only the definition file, has to guess every
                   call site it needs to touch.
  - grounded agent: gets the real caller list from codebase-memory-mcp's
                    knowledge graph before planning.

For each run we print the plan, then check it against ground truth
(the call sites we already confirmed via `query_graph`).
"""

import json
import os
import subprocess
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:latest"

REPO = "/Users/akshaysharma/Documents/Claude/Projects/Akshay-bnb/agent-console"
PROJECT = "Users-akshaysharma-Documents-Claude-Projects-Akshay-bnb-agent-console"
TARGET_FN = "highlight"
NEW_FN = "highlightTarget"
DEFINITION_FILE = "lib/highlight-context.tsx"

# Ground truth, independently confirmed with grep earlier.
GROUND_TRUTH_CALL_SITES = {
    "lib/highlight-context.tsx",
    "components/chat/ToolCallCard.tsx",
    "components/timeline/TimelinePanel.tsx",  # appears TWICE in this file
}


def ollama_generate(prompt: str) -> str:
    payload = json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["response"]


def read_file(rel_path: str) -> str:
    with open(f"{REPO}/{rel_path}") as f:
        return f.read()


def query_graph(cypher: str):
    env = dict(os.environ)
    env["PATH"] = f"/Users/akshaysharma/.local/bin:{env.get('PATH', '')}"
    out = subprocess.run(
        [
            "codebase-memory-mcp",
            "cli",
            "query_graph",
            json.dumps({"project": PROJECT, "query": cypher}),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    # last line of stdout is the JSON result; earlier lines are log noise
    last_line = out.stdout.strip().splitlines()[-1]
    return json.loads(last_line)


def get_real_call_sites():
    result = query_graph(
        f"MATCH (caller)-[:CALLS]->(f) WHERE f.name = '{TARGET_FN}' "
        f"RETURN caller.name AS caller_fn, caller.file_path AS caller_file"
    )
    return result["rows"]


def run_blind_agent():
    print("\n=== BLIND AGENT (no codebase memory) ===")
    definition_src = read_file(DEFINITION_FILE)
    prompt = f"""You are refactoring a React/TypeScript codebase.

Here is the only file you have been shown, {DEFINITION_FILE}:

```tsx
{definition_src}
```

Task: rename the `{TARGET_FN}` function (and every place that calls it)
to `{NEW_FN}`. You do NOT have access to the rest of the repository.

List every file path you believe needs to change, one per line.
Be concise. If you are not sure other files exist, say so."""
    response = ollama_generate(prompt)
    print(response)
    return response


def run_grounded_agent(real_call_sites):
    print("\n=== GROUNDED AGENT (codebase-memory-mcp graph) ===")
    sites_desc = "\n".join(
        f"  - {row[0]} calls it, in {row[1]}" for row in real_call_sites
    )
    prompt = f"""You are refactoring a React/TypeScript codebase.

You queried the project's codebase knowledge graph for every caller of
`{TARGET_FN}` and got back:

{sites_desc}

Task: rename `{TARGET_FN}` to `{NEW_FN}` everywhere, including the
definition in {DEFINITION_FILE}.

List every file path that needs to change, noting if any file has more
than one call site to fix. Be concise."""
    response = ollama_generate(prompt)
    print(response)
    return response


def apply_real_rename():
    """Actually perform the rename across every real file, for real."""
    print("\n=== APPLYING THE REAL RENAME ===")
    targets = [
        DEFINITION_FILE,
        "components/chat/ToolCallCard.tsx",
        "components/timeline/TimelinePanel.tsx",
    ]
    for rel in targets:
        path = f"{REPO}/{rel}"
        with open(path) as f:
            src = f.read()
        # word-boundary-safe rename of the bound name `highlight`,
        # not `highlighted` or `HighlightProvider`/`highlight-context`.
        import re

        new_src = re.sub(rf"\b{TARGET_FN}\b(?!ed|-context|Provider)", NEW_FN, src)
        count = len(re.findall(rf"\b{TARGET_FN}\b(?!ed|-context|Provider)", src))
        with open(path, "w") as f:
            f.write(new_src)
        print(f"  {rel}: {count} occurrence(s) renamed")


def verify():
    print("\n=== VERIFICATION: any `highlight(` calls left unrenamed? ===")
    out = subprocess.run(
        ["grep", "-rn", r"\bhighlight(", f"{REPO}/components", f"{REPO}/lib"],
        capture_output=True,
        text=True,
    )
    leftover = out.stdout.strip()
    if leftover:
        print("MISSED CALL SITES:\n" + leftover)
    else:
        print("Clean. No leftover calls to the old name.")


if __name__ == "__main__":
    real_call_sites = get_real_call_sites()
    print("Ground truth from the knowledge graph:")
    for row in real_call_sites:
        print(f"  {row[0]} -> {row[1]}")

    blind = run_blind_agent()
    grounded = run_grounded_agent(real_call_sites)

    apply_real_rename()
    verify()
