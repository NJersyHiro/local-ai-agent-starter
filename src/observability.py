"""監視（任意）。LANGFUSE_ENABLED=1 のとき Langfuse のコールバックを返す。

未設定・未インストールなら空リストを返すだけ（本体の動作には影響しない）。
コスト・レイテンシ・トレースを Langfuse ダッシュボードで可視化できる。
"""
from __future__ import annotations

import os


def get_callbacks() -> list:
    if os.getenv("LANGFUSE_ENABLED", "").lower() not in ("1", "true", "yes"):
        return []
    try:
        from langfuse.callback import CallbackHandler

        return [CallbackHandler()]  # 認証は LANGFUSE_* 環境変数から
    except Exception as e:  # 未インストール等は黙って無効化
        print(f"[observability] Langfuse 無効化: {e}")
        return []
