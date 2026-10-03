"""Ask a Claude model the 20 eval questions, with the MCP server as its only tool.

The script starts server.py, reads its tools over MCP, hands them to the model,
and runs each tool call the model makes back through the server. Answers are
saved as JSON lines, then scored with eval/score.py.

Needs:  ANTHROPIC_API_KEY in your environment.
Run:    python eval/run_eval.py                      # Haiku 4.5, plain prompt
        python eval/run_eval.py --prompt guarded     # with grounding rules
        python eval/run_eval.py --model claude-sonnet-5-5
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from anthropic import AsyncAnthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--prompt", choices=PROMPTS, default="plain")
    args = parser.parse_args()

    questions = json.loads((ROOT / "eval" / "questions.json").read_text())
    client = AsyncAnthropic()
    server = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    run_path = out_dir / f"run_{args.model}_{args.prompt}.jsonl"

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools = [
                {"name": t.name, "description": t.description or "", "input_schema": t.inputSchema}
                for t in mcp_tools
            ]
            with run_path.open("w") as f:
                for q in questions:
                    answer, calls = await ask(
                        client, session, tools, args.model, PROMPTS[args.prompt], q["question"]
                    )
                    record = {
                        "id": q["id"], "model": args.model, "prompt": args.prompt,
                        "answer": answer, "tool_calls": calls,
                    }
                    f.write(json.dumps(record) + "\n")
                    print(f"{q['id']}: {answer[:80]!r}")

    card = build_scorecard(run_path)
    card_path = run_path.with_name(run_path.name.replace("run_", "scorecard_")).with_suffix(".md")
    card_path.write_text(card + "\n")
    print("\n" + card)


if __name__ == "__main__":
    asyncio.run(main())
