"""Test connector Webcake Landing trong system/mcp-catalog.json. Chạy tay / CI:

    python tests/run.py webcake_env

Không cần pytest, không chạm mạng, không cần JWT thật.

VÌ SAO CÓ FILE NÀY (lỗi thật đã dẫm phải): 9 tool "lưu trữ" của webcake-landing-mcp
(list_organizations, create_page, list_pages, find_pages, get_page, update_page,
add_section, patch_page, publish_page) cần BASE URL của API. Trong source package,
base được giải theo thứ tự:

    base = overrides.base ?? process.env.WEBCAKE_API_BASE ?? preset?.apiBase ?? saved.base

`preset` lấy từ WEBCAKE_ENV (local | staging | prod), prod = https://api.webcake.io.
Catalog Javis chỉ map WEBCAKE_JWT + WEBCAKE_ORG_ID từ ô đăng nhập, KHÔNG hề cấp base,
nên user đấu Webcake xong là mọi tool lưu trữ trả `missing: ["WEBCAKE_API_BASE"]` -
kể cả tool validate (list_organizations), tức connector đỏ ngay sau khi kết nối.
Đường lui duy nhất là bắt user tự gõ `npx webcake-landing-mcp login`, đúng thứ Javis
không được phép bắt user làm.

Phủ: entry tồn tại + đúng runner, base URL tự có mà KHÔNG bắt user gõ, JWT vẫn map,
cơ chế env tĩnh mức connector (dùng chung cho mọi connector sau này) và thứ tự ưu tiên
của nó so với ô đăng nhập + env user tự đặt ở connection.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sys
import tempfile

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-webcaketest-"))

import mcp_catalog  # noqa: E402

_fails = []

# 9 tool cần WEBCAKE_API_BASE + WEBCAKE_JWT (nhóm "Lưu trữ" ở README package).
STORAGE_TOOLS = ["list_organizations", "create_page", "list_pages", "find_pages", "get_page",
                 "update_page", "add_section", "patch_page", "publish_page"]

# Giá trị WEBCAKE_ENV mà package hiểu (ENVIRONMENTS trong dist/persistence/config.js).
PRESET_ENVS = ("local", "staging", "prod")


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


con = mcp_catalog.get("webcake-landing")
check("catalog có connector 'webcake-landing'", con is not None)

if con is None:
    print(f"\nFAIL - test_webcake_env: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)

# ---- hình dạng entry ----
check("transport = stdio", con.get("transport") == "stdio")
check("chạy bằng npx", con.get("command") == "npx")
check("args gọi package webcake-landing-mcp",
      "webcake-landing-mcp" in (con.get("args") or []))

# ---- LỖI CHÍNH: base URL phải tự có, user chỉ dán JWT ----
env = mcp_catalog.build_env(con, {"api_key": "JWT-GIA-DINH"})

check("dán JWT là đủ -> env giải được BASE URL (WEBCAKE_API_BASE hoặc WEBCAKE_ENV preset), "
      "không thì 9 tool lưu trữ chết vì missing_env",
      bool(env.get("WEBCAKE_API_BASE")) or env.get("WEBCAKE_ENV") in PRESET_ENVS)
check("dùng WEBCAKE_ENV=prod thay vì ghi cứng URL (URL đổi thì package tự lo)",
      env.get("WEBCAKE_ENV") == "prod")
check("JWT vẫn được truyền qua WEBCAKE_JWT",
      env.get("WEBCAKE_JWT") == "JWT-GIA-DINH")

# Base URL KHÔNG phải thứ user biết -> tuyệt đối không được đẻ thêm ô nhập.
field_keys = [f.get("key") for f in ((con.get("auth") or {}).get("fields") or [])]
field_envs = [f.get("env") for f in ((con.get("auth") or {}).get("fields") or [])]
check("KHÔNG đẻ ô nhập cho base URL (user chỉ dán JWT, không phải gõ URL kỹ thuật)",
      "WEBCAKE_ENV" not in field_envs and "WEBCAKE_API_BASE" not in field_envs)
check("ô đăng nhập vẫn đúng bộ cũ: api_key + org_id",
      sorted(k for k in field_keys if k) == ["api_key", "org_id"])
check("org_id là TUỲ CHỌN (tài khoản 1 tổ chức bỏ trống vẫn đấu được)",
      any(f.get("key") == "org_id" and f.get("optional")
          for f in ((con.get("auth") or {}).get("fields") or [])))

# Bỏ trống ô tuỳ chọn thì không được rơi rớt base.
env_no_org = mcp_catalog.build_env(con, {"api_key": "JWT-X"})
check("bỏ trống org_id -> env KHÔNG có WEBCAKE_ORG_ID rỗng",
      "WEBCAKE_ORG_ID" not in env_no_org)
check("bỏ trống org_id -> base URL vẫn còn", env_no_org.get("WEBCAKE_ENV") == "prod")

# ---- tool validate phải là tool CẦN base, nếu không thì connector đỏ/xanh nói dối ----
vt = (con.get("validate") or {}).get("tool")
check("validate.tool nằm trong nhóm lưu trữ (đúng thứ cần base+JWT)", vt in STORAGE_TOOLS)

# ---- cơ chế env tĩnh mức connector: dùng chung, không phải vá riêng webcake ----
fake = {"env": {"FOO_BASE": "https://foo.example", "TRONG_RONG": ""},
        "auth": {"fields": [{"key": "tok", "env": "FOO_TOKEN"}]}}
fenv = mcp_catalog.build_env(fake, {"tok": "T1"})
check("env tĩnh mức connector được nạp", fenv.get("FOO_BASE") == "https://foo.example")
check("giá trị rỗng trong env tĩnh bị bỏ qua", "TRONG_RONG" not in fenv)
check("env tĩnh và ô đăng nhập sống chung", fenv.get("FOO_TOKEN") == "T1")

# Ô đăng nhập (user gõ) phải THẮNG env tĩnh khi trùng tên biến - env tĩnh chỉ là mặc định.
fake_clash = {"env": {"FOO_TOKEN": "mac-dinh"},
              "auth": {"fields": [{"key": "tok", "env": "FOO_TOKEN"}]}}
check("trùng tên biến: giá trị user gõ THẮNG env tĩnh",
      mcp_catalog.build_env(fake_clash, {"tok": "user-go"}).get("FOO_TOKEN") == "user-go")
check("trùng tên biến nhưng user bỏ trống: giữ env tĩnh làm mặc định",
      mcp_catalog.build_env(fake_clash, {"tok": ""}).get("FOO_TOKEN") == "mac-dinh")

# ---- env user tự đặt ở CONNECTION phải thắng cả catalog (đường lui self-hosted/staging) ----
# mcp_store.resolved đặt env connection TRƯỚC rồi mới setdefault từ catalog, nên chỉ cần
# chứng minh build_env không tự ý ghi đè: hợp nhất theo đúng thứ tự đó phải giữ giá trị user.
merged = {"WEBCAKE_API_BASE": "https://api.staging.webcake.io"}
for k, v in mcp_catalog.build_env(con, {"api_key": "JWT-X"}).items():
    merged.setdefault(k, v)
check("user tự đặt WEBCAKE_API_BASE ở connection -> vẫn thắng (package ưu tiên API_BASE "
      "trước preset, nên staging/self-hosted không bị kéo về prod)",
      merged.get("WEBCAKE_API_BASE") == "https://api.staging.webcake.io")

# ---- cách 2: đăng nhập trên web (OAuth qua máy chủ hosted) ----
# Máy chủ hosted công bố OAuth chuẩn (RFC 9728 + DCR), nên khai như higgsfield: chỉ url +
# auth.type=oauth, KHÔNG khai authorize_url/token_url - oauth_mcp tự discovery rồi tự đăng ký.
web = mcp_catalog.get("webcake-landing-web")
check("catalog có connector 'webcake-landing-web'", web is not None)
if web is not None:
    check("web: transport http", web.get("transport") == "http")
    check("web: trỏ đúng endpoint hosted", web.get("url") == "https://mcp.toolvn.io.vn/mcp")
    check("web: auth kiểu oauth", ((web.get("auth") or {}).get("type")) == "oauth")
    check("web: KHÔNG ô nhập nào (một chạm, không dán JWT)",
          ((web.get("auth") or {}).get("fields") or []) == [])
    check("web: KHÔNG khai authorize_url/token_url (để oauth_mcp tự discovery như higgsfield)",
          not (web.get("auth") or {}).get("authorize_url")
          and not (web.get("auth") or {}).get("token_url"))
    check("web: không cần env (http, không spawn tiến trình)", not web.get("env"))
    check("web: nói rõ rủi ro máy chủ trung gian trong risk",
          "trung gian" in (web.get("risk") or ""))
    # Hai cách phải cùng bộ quyền, lệch là một cách sẽ cho qua thứ cách kia chặn.
    check("hai cách gom về CÙNG một thẻ (group)",
          web.get("group") == con.get("group") == "webcake")
    check("mỗi cách có group_line riêng để user chọn được",
          bool(web.get("group_line")) and bool(con.get("group_line"))
          and web.get("group_line") != con.get("group_line"))
    check("hai cách CÙNG tool_meta (không lệch quyền giữa hai đường)",
          web.get("tool_meta") == con.get("tool_meta"))
    check("hai cách CÙNG tool validate", (web.get("validate") or {}).get("tool")
          == (con.get("validate") or {}).get("tool"))
    check("hai cách CÙNG default_perm", web.get("default_perm") == con.get("default_perm"))

# ---- BẤT BIẾN BẢO MẬT TOÀN CATALOG: không được nhét credential vào url ----
# Tài liệu Webcake gợi ý kiểu link 'https://.../mcp?jwt=<token>'. Javis KHÔNG được dùng kiểu đó:
# mcp_store.add_connection lưu 'url' KHÔNG qua secrets_store, và _public() trả nguyên url ra
# frontend (chỉ headers/env/secrets mới được che). Token trong url là rơi thẳng ra dashboard + log.
_CRED_PARAMS = ("jwt=", "token=", "api_key=", "apikey=", "secret=", "password=", "access_token=")
_ban = []
for _c in mcp_catalog.load().values():
    _u = (_c.get("url") or "").lower()
    if any(p in _u for p in _CRED_PARAMS):
        _ban.append(_c.get("id"))
check(f"không connector nào nhét credential vào url (url không được che, xem ghi chú){_ban and ': ' + str(_ban) or ''}",
      not _ban)

# ---- CANARY: chứng minh các check ở trên có quyền lực thật, không phải luôn-xanh ----
_fake_khong_env = {"auth": {"fields": [{"key": "api_key", "env": "WEBCAKE_JWT"}]}}
_canary = mcp_catalog.build_env(_fake_khong_env, {"api_key": "J"})
check("CANARY: connector KHÔNG khai env tĩnh thì build_env phải KHÔNG có base "
      "-> tức check base ở trên thật sự đọc catalog chứ không luôn xanh",
      not _canary.get("WEBCAKE_API_BASE") and _canary.get("WEBCAKE_ENV") not in PRESET_ENVS)

_url_gia = "https://mcp.toolvn.io.vn/mcp?jwt=TOKEN-THAT-CUA-USER"
check("CANARY: url kiểu dán-link-kèm-token phải BỊ BẮT -> tức bất biến bảo mật ở trên "
      "thật sự soi chứ không phải luôn xanh vì catalog đang sạch",
      any(p in _url_gia.lower() for p in _CRED_PARAMS))

if _fails:
    print(f"\nFAIL - test_webcake_env: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)
print("\nOK - test_webcake_env: tất cả pass")
