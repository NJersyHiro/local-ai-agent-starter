# GitHub 公開ガイド

> push・リポジトリ作成は**あなたが実行**してください（外部公開のため）。以下はその手順。

## 0. 公開前チェック（重要）
- [x] `.env` は `.gitignore` 済み（APIキーは含まれない）
- [x] サンプルデータはダミーのみ（実顧客情報なし）
- [x] LICENSE（MIT）あり
- [ ] README の冒頭説明・スクショ（任意）を確認
- [ ] 競業避止: 社長許可済み（同一ドメインOK）— 念のため公開内容に現職固有情報が無いか最終確認

## 1. リポジトリ作成 & push（gh CLI / 認証済み）
```bash
cd ~/local-ai-agent-starter

# 公開リポジトリを作成して push（説明文つき）
gh repo create local-ai-agent-starter \
  --public \
  --source=. \
  --remote=origin \
  --description="ローカルLLM(Ollama)で動く業務AIエージェント。LangGraph + 自作MCP + RAG + Ragas評価まで一気通貫。PoC止まりにしないスターター。" \
  --push
```

手動でやる場合:
```bash
gh repo create local-ai-agent-starter --public --description "..."
git remote add origin https://github.com/NJersyHiro/local-ai-agent-starter.git
git branch -M main
git push -u origin main
```

## 2. リポジトリ設定（任意・見つけてもらうため）
- Topics: `llm` `langgraph` `mcp` `rag` `ragas` `ollama` `llmops` `ai-agent` `japanese`
```bash
gh repo edit NJersyHiro/local-ai-agent-starter \
  --add-topic llm,langgraph,mcp,rag,ragas,ollama,llmops,ai-agent
```

## 3. 公開後
- README の先頭に GitHub の Star バッジ（任意）。
- Zenn記事①（`docs/zenn-article.md`）末尾の「リポジトリ」リンクを実URLに差し替えて公開。
- kpi.md の「公開: GitHub Star / 記事本数」を更新開始。
