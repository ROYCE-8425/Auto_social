"""Regression: model ChatGPT của Javis phải đến từ Codex app-server, không từ list ghim cứng.

    python tests/run.py codex_models

Không chạy Codex thật và không chạm mạng.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import sys

import codex_models as cm  # noqa: E402


_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


class _Input:
    def __init__(self):
        self.lines = []

    def write(self, value):
        self.lines.append(value)

    def flush(self):
        pass

    def close(self):
        pass


class _Output:
    def __init__(self, messages):
        self.lines = iter(json.dumps(x) + "\n" for x in messages)

    def readline(self):
        return next(self.lines, "")


class _Proc:
    def __init__(self, messages):
        self.stdin = _Input()
        self.stdout = _Output(messages)
        self.returncode = None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = 0

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9


spawned = {}


def _fake_popen(argv, **kwargs):
    spawned["argv"] = argv
    spawned["kwargs"] = kwargs
    proc = _Proc([
        {"id": 0, "result": {"userAgent": "Codex/test"}},
        {"method": "notice", "params": {}},
        {"id": 1, "result": {
            "data": [
                {"id": "gpt-old", "displayName": "Old", "hidden": False, "isDefault": False},
                {"id": "gpt-hidden", "hidden": True, "isDefault": False},
                {"id": "gpt-new", "displayName": "New", "hidden": False, "isDefault": True,
                 "defaultReasoningEffort": "low",
                 "supportedReasoningEfforts": [{"reasoningEffort": "low"},
                                                {"reasoningEffort": "max"}]},
                {"id": "gpt-new", "hidden": False},
            ],
            "nextCursor": None,
        }},
    ])
    spawned["proc"] = proc
    return proc


result = cm.list_models(timeout=2, cli_path="codex-test", popen_factory=_fake_popen)
check("spawn đúng app-server", spawned["argv"] == ["codex-test", "app-server"])
check("default live được đưa lên đầu", result["models"] == ["gpt-new", "gpt-old"])
check("không lộ model hidden hoặc trùng", "gpt-hidden" not in result["models"])
check("giữ metadata effort từ Codex", result["items"][0]["supported_reasoning_efforts"] == ["low", "max"])
check("trả nguồn và default rõ ràng",
      result["source"] == "codex-app-server" and result["default_model"] == "gpt-new")

sent = [json.loads(x) for x in spawned["proc"].stdin.lines]
check("handshake initialize trước model/list",
      [x.get("method") for x in sent] == ["initialize", "initialized", "model/list"])
check("picker chỉ hỏi model đang hiển thị",
      sent[-1]["params"]["includeHidden"] is False and sent[-1]["params"]["limit"] == 100)
check("subprocess luôn được dừng", spawned["proc"].returncode == 0)

bad = cm.list_models(
    timeout=2,
    cli_path="codex-test",
    popen_factory=lambda *a, **k: _Proc([{"id": 0, "error": {"message": "old CLI"}}]),
)
check("CLI cũ/lỗi trả None để caller fallback", bad is None)

print()
if _fails:
    print(f"{len(_fails)} test HỎNG: " + ", ".join(_fails))
    sys.exit(1)
print("Tất cả test codex_models đã qua.")
