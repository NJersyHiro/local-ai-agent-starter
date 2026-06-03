"""プロバイダ非依存の LLM / Embeddings ファクトリ。

LLM_PROVIDER で ollama(デフォルト) / openai / gemini を切り替える。
評価のジャッジだけ別プロバイダにしたい場合は JUDGE_PROVIDER を指定する
（例: エージェントはローカル ollama、評価ジャッジだけ openai）。
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()


def _llm_for(provider: str):
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=os.getenv("OLLAMA_LLM", "qwen2.5:7b"), temperature=0)
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), temperature=0
        )
    raise ValueError(f"未対応のプロバイダ: {provider}")


def _embeddings_for(provider: str):
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=os.getenv("OLLAMA_EMBED", "nomic-embed-text"))
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBED", "text-embedding-3-small"))
    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model=os.getenv("GEMINI_EMBED", "models/text-embedding-004")
        )
    raise ValueError(f"未対応のプロバイダ: {provider}")


# --- エージェント用（デフォルト） ---
def get_llm():
    return _llm_for(PROVIDER)


def get_embeddings():
    return _embeddings_for(PROVIDER)


# --- 評価ジャッジ用（JUDGE_PROVIDER 未指定なら LLM_PROVIDER と同じ） ---
def get_judge_llm():
    return _llm_for(os.getenv("JUDGE_PROVIDER", PROVIDER).lower())


def get_judge_embeddings():
    return _embeddings_for(os.getenv("JUDGE_PROVIDER", PROVIDER).lower())
