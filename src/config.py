"""プロバイダ非依存の LLM / Embeddings ファクトリ。

LLM_PROVIDER で ollama(デフォルト) / openai / gemini を切り替える。
コード本体はこの関数だけ見ればよく、プロバイダ差し替えは env の1行で済む
（＝ベンダーロックインを避け、オンプレ要件にも応えられる）。
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()


def get_llm():
    if PROVIDER == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=os.getenv("OLLAMA_LLM", "qwen2.5:7b"), temperature=0)
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    if PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), temperature=0
        )
    raise ValueError(f"未対応の LLM_PROVIDER: {PROVIDER}")


def get_embeddings():
    if PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=os.getenv("OLLAMA_EMBED", "nomic-embed-text"))
    if PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBED", "text-embedding-3-small"))
    if PROVIDER == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model=os.getenv("GEMINI_EMBED", "models/text-embedding-004")
        )
    raise ValueError(f"未対応の LLM_PROVIDER: {PROVIDER}")
