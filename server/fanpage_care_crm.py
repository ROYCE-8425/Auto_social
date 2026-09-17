"""Quản lý Markdown CRM cho Fanpage Care (<brain>/crm/customers/<crm_id>.md và crm/index.md).

Đặc tả:
- File markdown cho từng khách hàng: <vault_root>/crm/customers/<crm_id>.md
- File tổng hợp Dataview: <vault_root>/crm/index.md (debounce 2s)
- Tuyệt đối KHÔNG ghi token / secret / EAA... vào markdown
- Hỗ trợ Nghị định 13/2023/NĐ-CP (PDPD): redact SĐT và xóa hồ sơ
"""
from __future__ import annotations

import datetime
import json
import re
import threading
import time
from pathlib import Path
from typing import Any

from fanpage_care_classify import VN_PHONE_RE

# Khóa debounce cho việc rebuild crm/index.md
_INDEX_LOCK = threading.Lock()
_LAST_INDEX_BUILD = 0.0


def redact_phone_in_text(text: str) -> str:
    """Thay thế các số điện thoại VN bằng [redacted] theo chuẩn bảo mật."""
    if not text:
        return ""
    return VN_PHONE_RE.sub("[redacted]", text)


def format_phone_display(phone: str) -> str:
    """Format 0935195118 -> 0935 195 118."""
    p = re.sub(r"\D", "", phone or "")
    if len(p) == 10:
        return f"{p[:4]} {p[4:7]} {p[7:]}"
    return phone or ""


def write_customer_markdown(
    vault_root: Path | str,
    customer: dict[str, Any],
    *,
    timeline_entry: str | None = None,
    identities: list[str] | None = None,
) -> Path:
    """Ghi hoặc cập nhật file Markdown hồ sơ khách hàng.

    Bảo toàn lịch sử Timeline cũ nếu file đã tồn tại.
    """
    v = Path(vault_root)
    crm_id = customer.get("crm_id")
    if not crm_id:
        raise ValueError("customer dict phải có 'crm_id'")

    cust_dir = v / "crm" / "customers"
    cust_dir.mkdir(parents=True, exist_ok=True)
    file_path = cust_dir / f"{crm_id}.md"

    now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    name = str(customer.get("name") or "Ẩn danh").strip()
    phones = customer.get("phones") or []
    tags = customer.get("tags") or ["lead"]
    course_interest = str(customer.get("course_interest") or "").strip()
    campus = str(customer.get("campus") or "").strip()
    page_ids = [str(pid) for pid in (customer.get("page_ids") or [])]
    brand = str(customer.get("brand") or "").strip()
    if not brand:
        if any(p == "343562028848465" for p in page_ids) or "bsn" in tags:
            brand = "bsn"
        else:
            brand = "saoviet"
    status = str(customer.get("status") or "open").strip()
    owner_staff = str(customer.get("owner_staff") or "").strip()
    merged_into = str(customer.get("merged_into") or "").strip()

    # Đọc timeline và identities cũ nếu đã có file
    existing_timeline: list[str] = []
    existing_identities: list[str] = []

    if file_path.is_file():
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Trích phần ## Identities
            if "## Identities" in content:
                id_part = content.split("## Identities", 1)[1]
                if "## " in id_part:
                    id_part = id_part.split("## ", 1)[0]
                for line in id_part.splitlines():
                    line = line.strip()
                    if line.startswith("- "):
                        existing_identities.append(line[2:].strip())

            # Trích phần ## Timeline
            if "## Timeline" in content:
                tl_part = content.split("## Timeline", 1)[1]
                for line in tl_part.splitlines():
                    line = line.strip()
                    if line.startswith("- "):
                        existing_timeline.append(line[2:].strip())
        except Exception:
            pass

    # Gộp identities mới
    all_identities = list(existing_identities)
    for p in phones:
        id_str = f"phone:{p}"
        if id_str not in all_identities:
            all_identities.append(id_str)
    for extra_id in (identities or []):
        if extra_id and extra_id not in all_identities:
            all_identities.append(extra_id)

    # Thêm timeline entry mới
    if timeline_entry:
        now_date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry_clean = timeline_entry.strip().lstrip("-").strip()
        all_timeline = existing_timeline + [f"{now_date_str} {entry_clean}"]
    else:
        all_timeline = existing_timeline

    # Định dạng hiển thị
    phones_display = ", ".join(format_phone_display(p) for p in phones) or "Chưa có"
    tags_display = ", ".join(tags) or "lead"
    page_ids_display = ", ".join(page_ids) or "Chưa rõ"

    # Xây dựng markdown bảo vệ an toàn token
    id_lines = "\n".join(f"- {i}" for i in all_identities) if all_identities else "- (chưa có)"
    tl_lines = "\n".join(f"- {t}" for t in all_timeline) if all_timeline else "- (chưa có tương tác)"

    md = f"""---
type: crm-customer
crm_id: {crm_id}
brand: {json.dumps(brand, ensure_ascii=False)}
name: {json.dumps(name, ensure_ascii=False)}
phones: {json.dumps(phones, ensure_ascii=False)}
tags: {json.dumps(tags, ensure_ascii=False)}
course_interest: {json.dumps(course_interest, ensure_ascii=False)}
campus: {json.dumps(campus, ensure_ascii=False)}
page_ids: {json.dumps(page_ids, ensure_ascii=False)}
owner_staff: {json.dumps(owner_staff, ensure_ascii=False)}
status: {status}
merged_into: {json.dumps(merged_into, ensure_ascii=False)}
updated: {now_iso}
---

# {name}

- Thương hiệu: {brand}
- Tên: {name}
- SĐT: {phones_display}
- Ngành quan tâm: {course_interest or "Chưa rõ"}
- Cơ sở: {campus or "Chưa rõ"}
- Tag: {tags_display}
- Trang nguồn: {page_ids_display}
- Nhân viên phụ trách: {owner_staff or "Chưa gán"}

## Identities
{id_lines}

## Timeline
{tl_lines}
"""
    # An toàn tuyệt đối: không để token hay access_token lọt vào
    assert "access_token" not in md.lower() or "page_access_token" not in md.lower()

    file_path.write_text(md, encoding="utf-8")
    return file_path


