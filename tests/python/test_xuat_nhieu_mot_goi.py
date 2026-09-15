"""Chọn nhiều skill/workflow/agent rồi tải về MỘT gói - và gói đó nhập lại được nguyên vẹn.

    python tests/run.py xuat_nhieu_mot_goi     (KHÔNG mạng)

Yêu cầu chủ repo (16/08): trang Skills/Workflows chưa có "chọn tất cả" và "tải về những
cái đã chọn" - muốn chia sẻ 10 skill là phải bấm Xuất 10 lần, nhận 10 file zip. Nay:
tick từng thẻ hoặc Chọn tất cả → MỘT gói javis-bundle duy nhất, nhập lại một phát.

Điểm phải ghim: manifest v1 GIỮ NGUYÊN hình dạng (primary + items) nên gói chọn-nhiều
mở được bằng cả bản Javis cũ - items vốn là danh sách từ đầu, phía nhập không cần biết
gì mới.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


import share_bundle  # noqa: E402


def _dung_brain(td):
    """Brain giả: 2 workflow dùng 2 agent, mỗi agent 1 skill; thêm 1 skill mồ côi."""
    ag, wf, sk = Path(td) / "agents", Path(td) / "workflows", Path(td) / "skills"
    for d in (ag, wf, sk):
        d.mkdir(parents=True, exist_ok=True)
    for i in (1, 2):
        (sk / f"skill-{i}").mkdir()
        (sk / f"skill-{i}" / "SKILL.md").write_text(
            f"---\nname: Skill {i}\n---\nthân {i}\n", encoding="utf-8")
        (ag / f"agent-{i}.md").write_text(
            f"---\nname: Agent {i}\nrole: vai {i}\nskills:\n  - skill-{i}\n---\n",
            encoding="utf-8")
        (wf / f"wf-{i}.md").write_text(
            f"---\nname: Wf {i}\nsteps:\n  - agent: agent-{i}\n    task: lam viec\n---\n",
            encoding="utf-8")
    (sk / "skill-le").mkdir()
    (sk / "skill-le" / "SKILL.md").write_text("---\nname: Skill lẻ\n---\n", encoding="utf-8")
    return ag, wf, sk


with tempfile.TemporaryDirectory() as td:
    ag, wf, sk = _dung_brain(td)
    KW = dict(agents_dir=ag, workflows_dir=wf, skills_root=sk)

    # ---- 1. Một slug (đường cũ) vẫn y nguyên ----
    data1, ten1 = share_bundle.build_bundle("workflow", "wf-1", **KW)
    check("một slug: vẫn xuất được như cũ", bool(data1) and ten1.endswith(".javis.zip"))
    z1 = zipfile.ZipFile(io.BytesIO(data1))
    check("một slug: tên file theo TÊN năng lực (không đổi hành vi cũ)", ten1 == "Wf-1.javis.zip")

    # ---- 2. Nhiều slug → MỘT gói, đủ phụ thuộc ----
    data, ten = share_bundle.build_bundle("workflow", ["wf-1", "wf-2"], **KW)
    check("CANARY: chọn 2 workflow ra MỘT gói", bool(data))
    z = zipfile.ZipFile(io.BytesIO(data))
    co = set(z.namelist())
    for f in ("workflows/wf-1.md", "workflows/wf-2.md", "agents/agent-1.md",
              "agents/agent-2.md", "skills/skill-1/SKILL.md", "skills/skill-2/SKILL.md"):
        check(f"gói chứa {f}", f in co)
    check("skill lẻ KHÔNG bị vơ vào", "skills/skill-le/SKILL.md" not in co)
    check("tên file nói rõ số lượng", ten == "javis-workflow-x2.javis.zip")

    mf = json.loads(z.read("javis-bundle.json"))
    check("manifest giữ hình dạng v1 (primary + items) - bản Javis cũ vẫn nhập được",
          mf.get("version") == 1 and isinstance(mf.get("primary"), dict)
          and isinstance(mf.get("items"), list))
    check("items đủ 6 mục (2 wf + 2 agent + 2 skill)", len(mf["items"]) == 6)

    # Slug rác trong danh sách không làm chết cả gói (bỏ qua như đường cũ).
    d3, _ = share_bundle.build_bundle("workflow", ["wf-1", "khong-co"], **KW)
    check("slug không tồn tại bị bỏ qua, gói vẫn ra", bool(d3))

    # ---- 3. Vòng tròn: nhập gói vào brain TRỐNG, đủ lại nguyên bộ ----
    with tempfile.TemporaryDirectory() as td2:
        ag2, wf2, sk2 = Path(td2) / "agents", Path(td2) / "workflows", Path(td2) / "skills"
        res = share_bundle.import_bundle(data, ten, agents_dir=ag2, workflows_dir=wf2,
                                         skills_root=sk2)
        check("CANARY: nhập lại không lỗi", not res.get("errors"))
        check("đủ 2 workflow", (wf2 / "wf-1.md").is_file() and (wf2 / "wf-2.md").is_file())
        check("đủ 2 agent", (ag2 / "agent-1.md").is_file() and (ag2 / "agent-2.md").is_file())
        check("đủ 2 skill", (sk2 / "skill-1" / "SKILL.md").is_file()
              and (sk2 / "skill-2" / "SKILL.md").is_file())

# ---- 4. Dây nối endpoint + UI ----
src = (SERVER / "main.py").read_text(encoding="utf-8")
check("/export nhận slug CSV (chọn nhiều)", 'str(slug or "").split(",")' in src)
check("/export có trần số lượng", "len(slugs) > 200" in src)

sj = (ROOT / "dashboard" / "studio.js").read_text(encoding="utf-8")
check("UI có Chọn tất cả + Tải đã chọn dùng chung cho 3 trang",
      "chonTatCa" in sj and "taiDaChon" in sj)
for cls, trang in (("wf-sel", "workflow"), ("sk2-sel", "skill"), ("ag-sel", "agent")):
    check(f"trang {trang} có ô tick từng thẻ ({cls})", f'class="{cls}"' in sj)
check("skill hệ thống không vào diện chọn (không xuất được, brain nào cũng sẵn)",
      "filter(s => !s.system)" in sj)

if _fails:
    print(f"\nFAIL {len(_fails)} muc: " + ", ".join(_fails))
    sys.exit(1)
print("\nOK - test_xuat_nhieu_mot_goi: tat ca pass")
