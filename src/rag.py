"""RAG: data/corpus を InMemoryVectorStore に取り込み、検索・回答生成する。

MVP は依存ゼロの InMemoryVectorStore（langchain-core同梱）を使用。
コーパスが小さいため毎プロセスで即時構築する。本番は pgvector 等に
差し替え可能（get_vectorstore だけ置き換えればよい）。
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import get_embeddings, get_llm

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"


def _load_chunks() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=280, chunk_overlap=40)
    docs: list[Document] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for chunk in splitter.split_text(text):
            docs.append(Document(page_content=chunk, metadata={"source": path.name}))
    return docs


@lru_cache(maxsize=1)
def get_vectorstore() -> InMemoryVectorStore:
    """コーパスから埋め込みインデックスを構築（プロセス内キャッシュ）。"""
    vs = InMemoryVectorStore(get_embeddings())
    vs.add_documents(_load_chunks())
    return vs


def build_index() -> int:
    """インデックスを構築してチャンク数を返す（検証用）。"""
    vs = get_vectorstore()
    return len(vs.store)


def retrieve(query: str, k: int = 4) -> list[Document]:
    return get_vectorstore().similarity_search(query, k=k)


_RAG_PROMPT = """あなたは社内ナレッジに基づいて回答するアシスタントです。
以下の参考情報だけを根拠に、簡潔かつ正確に日本語で答えてください。
参考情報に無いことは「資料に記載がありません」と答えてください。

# 参考情報
{context}

# 質問
{question}
"""


def rag_answer(question: str, k: int = 4) -> tuple[str, list[str]]:
    """RAGで回答し、(回答, 使った参考コンテキスト) を返す。評価で使う。"""
    docs = retrieve(question, k=k)
    contexts = [d.page_content for d in docs]
    prompt = _RAG_PROMPT.format(context="\n\n".join(contexts), question=question)
    answer = get_llm().invoke(prompt).content
    return answer, contexts


if __name__ == "__main__":
    n = build_index()
    print(f"インデックス構築完了: {n} チャンク（InMemoryVectorStore）")
