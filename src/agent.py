"""LangGraph エージェント本体。

ツール = ①社内ナレッジ検索(RAG) ②MCPサーバー経由の業務データ照会。
LLM がどちらを使うか判断して回答する（ReAct）。
"""
from __future__ import annotations

import sys
from pathlib import Path

from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from .config import get_llm
from .rag import retrieve

ROOT = Path(__file__).resolve().parent.parent

SYSTEM = (
    "あなたは社内向け業務アシスタント。**回答の前に必ずツールを使って根拠を集めること。**\n"
    "- 返品・キャンセル・返金・送料・配送・支払い・営業時間・会員プラン・料金・ポイント・"
    "各種手続きなど『社内制度に関する質問』は、例外なくまず search_knowledge_base を呼ぶ。\n"
    "- 特定の注文IDや顧客IDの状況は lookup_order_status / get_customer_plan を呼ぶ。\n"
    "自分の一般知識だけで答えてはならない。ツールを一度も呼ばずに『資料に記載がありません』と"
    "答えることは禁止。ツール結果に基づき日本語で簡潔に答え、結果に無い場合のみ"
    "『資料に記載がありません』と述べる。"
)


@tool
def search_knowledge_base(query: str) -> str:
    """社内ナレッジ(マニュアル/FAQ/ポリシー)を検索し、関連箇所を返す。"""
    docs = retrieve(query, k=4)
    if not docs:
        return "関連するナレッジは見つかりませんでした。"
    return "\n\n".join(f"[{d.metadata.get('source','?')}] {d.page_content}" for d in docs)


def _mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "biz": {
                "command": sys.executable,
                "args": ["-m", "src.mcp_server"],
                "transport": "stdio",
                "cwd": str(ROOT),
            }
        }
    )


async def build_agent():
    mcp_tools = await _mcp_client().get_tools()
    tools = [search_knowledge_base, *mcp_tools]
    return create_react_agent(get_llm(), tools)


async def ask(question: str) -> str:
    agent = await build_agent()
    # システム指示は入力メッセージとして確実に渡す（prompt= 引数はバージョン差で
    # 効かないことがあるため）。
    result = await agent.ainvoke(
        {
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": question},
            ]
        }
    )
    return result["messages"][-1].content
