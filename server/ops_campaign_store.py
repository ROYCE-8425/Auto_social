# -*- coding: utf-8 -*-
"""Durable SQLite Store for Ops Campaigns and Content Items.

Quản lý trạng thái thực tế của các chiến dịch Campaign Autopilot:
- ops_campaigns: Lưu thông tin chiến dịch, mục tiêu, ngân sách, ROI và kế hoạch tổng thể.
- ops_campaign_items: Lưu từng bài đăng/hạng mục trong ma trận nội dung của chiến dịch,
  liên kết với Kanban task ID và external post ID thực tế (khi đã xuất bản).
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import config

DEFAULT_DB_PATH = config.STATE_DIR / "ops_campaigns.sqlite3"


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    p = Path(db_path) if db_path else DEFAULT_DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path | str | None = None) -> None:
    """Khởi tạo cấu trúc bảng SQLite nếu chưa tồn tại."""
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ops_campaigns (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                target_metric TEXT NOT NULL DEFAULT '',
                duration_weeks INTEGER NOT NULL DEFAULT 4,
                budget_vnd INTEGER NOT NULL DEFAULT 0,
                target_revenue_vnd INTEGER NOT NULL DEFAULT 0,
                roi_projected TEXT NOT NULL DEFAULT '5.0x',
                platforms TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'active',
                task_ids TEXT NOT NULL DEFAULT '[]',
                plan_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ops_campaign_items (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                day INTEGER NOT NULL,
                week INTEGER NOT NULL,
                platform TEXT NOT NULL,
                content_type TEXT NOT NULL,
                angle TEXT NOT NULL DEFAULT '',
                hook TEXT NOT NULL DEFAULT '',
                cta TEXT NOT NULL DEFAULT '',
                lead_target INTEGER NOT NULL DEFAULT 4,
                status TEXT NOT NULL DEFAULT 'draft',
                task_id TEXT NOT NULL DEFAULT '',
                external_post_id TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES ops_campaigns(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ops_campaign_items_campaign_id
                ON ops_campaign_items(campaign_id);
            CREATE INDEX IF NOT EXISTS idx_ops_campaigns_created_at
                ON ops_campaigns(created_at DESC);
            """
        )
        conn.commit()


