"""最小の MCP サーバー（業務システムの代理）。

「社内データ/APIをエージェントから安全に呼ぶ」例。実運用ではここを
基幹DB・SaaS API・社内サービスへの認可付きアクセスに置き換える。
stdio トランスポートで起動し、agent.py から接続される。
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("biz-data")

# --- ダミーの業務データ（本番はDB/APIに置換） ---
_ORDERS = {
    "A-1001": {"status": "出荷済み", "carrier": "ヤマト", "eta": "2026-06-05"},
    "A-1002": {"status": "倉庫保留", "reason": "在庫待ち", "eta": "未定"},
    "A-1003": {"status": "キャンセル", "reason": "顧客都合", "eta": "-"},
}
_CUSTOMERS = {
    "C-01": {"name": "山田商事", "plan": "Pro", "monthly_fee": 50000, "since": "2024-04"},
    "C-02": {"name": "佐藤工業", "plan": "Standard", "monthly_fee": 30000, "since": "2025-01"},
}


@mcp.tool()
def lookup_order_status(order_id: str) -> str:
    """注文IDから出荷ステータス・配送業者・到着予定を返す。例: A-1001"""
    o = _ORDERS.get(order_id.strip().upper())
    if not o:
        return f"注文 {order_id} は見つかりませんでした。"
    return f"注文{order_id}: ステータス={o['status']}, " + ", ".join(
        f"{k}={v}" for k, v in o.items() if k != "status"
    )


@mcp.tool()
def get_customer_plan(customer_id: str) -> str:
    """顧客IDから契約プランと月額・契約開始月を返す。例: C-01"""
    c = _CUSTOMERS.get(customer_id.strip().upper())
    if not c:
        return f"顧客 {customer_id} は見つかりませんでした。"
    return f"{c['name']}({customer_id}): プラン={c['plan']}, 月額={c['monthly_fee']}円, 契約開始={c['since']}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
