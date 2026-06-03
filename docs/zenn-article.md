---
title: "ローカルLLMで“PoC止まり”にしない業務AIエージェント ― MCP＋RAG評価まで一気通貫"
emoji: "🔒"
type: "tech"
topics: ["llm", "langgraph", "mcp", "rag", "ollama"]
published: false
---

## はじめに：なぜ生成AIはPoCで止まるのか

「社内でAIエージェントを作ってみた。デモは動いた。でも本番に出せない」――よく聞く話です。理由はだいたい3つに集約されます。

1. **精度が測れない**（良くなった/悪くなったを数値で言えない）
2. **コストが読めない**（運用したら毎月いくら？）
3. **運用できない**（監視も改善サイクルも無い）

この記事では、これらを**最初から作り込んだ**最小の業務AIエージェントを、**完全ローカル（Ollama）**で動かして示します。データが外に出ないので、権限分離・監査要件の厳しいオンプレ用途にもそのまま使えます。

リポジトリ: https://github.com/NJersyHiro/local-ai-agent-starter

## アーキテクチャ

```
ユーザー質問
   │
   ▼
LangGraph エージェント (ReAct)  ── LLM: Ollama qwen2.5（ローカル）
   ├─ search_knowledge_base : RAG（InMemoryVectorStore + nomic-embed-text）
   └─ MCPツール (stdio)      : 業務データ照会（注文/顧客）= 自作MCPサーバー
   │
   ▼
回答（根拠つき）
        └── Ragas で精度を数値化（Faithfulness / Recall ...）
        └── Langfuse で監視（任意）
```

スタック: LangGraph / langchain-mcp-adapters / Ollama(qwen2.5:7b, nomic-embed-text) / Ragas。

## 1. MCPサーバーを自作する

「社内データ/APIをエージェントから安全に呼ぶ」部分を MCP で切り出します。`FastMCP` で数行です（本番はここをDB/SaaS APIへの認可付きアクセスに置換）。

```python
# src/mcp_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("biz-data")

@mcp.tool()
def lookup_order_status(order_id: str) -> str:
    """注文IDから出荷ステータス・配送業者・到着予定を返す。例: A-1001"""
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## 2. LangGraphエージェントに RAG と MCP を持たせる

MCPツールは `MultiServerMCPClient` で読み込み、ローカルRAG検索ツールと合わせて `create_react_agent` に渡します。

```python
# src/agent.py（抜粋）
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async def build_agent():
    client = MultiServerMCPClient({"biz": {
        "command": sys.executable, "args": ["-m", "src.mcp_server"], "transport": "stdio",
    }})
    tools = [search_knowledge_base, *await client.get_tools()]
    return create_react_agent(get_llm(), tools)
```

LLMは `LLM_PROVIDER` で ollama / openai / gemini を切替（envの1行）。**ベンダーロックインを避け、オンプレ要件にも応えられる**のが狙いです。

### 💡 ハマりどころ①：小型ローカルモデルは曖昧な指示だとツールを呼ばない
最初、`返品は何日以内？` と聞くとエージェントが検索ツールを使わず「資料に記載がありません」と即答しました。**システム指示に対象トピックを具体列挙**したら安定しました。

```python
SYSTEM = (
    "回答の前に必ずツールを使って根拠を集めること。\n"
    "- 返品・送料・営業時間・会員プラン・ポイント等『社内制度』はまず search_knowledge_base を呼ぶ\n"
    "- 注文ID/顧客IDの状況は lookup_order_status / get_customer_plan を呼ぶ"
)
```

### 💡 ハマりどころ②：`create_react_agent(prompt=...)` が効かないことがある
バージョンによっては `prompt=` が反映されません。**system messageは入力メッセージとして渡す**のが確実でした。

```python
await agent.ainvoke({"messages": [
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": question},
]})
```

### 💡 ハマりどころ③：小型モデルはツール呼び出しを“テキストで漏らす”ことがある
qwen2.5:7b はたまに `<tool_call>{...}</tool_call>` を本文に出してしまいます。安定性が要るなら **qwen2.5:14b など一回り大きいモデル**にすると改善します（このリポジトリは env でモデルを差し替え可能）。

## 3. RAGを“評価できる”状態にする（ここが本題）

「作れる」と「本番に出せる」の差は**評価が回るか**です。Ragas で計測します。

```python
# eval/evaluate.py（抜粋）
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision

result = evaluate(
    dataset=dataset,             # user_input / response / retrieved_contexts / reference
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    llm=judge_llm, embeddings=judge_emb,
)
```

実測（ジャッジ＝ローカル qwen2.5:7b）:

```
faithfulness: 0.78 | context_recall: 1.00 | context_precision: 0.67 | answer_relevancy: 0.41
```

### 💡 ハマりどころ④：ローカル小型モデルをジャッジにすると評価が不安定
回答自体は正しいのに `answer_relevancy` が 0.41 と不自然に低い。これは**評価者(ジャッジ)が弱い**のが原因です。本スターターでは **エージェントはローカルのまま、評価ジャッジだけ強いモデル**に切り替えられます。

```bash
JUDGE_PROVIDER=openai make eval   # エージェント=ローカル, 評価=GPTで安定
```

「精度を測る仕組みそのものの信頼性を設計する」――ここがPoCと本番の分水嶺です。

## 4. 依存地獄を避ける（実話）

最新版を総取りしたら壊れました（`langchain 1.x` × `ragas 0.4` × `Python 3.14` で import エラー、`langchain-chroma` 経由の古い `tokenizers` がビルド不能）。**Python 3.12 ＋ 安定版にピン留め**して解決。再現性のため `uv.lock` もコミットしています。

```toml
requires-python = ">=3.12,<3.13"
# langchain 0.3系 / ragas 0.2系 にピン
```

## 動かし方

```bash
make setup && cp .env.example .env
make index
make ask Q="返品は何日以内？"        # RAGで回答
make ask Q="A-1002の出荷状況は？"     # MCP経由で業務データ照会
make eval                            # Ragasで精度を数値化
```

## まとめ

- **評価・監視・ロック回避を最初から**組み込むと、PoCが本番運用に化ける。
- **ローカルLLM**ならデータが外に出ず、オンプレ・監査要件にも対応できる。
- 評価は「測れること」だけでなく「**測る仕組みの信頼性**」まで設計する。

---

### お知らせ
業務AIエージェント/RAGの**本番化・評価・監視・オンプレ導入**を支援しています。「PoCは動いたが本番で詰まっている」方、相談・ウェイトリストはこちら → https://njersyhiro.github.io/ai-agent-consulting/
