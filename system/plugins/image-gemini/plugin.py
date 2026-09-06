"""Plugin bundled: tạo ảnh bằng Google Imagen 3 qua API key Gemini cho MỌI engine.

Đăng ký tool gemini_generate_image, gọi image_gen.generate_gemini
(Google Imagen 3 API) bằng API key Gemini đã cấu hình ở trang Models hoặc biến môi trường GEMINI_API_KEY.
Bất kỳ engine nào (Claude Code/Codex/API) khi user bảo "vẽ ảnh bằng gemini..." hoặc tạo cover AI đều gọi được tool này.

- min_mode=safe: thao tác GHI (tạo file + dùng quota API) -> chặn ở chế độ suggest.
- check_fn: chưa có key Gemini -> tool báo rõ cách cấu hình key.
"""
from __future__ import annotations

import re

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
        model = str(args.get("model") or "").strip() or None
        refs = args.get("images") or args.get("image") or args.get("reference_images") or []
        if isinstance(refs, str):
            refs = [p.strip() for p in refs.split(",") if p.strip()]
        elif isinstance(refs, list):
            refs = [str(p).strip() for p in refs if str(p).strip()]
        logo = str(args.get("logo") or "").strip()
        refs = [image_gen.fix_dataset_path(p) for p in refs]
        logo = image_gen.fix_dataset_path(logo)
        if logo:
            refs = [logo] + [p for p in refs if p != logo]
        need_brand = bool(re.search(
            r"cover|poster|fanpage|sao viet|facebook|brand|tin hoc|khoa hoc", prompt, re.I))
        if need_brand and not logo:
            logo = "attachments/dataset/chung/thsv-logo-2025.png"
            refs = [logo] + [p for p in refs if p != logo]
        if need_brand and logo and len([p for p in refs if p != logo]) == 0:
            folder = "tin-hoc _ai"
            if re.search(r"ke.toan|accounting", prompt, re.I):
                folder = "ke-toan"
            elif re.search(r"do.hoa|photoshop|illustrator", prompt, re.I):
                folder = "do-hoa"
            elif re.search(r"autocad|ve.ky|solidworks", prompt, re.I):
                folder = "ve-ky-thuat"
            raw = image_gen.first_dataset_photo(getattr(cctx, "vault_root", None), folder)
            if raw:
                refs.append(raw)
            else:
                return (
                    "ERROR: không có ảnh raw trong attachments/dataset/"
                    + folder + " (tin học = 'tin-hoc _ai' có dấu cách, không phải tin-hoc/_ai)."
                )

        page_id = args.get("page_id")
        course_id = args.get("course_id")
        hotline = args.get("hotline")
        footer_text = args.get("footer_text")

        res = await image_gen.generate_gemini(
            prompt=prompt,
            aspect_ratio=aspect,
            vault_root=cctx.vault_root,
            api_key=api_key,
            model=model,
            reference_images=refs,
            save_under="attachments/dataset/_xuat",
            page_id=page_id,
            course_id=course_id,
            hotline=hotline,
            footer_text=footer_text,
        )
        if not res.get("ok"):
            return "ERROR: " + str(res.get("error") or "tạo ảnh thất bại")
        rel = res["rel_path"]
        return (
            f"Đã tạo ảnh Google ({res.get('aspect')}, model {res.get('model')}), lưu tại {rel}. "
            f"HÃY NHÚNG ngay vào câu trả lời cho người dùng bằng cú pháp markdown: "
            f"![{prompt[:40]}]({rel})"
        )

    ctx.register_tool(
        name="gemini_generate_image",
        description=(
            "Tạo cover Fanpage chuẩn Facebook bằng Google Imagen (hỗ trợ Imagen 4 / Imagen 3 kết hợp ảnh thật dataset) hoặc Graphic Engine: "
            "BẮT BUỘC logo (file Logo chính kit) + images (1 ảnh raw dataset). "
            "Hệ thống tự động dán pixel logo thật từ dataset, cấm vẽ chữ đường dẫn, typography chuẩn Unicode 0% lỗi font. "
            "aspect_ratio square (2000x2000 px). Lưu attachments/dataset/_xuat/."
        ),
        handler=_gen,
        min_mode="safe",
        check_fn=_check,
        schema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Mô tả ảnh cần tạo (prompt chi tiết bằng tiếng Anh hoặc tiếng Việt)"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["square", "landscape", "portrait", "1:1", "16:9", "9:16", "4:3", "3:4"],
                    "description": "Tỉ lệ khung ảnh, mặc định square (1:1)"
                },
                "model": {
                    "type": "string",
                    "description": "Model ảnh Google (mặc định để trống sẽ luôn tuân theo model đã chọn trong Cài đặt): "
                                   "imagen-4.0-generate-001, imagen-3.0-generate-002, imagen-3.0-fast-generate-001"
                },
                "logo": {
                    "type": "string",
                    "description": "File Logo chính trong kit, vd attachments/dataset/chung/thsv-logo-2025.png"
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "1 ảnh raw dataset (mảng đường dẫn trong vault, vd: [\"attachments/dataset/tin-hoc _ai/raw.jpg\"])"
                },
                "image": {
                    "type": "string",
                    "description": "1 ảnh raw dataset (chuỗi đường dẫn trong vault)"
                },
                "page_id": {
                    "type": "string",
                    "description": "ID hoặc slug của Fanpage để nạp đúng Brand Kit (Hotline, Logo, Tên Fanpage riêng)"
                },
                "course_id": {
                    "type": "string",
                    "description": "ID khóa học (tin-hoc _ai, ke-toan, do-hoa, ve-ky-thuat, tre-em) để lấy tri thức chuẩn"
                },
                "hotline": {
                    "type": "string",
                    "description": "Hotline chỉ định riêng (nếu không truyền sẽ tự lấy từ Brand Kit của Fanpage)"
                },
                "footer_text": {
                    "type": "string",
                    "description": "Tên thương hiệu ở footer (nếu không truyền sẽ tự lấy từ Brand Kit của Fanpage)"
                }
            },
            "required": ["prompt"]
        },
    )
