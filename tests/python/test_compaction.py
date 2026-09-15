"""Test nén hội thoại dài engine API (v0.9.34). Chạy tay / CI:

    python tests/run.py compaction

Không cần API key, không chạm mạng (api_stream giả). Phủ: trim_history giữ run system
dẫn đầu, migration cột compact cho DB cũ, seed_messages chèn tóm tắt, maybe_compact
nén đúng ngưỡng + gộp tóm tắt cũ + không phá khi provider lỗi.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import asyncio
import os
import sqlite3
import sys
import tempfile
from pathlib import Path


import compaction                      # noqa: E402
from sessions import SessionStore     # noqa: E402

_fails = []


def check(name, cond):
    print(("ok  " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ---- 1. trim_history ----
check("trim: rỗng an toàn", compaction.trim_history([]) == [])
short = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
check("trim: ngắn giữ nguyên", compaction.trim_history(short) is short)

msgs = [{"role": "system", "content": "sys"}, {"role": "system", "content": "tóm tắt nén"}]
for i in range(20):
    msgs.append({"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"})
out = compaction.trim_history(msgs, max_msgs=12)
check("trim: giữ CẢ 2 system dẫn đầu (system prompt + tóm tắt)",
      [m["content"] for m in out[:2]] == ["sys", "tóm tắt nén"])
check("trim: tail đúng cửa sổ", len(out) <= 2 + 12)
check("trim: tail mở đầu bằng user", out[2]["role"] == "user")
check("trim: không mutate input", len(msgs) == 22)

# ---- 2. Migration DB cũ (chưa có cột compact) ----
tmp = Path(tempfile.mkdtemp(prefix="javis-compacttest-"))
old_db = tmp / "old.db"
conn = sqlite3.connect(str(old_db))
conn.executescript("""
CREATE TABLE sessions (
    id TEXT PRIMARY KEY, title TEXT, brain TEXT NOT NULL DEFAULT 'brain',
    engine TEXT, model TEXT, cli_session_id TEXT,
    created_at REAL NOT NULL, updated_at REAL NOT NULL,
    msg_count INTEGER NOT NULL DEFAULT 0, parent_session_id TEXT,
    archived INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL, content TEXT, ts REAL NOT NULL, tool_calls_json TEXT
);
""")
conn.commit()
conn.close()
store = SessionStore(db_path=old_db)
sid = store.create_session(brain="brain")
store.set_compact(sid, "tóm tắt thử", 4)
sess = store.get_session(sid)
check("migration: DB cũ thêm cột + set/get compact chạy",
      sess.get("compact_summary") == "tóm tắt thử" and sess.get("compact_count") == 4)

# ---- 3. seed_messages ----
store2 = SessionStore(db_path=tmp / "s2.db")
sid2 = store2.create_session(brain="brain")
raw = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(10)]
check("seed: chưa nén → giữ nguyên", compaction.seed_messages(store2, sid2, raw) is raw)
store2.set_compact(sid2, "đã bàn về X, chốt Y", 6)
seeded = compaction.seed_messages(store2, sid2, raw)
check("seed: bỏ 6 message đầu đã phủ", len(seeded) == 1 + 4)
check("seed: tóm tắt là system message đầu",
      seeded[0]["role"] == "system" and "đã bàn về X" in seeded[0]["content"])
check("seed: message sau tóm tắt đúng mạch", seeded[1]["content"] == "m6")

# ---- 4. maybe_compact với api_stream giả ----
calls = []


def fake_stream(text):
    async def _f(prov, key, model, messages, reasoning):
        calls.append(messages[0]["content"])
        yield {"type": "meta", "model": model}
        yield {"type": "text", "content": text}
    return _f


async def main():
    st = SessionStore(db_path=tmp / "s3.db")
    s = st.create_session(brain="brain")
    for i in range(10):   # 10 message: cut = 10-12 < 0 → chưa nén
        st.append_message(s, "user" if i % 2 == 0 else "assistant", f"nội dung {i}")
    r = await compaction.maybe_compact(st, s, "openrouter", "k", "m", fake_stream("TT1"))
    check("compact: dưới ngưỡng → không nén", r is False and not calls)

    for i in range(10, 20):   # 20 message: cut = 8 >= min_chunk 6 → nén msgs[0:8]
        st.append_message(s, "user" if i % 2 == 0 else "assistant", f"nội dung {i}")
    r = await compaction.maybe_compact(st, s, "openrouter", "k", "m", fake_stream("TT1"))
    sess = st.get_session(s)
    check("compact: đủ ngưỡng → nén", r is True)
    check("compact: lưu summary + count=8",
          sess.get("compact_summary") == "TT1" and sess.get("compact_count") == 8)
    check("compact: prompt chứa nội dung cần nén", "nội dung 0" in calls[-1] and "nội dung 7" in calls[-1])

    r = await compaction.maybe_compact(st, s, "openrouter", "k", "m", fake_stream("TT-thừa"))
    check("compact: ngay sau đó → không nén lại (idempotent)", r is False)

    for i in range(20, 26):   # 26 message: cut = 14, 14-8 = 6 → nén tiếp, GỘP tóm tắt cũ
        st.append_message(s, "user" if i % 2 == 0 else "assistant", f"nội dung {i}")
    r = await compaction.maybe_compact(st, s, "openrouter", "k", "m", fake_stream("TT2"))
    sess = st.get_session(s)
    check("compact: vòng 2 nén tiếp count=14", r is True and sess.get("compact_count") == 14)
    check("compact: prompt vòng 2 mang tóm tắt cũ để gộp", "TT1" in calls[-1])

    async def err_stream(prov, key, model, messages, reasoning):
        yield {"type": "error", "content": "provider chết"}
    for i in range(26, 34):
        st.append_message(s, "user" if i % 2 == 0 else "assistant", f"nội dung {i}")
    r = await compaction.maybe_compact(st, s, "openrouter", "k", "m", err_stream)
    sess = st.get_session(s)
    check("compact: provider lỗi → False, giữ nguyên tóm tắt cũ",
          r is False and sess.get("compact_summary") == "TT2" and sess.get("compact_count") == 14)


async def prepare_tests():
    """prepare_history: KHÔNG bỏ câm ngữ cảnh (bug đổi engine Claude→API mất trí nhớ)."""
    tmp2 = Path(tempfile.mkdtemp(prefix="javis-prep-"))
    head = [{"role": "system", "content": "SYS"}]

    # (a) Phiên vừa đổi từ Claude CLI sang API: có 30 message trong store, CHƯA có tóm tắt
    # (CLI không nén). Trước đây trim cắt còn 12, bỏ 18 message đầu KHÔNG tóm tắt → mất mạch.
    st = SessionStore(db_path=tmp2 / "switch.db")
    s = st.create_session(brain="brain")
    for i in range(30):
        st.append_message(s, "user" if i % 2 == 0 else "assistant", f"m{i}")
    st.append_message(s, "user", "câu hỏi hiện tại")   # câu user vừa lưu (sẽ bị [:-1] loại)
    raw = [{"role": m["role"], "content": m["content"]}
           for m in st.get_messages(s)[:-1] if m["role"] in ("user", "assistant")]
    out = await compaction.prepare_history(head, st, s, raw,
                                           "openrouter", "k", "m", fake_stream("TÓM-TẮT"))
    contents = " ".join(m["content"] for m in out)
    check("prepare: đuôi dài + chưa tóm tắt → nén ĐỒNG BỘ, không mất phần đầu",
          "TÓM-TẮT" in contents and out[0]["content"] == "SYS")
    # message cũ nhất (m0) không còn nguyên văn NHƯNG phải nằm trong tóm tắt (không biến mất câm)
    sess = st.get_session(s)
    check("prepare: đã tạo tóm tắt nén phủ phần đầu", (sess.get("compact_count") or 0) > 0)
    check("prepare: payload bị chặn kích thước (head + tóm tắt + đuôi gần)", len(out) <= 1 + 1 + 12)
    check("prepare: giữ được các message GẦN nhất nguyên văn", any(m["content"] == "m29" for m in out))

    # (b) Phiên ngắn (10 message, chưa quá ngưỡng): gửi NGUYÊN VĂN hết, không nén, không bỏ.
    st2 = SessionStore(db_path=tmp2 / "short.db")
    s2 = st2.create_session(brain="brain")
    for i in range(10):
        st2.append_message(s2, "user" if i % 2 == 0 else "assistant", f"n{i}")
    st2.append_message(s2, "user", "hỏi tiếp")
    raw2 = [{"role": m["role"], "content": m["content"]}
            for m in st2.get_messages(s2)[:-1] if m["role"] in ("user", "assistant")]
    out2 = await compaction.prepare_history(head, st2, s2, raw2,
                                            "openrouter", "k", "m", fake_stream("KHÔNG-DÙNG"))
    c2 = [m["content"] for m in out2]
    check("prepare: phiên ngắn → giữ nguyên văn TẤT CẢ, không nén",
          out2[0]["content"] == "SYS" and c2.count("KHÔNG-DÙNG") == 0
          and all(f"n{i}" in c2 for i in range(10)))


async def mem_tests():
    """compact_mem: nén lịch sử IN-MEMORY (phiên Telegram) - phần cũ vào tóm tắt, KHÔNG cắt câm.
    Đây là cùng lớp lỗi mất ngữ cảnh đã vá cho dashboard, nhưng cho nhánh giữ sess['or'] in RAM."""
    head_sys = {"role": "system", "content": "SYS+ident"}

    # (a) Phiên dài: 20 message user/assistant, cut = 20-12 = 8 >= min_chunk 6 → nén phần đầu.
    mem_calls = []

    def mem_stream(text):
        async def _f(prov, key, model, messages, reasoning):
            mem_calls.append(messages[0]["content"])
            yield {"type": "meta", "model": model}
            yield {"type": "text", "content": text}
        return _f

    mem = [head_sys]
    for i in range(20):
        mem.append({"role": "user" if i % 2 == 0 else "assistant", "content": f"t{i}"})
    out = await compaction.compact_mem(mem, "openrouter", "k", "m", mem_stream("MEM-TT"))
    contents = [m["content"] for m in out]
    check("compact_mem: giữ system cố định đầu tiên", out[0]["content"] == "SYS+ident")
    check("compact_mem: chèn 1 system tóm tắt sau head",
          out[1]["role"] == "system" and out[1]["content"].startswith(compaction.SUMMARY_HEADER)
          and "MEM-TT" in out[1]["content"])
    check("compact_mem: giữ message GẦN nhất nguyên văn", "t19" in contents)
    check("compact_mem: bỏ nguyên văn message CŨ (t0) - đã vào tóm tắt, không mất câm",
          "t0" not in contents and "t0" in mem_calls[-1] and "t7" in mem_calls[-1])
    check("compact_mem: payload bị chặn (head + tóm tắt + <=12 gần)", len(out) <= 1 + 1 + 12)
    check("compact_mem: đuôi mở đầu bằng user", out[2]["role"] == "user")
    check("compact_mem: KHÔNG mutate input", len(mem) == 21)

    # (b) Vòng 2 (rolling): nối thêm lượt mới rồi nén tiếp → tóm tắt cũ được GỘP vào prompt.
    mem2 = list(out)
    for i in range(20, 28):
        mem2.append({"role": "user" if i % 2 == 0 else "assistant", "content": f"t{i}"})
    out2 = await compaction.compact_mem(mem2, "openrouter", "k", "m", mem_stream("MEM-TT2"))
    check("compact_mem: vòng 2 gộp tóm tắt cũ vào prompt", "MEM-TT" in mem_calls[-1])
    check("compact_mem: vòng 2 ra tóm tắt mới", "MEM-TT2" in out2[1]["content"])
    check("compact_mem: vòng 2 vẫn giữ message mới nhất", any(m["content"] == "t27" for m in out2))

    # (c) Phiên ngắn (8 message, cut < min_chunk): giữ NGUYÊN, KHÔNG gọi provider, không mất gì.
    before = len(mem_calls)
    short_mem = [head_sys] + [{"role": "user" if i % 2 == 0 else "assistant", "content": f"s{i}"}
                             for i in range(8)]
    outS = await compaction.compact_mem(short_mem, "openrouter", "k", "m", mem_stream("NOPE"))
    cS = [m["content"] for m in outS]
    check("compact_mem: phiên ngắn → không gọi tóm tắt", len(mem_calls) == before)
    check("compact_mem: phiên ngắn → giữ nguyên văn tất cả",
          all(f"s{i}" in cS for i in range(8)) and "NOPE" not in " ".join(cS))

    # (d) Provider lỗi khi nén phiên dài → fallback trim_history: chặn phình, không văng, không mất head.
    async def mem_err(prov, key, model, messages, reasoning):
        yield {"type": "error", "content": "provider chết"}
    mem_long = [head_sys]
    for i in range(20):
        mem_long.append({"role": "user" if i % 2 == 0 else "assistant", "content": f"e{i}"})
    outE = await compaction.compact_mem(mem_long, "openrouter", "k", "m", mem_err)
    check("compact_mem: provider lỗi → fallback trim, giữ head + chặn kích thước",
          outE[0]["content"] == "SYS+ident" and len(outE) <= 1 + 1 + 12 and any(m["content"] == "e19" for m in outE))


asyncio.run(main())
asyncio.run(prepare_tests())
asyncio.run(mem_tests())

if _fails:
    print(f"\nFAIL - {len(_fails)} test: {_fails}")
    sys.exit(1)
print("\nOK - test_compaction: tất cả pass")
