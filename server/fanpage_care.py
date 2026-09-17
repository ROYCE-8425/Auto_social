"""Fanpage Care Feature: Router, Poller, Settings, CRM & Graph Integration.

Tuân thủ:
1. docs/dev/2026-09-16-fanpage-care-design.md
2. Single-flight poller, Zero-Token preflight
3. Graph calls qua fanpage_care_graph.call
4. CRM qua SQLite WAL (fanpage_care_store) & Markdown (fanpage_care_crm)
5. Policy suggest / auto / full
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import APIRouter, Body, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

import config
from config import STATE_DIR
import fanpage_care_crm as crm
import fanpage_care_graph
import fanpage_care_store as store
from brand_kit import detect_brand_from_kit, parse_brand_kit_channels
from fanpage_care_classify import classify_comment
from fanpage_care_ground import address_short, get_course_fee, render_template, sanitize_kit
from fanpage_care_policy import effective_mode, policy_allows
from quiet_hours import in_quiet_hours

_FEATURE: Optional[FanpageCareFeature] = None


@dataclass
class FanpageCareDeps:
    vault_root: str | Path
    brain: str = "Brain Default"
    get_settings: Callable[[], dict[str, Any]] | None = None
    update_settings: Callable[[dict[str, Any]], None] | None = None
    tasks_feature: Any = None
    inbox_add: Callable[..., Any] | None = None


def _load_kit_for_page(vault_root: str | Path, page_id: str) -> dict[str, Any] | None:
    """Tải brand kit có Page ID khớp (khối Kênh Facebook hoặc Page ID cũ)."""
    d = Path(vault_root) / "wiki" / "brand-kits"
    if not d.is_dir():
        return None
    pid = str(page_id).strip()
    for p in d.glob("*.md"):
        if p.name.startswith("_"):
            continue
        try:
            parsed = parse_brand_kit_channels(p)
        except OSError:
            continue
        if (parsed.facebook.ids.get("page_id") or "").strip() != pid:
            continue
        md = parsed.raw_content
        m_addr = re.search(r"(?:Cơ sở / địa chỉ|Địa chỉ):\s*([^\n]+)", md, re.I)
        addr = m_addr.group(1).strip() if m_addr else ""
        m_hotline = re.search(r"(?:Hotline / Zalo|Hotline riêng|Hotline):\s*([^\n]+)", md, re.I)
        hotline = m_hotline.group(1).strip() if m_hotline else ""
        return {
            "file": p.name,
            "name": parsed.name or p.stem,
            "address": addr,
            "hotline": hotline,
            "md": md,
            "brand": parsed.brand,
        }
    return None


def list_eligible_pages(vault_root: str | Path) -> list[dict[str, Any]]:
    """Trang Facebook có kit và kênh Facebook bật."""
    d = Path(vault_root) / "wiki" / "brand-kits"
    if not d.is_dir():
        return []
    out = []
    seen: set[str] = set()
    for p in sorted(d.glob("*.md")):
        if p.name.startswith("_"):
            continue
        try:
            parsed = parse_brand_kit_channels(p)
        except OSError:
            continue
        if not parsed.facebook.enabled:
            continue
        pid = (parsed.facebook.ids.get("page_id") or "").strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        out.append({
            "page_id": pid,
            "id": pid,
            "name": parsed.name or p.stem,
            "kit_file": p.name,
            "brand": parsed.brand,
        })
    return out


def facebook_pages_status() -> dict[str, Any]:
    """Fail-closed: chưa nối -> connected=False, perm=readonly.
    Đọc mcp_store.list_connections() theo connector_id == 'facebook-pages'.
    Nếu có nhiều connection: ưu tiên cái perm=='full' đang enabled.
    """
    try:
        import mcp_store
        conns = mcp_store.list_connections()
        fb_conns = [c for c in conns if c.get("connector_id") == "facebook-pages"]
        if not fb_conns:
            return {"connected": False, "perm": "readonly", "label": ""}

        # Ưu tiên connection enabled và có quyền full
        full_conn = next((c for c in fb_conns if c.get("enabled", True) and c.get("perm") == "full"), None)
        if full_conn:
            return {
                "connected": True,
                "perm": "full",
                "label": full_conn.get("name") or full_conn.get("label") or "Facebook Trang",
            }

        first_enabled = next((c for c in fb_conns if c.get("enabled", True)), fb_conns[0])
        return {
            "connected": True,
            "perm": first_enabled.get("perm") or "readonly",
            "label": first_enabled.get("name") or first_enabled.get("label") or "Facebook Trang",
        }
    except Exception:
        return {"connected": False, "perm": "readonly", "label": ""}


class FanpageCareFeature:
    def __init__(self, deps: FanpageCareDeps) -> None:
        self.deps = deps
        self.vault_root = Path(deps.vault_root)
        self.brain = deps.brain
        self._poller_task: Optional[asyncio.Task] = None
        self._digest_task: Optional[asyncio.Task] = None
        self._tick_running = False
        self._last_digest_date = ""
        self._round_robin_idx = 0
        self._llm_lock = asyncio.Lock()
        self.router = self._make_router()

    def eligible_pages(self) -> list[dict[str, Any]]:
        """Danh sách Trang có brand kit trong vault."""
        return list_eligible_pages(self.vault_root)

    def get_config(self) -> dict[str, Any]:
        if self.deps.get_settings:
            s = self.deps.get_settings()
        else:
            s = config.read_settings()
        return s.get("fanpage_care", {})

    def save_config(self, patch: dict[str, Any]) -> dict[str, Any]:
        s = config.read_settings()
        care = s.setdefault("fanpage_care", {})
        care.update(patch)
        if self.deps.update_settings:
            self.deps.update_settings(s)
        else:
            config.write_settings(s)
        return care

    async def start(self) -> None:
        """Khởi động các background loop: poller và digest."""
        if self._poller_task is None or self._poller_task.done():
            self._poller_task = asyncio.create_task(self._poll_loop())
        if self._digest_task is None or self._digest_task.done():
            self._digest_task = asyncio.create_task(self._digest_loop())

    async def stop(self) -> None:
        if self._poller_task and not self._poller_task.done():
            self._poller_task.cancel()
        if self._digest_task and not self._digest_task.done():
            self._digest_task.cancel()

    async def _poll_loop(self) -> None:
        """Vòng lặp định kỳ cho Poller (mặc định 5 phút/lần)."""
        while True:
            try:
                cfg = self.get_config()
                interval_sec = max(60, int(cfg.get("poll_interval_min", 5)) * 60)
                await asyncio.sleep(interval_sec)
                await self.poll_tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[fanpage_care] Lỗi poll loop: {e}", file=sys.stderr)
                await asyncio.sleep(60)

    async def _digest_loop(self) -> None:
        """Vòng lặp kiểm tra gửi Daily Digest lúc 20:00 VN."""
        while True:
            try:
                await asyncio.sleep(60)
                cfg = self.get_config()
                if not cfg.get("digest_enabled", True):
                    continue
                digest_hour = int(cfg.get("digest_hour", 20))
                now = datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                if now.hour == digest_hour and self._last_digest_date != today_str:
                    self._last_digest_date = today_str
                    await self.send_daily_digest()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[fanpage_care] Lỗi digest loop: {e}", file=sys.stderr)

    async def send_daily_digest(self) -> None:
        """Tạo và gửi báo cáo tổng kết ngày vào hòm thư (inbox)."""
        st = store.get_stats()
        ev = st.get("events_24h", 0)
        leads = st.get("leads_24h", 0)
        human = st.get("human_needed_24h", 0)
        spam = st.get("spam_hidden_24h", 0)
        drafts = st.get("pending_drafts", 0)

        summary_line = f"{ev} bình luận mới · {leads} lead (có SĐT) · {human} cần người · {spam} spam đã ẩn · {drafts} draft chờ duyệt"
        text = f"Báo cáo Chăm sóc Fanpage (20h):\n> {summary_line}"

        if self.deps.inbox_add:
            try:
                self.deps.inbox_add(
                    text,
                    kind="report",
                    source="fanpage_care",
                    brain=self.brain,
                    title="Báo cáo Fanpage Care",
                    read=False,
                )
            except Exception as e:
                print(f"[fanpage_care] Gửi digest inbox lỗi: {e}", file=sys.stderr)

    async def poll_tick(
        self,
        page_id: str | None = None,
        *,
        force_ingest: bool = False,
    ) -> dict[str, Any]:
        """Một tick quét bình luận (single-flight).

        page_id: chỉ quét đúng Trang (vd BSN). force_ingest: poll-now vẫn kéo
        comment khi Care đang tắt — ghi event/nháp, không tự gửi Graph.
        """
        if self._tick_running:
            return {"status": "skipped", "reason": "already_running"}

        self._tick_running = True
        t0 = time.time()
        res = {
            "status": "ok",
            "events_ingested": 0,
            "drafts_created": 0,
            "replies_sent": 0,
            "page_errors": [],
        }

        try:
            cfg = self.get_config()
            if not cfg.get("enabled", False) and not force_ingest:
                return {"status": "skipped", "reason": "disabled"}

            eligible = list_eligible_pages(self.vault_root)
            if not eligible:
                return {"status": "ok", "reason": "no_eligible_pages"}

            pages_cfg = cfg.get("pages", {})
            active_pages = [
                p for p in eligible
                if pages_cfg.get(p["page_id"], {}).get("enabled", True) is not False
            ]
            if page_id:
                want = str(page_id).strip()
                active_pages = [p for p in active_pages if p["page_id"] == want]
                if not active_pages:
                    return {"status": "ok", "reason": "page_not_in_kits", "page_id": want}

            if not active_pages:
                return {"status": "ok", "reason": "all_pages_disabled"}

            if page_id:
                batch_pages = active_pages
            else:
                pages_per_tick = max(1, int(cfg.get("pages_per_tick", 10)))
                total_active = len(active_pages)
                start_idx = self._round_robin_idx % total_active
                batch_pages = []
                for i in range(min(pages_per_tick, total_active)):
                    batch_pages.append(active_pages[(start_idx + i) % total_active])
                self._round_robin_idx = (start_idx + len(batch_pages)) % total_active

            sem = asyncio.Semaphore(2)
            max_events = int(cfg.get("max_events_per_tick", 100))
            max_new_cust = int(cfg.get("max_new_customers_per_tick", 40))
            new_cust_count = 0

            for p in batch_pages:
                if res["events_ingested"] >= max_events:
                    break

                pid = p["page_id"]
                page_name = p["name"]

                async with sem:
                    # Gọi fb_page_inbox_comments qua fanpage_care_graph.call
                    call_res = await fanpage_care_graph.call(
                        "fb_page_inbox_comments",
                        {"page_id": pid, "posts_limit": 5, "comments_per_post": 25, "filter": "stream"},
                        actor="care-worker",
                        vault_root=str(self.vault_root),
                    )

                if str(call_res).startswith("ERROR:"):
                    res["page_errors"].append({"page_id": pid, "name": page_name, "error": str(call_res)[:300]})
                    continue

                try:
                    data = json.loads(call_res) if isinstance(call_res, str) else call_res
                except Exception:
                    continue

                items = data.get("items", []) if isinstance(data, dict) else []
                if not items:
                    continue

                for item in items:
                    if res["events_ingested"] >= max_events:
                        break

                    cid = str(item.get("comment_id") or "").strip()
                    if not cid:
                        continue

                    from_id = str(item.get("from_id") or "").strip()
                    from_name = str(item.get("from_name") or "Ẩn danh").strip()
                    body = str(item.get("message") or "")
                    post_id = str(item.get("post_id") or "")
                    created_ts = item.get("created_time")

                    c_res = await self.process_inbound_comment(
                        pid, cid, post_id, None, from_id, from_name, body, created_ts,
                        cfg=cfg, sem=sem
                    )
                    if c_res.get("status") == "ok":
                        res["events_ingested"] += 1
                        if c_res.get("replied"):
                            res["replies_sent"] += 1
                        if c_res.get("draft_created"):
                            res["drafts_created"] += 1
                        if c_res.get("new_customer"):
                            new_cust_count += 1

        finally:
            self._tick_running = False

        res["duration_ms"] = int((time.time() - t0) * 1000)
        return res

    async def process_inbound_comment(
        self,
        pid: str,
        cid: str,
        post_id: str,
        parent_id: str | None,
        from_id: str,
        from_name: str,
        body: str,
        created_ts: Any = None,
        *,
        cfg: dict[str, Any] | None = None,
        sem: asyncio.Semaphore | None = None,
    ) -> dict[str, Any]:
        """Xử lý thống nhất một bình luận đến (từ poller hoặc webhook)."""
        if not cid or not body:
            return {"status": "skipped", "reason": "empty"}

        # Bỏ qua comment của chính Page
        if from_id == pid:
            return {"status": "skipped", "reason": "own_page"}

        if cfg is None:
            cfg = self.get_config()

        kit = _load_kit_for_page(self.vault_root, pid)
        brand = detect_brand_from_kit(kit["file"]) if (kit and kit.get("file")) else "saoviet"
        pages_cfg = cfg.get("pages", {})
        page_mode = pages_cfg.get(pid, {}).get("mode")
        eff_m = effective_mode(cfg.get("mode", "suggest"), page_mode)
        is_quiet = in_quiet_hours(cfg.get("quiet_hours", "21-07"))
        kill_switch = bool(cfg.get("kill_switch", False))
        max_rate = int(cfg.get("rate_limit", {}).get("max_replies_per_page_per_hour", 8))

        # 1. Phân loại comment thuần Python
        cls_res = classify_comment(
            body,
            page_id=pid,
            from_id=from_id,
            parent_id=parent_id,
            platform="facebook",
            brand=brand,
        )

        # 2. Ghi nhận event vào SQLite (dedup qua kind + object_id)
        ev_id, is_new = store.record_event({
            "kind": "comment",
            "platform": "facebook",
            "page_id": pid,
            "object_id": cid,
            "thread_id": post_id,
            "from_id": from_id,
            "from_name": from_name,
            "body": body,
            "class": cls_res.get("class"),
            "faq_intent": cls_res.get("faq_intent"),
            "created_ts": created_ts or time.time(),
        })
        if not is_new:
            return {"status": "dedup", "event_id": ev_id}

        out = {
            "status": "ok",
            "event_id": ev_id,
            "class": cls_res.get("class"),
            "replied": False,
            "draft_created": False,
            "new_customer": False,
        }

        # 3. CRM update
        cust_crm_id = None
        phones_list = cls_res.get("phones", [])
        course_hints = cls_res.get("course_hints", [])
        class_name = cls_res.get("class", "ambiguous")

        try:
            cust, is_new_cust = store.get_or_create_customer(
                name=from_name,
                phones=phones_list,
                page_id=pid,
                from_id=from_id,
                course_interest=course_hints[0] if course_hints else "",
                campus=kit.get("name") if kit else "",
                tag=class_name if class_name == "lead" else "",
            )
            cust_crm_id = cust.get("crm_id")
            if cust_crm_id:
                crm.sync_customer_markdown(
                    self.vault_root,
                    cust_crm_id,
                    name=from_name,
                    phones=phones_list,
                    tags=[class_name] if class_name == "lead" else [],
                    course_interest=course_hints[0] if course_hints else "",
                    campus=kit.get("name") if kit else "",
                    page_id=pid,
                    timeline_entry=f"Bình luận '{body[:100]}' (class={class_name})",
                )
                out["new_customer"] = is_new_cust
        except Exception as e:
            print(f"[fanpage_care] CRM sync error: {e}", file=sys.stderr)

        # 4. Rate check
        tz_vn = timezone(timedelta(hours=7))
        hour_key = datetime.now(tz_vn).strftime("%Y-%m-%dT%H")
        cur_replies = store.get_rate_count(pid, hour_key)
        rate_exceeded = cur_replies >= max_rate

        async def _call_graph(*args, **kwargs):
            if sem:
                async with sem:
                    return await fanpage_care_graph.call(*args, **kwargs)
            else:
                return await fanpage_care_graph.call(*args, **kwargs)

        # 5. Đánh giá policy và xử lý action
        # Xử lý FAQ
        if class_name == "faq":
            reply_text = render_template(
                cls_res.get("faq_intent") or "hoc_phi",
                kit,
                course_hint=course_hints[0] if course_hints else None,
                vault_root=self.vault_root,
            )
            ok, why = policy_allows(
                "faq_reply",
                mode=eff_m,
                class_name="faq",
                is_quiet=is_quiet,
                rate_exceeded=rate_exceeded,
                kill_switch=kill_switch,
            )
            if ok and reply_text:
                send_res = await _call_graph(
                    "fb_page_reply",
                    {"comment_id": cid, "message": reply_text, "page_id": pid},
                    actor="care-worker",
                    vault_root=str(self.vault_root),
                    policy_context={"action": "faq_reply", "mode": eff_m, "class_name": "faq"},
                )
                if not str(send_res).startswith("ERROR:"):
                    store.record_action(ev_id, "reply", cid, eff_m, "care-worker")
                    store.increment_rate_count(pid, hour_key)
                    out["replied"] = True
                else:
                    store.create_draft(ev_id, pid, cid, reply_text, "faq")
                    out["draft_created"] = True
            else:
                store.create_draft(ev_id, pid, cid, reply_text or "Cần hỗ trợ tư vấn FAQ", "faq")
                out["draft_created"] = True

        # Xử lý Lead
        elif class_name == "lead":
            reply_text = render_template(
                "lead_thanks",
                kit,
                course_hint=course_hints[0] if course_hints else None,
                vault_root=self.vault_root,
            )
            ok, why = policy_allows(
                "lead_thanks",
                mode=eff_m,
                class_name="lead",
                is_quiet=is_quiet,
                rate_exceeded=rate_exceeded,
                kill_switch=kill_switch,
            )
            if ok and reply_text:
                send_res = await _call_graph(
                    "fb_page_reply",
                    {"comment_id": cid, "message": reply_text, "page_id": pid},
                    actor="care-worker",
                    vault_root=str(self.vault_root),
                    policy_context={"action": "lead_thanks", "mode": eff_m, "class_name": "lead"},
                )
                if not str(send_res).startswith("ERROR:"):
                    store.record_action(ev_id, "reply", cid, eff_m, "care-worker")
                    store.increment_rate_count(pid, hour_key)
                    out["replied"] = True
                else:
                    store.create_draft(ev_id, pid, cid, reply_text, "lead")
                    out["draft_created"] = True
            else:
                store.create_draft(ev_id, pid, cid, reply_text or "Cảm ơn đã để lại thông tin", "lead")
                out["draft_created"] = True

            # Giao việc Kanban cho nhân viên
            if self.deps.tasks_feature and hasattr(self.deps.tasks_feature, "enqueue"):
                try:
                    phone_str = ", ".join(phones_list) if phones_list else "chưa có"
                    course_str = course_hints[0] if course_hints else "Tin học"
                    campus_str = kit.get("name") if kit else "Cơ sở"
                    self.deps.tasks_feature.enqueue(
                        brain=self.brain,
                        title=f"Lead Fanpage: {from_name} ({phone_str}) — {campus_str}",
                        intent=(
                            f"Gọi/Zalo {phone_str}. Quan tâm {course_str}. "
                            f"Comment: {body[:300]}. "
                            f"Hồ sơ crm/customers/{cust_crm_id}.md. "
                            f"Không gửi thêm comment nếu đã lead_thanks."
                        ),
                        route="auto",
                        priority=1 if phones_list else 2,
                        capability="mcp-read",
                        execution_mode="suggest",
                        created_by="fanpage_care",
                        idempotency_key=f"care:{cid}",
                    )
                except Exception as e:
                    print(f"[fanpage_care] Enqueue task error: {e}", file=sys.stderr)

        # Xử lý Khen
        elif class_name == "khen":
            ok, why = policy_allows(
                "comment_like",
                mode=eff_m,
                class_name="khen",
                is_quiet=is_quiet,
                rate_exceeded=rate_exceeded,
                kill_switch=kill_switch,
                like_khen=bool(cfg.get("like_khen", False)),
            )
            if ok:
                like_res = await _call_graph(
                    "fb_page_comment_like",
                    {"comment_id": cid, "page_id": pid},
                    actor="care-worker",
                    vault_root=str(self.vault_root),
                    policy_context={"action": "comment_like", "mode": eff_m, "class_name": "khen"},
                )
                if not str(like_res).startswith("ERROR:"):
                    store.record_action(ev_id, "like", cid, eff_m, "care-worker")

        # Xử lý Spam
        elif class_name in ("spam", "toxic"):
            ok, why = policy_allows(
                "comment_hide",
                mode=eff_m,
                class_name=class_name,
                is_quiet=is_quiet,
                rate_exceeded=rate_exceeded,
                kill_switch=kill_switch,
                hide_spam=bool(cfg.get("hide_spam", False)),
                hide_spam_in_auto=bool(cfg.get("hide_spam_in_auto", False)),
            )
            if ok:
                hide_res = await _call_graph(
                    "fb_page_comment_hide",
                    {"comment_id": cid, "is_hidden": True, "page_id": pid},
                    actor="care-worker",
                    vault_root=str(self.vault_root),
                    policy_context={"action": "comment_hide", "mode": eff_m, "class_name": class_name},
                )
                if not str(hide_res).startswith("ERROR:"):
                    store.record_action(ev_id, "hide", cid, eff_m, "care-worker")

        # Xử lý Kỹ thuật / Mơ hồ (ky_thuat, ambiguous)
        elif class_name in ("ambiguous", "ky_thuat"):
            ok, why = policy_allows(
                "llm_reply",
                mode=eff_m,
                class_name=class_name,
                is_quiet=is_quiet,
                rate_exceeded=rate_exceeded,
                kill_switch=kill_switch,
            )
            if ok:
                from fanpage_care_ground import build_care_llm_prompt
                sys_p, user_p = build_care_llm_prompt(
                    pid, kit, body, thread_comments=None, vault_root=self.vault_root
                )
                import aux_engine
                async with self._llm_lock:
                    llm_res = await aux_engine.complete_json(sys_p, user_p, timeout_s=20)

                if not llm_res.get("refuse") and llm_res.get("reply"):
                    reply_text = llm_res["reply"]
                    send_res = await _call_graph(
                        "fb_page_reply",
                        {"comment_id": cid, "message": reply_text, "page_id": pid},
                        actor="care-worker",
                        vault_root=str(self.vault_root),
                        policy_context={"action": "llm_reply", "mode": eff_m, "class_name": class_name},
                    )
                    if not str(send_res).startswith("ERROR:"):
                        store.record_action(ev_id, "reply", cid, eff_m, "care-worker")
                        store.increment_rate_count(pid, hour_key)
                        out["replied"] = True
                    else:
                        store.create_draft(ev_id, pid, cid, reply_text, class_name)
                        out["draft_created"] = True
                else:
                    refuse_err = llm_res.get("error") or "Không đủ dữ liệu chắc chắn để trả lời"
                    fallback_key = "ambiguous" if (kit and kit.get("brand") == "bsn") else "hoc_phi"
                    draft_content = (
                        llm_res.get("reply")
                        or render_template(fallback_key, kit, vault_root=self.vault_root)
                        or render_template("hoc_phi", kit, vault_root=self.vault_root)
                        or "Cần tư vấn hỗ trợ"
                    )
                    store.create_draft(ev_id, pid, cid, draft_content, class_name)
                    out["draft_created"] = True
                    if self.deps.tasks_feature and hasattr(self.deps.tasks_feature, "enqueue"):
                        try:
                            campus_str = kit.get("name") if kit else "Cơ sở"
                            self.deps.tasks_feature.enqueue(
                                brain=self.brain,
                                title=f"Cần người xử lý: {from_name} — {campus_str}",
                                intent=(
                                    f"Bình luận cần người hỗ trợ: '{body[:300]}'. Lý do: {refuse_err}. "
                                    f"Đã tạo nháp trong Chăm sóc Fanpage."
                                ),
                                route="auto",
                                priority=2,
                                capability="mcp-read",
                                execution_mode="suggest",
                                created_by="fanpage_care",
                                idempotency_key=f"care:{cid}",
                            )
                        except Exception as e:
                            print(f"[fanpage_care] Enqueue task error: {e}", file=sys.stderr)
            else:
                draft_content = render_template("hoc_phi", kit, vault_root=self.vault_root) or "Cần tư vấn hỗ trợ"
                store.create_draft(ev_id, pid, cid, draft_content, class_name)
                out["draft_created"] = True

        # Mọi trường hợp còn lại (suggest mode / unknown):
        else:
            draft_content = render_template("hoc_phi", kit, vault_root=self.vault_root) or "Cần tư vấn hỗ trợ"
            store.create_draft(ev_id, pid, cid, draft_content, class_name)
            out["draft_created"] = True

        return out

    async def process_inbound_message(
        self, pid: str, item: dict[str, Any], cfg: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Xử lý tin nhắn và echo từ Messenger Webhook."""
        cfg = cfg or self.get_config()
        out = {"replied": False, "draft_created": False, "takeover_activated": False}
        if not cfg.get("enabled", False):
            return out

        sender_id = str(item.get("sender", {}).get("id", "")).strip()
        recipient_id = str(item.get("recipient", {}).get("id", "")).strip()
        timestamp = item.get("timestamp")
        msg = item.get("message", {}) or {}
        mid = str(msg.get("mid") or f"m_{time.time()}").strip()
        text = str(msg.get("text") or "").strip()
        is_echo = bool(msg.get("is_echo") or (sender_id == pid))
        metadata = str(msg.get("metadata") or "").strip()

        # Mode và policy context
        eff_m = effective_mode(cfg.get("mode", "suggest"), cfg.get("pages", {}).get(pid, {}).get("mode"))
        is_quiet = in_quiet_hours(cfg.get("quiet_hours", "21-07"), timezone_str=cfg.get("tz", "Asia/Ho_Chi_Minh"))
        kill_switch = bool(cfg.get("kill_switch", False))

        # 1. Xử lý message_echoes
        if is_echo:
            psid = recipient_id
            if metadata == "care-worker":
                # Do chính Javis Care gửi qua fb_message_send
                store.update_messaging_window(pid, psid, is_user=False)
            else:
                # Do nhân viên trực tiếp chat trên Meta Business Suite / Messenger
                # -> Kích hoạt Human Takeover (đóng băng thread 4 giờ)
                takeover_hours = float(cfg.get("takeover_hours", 4.0))
                until = store.set_human_takeover(pid, psid, duration_hours=takeover_hours)
                store.record_event({
                    "kind": "echo",
                    "platform": "messenger",
                    "page_id": pid,
                    "object_id": mid,
                    "thread_id": psid,
                    "from_id": pid,
                    "from_name": "Nhân viên Fanpage",
                    "body": text,
                    "class": "human_echo",
                    "created_ts": (timestamp / 1000.0) if timestamp else time.time(),
                })
                out["takeover_activated"] = True
                print(f"[fanpage_care] Human takeover activated on page {pid}, psid {psid} for {takeover_hours}h (until {until})", file=sys.stderr)
            return out

        # 2. Tin nhắn từ khách hàng (inbound)
        psid = sender_id
        store.update_messaging_window(pid, psid, is_user=True)

        ev_id, is_new = store.record_event({
            "kind": "message",
            "platform": "messenger",
            "page_id": pid,
            "object_id": mid,
            "thread_id": psid,
            "from_id": psid,
            "from_name": f"Khách Messenger {psid[-4:] if len(psid) >= 4 else psid}",
            "body": text,
            "created_ts": (timestamp / 1000.0) if timestamp else time.time(),
        })
        if not is_new:
            return out

        # 3. Phân loại tin nhắn
        kit = _load_kit_for_page(self.vault_root, pid)
        brand = detect_brand_from_kit(kit["file"]) if (kit and kit.get("file")) else "saoviet"
        cls_res = classify_comment(
            text,
            page_id=pid,
            from_id=psid,
            platform="messenger",
            brand=brand,
        )
        class_name = cls_res.get("class", "ambiguous")
        phones_list = cls_res.get("phones", [])
        course_hints = cls_res.get("course_hints", [])

        # 4. Ghi nhận CRM
        try:
            cust, is_new_cust = store.get_or_create_customer(
                name=f"Khách Messenger {psid[-4:] if len(psid) >= 4 else psid}",
                phones=phones_list,
                page_id=pid,
                psid=psid,
                course_interest=course_hints[0] if course_hints else "",
                campus=kit.get("name") if kit else "",
                tag=class_name if class_name == "lead" else "",
            )
            cust_crm_id = cust.get("crm_id")
            if cust_crm_id:
                crm.sync_customer_markdown(
                    self.vault_root,
                    cust_crm_id,
                    name=f"Khách Messenger {psid[-4:] if len(psid) >= 4 else psid}",
                    phones=phones_list,
                    tags=[class_name] if class_name == "lead" else [],
                    course_interest=course_hints[0] if course_hints else "",
                    campus=kit.get("name") if kit else "",
                    page_id=pid,
                    timeline_entry=f"Tin nhắn '{text[:100]}' (class={class_name})",
                )
        except Exception as e:
            print(f"[fanpage_care] CRM sync error: {e}", file=sys.stderr)

        # 5. Kiểm tra Human Takeover
        if store.is_under_takeover(pid, psid):
            print(f"[fanpage_care] PSID {psid} đang trong thời gian nhân viên takeover -> bỏ qua auto-reply.", file=sys.stderr)
            return out

        # 6. Kiểm tra Cửa sổ 24 giờ
        if not store.is_in_24h_window(pid, psid):
            store.create_draft(ev_id, pid, psid, "Ngoài cửa sổ 24 giờ của Meta", "expired_window")
            out["draft_created"] = True
            return out

        # 7. Đánh giá policy và phản hồi
        ok, why = policy_allows(
            "messenger_reply",
            mode=eff_m,
            class_name=class_name,
            is_quiet=is_quiet,
            rate_exceeded=False,
            kill_switch=kill_switch,
        )

        reply_text = None
        if ok and eff_m == "full":
            if class_name == "faq":
                reply_text = render_template(
                    cls_res.get("faq_intent") or "hoc_phi",
                    kit,
                    course_hint=course_hints[0] if course_hints else None,
                    vault_root=self.vault_root,
                )
            elif class_name == "lead":
                reply_text = render_template(
                    "lead_thanks",
                    kit,
                    course_hint=course_hints[0] if course_hints else None,
                    vault_root=self.vault_root,
                )
            elif class_name in ("ambiguous", "ky_thuat"):
                from fanpage_care_ground import build_care_llm_prompt
                sys_p, user_p = build_care_llm_prompt(
                    pid, kit, text, thread_comments=None, vault_root=self.vault_root
                )
                import aux_engine
                async with self._llm_lock:
                    llm_res = await aux_engine.complete_json(sys_p, user_p, timeout_s=20)
                if not llm_res.get("refuse") and llm_res.get("reply"):
                    reply_text = llm_res["reply"]

            if reply_text:
                send_res = await fanpage_care_graph.call(
                    "fb_message_send",
                    {"recipient_id": psid, "message": reply_text, "page_id": pid},
                    actor="care-worker",
                    vault_root=str(self.vault_root),
                    policy_context={"action": "messenger_reply", "mode": eff_m, "class_name": class_name},
                )
                if not str(send_res).startswith("ERROR:"):
                    store.record_action(ev_id, "send", psid, eff_m, "care-worker")
                    store.update_messaging_window(pid, psid, is_user=False)
                    out["replied"] = True
                else:
                    store.create_draft(ev_id, pid, psid, reply_text, class_name)
                    out["draft_created"] = True
            else:
                store.create_draft(ev_id, pid, psid, "Cần hỗ trợ tư vấn", class_name)
                out["draft_created"] = True
        else:
            draft_content = render_template("hoc_phi", kit, vault_root=self.vault_root) or "Cần hỗ trợ tư vấn"
            store.create_draft(ev_id, pid, psid, draft_content, class_name)
            out["draft_created"] = True

        return out

    async def process_webhook_payload(self, payload: dict[str, Any]) -> None:
        """Xử lý sự kiện gửi về từ Meta Webhook."""
        cfg = self.get_config()
        if not cfg.get("enabled", False):
            return

        entries = payload.get("entry", []) or []
        for entry in entries:
            pid = str(entry.get("id", ""))
            # 1. Changes (feed comments)
            changes = entry.get("changes", []) or []
            for ch in changes:
                field = ch.get("field")
                val = ch.get("value", {}) or {}
                if field == "feed":
                    item = val.get("item")
                    verb = val.get("verb")
                    if item in ("comment", "reply"):
                        cid = str(val.get("comment_id", ""))
                        post_id = str(val.get("post_id", ""))
                        parent_id = str(val.get("parent_id", "")) if item == "reply" else None
                        body = str(val.get("message", "")).strip()
                        from_info = val.get("from", {}) or {}
                        from_id = str(from_info.get("id", ""))
                        from_name = str(from_info.get("name", "") or "Ẩn danh")
                        created_time = val.get("created_time")

                        if from_id == pid:
                            continue

                        if verb == "edited":
                            store.update_event_body("comment", cid, body, from_name)
                            continue

                        if verb == "add":
                            await self.process_inbound_comment(
                                pid, cid, post_id, parent_id, from_id, from_name, body, created_time, cfg=cfg
                            )

            # 2. Messaging (Messenger messages & message_echoes)
            messaging_events = entry.get("messaging", []) or []
            for item in messaging_events:
                await self.process_inbound_message(pid, item, cfg=cfg)

    def _make_router(self) -> APIRouter:
        router = APIRouter()

        @router.get("/hook/facebook")
        async def fb_webhook_verify(
            hub_mode: str = Query(None, alias="hub.mode"),
            hub_verify_token: str = Query(None, alias="hub.verify_token"),
            hub_challenge: str = Query(None, alias="hub.challenge"),
        ):
            cfg = self.get_config()
            expected_token = cfg.get("webhook_verify_token") or ""
            if not expected_token:
                try:
                    import secrets_store
                    expected_token = secrets_store.get_secret("facebook_webhook.verify_token") or ""
                except Exception:
                    pass

            if hub_mode == "subscribe" and hub_verify_token and expected_token and hub_verify_token == expected_token:
                return PlainTextResponse(content=hub_challenge or "", status_code=200)

            print("[fanpage_care] verify fail", file=sys.stderr)
            raise HTTPException(status_code=403, detail="Verification failed")

        @router.post("/hook/facebook")
        async def fb_webhook_event(request: Request):
            raw_body = await request.body()
            sig_header = request.headers.get("X-Hub-Signature-256", "")

            # Get App Secret
            app_secret = ""
            try:
                import mcp_store
                app_secret = mcp_store.connection_secrets("facebook-pages").get("client_secret", "")
            except Exception:
                pass
            if not app_secret:
                cfg = self.get_config()
                app_secret = cfg.get("app_secret", "")

            if not app_secret or not sig_header:
                raise HTTPException(status_code=403, detail="Missing signature or secret")

            expected_sig = "sha256=" + hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_sig, sig_header):
                print("[fanpage_care] HMAC signature mismatch", file=sys.stderr)
                raise HTTPException(status_code=403, detail="Invalid signature")

            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                return JSONResponse({"status": "error", "error": "invalid_json"}, status_code=400)

            cfg = self.get_config()
            if not cfg.get("enabled", False):
                return JSONResponse({"status": "ignored_disabled"})

            asyncio.create_task(self.process_webhook_payload(payload))
            return JSONResponse({"status": "ok"})

        @router.get("/fanpage-care/state")
        async def care_state():
            cfg = self.get_config()
            eligible = list_eligible_pages(self.vault_root)
            st = store.get_stats()
            fb_st = facebook_pages_status()
            return {
                "ok": True,
                "config": cfg,
                "stats": st,
                "eligible_pages": eligible,
                "connection_perm": fb_st.get("perm", "readonly"),
                "facebook_connected": fb_st.get("connected", False),
                "facebook_label": fb_st.get("label", ""),
                "is_quiet": in_quiet_hours(cfg.get("quiet_hours", "21-07")),
                "poller_running": self._tick_running,
            }

        @router.post("/fanpage-care/settings")
        async def care_save_settings(payload: dict = Body(...)):
            cfg = self.save_config(payload)
            return {"ok": True, "config": cfg}

        @router.get("/fanpage-care/inbox")
        async def care_inbox(
            page_id: str | None = None,
            class_name: str | None = None,
            platform: str | None = None,
            limit: int = 50,
            offset: int = 0,
        ):
            events = store.list_events(
                page_id=page_id,
                class_name=class_name,
                platform=platform,
                limit=limit,
                offset=offset,
            )
            drafts = store.list_drafts(status="pending", limit=50)
            return {
                "ok": True,
                "events": events,
                "drafts": drafts,
                "stats": store.get_stats(),
            }

        @router.post("/fanpage-care/drafts/{draft_id}/send")
        async def care_draft_send(draft_id: int):
            d = store.get_draft(draft_id)
            if not d:
                raise HTTPException(status_code=404, detail="draft_not_found")
            if d.get("status") != "pending":
                raise HTTPException(status_code=400, detail="draft_already_processed")

            pid = d["page_id"]
            cid = d["target_id"]
            msg = d["proposed"]

            res = await fanpage_care_graph.call(
                "fb_page_reply",
                {"comment_id": cid, "message": msg, "page_id": pid},
                actor="user",
                vault_root=str(self.vault_root),
            )
            if str(res).startswith("ERROR:"):
                return {"ok": False, "error": str(res)}

            from datetime import timezone, timedelta
            tz_vn = timezone(timedelta(hours=7))
            hour_key = datetime.now(tz_vn).strftime("%Y-%m-%dT%H")
            store.update_draft_status(draft_id, "sent")
            store.record_action(d.get("event_id"), "reply", cid, "manual", "user")
            store.increment_rate_count(pid, hour_key)
            return {"ok": True, "status": "sent"}

        @router.post("/fanpage-care/drafts/{draft_id}/reject")
        async def care_draft_reject(draft_id: int):
            store.update_draft_status(draft_id, "rejected")
            return {"ok": True, "status": "rejected"}

        @router.get("/fanpage-care/customers")
        async def care_customers(q: str | None = None, tag: str | None = None, limit: int = 50):
            custs = store.search_customers(query=q, tag=tag, limit=limit)
            return {"ok": True, "customers": custs}

        @router.get("/fanpage-care/customers/{crm_id}")
        async def care_customer_detail(crm_id: str, format: str | None = None):
            cust = store.get_customer(crm_id)
            if not cust:
                raise HTTPException(status_code=404, detail="customer_not_found")
            md_path = self.vault_root / "crm" / "customers" / f"{crm_id}.md"
            md_text = ""
            if md_path.exists():
                try:
                    md_text = md_path.read_text(encoding="utf-8")
                except OSError:
                    pass

            if format == "md":
                return {"ok": True, "crm_id": crm_id, "markdown": md_text}

            return {
                "ok": True,
                "customer": cust,
                "identities": store.get_identities_for_customer(crm_id),
                "markdown": md_text,
            }

        @router.post("/fanpage-care/customers/merge")
        async def care_customer_merge(primary_crm_id: str = Body(..., embed=True), secondary_crm_id: str = Body(..., embed=True)):
            merged_id = crm.merge_customers(self.vault_root, primary_crm_id, secondary_crm_id)
            if not merged_id:
                raise HTTPException(status_code=400, detail="cannot_merge")
            return {"ok": True, "crm_id": merged_id}

        @router.delete("/fanpage-care/customers/{crm_id}")
        async def care_customer_delete(crm_id: str):
            crm.delete_customer_pdpd(self.vault_root, crm_id)
            return {"ok": True, "deleted": True}

        @router.post("/fanpage-care/handoff")
        async def care_handoff(
            title: str = Body(...),
            intent: str = Body(...),
            priority: int = Body(2),
            comment_id: str = Body(""),
        ):
            if not self.deps.tasks_feature:
                raise HTTPException(status_code=503, detail="tasks_feature_not_available")
            tid = self.deps.tasks_feature.enqueue(
                brain=self.brain,
                title=title,
                intent=intent,
                route="auto",
                priority=priority,
                capability="mcp-read",
                execution_mode="suggest",
                created_by="fanpage_care",
                idempotency_key=f"care:{comment_id}" if comment_id else "",
            )
            return {"ok": True, "task_id": tid}

        @router.post("/fanpage-care/poll-now")
        async def care_poll_now(payload: dict[str, Any] | None = Body(None)):
            data = payload or {}
            pid = str(data.get("page_id") or "").strip() or None
            res = await self.poll_tick(page_id=pid, force_ingest=True)
            return {"ok": True, "result": res}

        @router.get("/fanpage-care/conversations")
        async def care_conversations():
            convs = store.get_recent_conversations()
            return {"ok": True, "conversations": convs}

        @router.post("/fanpage-care/conversations/release-takeover")
        async def care_release_takeover(
            page_id: str = Body(...),
            psid: str = Body(...),
        ):
            store.release_human_takeover(page_id, psid)
            return {"ok": True, "page_id": page_id, "psid": psid, "takeover_until": 0.0}

        return router


def register(app, deps: FanpageCareDeps) -> FanpageCareFeature:
    global _FEATURE
    feature = FanpageCareFeature(deps)
    app.include_router(feature.router)
    _FEATURE = feature
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(feature.start())
    except RuntimeError:
        pass
    return feature


def current() -> Optional[FanpageCareFeature]:
    return _FEATURE
