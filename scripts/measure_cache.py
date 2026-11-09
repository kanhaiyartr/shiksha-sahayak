"""Show the prompt-cache price difference. --live calls Claude twice."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from app.config import STANDARD_MODEL
from app.cost import cost_usd
from app.generate import prompt_token_split
from app.models import GenerateIn


def projection(model: str, system_tokens: int, user_tokens: int, output_tokens: int) -> dict[str, float]:
    first = cost_usd(model, user_tokens, output_tokens, cache_write_tokens=system_tokens)
    cached = cost_usd(model, user_tokens, output_tokens, cache_read_tokens=system_tokens)
    return {"first_usd": first, "cached_usd": cached, "saved_usd": round(first - cached, 6)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=STANDARD_MODEL)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    spec = GenerateIn(topic="Fractions", class_level="5", language="en", task_type="worksheet", subject="Mathematics")
    system_tokens, user_tokens = prompt_token_split(spec, "")
    numbers = projection(args.model, system_tokens, user_tokens, 700)
    print(
        f"Estimated system tokens {system_tokens}, user tokens {user_tokens}. "
        f"First request ${numbers['first_usd']:.6f}. Cached request ${numbers['cached_usd']:.6f}. "
        f"Saving ${numbers['saved_usd']:.6f}."
    )
    if not args.live:
        print("Dry run. Pass --live to send two short calls and read the cache counters.")
        return
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set.")
    from anthropic import Anthropic

    from app.generate import system_blocks, user_message

    client = Anthropic()
    usages = []
    for _ in range(2):
        response = client.messages.create(
            model=args.model,
            max_tokens=32,
            system=system_blocks(spec.task_type),
            messages=[{"role": "user", "content": user_message(spec, "") + "\nReply with one short sentence."}],
        )
        usages.append(response.usage)
    for index, usage in enumerate(usages, start=1):
        print(
            f"Call {index}: input={usage.input_tokens} "
            f"cache_write={getattr(usage, 'cache_creation_input_tokens', 0)} "
            f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)} "
            f"output={usage.output_tokens}"
        )


if __name__ == "__main__":
    main()
