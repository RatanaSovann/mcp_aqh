"""Ask a Claude model the 20 eval questions, with the MCP server as its only tool.

Two ways to reach the model (--backend):

- cli (default): runs the Claude Code CLI headless (`claude -p`) once per
  question, with server.py as its only tool. Uses whatever login Claude Code
  already has, so it works in Claude Code cloud sessions with no API key.
- sdk: the Anthropic Python SDK. Starts server.py itself, hands its tools to the
  model and runs each tool call back through the server. Needs ANTHROPIC_API_KEY.

Each run gets its own dated folder (answers as JSON lines, plus the scorecard
from eval/score.py), and one row is added to history.md so you can see scores
change as the project grows. Results go to results/ unless you pass --out-dir
or set EVAL_RESULTS_DIR (e.g. a shared project folder).

Run:    python eval/run_eval.py                      # Haiku 4.5, plain prompt
        python eval/run_eval.py --prompt guarded     # with grounding rules
        python eval/run_eval.py --model claude-sonnet-5-5
        python eval/run_eval.py --backend sdk        # API key route
"""

import argparse
import asyncio
import json
import os
import subprocess
from datetime import datetime, timezone
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from score import build_scorecard, score_answer  # noqa: E402

PROMPTS = {
    # What a typical connector user gets: no special instructions.
    "plain": "You are a helpful assistant with access to a Sydney suburb data tool.",
    # The same, plus explicit grounding rules.
    "guarded": (
        "You are a helpful assistant with access to a Sydney suburb data tool. "
        "Answer only with facts returned by the tool. If a value has "
        "source='modelled', say clearly that it is a modelled estimate, not a "
        "Census count. If the tool does not have the data, say so plainly and "
        "do not guess or use outside knowledge."
    ),
}
MAX_TURNS = 8
SERVER_NAME = "segments"

# Session context a parent Claude Code session passes down (memory, extra
# CLAUDE.md folders, the user's email). Dropped so the model under test sees
# only the system prompt, the question and the tool.
CLI_ENV_DROP = [
    "CLAUDE_MEMORY_STORES",
    "CLAUDE_COWORK_MEMORY_PATH_OVERRIDE",
    "CLAUDE_CODE_REMOTE_MEMORY_DIR",
    "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD",
    "CLAUDE_CODE_USER_EMAIL",
]


def ask_cli(model, system, question, workdir) -> tuple[str, list]:
    """One question through `claude -p`, with the MCP server as the only tool."""
    mcp_config = {
        "mcpServers": {
            SERVER_NAME: {"command": sys.executable, "args": [str(ROOT / "server.py")]}
        }
    }
    cmd = [
        "claude", "-p", question,
        "--model", model,
        "--system-prompt", system,
        "--mcp-config", json.dumps(mcp_config),
        "--strict-mcp-config",
        "--tools", "",  # no built-in tools: no web, no files, no shell
        "--allowedTools", f"mcp__{SERVER_NAME}__*",
        "--setting-sources", "",
        "--no-session-persistence",
        "--max-turns", str(MAX_TURNS),
        "--output-format", "stream-json", "--verbose",
    ]
    env = {k: v for k, v in os.environ.items() if k not in CLI_ENV_DROP}
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    proc = subprocess.run(
        cmd, cwd=workdir, env=env, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=300,
    )

    calls, answer = [], None
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event["message"]["content"]:
                if block.get("type") == "tool_use":
                    name = block["name"].removeprefix(f"mcp__{SERVER_NAME}__")
                    calls.append({"tool": name, "input": block["input"]})
        elif event.get("type") == "result":
            answer = event.get("result")
            if event.get("subtype") == "error_max_turns":
                answer = "[stopped: too many tool calls]"
            elif event.get("is_error"):
                answer = f"[error: {answer}]"
    if answer is None:
        answer = f"[error: claude exited {proc.returncode}: {proc.stderr.strip()[-300:]}]"
    return answer, calls


