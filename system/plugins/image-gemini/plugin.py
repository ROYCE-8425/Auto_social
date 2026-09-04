"""Plugin bundled: tạo ảnh bằng Google Imagen 3 qua API key Gemini cho MỌI engine.

Đăng ký tool gemini_generate_image, gọi image_gen.generate_gemini
(Google Imagen 3 API) bằng API key Gemini đã cấu hình ở trang Models hoặc biến môi trường GEMINI_API_KEY.
Bất kỳ engine nào (Claude Code/Codex/API) khi user bảo "vẽ ảnh bằng gemini..." hoặc tạo cover AI đều gọi được tool này.

- min_mode=safe: thao tác GHI (tạo file + dùng quota API) -> chặn ở chế độ suggest.
- check_fn: chưa có key Gemini -> tool báo rõ cách cấu hình key.
"""
from __future__ import annotations

import image_gen


def register(ctx):
    def _check():
        try:
            key = image_gen.get_gemini_api_key()
            if not key:
                return (
                    "Chưa có API key Gemini. Vào trang Cài đặt > Models nhập key Google Gemini "
                    "(hoặc đặt biến môi trường GEMINI_API_KEY) rồi thử lại."
                )
        except Exception as e:
            return f"Không kiểm tra được API key Gemini: {e}"
        return None

    async def _gen(args, cctx):
        args = args or {}
        prompt = str(args.get("prompt") or "").strip()
        if not prompt:
            return "ERROR: thiếu 'prompt' (mô tả ảnh cần tạo)."
        aspect = str(args.get("aspect_ratio") or "square")
        api_key = args.get("api_key")

        res = await image_gen.generate_gemini(
            prompt=prompt,
            aspect_ratio=aspect,
            vault_root=cctx.vault_root,
            api_key=api_key,
        )
        if not res.get("ok"):
            return "ERROR: " + str(res.get("error") or "tạo ảnh thất bại")
        rel = res["rel_path"]
        return (
            f"Đã tạo ảnh Google Imagen 3 ({res.get('aspect')}, model {res.get('model')}), lưu tại {rel}. "
            f"HÃY NHÚNG ngay vào câu trả lời cho người dùng bằng cú pháp markdown: "
            f"![{prompt[:40]}]({rel})"
        )

    ctx.register_tool(
        name="gemini_generate_image",
        description=(
            "Tạo ảnh thương mại 3D chất lượng cao bằng Google Imagen 3 (dùng chung API key Gemini). "
            "Tham số: prompt (mô tả chi tiết ảnh cần tạo bằng tiếng Anh hoặc tiếng Việt), "
            "aspect_ratio (square|landscape|portrait, mặc định square 1:1). "
            "Sau khi gọi, NHÚNG ![](đường-dẫn) trả về vào câu trả lời."
        ),
        handler=_gen,
        min_mode="safe",
        check_fn=_check,
        schema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Mô tả ảnh cần tạo (prompt chi tiết bằng tiếng Anh cho kết quả đẹp nhất)"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["square", "landscape", "portrait", "1:1", "16:9", "9:16", "4:3", "3:4"],
                    "description": "Tỉ lệ khung ảnh, mặc định square (1:1)"
                },
                "api_key": {
                    "type": "string",
                    "description": "Tuỳ chọn: truyền API key Gemini trực tiếp nếu chưa lưu trong Cài đặt"
                }
            },
            "required": ["prompt"]
        },
    )