def create_campaign(
    goal: str,
    target_metric: str,
    duration_weeks: int,
    budget_vnd: int,
    target_revenue_vnd: int,
    roi_projected: str,
    platforms: List[str],
    plan: Dict[str, Any],
    items: List[Dict[str, Any]],
    task_ids: Optional[List[str]] = None,
    campaign_id: Optional[str] = None,
    db_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Lưu chiến dịch mới và danh sách bài đăng/hạng mục vào database."""
    init_db(db_path)
    now_ts = time.time()
    cid = campaign_id or f"camp_{uuid.uuid4().hex[:10]}"
    tids = task_ids or []

    created_items: List[Dict[str, Any]] = []
    with get_connection(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                """
                INSERT INTO ops_campaigns (
                    id, goal, target_metric, duration_weeks, budget_vnd,
                    target_revenue_vnd, roi_projected, platforms, status,
                    task_ids, plan_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    goal,
                    target_metric,
                    duration_weeks,
                    budget_vnd,
                    target_revenue_vnd,
                    roi_projected,
                    json.dumps(platforms, ensure_ascii=False),
                    "active",
                    json.dumps(tids, ensure_ascii=False),
                    json.dumps(plan, ensure_ascii=False),
                    now_ts,
                    now_ts,
                ),
            )

            for idx, it in enumerate(items):
                item_id = it.get("id") or f"item_{cid}_{idx + 1:02d}_{uuid.uuid4().hex[:4]}"
                day = int(it.get("day") or 1)
                week = int(it.get("week") or ((day - 1) // 7 + 1))
                plat = str(it.get("platform") or "tiktok").lower()
                c_type = str(it.get("content_type") or "Bài viết")
                angle = str(it.get("angle") or "")
                hook = str(it.get("hook") or it.get("title") or "")
                cta = str(it.get("cta") or "")
                lead_target = int(it.get("lead_target") or 4)
                status = str(it.get("status") or "draft")
                task_id = str(it.get("task_id") or "")
                ext_id = str(it.get("external_post_id") or "")

                conn.execute(
                    """
                    INSERT INTO ops_campaign_items (
                        id, campaign_id, day, week, platform, content_type,
                        angle, hook, cta, lead_target, status, task_id,
                        external_post_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        cid,
                        day,
                        week,
                        plat,
                        c_type,
                        angle,
                        hook,
                        cta,
                        lead_target,
                        status,
                        task_id,
                        ext_id,
                        now_ts,
                        now_ts,
                    ),
                )
                created_items.append({
                    "id": item_id,
                    "campaign_id": cid,
                    "day": day,
                    "week": week,
                    "platform": plat,
                    "content_type": c_type,
                    "angle": angle,
                    "hook": hook,
                    "cta": cta,
                    "lead_target": lead_target,
                    "status": status,
                    "task_id": task_id,
                    "external_post_id": ext_id,
                    "created_at": now_ts,
                    "updated_at": now_ts,
                })
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return {
        "id": cid,
        "goal": goal,
        "target_metric": target_metric,
        "duration_weeks": duration_weeks,
        "budget_vnd": budget_vnd,
        "target_revenue_vnd": target_revenue_vnd,
        "roi_projected": roi_projected,
        "platforms": platforms,
        "status": "active",
        "task_ids": tids,
        "created_at": now_ts,
        "updated_at": now_ts,
        "items": created_items,
        "plan": plan,
    }


def update_campaign_task_ids(
    campaign_id: str,
    task_ids: List[str],
    db_path: Path | str | None = None,
) -> bool:
    """Cập nhật danh sách task_ids được tạo cho chiến dịch."""
    init_db(db_path)
    now_ts = time.time()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE ops_campaigns
            SET task_ids = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(task_ids, ensure_ascii=False), now_ts, campaign_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_campaign(
    campaign_id: str,
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Đọc thông tin 1 chiến dịch kèm danh sách các items thực tế."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM ops_campaigns WHERE id = ?", (campaign_id,)
        ).fetchone()
        if not row:
            return None

        c_dict = dict(row)
        try:
            c_dict["platforms"] = json.loads(c_dict.get("platforms") or "[]")
        except Exception:
            c_dict["platforms"] = []
        try:
            c_dict["task_ids"] = json.loads(c_dict.get("task_ids") or "[]")
        except Exception:
            c_dict["task_ids"] = []
        try:
            c_dict["plan"] = json.loads(c_dict.get("plan_json") or "{}")
        except Exception:
            c_dict["plan"] = {}
        c_dict.pop("plan_json", None)

        item_rows = conn.execute(
            """
            SELECT * FROM ops_campaign_items
            WHERE campaign_id = ?
            ORDER BY day ASC, id ASC
            """,
            (campaign_id,),
        ).fetchall()
        c_dict["items"] = [dict(r) for r in item_rows]
        c_dict["total_items"] = len(c_dict["items"])
        return c_dict


def list_campaigns(
    limit: int = 50,
    db_path: Path | str | None = None,
) -> List[Dict[str, Any]]:
    """Liệt kê danh sách các chiến dịch gần nhất trong hệ thống."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT 
                c.id, c.goal, c.target_metric, c.duration_weeks, c.budget_vnd,
                c.target_revenue_vnd, c.roi_projected, c.platforms, c.status,
                c.task_ids, c.created_at, c.updated_at,
                COUNT(i.id) as total_items
            FROM ops_campaigns c
            LEFT JOIN ops_campaign_items i ON c.id = i.campaign_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT ?
            """,
            (max(1, min(200, limit)),),
        ).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            try:
                d["platforms"] = json.loads(d.get("platforms") or "[]")
            except Exception:
                d["platforms"] = []
            try:
                d["task_ids"] = json.loads(d.get("task_ids") or "[]")
            except Exception:
                d["task_ids"] = []
            results.append(d)
        return results


def delete_campaign(
    campaign_id: str,
    db_path: Path | str | None = None,
) -> bool:
    """Xóa chiến dịch và các items liên quan."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM ops_campaign_items WHERE campaign_id = ?", (campaign_id,))
        cur = conn.execute("DELETE FROM ops_campaigns WHERE id = ?", (campaign_id,))
        conn.commit()
        return cur.rowcount > 0