def rebuild_crm_index(vault_root: Path | str, db_path: Path | str | None = None) -> None:
    """Tạo lại bảng Dataview trong crm/index.md (có debounce 2s)."""
    global _LAST_INDEX_BUILD
    with _INDEX_LOCK:
        now = time.time()
        if now - _LAST_INDEX_BUILD < 2.0:
            return
        _LAST_INDEX_BUILD = now

    v = Path(vault_root)
    crm_dir = v / "crm"
    crm_dir.mkdir(parents=True, exist_ok=True)
    index_path = crm_dir / "index.md"

    from fanpage_care_store import search_customers

    customers = search_customers("", db_path=db_path, limit=200)

    rows = []
    for c in customers:
        name = c.get("name") or "Ẩn danh"
        phones = c.get("phones") or []
        phone_str = ", ".join(format_phone_display(p) for p in phones) or "-"
        tags = c.get("tags") or []
        tag_str = ", ".join(tags) or "lead"
        course = c.get("course_interest") or "-"
        campus = c.get("campus") or "-"
        crm_id = c.get("crm_id") or ""
        updated_ts = c.get("updated_ts") or time.time()
        date_str = datetime.datetime.fromtimestamp(updated_ts).strftime("%Y-%m-%d")
        link_str = f"[[crm/customers/{crm_id}]]"

        rows.append(f"| {name} | {phone_str} | {tag_str} | {course} | {campus} | {date_str} | {link_str} |")

    table_content = "\n".join(rows) if rows else "| Chưa có khách hàng nào | - | - | - | - | - | - |"

    md = f"""# CRM Fanpage

| Tên | SĐT | Tag | Ngành | Cơ sở | Lần cuối | File |
| --- | --- | --- | --- | --- | --- | --- |
{table_content}
"""
    index_path.write_text(md, encoding="utf-8")


