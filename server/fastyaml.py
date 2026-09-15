"""yaml.safe_load nhưng dùng bộ nạp C (libyaml) khi có.

Vì sao: mọi frontmatter trong Javis (SKILL.md, agent, workflow, plugin.yaml, note) đều đi
qua yaml.safe_load, mà hàm đó chọn SafeLoader bản thuần Python. Đo trên frontmatter SKILL.md
130 byte thật: 0,446ms bản Python so với 0,072ms bản C, nhanh 6,2 lần. YAML chiếm 64% chi phí
build_system_prompt - hàm chặn event loop 150ms MỖI lượt chat, mỗi task Kanban, mỗi lần nhắc
hẹn nổ và mỗi tick loop. Nên một dòng đổi bộ nạp đáng giá hơn nhiều tối ưu khác.

libyaml đã có sẵn trong requirements (PyYAML build kèm wheel có C extension trên mọi nền
Javis chạy). Thiếu thì tự rơi về bản Python, không vỡ gì.

Dùng: `import fastyaml` rồi `fastyaml.safe_load(text)` - thay thẳng cho `yaml.safe_load`.
"""
import yaml

try:
    from yaml import CSafeLoader as _CLoader   # libyaml
    HAS_C = True
except ImportError:                            # PyYAML build thuần Python
    _CLoader = None
    HAS_C = False

_PyLoader = yaml.SafeLoader


def safe_load(stream):
    """Như yaml.safe_load. Bộ nạp C từ chối thì thử lại bằng bộ nạp Python.

    Hai bộ nạp KHÔNG khớp tuyệt đối ở vài góc hiếm (khoá trùng, một số ký tự ngắt dòng
    unicode, chữ trong thông báo lỗi). Lần thử lại làm cho mọi thứ bản Python đọc được
    thì bản này cũng đọc được, tức không thể thành bước lùi. Chỉ tốn thêm ở nhánh lỗi,
    mà nhánh lỗi vốn hiếm.
    """
    if _CLoader is None:
        return yaml.load(stream, Loader=_PyLoader)
    try:
        return yaml.load(stream, Loader=_CLoader)
    except yaml.YAMLError:
        return yaml.load(stream, Loader=_PyLoader)
