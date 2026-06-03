"""CLI: 質問を投げてエージェントの回答を表示する。

  uv run python -m src.run "A-1002の出荷状況は？"
  uv run python -m src.run "返品の期限は何日？"
"""
from __future__ import annotations

import asyncio
import sys

from .agent import ask


def main() -> None:
    if len(sys.argv) < 2:
        print('使い方: python -m src.run "質問文"')
        raise SystemExit(1)
    question = " ".join(sys.argv[1:])
    answer = asyncio.run(ask(question))
    print("\n=== 回答 ===")
    print(answer)


if __name__ == "__main__":
    main()
