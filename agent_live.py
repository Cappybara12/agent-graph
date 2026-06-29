"""
Live agentic demo: the model decides, on its own, to query the codebase
knowledge graph before answering. We don't hand it the facts — it asks
for them via a real tool call.

Run: python3 agent_live.py
"""

import json
import subprocess
import os
import sys
import time
import urllib.request

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:latest"

REPO = "/Users/akshaysharma/Documents/Claude/Projects/Akshay-bnb/agent-console"
PROJECT = "Users-akshaysharma-Documents-Claude-Projects-Akshay-bnb-agent-console"

# Uniquely-named function, no collisions with built-ins like Array.push.
TARGET_FN = "highlightTarget"
TARGET_FILE = "lib/highlight-context.tsx"

# --- terminal styling, no deps ------------------------------------------------

class C:
    DIM = "\033[2m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"


def banner(label, color=C.CYAN):
    print(f"\n{color}{C.BOLD}── {label} ──{C.RESET}")


def type_out(text, delay=0.0):
    """Print incrementally so streamed tokens visibly appear over time."""
    sys.stdout.write(text)
    sys.stdout.flush()


# --- the actual tool, backed by the real knowledge graph ----------------------
#hey this is a test
def get_callers(function_name: str):
    """Ground-truth lookup against codebase-memory-mcp. The model calls this
    itself; we don't pre-fetch the answer for it."""
    env = dict(os.environ)
    env["PATH"] = f"/Users/akshaysharma/.local/bin:{env.get('PATH', '')}"
    cypher = (
        f"MATCH (caller)-[:CALLS]->(f) WHERE f.name = '{function_name}' "
        f"RETURN caller.name AS caller_fn, caller.file_path AS caller_file"
    )
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
    last_line = out.stdout.strip().splitlines()[-1]
    result = json.loads(last_line)
    return result.get("rows", [])


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_callers",
            "description": (
                "Query the project's codebase knowledge graph for every "
                "function/component that calls a given function. Use this "
                "before claiming you know all the places a function is used."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function to look up callers for.",
                    }
                },
                "required": ["function_name"],
            },
        },
    }
]


def _request(messages, tools, stream):
    payload = {"model": MODEL, "messages": messages, "stream": stream}
    if tools:
        payload["tools"] = tools
    return urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )


def ollama_chat(messages, tools=None):
    """Single non-streamed turn. Returns the parsed JSON response."""
    req = _request(messages, tools, stream=False)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())


def ollama_chat_stream(messages):
    """Streamed turn. Yields each parsed JSON chunk as it arrives."""
    req = _request(messages, None, stream=True)
    with urllib.request.urlopen(req, timeout=180) as resp:
        for line in resp:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main():
    banner("TASK GIVEN TO THE AGENT", C.MAGENTA)
    task = (
        f"I want to change the signature of the function `{TARGET_FN}` "
        f"(defined in {TARGET_FILE}) to take an options object instead of "
        f"a plain string. Before you give me a plan, find out exactly who "
        f"calls it — don't guess."
    )
    print(task)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a refactoring agent working inside a real codebase. "
                "You have a tool that queries a knowledge graph of the actual "
                "codebase. Always call it to check real call sites before "
                "answering questions about renames or call sites. Never guess."
            ),
        },
        {"role": "user", "content": task},
    ]

    banner("MODEL DECIDING WHETHER TO USE A TOOL", C.YELLOW)
    first = ollama_chat(messages, tools=TOOLS)
    msg = first["message"]
    tool_calls = msg.get("tool_calls") or []

    if not tool_calls:
        print("(model answered without using the tool — printing raw answer)")
        print(msg.get("content", ""))
        return

    messages.append(msg)

    for call in tool_calls:
        fn_name = call["function"]["name"]
        args = call["function"]["arguments"]
        print(f"{C.BOLD}model called:{C.RESET} {fn_name}({args})")

        if fn_name == "get_callers":
            banner("EXECUTING REAL QUERY AGAINST THE KNOWLEDGE GRAPH", C.GREEN)
            rows = get_callers(args["function_name"])
            for r in rows:
                print(f"  {C.GREEN}->{C.RESET} {r[0]}  in  {r[1]}")
            tool_result = json.dumps({"callers": rows})
        else:
            tool_result = json.dumps({"error": "unknown tool"})

        messages.append(
            {
                "role": "tool",
                "content": tool_result,
            }
        )

    banner("MODEL'S FINAL ANSWER (streamed live)", C.CYAN)
    full_text = ""
    for chunk in ollama_chat_stream(messages):
        piece = chunk.get("message", {}).get("content", "")
        if piece:
            type_out(piece)
            full_text += piece
        if chunk.get("done"):
            break
    print()

    banner("DONE", C.BOLD)
    print("The model decided on its own to query the real call graph before answering.")


if __name__ == "__main__":
    main()
