"""Ask a Claude model the 20 eval questions, with the MCP server as its only tool.

Two ways to reach the model (--backend):

- cli (default): runs the Claude Code CLI headless (`claude -p`) once per
  question, with server.py as its only tool. Uses whatever login Claude Code
  already has, so it works in Claude Code cloud sessions with no API key.
- sdk: the Anthropic Python SDK. Starts server.py itself, hands its tools to the
  model and runs each tool call back through the server. Needs ANTHROPIC_API_KEY.

Answers are saved as JSON lines, then scored with eval/score.py.

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
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from score import build_scorecard  # noqa: E402

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--prompt", choices=PROMPTS, default="plain")
    parser.add_argument("--backend", choices=["cli", "sdk"], default="cli")
    args = parser.parse_args()

    questions = json.loads((ROOT / "eval" / "questions.json").read_text())
    system = PROMPTS[args.prompt]
    if args.backend == "cli":
        answers = run_cli(questions, args.model, system)
    else:
        answers = asyncio.run(run_sdk(questions, args.model, system))

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    run_path = out_dir / f"run_{args.model}_{args.prompt}.jsonl"
    with run_path.open("w") as f:
        for q, (answer, calls) in zip(questions, answers):
            record = {
                "id": q["id"], "model": args.model, "prompt": args.prompt,
                "backend": args.backend, "answer": answer, "tool_calls": calls,
            }
            f.write(json.dumps(record) + "\n")
            print(f"{q['id']}: {answer[:80]!r}")

    card = build_scorecard(run_path)
    card_path = run_path.with_name(run_path.name.replace("run_", "scorecard_")).with_suffix(".md")
    card_path.write_text(card + "\n")
    print("\n" + card)


if __name__ == "__main__":
    main()
