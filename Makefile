.PHONY: setup index ask eval mcp clean

# 依存インストール（uvが管理する仮想環境）
setup:
	uv sync

# RAGインデックス構築（data/corpus -> インメモリ索引）
index:
	uv run python -m src.rag

# エージェントに質問（例: make ask Q="A-1002の出荷状況は？"）
ask:
	uv run python -m src.run "$(Q)"

# RAG品質をRagasで評価
eval:
	uv run python -m eval.evaluate

# MCPサーバー単体起動（デバッグ用）
mcp:
	uv run python -m src.mcp_server

clean:
	rm -rf data/chroma .ragas_cache
