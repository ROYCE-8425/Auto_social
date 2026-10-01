"""
Javis Ops - Persistent Tasks Store for Social Commerce Kanban
Manages tasks for CSKH staff and managers.
Data file: STATE_DIR / "ops_tasks.json"
"""
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
try:
    import config as cfgmod
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import config as cfgmod

TASKS_FILE = cfgmod.STATE_DIR / "ops_tasks.json"

DEFAULT_TASKS: List[Dict[str, Any]] = [
    # Cột 1: Cần làm
    {
        "id": "rescue_1",
        "title": "Cứu khách dừng phản hồi 24h: Tặng voucher giảm 10%",
        "customer": "Hoàng Anh Tuấn",
        "tag": "Cứu lead 24h",
        "tagColor": "rose",
        "time": "24 giờ trước",
        "isUrgent": True,
        "columnId": "todo",
        "leadScore": 88,
        "rescueStage": "24h",
        "approvalRisk": "medium",
        "assignee": {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 86400,
    },
    {
        "id": "task_1",
        "title": "Hỗ trợ cài đặt game cho khách",
        "customer": "Nguyễn Văn An",
        "tag": "Hỗ trợ kỹ thuật",
        "tagColor": "slate",
        "time": "Hôm nay",
        "isUrgent": True,
        "columnId": "todo",
        "leadScore": 70,
        "approvalRisk": "low",
        "assignee": {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 7200,
    },
    {
        "id": "task_2",
        "title": "Gửi bảng giá cho khách",
        "customer": "Trần Thị Mai",
        "tag": "Tư vấn",
        "tagColor": "amber",
        "time": "Hôm nay",
        "isUrgent": True,
        "columnId": "todo",
        "assignee": {"code": "LT", "name": "Lê Thảo", "username": "nv_thao", "bg": "bg-blue-800 text-white"},
        "created_at": time.time() - 10800,
    },
    {
        "id": "task_3",
        "title": "Kiểm tra đơn hàng lỗi",
        "customer": "#DHT2345",
        "tag": "Đơn hàng",
        "tagColor": "rose",
        "time": "Hôm nay",
        "isUrgent": True,
        "columnId": "todo",
        "assignee": {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 3600,
    },
    # Cột 2: Đang xử lý
    {
        "id": "task_4",
        "title": "Khách báo lỗi không vào game",
        "customer": "Lê Hoàng Nam",
        "tag": "Khiếu nại",
        "tagColor": "orange",
        "time": "2 giờ trước",
        "isUrgent": True,
        "columnId": "in_progress",
        "assignee": {"code": "TH", "name": "Trần Hùng", "username": "nv_hung", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 7200,
    },
    {
        "id": "task_5",
        "title": "Tư vấn gói nâng cấp",
        "customer": "Phạm Minh Tú",
        "tag": "Tư vấn",
        "tagColor": "amber",
        "time": "3 giờ trước",
        "isUrgent": False,
        "columnId": "in_progress",
        "assignee": {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 10800,
    },
    {
        "id": "task_6",
        "title": "Liên hệ lại khách chưa phản hồi",
        "customer": "Đỗ Quang Huy",
        "tag": "Follow up",
        "tagColor": "blue",
        "time": "4 giờ trước",
        "isUrgent": False,
        "columnId": "in_progress",
        "assignee": {"code": "LT", "name": "Lê Thảo", "username": "nv_thao", "bg": "bg-blue-800 text-white"},
        "created_at": time.time() - 14400,
    },
    # Cột 3: Chờ phản hồi
    {
        "id": "rescue_2",
        "title": "Cứu khách dừng phản hồi 3 ngày: Gửi case study doanh nghiệp SME",
        "customer": "Vũ Minh Tú",
        "tag": "Cứu lead 3d",
        "tagColor": "rose",
        "time": "3 ngày trước",
        "isUrgent": True,
        "columnId": "waiting",
        "leadScore": 72,
        "rescueStage": "3d",
        "approvalRisk": "low",
        "assignee": {"code": "TM", "name": "Trần Minh", "username": "nv_minh", "bg": "bg-blue-800 text-white"},
        "created_at": time.time() - 259200,
    },
    {
        "id": "rescue_3",
        "title": "Cứu khách dừng phản hồi 7 ngày: Đề xuất gói dùng thử miễn phí 14 ngày",
        "customer": "Phạm Lan Anh",
        "tag": "Cứu lead 7d",
        "tagColor": "rose",
        "time": "7 ngày trước",
        "isUrgent": True,
        "columnId": "waiting",
        "leadScore": 61,
        "rescueStage": "7d",
        "approvalRisk": "high",
        "assignee": {"code": "LT", "name": "Lê Tuấn (QL)", "username": "ql_tuan", "bg": "bg-blue-800 text-white"},
        "created_at": time.time() - 604800,
    },
    {
        "id": "task_7",
        "title": "Chờ khách gửi thông tin",
        "customer": "Nguyễn Thảo Vy",
        "tag": "Chờ khách",
        "tagColor": "amber",
        "time": "1 ngày trước",
        "isUrgent": False,
        "columnId": "waiting",
        "assignee": {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 86400,
    },
    {
        "id": "task_8",
        "title": "Đã gửi hướng dẫn, chờ test",
        "customer": "Trần Gia Bảo",
        "tag": "Chờ khách",
        "tagColor": "amber",
        "time": "1 ngày trước",
        "isUrgent": False,
        "columnId": "waiting",
        "assignee": {"code": "TM", "name": "Trần Minh", "username": "nv_minh", "bg": "bg-blue-800 text-white"},
        "created_at": time.time() - 86400,
    },
    # Cột 4: Hoàn tất
    {
        "id": "task_9",
        "title": "Đã cài đặt thành công",
        "customer": "Bùi Minh Khoa",
        "tag": "Hoàn tất",
        "tagColor": "emerald",
        "time": "Hôm qua",
        "isUrgent": False,
        "columnId": "done",
        "assignee": {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 86400,
    },
    {
        "id": "task_10",
        "title": "Đã gửi key game",
        "customer": "Vũ Thị Hằng",
        "tag": "Hoàn tất",
        "tagColor": "emerald",
        "time": "Hôm qua",
        "isUrgent": False,
        "columnId": "done",
        "assignee": {"code": "LT", "name": "Lê Thảo", "username": "nv_thao", "bg": "bg-blue-800 text-white"},
        "created_at": time.time() - 86400,
    },
    {
        "id": "task_11",
        "title": "Đã xử lý khiếu nại",
        "customer": "Phạm Quốc Đạt",
        "tag": "Hoàn tất",
        "tagColor": "emerald",
        "time": "20/04",
        "isUrgent": False,
        "columnId": "done",
        "assignee": {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time() - 172800,
    },
]


def load_tasks() -> List[Dict[str, Any]]:
    if not TASKS_FILE.exists():
        save_tasks(DEFAULT_TASKS)
        return list(DEFAULT_TASKS)
    try:
        data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return list(DEFAULT_TASKS)
    except Exception:
        return list(DEFAULT_TASKS)


def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    try:
        TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[ops_tasks_store] Lỗi ghi tasks: {e}")


def create_task(data: Dict[str, Any]) -> Dict[str, Any]:
    tasks = load_tasks()
    task_id = data.get("id") or f"task_{uuid.uuid4().hex[:8]}"
    new_task = {
        "id": task_id,
        "title": data.get("title", "").strip(),
        "customer": data.get("customer", "Khách hàng mới").strip(),
        "tag": data.get("tag", "Hỗ trợ kỹ thuật"),
        "tagColor": data.get("tagColor", "slate"),
        "time": data.get("time", "Vừa tạo"),
        "isUrgent": bool(data.get("isUrgent", False)),
        "columnId": data.get("columnId", "todo"),
        "leadScore": data.get("leadScore"),
        "rescueStage": data.get("rescueStage"),
        "approvalRisk": data.get("approvalRisk"),
        "assignee": data.get("assignee") or {"code": "NV", "name": "Nguyễn Văn An", "username": "nv_an", "bg": "bg-slate-800 text-white"},
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    tasks.insert(0, new_task)
    save_tasks(tasks)
    return new_task


def move_task(task_id: str, target_column: str) -> Optional[Dict[str, Any]]:
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["columnId"] = target_column
            t["updated_at"] = time.time()
            save_tasks(tasks)
            return t
    return None


def update_task(task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            for k, v in updates.items():
                if k != "id":
                    t[k] = v
            t["updated_at"] = time.time()
            save_tasks(tasks)
            return t
    return None


def delete_task(task_id: str) -> bool:
    tasks = load_tasks()
    initial_len = len(tasks)
    tasks = [t for t in tasks if t.get("id") != task_id]
    if len(tasks) < initial_len:
        save_tasks(tasks)
        return True
    return False
