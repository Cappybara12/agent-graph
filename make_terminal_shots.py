"""
Renders real terminal output (captured during the actual demo runs) as
PNG images styled like a real terminal window, for embedding in the
Medium article. No fabricated content -- every line here is copy-pasted
from a real command run earlier in the session.
"""

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
FONT_SIZE = 16
LINE_HEIGHT = 24
PAD_X = 24
PAD_TOP = 56
PAD_BOTTOM = 24
TITLEBAR_H = 40
WIDTH = 980

BG = (30, 30, 30)
TITLEBAR_BG = (50, 50, 50)
DEFAULT_FG = (212, 212, 212)
TITLE_FG = (154, 154, 154)

DOT_RED = (255, 95, 86)
DOT_YELLOW = (255, 189, 46)
DOT_GREEN = (39, 201, 63)

font = ImageFont.truetype(FONT_PATH, FONT_SIZE, index=0)


def render(lines, title, out_path):
    height = TITLEBAR_H + PAD_TOP - TITLEBAR_H + len(lines) * LINE_HEIGHT + PAD_BOTTOM
    img = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, WIDTH, TITLEBAR_H], fill=TITLEBAR_BG)
    for i, color in enumerate([DOT_RED, DOT_YELLOW, DOT_GREEN]):
        cx = 22 + i * 20
        draw.ellipse([cx - 6, TITLEBAR_H // 2 - 6, cx + 6, TITLEBAR_H // 2 + 6], fill=color)
    draw.text((90, TITLEBAR_H // 2 - 7), title, font=font, fill=TITLE_FG)

    y = PAD_TOP
    for line in lines:
        x = PAD_X
        if isinstance(line, str):
            line = [(line, DEFAULT_FG)]
        for text, color in line:
            draw.text((x, y), text, font=font, fill=color)
            x += draw.textlength(text, font=font)
        y += LINE_HEIGHT

    img.save(out_path)
    print(f"wrote {out_path} ({WIDTH}x{height})")


MAGENTA = (197, 134, 192)
YELLOW = (220, 220, 170)
GREEN = (106, 153, 85)
TEAL = (78, 201, 176)
GRAY = (128, 128, 128)
BLUE = (86, 156, 214)
RED = (244, 71, 71)

# 1. live agent decision -------------------------------------------------
lines_1 = [
    [("── TASK GIVEN TO THE AGENT ──", MAGENTA)],
    "I want to change the signature of the function `highlightTarget`",
    "(defined in lib/highlight-context.tsx) to take an options object",
    "instead of a plain string. Before you give me a plan, find out",
    "exactly who calls it — don't guess.",
    "",
    [("── MODEL DECIDING WHETHER TO USE A TOOL ──", YELLOW)],
    [("model called: ", DEFAULT_FG), ("get_callers({'function_name': 'highlightTarget'})", DEFAULT_FG)],
    "",
    [("── EXECUTING REAL QUERY AGAINST THE KNOWLEDGE GRAPH ──", GREEN)],
    [("  -> ", GREEN), ("handleClick  in  components/timeline/TimelinePanel.tsx", DEFAULT_FG)],
    [("  -> ", GREEN), ("handleHeaderClick  in  components/chat/ToolCallCard.tsx", DEFAULT_FG)],
    "",
    [("── MODEL'S FINAL ANSWER (streamed live) ──", TEAL)],
    "The function `highlightTarget` is called from two locations in the",
    "codebase:",
    "",
    "1. The `handleClick` function in `components/timeline/TimelinePanel.tsx`",
    "2. The `handleHeaderClick` function in `components/chat/ToolCallCard.tsx`",
    "",
    "Before proceeding with refactoring, you should also determine what",
    "kind of options this new options object will include. However, based",
    "on the current callers, we can start by updating these two call sites",
    "to pass an options object instead of a string.",
    "",
    [("── DONE ──", GRAY)],
    "The model decided on its own to query the real call graph before answering.",
]
render(lines_1, "agent-memory-demo — python3 agent_live.py", "/tmp/shot_live_agent.png")

# 2. blind vs grounded -----------------------------------------------------
lines_2 = [
    "Ground truth from the knowledge graph:",
    "  connect -> lib/ws-machine.ts",
    "  handleClose -> lib/ws-machine.ts",
    "  handleOpen -> lib/ws-machine.ts",
    "  scheduleReconnect -> lib/ws-machine.ts",
    "",
    [("=== BLIND AGENT (no codebase memory) ===", YELLOW)],
    "/src/hooks/use-agent-socket.ts",
    "",
    [("=== GROUNDED AGENT (codebase-memory-mcp graph) ===", TEAL)],
    "Here is a list of files and their respective paths that need to be",
    "updated:",
    "",
    "1. lib/ws-machine.ts - 4 callsites (connect, handleClose, handleOpen,",
    "   scheduleReconnect)",
    "2. hooks/use-agent-socket.ts - 1 callsite",
    "",
    "So the file paths are:",
    "- lib/ws-machine.ts",
    "- hooks/use-agent-socket.ts",
]
render(lines_2, "agent-memory-demo — python3 demo.py", "/tmp/shot_blind_vs_grounded.png")

# 3. grep verification -------------------------------------------------
lines_3 = [
    [("$ ", BLUE), ("grep -rn \"highlightTarget(\" components/ lib/", DEFAULT_FG)],
    "",
    "components/chat/ToolCallCard.tsx:20:    highlightTarget(`tl-toolcall-${segment.callId}`);",
    "components/timeline/TimelinePanel.tsx:36:    highlightTarget(`chat-stream-${entry.streamId}`);",
    "components/timeline/TimelinePanel.tsx:85:      highlightTarget(`chat-tool-${entry.callId}`);",
]
render(lines_3, "agent-console — grep (no AI involved)", "/tmp/shot_grep_verify.png")

# 4. architecture overview ------------------------------------------------
lines_4 = [
    [("$ ", BLUE), ("codebase-memory-mcp cli get_architecture '{\"project\":\"agent-console\"}'", DEFAULT_FG)],
    "",
    "total_nodes: 254",
    "total_edges: 469",
    "",
    [("languages", TEAL)],
    "  TypeScript   24 files",
    "  CSS           1 file",
    "",
    [("node_labels", TEAL)],
    "  Method        40",
    "  Function      39",
    "  Type          37",
    "  File          32",
    "  Module        32",
    "  Section       23",
    "  Interface     17",
    "  Variable      15",
    "  Folder        11",
    "  Class          4",
    "  Channel        3",
    "  Project        1",
    "",
    [("edge_types", TEAL)],
    "  DEFINES         208",
    "  CALLS           105",
    "  DEFINES_METHOD   40",
    "  USAGE            40",
    "  IMPORTS          30",
    "  CONTAINS_FILE    28",
]
render(lines_4, "codebase-memory-mcp cli get_architecture", "/tmp/shot_architecture.png")

# 5. dead code false positive ---------------------------------------------
lines_5 = [
    [("$ ", BLUE), ("codebase-memory-mcp cli query_graph '{\"query\":", DEFAULT_FG)],
    "   \"MATCH (f:Function) WHERE NOT EXISTS { (f)<-[:CALLS]-() }",
    "    RETURN f.name, f.file_path LIMIT 10\"}'",
    "",
    "[\"RootLayout\",\"app/layout.tsx\"]",
    "[\"Home\",\"app/page.tsx\"]",
    "[\"HighlightProvider\",\"lib/highlight-context.tsx\"]",
    "[\"ToolCallCard\",\"components/chat/ToolCallCard.tsx\"]",
    "[\"TimelinePanel\",\"components/timeline/TimelinePanel.tsx\"]",
    "[\"handleClick\",\"components/timeline/TimelinePanel.tsx\"]",
    "[\"handleScroll\",\"components/timeline/TimelinePanel.tsx\"]",
    "",
    [("⚠ false positives — ", RED), ("these are React components", DEFAULT_FG)],
    "rendered as JSX (<ToolCallCard />) and handlers passed as",
    "props (onClick={handleClick}). The graph tracks direct function",
    "calls, not JSX rendering, so it misreads these as \"unused\".",
]
render(lines_5, "codebase-memory-mcp cli query_graph — dead code check", "/tmp/shot_dead_code.png")
