# local-ai-agent-starter 🤖🔒

**業務AIエージェントを「PoC止まり」にしない** ―― MCP＋RAG＋**評価**＋監視を、**ローカルLLM(Ollama)** で動かす最小スターター。

> 多くの生成AI導入は「PoCは動いたが、精度が測れない・コストが読めない・運用できない」で止まる。
> このリポジトリは、**評価(Ragas)と監視まで最初から組み込む**ことで、本番運用に耐える形を最小構成で示す。
> しかも**完全ローカル**（データが外に出ない）なので、権限分離・監査要件の厳しいオンプレ用途にも向く。

## アーキテクチャ
```
ユーザー質問
   │
   ▼
LangGraph エージェント (ReAct)  ── LLM: Ollama qwen2.5（ローカル）
   ├─ search_knowledge_base : RAG（InMemoryVectorStore + nomic-embed-text）→ 社内ナレッジ
   └─ MCPツール (stdio)      : 業務データ照会（注文/顧客）= src/mcp_server.py
   │
   ▼
回答（根拠つき）
        ▲
        └── eval/evaluate.py : Ragas で精度を数値化（Faithfulness/Recall 等）
        └── 監視(任意)        : Langfuse でコスト/レイテンシ
```

## 必要なもの
- [Ollama](https://ollama.com/)（ローカルLLM）と `uv`
- モデル: `ollama pull qwen2.5:7b && ollama pull nomic-embed-text`

## セットアップ & 実行
```bash
make setup                       # 依存インストール（uv）
cp .env.example .env             # 既定はローカル(Ollama)。変更不要で動く
make index                       # data/corpus をインメモリ索引に取り込み（即時）
make ask Q="返品は何日以内？"      # ナレッジ検索(RAG)で回答
make ask Q="A-1002の出荷状況は？"  # MCP経由で業務データ照会
make eval                        # ★ RAG品質を Ragas で評価（差別化の核）
```

## プロバイダの差し替え（ベンダーロックイン回避）
`.env` の `LLM_PROVIDER` を変えるだけ。コード変更不要。
- `ollama`（既定・ローカル/オンプレ）
- `openai`（`uv pip install -e ".[openai]"` ＋ `OPENAI_API_KEY`）
- `gemini`（`uv pip install -e ".[gemini]"` ＋ `GOOGLE_API_KEY`）

> 評価のジャッジは強いモデルが望ましい。**エージェントはローカルのまま、評価ジャッジだけ** `JUDGE_PROVIDER=openai` にできる（`make eval` 時のみ強モデルを使う実務的な構成）。

## 監視（任意・Langfuse）
`.env` で `LANGFUSE_ENABLED=1` ＋ `LANGFUSE_PUBLIC_KEY/SECRET_KEY` を設定すると、
エージェント実行のトレース・コスト・レイテンシが Langfuse に記録される（未設定なら何もしない）。
インストール: `uv pip install -e ".[observability]"`

## 構成
| パス | 役割 |
|---|---|
| `src/config.py` | プロバイダ非依存の LLM/Embeddings ファクトリ |
| `src/rag.py` | インメモリ索引への取り込み・検索・RAG回答（本番は pgvector に差替） |
| `src/mcp_server.py` | 最小MCPサーバー（業務データ照会の例） |
| `src/agent.py` | LangGraph ReActエージェント（RAG＋MCPツール） |
| `eval/evaluate.py` | Ragas評価（Faithfulness/AnswerRelevancy/ContextRecall/Precision） |

## 評価結果の例（ローカル qwen2.5 をジャッジに使用）
```
faithfulness: 0.78 | context_recall: 1.00 | context_precision: 0.67 | answer_relevancy: 0.41
```
> `answer_relevancy` が不自然に低いのは、**小型ローカルモデルをジャッジに使うと評価が不安定**になる典型例。
> 本番では `LLM_PROVIDER=openai` 等でジャッジだけ強いモデルに切り替えるとスコアが安定する。
> 「評価そのものの信頼性を設計する」のがこのスターターの主眼。

## なぜこれが「本番運用」なのか
1. **評価が回る**: 変更のたびに精度を数値で確認できる（改善前後を語れる＝単価交渉の武器）。
2. **監視できる**: コスト・レイテンシ・失敗を可視化（Langfuse、任意）。
3. **ロックインしない**: ローカル/クラウドをenvで切替。オンプレ要件にも対応。

## ライセンス
MIT
