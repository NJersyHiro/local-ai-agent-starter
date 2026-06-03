"""RAGの品質を Ragas で評価する（PoC止まりにしない＝差別化の核）。

各質問について RAG で回答し、(質問/回答/参考コンテキスト/正解) を集めて
Faithfulness / AnswerRelevancy / ContextRecall / ContextPrecision を算出する。

  uv run python -m eval.evaluate

注意: ローカル小型モデルをジャッジに使うとスコアが不安定になることがある。
本番の評価では、ジャッジだけ強いモデル(例: gpt-4o)に切り替えると信頼性が上がる
（LLM_PROVIDER=openai で実行）。
"""
from __future__ import annotations

import json
from pathlib import Path

from datasets import Dataset
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from src.config import get_judge_embeddings, get_judge_llm
from src.rag import rag_answer

ROOT = Path(__file__).resolve().parent.parent
EVAL_SET = ROOT / "eval" / "eval_set.json"


def main() -> None:
    items = json.loads(EVAL_SET.read_text(encoding="utf-8"))

    rows = {"user_input": [], "response": [], "retrieved_contexts": [], "reference": []}
    for it in items:
        answer, contexts = rag_answer(it["question"])
        rows["user_input"].append(it["question"])
        rows["response"].append(answer)
        rows["retrieved_contexts"].append(contexts)
        rows["reference"].append(it["reference"])
        print(f"Q: {it['question']}\nA: {answer}\n")

    dataset = Dataset.from_dict(rows)

    # ジャッジは JUDGE_PROVIDER で切替可（エージェントはローカルのまま、
    # 評価だけ強いモデルにするとスコアが安定する）。
    judge_llm = LangchainLLMWrapper(get_judge_llm())
    judge_emb = LangchainEmbeddingsWrapper(get_judge_embeddings())

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=judge_llm,
        embeddings=judge_emb,
    )

    print("=== Ragas 評価結果 ===")
    print(result)
    df = result.to_pandas()
    out = ROOT / "eval" / "last_result.csv"
    df.to_csv(out, index=False)
    print(f"\n詳細を保存: {out}")


if __name__ == "__main__":
    main()