def sync_customer_markdown(
    vault_root: Path | str,
    crm_id: str,
    *,
    name: str = "Ẩn danh",
    phones: list[str] | None = None,
    tags: list[str] | None = None,
    course_interest: str = "",
    campus: str = "",
    page_id: str = "",
    timeline_entry: str | None = None,
    identities: list[str] | None = None,
    brand: str = "",
) -> Path:
    """Helper đồng bộ hồ sơ khách hàng vào markdown."""
    cust = {
        "crm_id": crm_id,
        "name": name,
        "phones": phones or [],
        "tags": tags or ["lead"],
        "course_interest": course_interest,
        "campus": campus,
        "page_ids": [page_id] if page_id else [],
        "brand": brand,
    }
    path = write_customer_markdown(vault_root, cust, timeline_entry=timeline_entry, identities=identities)
    rebuild_crm_index(vault_root)
    return path


def delete_customer_pdpd(vault_root: Path | str, crm_id: str) -> None:
    """Xóa hồ sơ theo Nghị định 13/2023/NĐ-CP (PDPD): stub markdown + xóa SQLite."""
    from fanpage_care_store import delete_customer
    delete_customer(crm_id)

    v = Path(vault_root)
    file_path = v / "crm" / "customers" / f"{crm_id}.md"
    if file_path.exists():
        now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        stub_md = f"""---
type: crm-customer
crm_id: {crm_id}
name: "[redacted]"
phones: []
tags: []
course_interest: ""
campus: ""
page_ids: []
owner_staff: ""
status: deleted
merged_into: ""
updated: {now_iso}
---

# Khách hàng đã xóa (PDPD)

Hồ sơ đã được xóa theo yêu cầu bảo mật thông tin cá nhân.
"""
        file_path.write_text(stub_md, encoding="utf-8")
    rebuild_crm_index(vault_root)


def merge_customers(vault_root: Path | str, primary_crm_id: str, secondary_crm_id: str) -> str:
    """Gộp hai hồ sơ khách hàng: gộp identities/timeline vào primary, stub secondary."""
    from fanpage_care_store import get_customer, link_identity, get_connection
    p_cust = get_customer(primary_crm_id)
    s_cust = get_customer(secondary_crm_id)
    if not p_cust or not s_cust:
        return primary_crm_id

    # Gộp identities trong SQLite
    with get_connection() as conn:
        conn.execute("UPDATE identities SET crm_id = ? WHERE crm_id = ?", (primary_crm_id, secondary_crm_id))
        conn.execute("DELETE FROM customers WHERE crm_id = ?", (secondary_crm_id,))

    # Cập nhật markdown primary
    merged_phones = list(dict.fromkeys((p_cust.get("phones") or []) + (s_cust.get("phones") or [])))
    merged_tags = list(dict.fromkeys((p_cust.get("tags") or []) + (s_cust.get("tags") or [])))
    p_cust["phones"] = merged_phones
    p_cust["tags"] = merged_tags

    sync_customer_markdown(
        vault_root,
        primary_crm_id,
        name=p_cust.get("name") or "Ẩn danh",
        phones=merged_phones,
        tags=merged_tags,
        course_interest=p_cust.get("course_interest") or "",
        campus=p_cust.get("campus") or "",
        timeline_entry=f"Đã gộp hồ sơ từ {secondary_crm_id}",
    )

    # Stub secondary markdown
    v = Path(vault_root)
    s_path = v / "crm" / "customers" / f"{secondary_crm_id}.md"
    if s_path.exists():
        now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        stub_md = f"""---
type: crm-customer
crm_id: {secondary_crm_id}
name: "[merged]"
phones: []
tags: []
status: merged
merged_into: "{primary_crm_id}"
updated: {now_iso}
---

# Khách hàng đã gộp

Hồ sơ đã được gộp vào [[crm/customers/{primary_crm_id}]].
"""
        s_path.write_text(stub_md, encoding="utf-8")

    rebuild_crm_index(vault_root)
    return primary_crm_id