def run_cli(questions, model, system) -> list[tuple[str, list]]:
    # A neutral empty folder, so no CLAUDE.md or repo files leak into the answer.
    with tempfile.TemporaryDirectory() as workdir:
        with ThreadPoolExecutor(max_workers=4) as pool:
            return list(pool.map(lambda q: ask_cli(model, system, q["question"], workdir), questions))


async def ask(client, session, tools, model, system, question) -> tuple[str, list]:
    messages = [{"role": "user", "content": question}]
    calls = []
    for _ in range(MAX_TURNS):
        resp = await client.messages.create(
            model=model, max_tokens=1024, system=system, tools=tools, messages=messages
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return text, calls

        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            out = await session.call_tool(block.name, block.input)
            text = "".join(c.text for c in out.content if c.type == "text")
            calls.append({"tool": block.name, "input": block.input})
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": text})
        messages.append({"role": "user", "content": results})
    return "[stopped: too many tool calls]", calls


async def run_sdk(questions, model, system) -> list[tuple[str, list]]:
    from anthropic import AsyncAnthropic
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    client = AsyncAnthropic()
    server = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools = [
                {"name": t.name, "description": t.description or "", "input_schema": t.inputSchema}
                for t in mcp_tools
            ]
            return [
                await ask(client, session, tools, model, system, q["question"])
                for q in questions
            ]


HISTORY_HEADER = [
    "# Eval history",
    "",
    "One row per run, newest last. Click a run folder for its scorecard and raw answers.",
    "",
    "| When (UTC) | Model | Prompt | Code version | Grounded | Modelled | Out of scope | Overall | Run |",
    "|---|---|---|---|---|---|---|---|---|",
]


def git_version() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True,
        ).stdout.strip()
        return out + ("+edits" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "?"


def add_history_row(out_dir: Path, run_dir: Path, records: list[dict], when: str, version: str) -> None:
    scored = [score_answer(r["id"], r["answer"]) for r in records]

    def tally(cat=None):
        rows = [s for s in scored if cat is None or s["category"] == cat]
        return f"{sum(s['passed'] for s in rows)}/{len(rows)}"

    history = out_dir / "history.md"
    if not history.exists():
        history.write_text("\n".join(HISTORY_HEADER) + "\n")
    r = records[0]
    row = [
        when, r["model"], r["prompt"], version,
        tally("grounded"), tally("modelled"), tally("out_of_scope"), f"**{tally()}**",
        f"[{run_dir.name}]({run_dir.name}/scorecard.md)",
    ]
    with history.open("a") as f:
        f.write("| " + " | ".join(row) + " |\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--prompt", choices=PROMPTS, default="plain")
    parser.add_argument("--backend", choices=["cli", "sdk"], default="cli")
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path(os.environ.get("EVAL_RESULTS_DIR", ROOT / "results")),
    )
    args = parser.parse_args()
    started = datetime.now(timezone.utc)
    version = git_version()

    questions = json.loads((ROOT / "eval" / "questions.json").read_text())
    system = PROMPTS[args.prompt]
    if args.backend == "cli":
        answers = run_cli(questions, args.model, system)
    else:
        answers = asyncio.run(run_sdk(questions, args.model, system))

    run_dir = args.out_dir / f"{started:%Y-%m-%d_%H%M}_{args.model}_{args.prompt}"
    run_dir.mkdir(parents=True, exist_ok=True)
    run_path = run_dir / "run.jsonl"
    records = [
        {
            "id": q["id"], "model": args.model, "prompt": args.prompt,
            "backend": args.backend, "code_version": version,
            "answer": answer, "tool_calls": calls,
        }
        for q, (answer, calls) in zip(questions, answers)
    ]
    with run_path.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
            print(f"{record['id']}: {record['answer'][:80]!r}")

    card = build_scorecard(run_path)
    (run_dir / "scorecard.md").write_text(card + "\n")
    add_history_row(args.out_dir, run_dir, records, f"{started:%Y-%m-%d %H:%M}", version)
    print("\n" + card)
    print(f"\nSaved to {run_dir}; history in {args.out_dir / 'history.md'}")


if __name__ == "__main__":
    main()
