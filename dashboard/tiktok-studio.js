// ============================================================
// Javis OS - TikTok Carousel & Video Studio
// docs/dev/2026-09-17-gemini-tiktok-dang-that-ui.md
// Đăng bộ ảnh 9:16 thật qua PostPeer, nhạc tự động, quản lý dataset.
// ============================================================
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatTime(ts) {
    if (!ts) return "";
    try {
      var d = typeof ts === "number" ? new Date(ts > 1e11 ? ts : ts * 1000) : new Date(ts);
      return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" }) + " " +
        d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return String(ts);
    }
  }

  async function api(url, opts) {
    const r = await fetch(url, opts || {});
    let d = null;
    try {
      d = await r.json();
    } catch (e) {
      d = {};
    }
    if (!r.ok || d.ok === false) {
      throw new Error((d && (d.error || d.detail || d.message)) || ("Lỗi HTTP " + r.status));
    }
    return d;
  }

  let _hostEl = null;
  let _activeTab = "compose"; // "compose" | "media" | "loop" | "history"
  let _status = null;
  let _selectedKit = "game-gia-re-bsn";
  let _selectedAccount = "";
  let _caption = "";
  let _productTitle = "The Blood of Dawnwalker";
  let _productPrice = "45.000 ₫";
  let _autoAddMusic = true;
  let _isDraft = false;
  let _autoCrop = true;
  let _posting = false;
  let _postResult = null;
  let _uploading = false;
  let _uploadBrand = "bsn";
  let _uploadMsg = "";

  async function loadStatus() {
    try {
      _status = await api("/tiktok/status");
      if (_status && _status.kits && _status.kits.length > 0) {
        var found = _status.kits.find(k => k.stem === _selectedKit || k.file.startsWith(_selectedKit));
        if (!found) {
          _selectedKit = _status.kits[0].stem;
          found = _status.kits[0];
        }
        if (found && found.account_id && !_selectedAccount) {
          _selectedAccount = found.account_id;
        }
      }
      if (!_selectedAccount && _status && _status.accounts && _status.accounts.length > 0) {
        _selectedAccount = _status.accounts[0].id;
      }
    } catch (e) {
      console.error("[TikTok] loadStatus error:", e);
    }
  }

  function injectStyles() {
    if (document.getElementById("tiktok-studio-styles")) return;
    const style = document.createElement("style");
    style.id = "tiktok-studio-styles";
    style.textContent = `
      .tt-wrap {
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding: 4px;
        color: var(--text, #e2e8f0);
        font-family: inherit;
      }
      .tt-card {
        background: var(--card-bg, rgba(255, 255, 255, 0.03));
        border: 1px solid var(--border, rgba(255, 255, 255, 0.08));
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      }
      .tt-grid-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 16px;
      }
      .tt-stat-box {
        background: var(--card-sub, rgba(255, 255, 255, 0.02));
        border: 1px solid var(--border, rgba(255, 255, 255, 0.06));
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
      }
      .tt-tabs {
        display: flex;
        gap: 8px;
        border-bottom: 1px solid var(--border, rgba(255, 255, 255, 0.08));
        padding-bottom: 12px;
      }
      .tt-tab-btn {
        background: transparent;
        border: 1px solid transparent;
        color: var(--text2, #94a3b8);
        padding: 8px 16px;
        border-radius: 10px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s ease;
      }
      .tt-tab-btn:hover {
        background: rgba(255, 255, 255, 0.04);
        color: var(--text, #fff);
      }
      .tt-tab-btn.active {
        background: rgba(244, 63, 94, 0.15);
        color: #fb7185;
        border-color: rgba(244, 63, 94, 0.3);
      }
      .tt-badge {
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
      }
      .tt-badge-ok {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
      }
      .tt-badge-warn {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
      }
      .tt-badge-off {
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.2);
      }
      .tt-form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 16px;
      }
      .tt-label {
        font-size: 12px;
        font-weight: 600;
        color: var(--text2, #94a3b8);
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .tt-input, .tt-select, .tt-textarea {
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid var(--border, rgba(255, 255, 255, 0.12));
        border-radius: 10px;
        padding: 10px 14px;
        color: #fff;
        font-size: 13px;
        outline: none;
        transition: border 0.2s;
        font-family: inherit;
      }
      .tt-input:focus, .tt-select:focus, .tt-textarea:focus {
        border-color: #fb7185;
      }
      .tt-btn {
        background: #e11d48;
        color: #fff;
        border: none;
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all 0.2s;
        box-shadow: 0 4px 14px rgba(225, 29, 72, 0.35);
      }
      .tt-btn:hover:not(:disabled) {
        background: #be123c;
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(225, 29, 72, 0.45);
      }
      .tt-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .tt-btn-sec {
        background: rgba(255, 255, 255, 0.08);
        color: #fff;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: none;
      }
      .tt-btn-sec:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.14);
        box-shadow: none;
      }
      .tt-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
      }
      .tt-table th {
        text-align: left;
        padding: 10px 14px;
        color: var(--text2, #94a3b8);
        border-bottom: 1px solid var(--border, rgba(255, 255, 255, 0.08));
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .tt-table td {
        padding: 12px 14px;
        border-bottom: 1px solid var(--border, rgba(255, 255, 255, 0.05));
      }
      .tt-table tr:hover td {
        background: rgba(255, 255, 255, 0.02);
      }
      .tt-thumb-row {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 8px;
      }
      .tt-thumb-box {
        position: relative;
        width: 90px;
        height: 160px;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.15);
        flex-shrink: 0;
        background: #0f172a;
      }
      .tt-thumb-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      .tt-thumb-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(transparent, rgba(0,0,0,0.85));
        padding: 4px 6px;
        font-size: 10px;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    `;
    document.head.appendChild(style);
  }

  function render(el) {
    _hostEl = el;
    injectStyles();
    loadStatus().then(() => {
      renderContent();
    });
  }

  function renderContent() {
    if (!_hostEl) return;

    var isConnected = _status && _status.connected;
    var maskedKey = (_status && _status.masked_key) || "Chưa cấu hình";
    var loopOn = _status && _status.loop && _status.loop.enabled;
    var kits = (_status && _status.kits) || [];
    var accounts = (_status && _status.accounts) || [];
    var recentPosts = (_status && _status.recent_posts) || [];

    var curKit = kits.find(k => k.stem === _selectedKit || k.file.startsWith(_selectedKit)) || kits[0] || {
      name: "Game Giá Rẻ BSN",
      stem: "game-gia-re-bsn",
      brand: "bsn",
      account_id: "6aa3ba9df4c58f3c57921507",
      username: "@seotrum"
    };

    var html = `
      <div class="tt-wrap">
        <!-- Top Banner Header -->
        <div class="tt-card" style="border-left: 4px solid #f43f5e; background: linear-gradient(to right, rgba(244,63,94,0.08), rgba(0,0,0,0.2));">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
              <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                <h2 style="font-size: 20px; font-weight: 800; margin: 0; display: flex; align-items: center; gap: 8px;">
                  🎬 TikTok Studio (Carousel 9:16)
                </h2>
                <span class="tt-badge ${isConnected ? "tt-badge-ok" : "tt-badge-warn"}">
                  ${isConnected ? "● PostPeer Đã Kết Nối" : "○ Chưa Kết Nối"}
                </span>
                <span class="tt-badge ${loopOn ? "tt-badge-ok" : "tt-badge-off"}">
                  ${loopOn ? "● Daily Loop Đang Bật" : "○ Daily Loop Tắt"}
                </span>
              </div>
              <p style="font-size: 13px; color: var(--text2, #94a3b8); margin: 0;">
                Đăng thật bộ ảnh 9:16 dọc kèm nhạc auto trend qua PostPeer API. Máy chủ phục vụ file: <code>https://trannhuy.online/tiktok-media/...</code>
              </p>
            </div>
            <div style="display: flex; gap: 10px;">
              <button id="btnReloadStatus" class="tt-btn tt-btn-sec" style="padding: 8px 14px; font-size: 13px;">
                🔄 Làm mới
              </button>
            </div>
          </div>
        </div>

        <!-- System Status Bar -->
        <div class="tt-grid-stats">
          <div class="tt-stat-box">
            <span class="tt-label">Tài khoản PostPeer Live</span>
            <div style="font-size: 17px; font-weight: 700; color: #fff; margin: 6px 0;">
              ${accounts.length > 0 ? accounts.map(a => `<span style="color:#fb7185;">${esc(a.username || a.name)}</span>`).join(", ") : "@seotrum"}
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
              Khóa API: <span style="font-family: monospace; background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">${esc(maskedKey)}</span>
            </div>
          </div>

          <div class="tt-stat-box">
            <span class="tt-label">Vòng lặp tự động hàng ngày</span>
            <div style="font-size: 17px; font-weight: 700; color: ${loopOn ? "#34d399" : "#94a3b8"}; margin: 6px 0;">
              ${loopOn ? "Đang chạy tự động" : "Mặc định Tắt (An toàn)"}
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
              Tệp cấu hình: <code style="color:#e2e8f0;">dang-video-tiktok-hang-ngay.md</code>
            </div>
          </div>

          <div class="tt-stat-box">
            <span class="tt-label">Thương hiệu & Kit khả dụng</span>
            <div style="font-size: 17px; font-weight: 700; color: #fff; margin: 6px 0;">
              ${kits.length} Brand Kits
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
              BSN: <span style="color:#38bdf8;">@seotrum</span> · Sao Việt: <span style="color:#a78bfa;">@tinhocsaoviet</span>
            </div>
          </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="tt-tabs">
          <button class="tt-tab-btn ${_activeTab === "compose" ? "active" : ""}" data-tab="compose">
            🚀 Đăng thử Carousel Thật
          </button>
          <button class="tt-tab-btn ${_activeTab === "media" ? "active" : ""}" data-tab="media">
            🖼️ Thư viện 9:16 & Tải lên
          </button>
          <button class="tt-tab-btn ${_activeTab === "loop" ? "active" : ""}" data-tab="loop">
            ⏱️ Cấu hình Vòng lặp Loop
          </button>
          <button class="tt-tab-btn ${_activeTab === "history" ? "active" : ""}" data-tab="history">
            📜 Lịch sử 10 bài gần nhất (${recentPosts.length})
          </button>
        </div>

        <!-- Tab Content Area -->
        <div id="ttTabContainer"></div>
      </div>
    `;

    _hostEl.innerHTML = html;

    // Attach Header Events
    _hostEl.querySelector("#btnReloadStatus").onclick = async function () {
      this.textContent = "Đang nạp...";
      await loadStatus();
      renderContent();
    };

    _hostEl.querySelectorAll(".tt-tab-btn").forEach(btn => {
      btn.onclick = function () {
        _activeTab = this.getAttribute("data-tab");
        _hostEl.querySelectorAll(".tt-tab-btn").forEach(b => b.classList.remove("active"));
        this.classList.add("active");
        renderTabBody();
      };
    });

    renderTabBody();
  }

  function renderTabBody() {
    var container = _hostEl.querySelector("#ttTabContainer");
    if (!container) return;

    if (_activeTab === "compose") {
      renderComposeTab(container);
    } else if (_activeTab === "media") {
      renderMediaTab(container);
    } else if (_activeTab === "loop") {
      renderLoopTab(container);
    } else if (_activeTab === "history") {
      renderHistoryTab(container);
    }
  }

  // ==========================================
  // TAB 1: COMPOSE & POST REAL CAROUSEL
  // ==========================================
  function renderComposeTab(container) {
    var kits = (_status && _status.kits) || [];
    var accounts = (_status && _status.accounts) || [];
    var curKit = kits.find(k => k.stem === _selectedKit || k.file.startsWith(_selectedKit)) || kits[0] || {};
    var brand = curKit.brand || "bsn";
    var defaultAcc = curKit.account_id || (accounts[0] && accounts[0].id) || "6aa3ba9df4c58f3c57921507";

    container.innerHTML = `
      <div class="tt-card">
        <h3 style="margin-top: 0; font-size: 16px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px;">
          Đăng thử nghiệm Carousel lên TikTok thật (PostPeer API)
        </h3>
        <p style="font-size: 13px; color: #94a3b8; margin-top: -6px; margin-bottom: 20px;">
          Hệ thống sẽ chuẩn bị 4–6 ảnh tỉ lệ 9:16 dọc, chèn nhạc tự động (autoAddMusic), gán caption chuẩn thương hiệu và gửi tới PostPeer.
        </p>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
          <div class="tt-form-group">
            <label class="tt-label">1. Chọn Thương hiệu (Brand Kit)</label>
            <select id="ttKitSelect" class="tt-select">
              ${kits.map(k => `
                <option value="${esc(k.stem)}" ${k.stem === _selectedKit ? "selected" : ""}>
                  ${esc(k.name)} (${esc(k.brand.toUpperCase())})
                </option>
              `).join("")}
            </select>
          </div>

          <div class="tt-form-group">
            <label class="tt-label">2. Tài khoản TikTok đích</label>
            <select id="ttAccountSelect" class="tt-select">
              ${accounts.length > 0 ? accounts.map(a => `
                <option value="${esc(a.id)}" ${a.id === _selectedAccount ? "selected" : ""}>
                  ${esc(a.username || a.name)} [${esc(a.id)}]
                </option>
              `).join("") : `
                <option value="${esc(defaultAcc)}" selected>
                  @seotrum [${esc(defaultAcc)}]
                </option>
              `}
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
          <div class="tt-form-group">
            <label class="tt-label">Tên sản phẩm mẫu</label>
            <input type="text" id="ttProductTitle" class="tt-input" value="${esc(_productTitle)}" placeholder="Ví dụ: The Blood of Dawnwalker hoặc Khóa học Excel">
          </div>
          <div class="tt-form-group">
            <label class="tt-label">Giá niêm yết / Ưu đãi</label>
            <input type="text" id="ttProductPrice" class="tt-input" value="${esc(_productPrice)}" placeholder="Ví dụ: 45.000 ₫ hoặc Giảm 30%">
          </div>
        </div>

        <div class="tt-form-group">
          <label class="tt-label">Tùy chỉnh Caption (Để trống để Javis tự sinh theo Kit)</label>
          <textarea id="ttCaption" class="tt-textarea" rows="4" placeholder="Nếu để trống, hệ thống sẽ tự động tạo caption ngắn 8–18 dòng hấp dẫn kèm hashtag ${esc(curKit.hashtags || '#GameGiaReBSN #SteamOffline')} và số hotline.">${esc(_caption)}</textarea>
        </div>

        <!-- Options Checkboxes -->
        <div style="display: flex; flex-wrap: wrap; gap: 20px; background: rgba(0,0,0,0.15); padding: 14px 16px; border-radius: 10px; margin-bottom: 24px; border: 1px solid rgba(255,255,255,0.05);">
          <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer;">
            <input type="checkbox" id="chkMusic" ${_autoAddMusic ? "checked" : ""}>
            <span><strong>Tự động thêm nhạc thịnh hành</strong> (autoAddMusic=true)</span>
          </label>
          <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer;">
            <input type="checkbox" id="chkCrop" ${_autoCrop ? "checked" : ""}>
            <span><strong>Tự động căn giữa crop 9:16 dọc</strong> (1080x1920)</span>
          </label>
          <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer;">
            <input type="checkbox" id="chkDraft" ${_isDraft ? "checked" : ""}>
            <span>Chế độ: <strong>Lưu vào Hộp thư nháp TikTok (Draft)</strong></span>
          </label>
        </div>

        <!-- Action Button -->
        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
          <button id="btnPostTikTok" class="tt-btn" ${_posting ? "disabled" : ""}>
            ${_posting ? "⏳ Đang chuẩn bị ảnh & đăng lên PostPeer..." : "🚀 ĐĂNG THỬ LÊN TIKTOK NGAY"}
          </button>
          <button id="btnSaveKitAccount" class="tt-btn tt-btn-sec">
            💾 Gán tài khoản này vào Kit
          </button>
        </div>

        <!-- Result Box -->
        <div id="ttResultBox" style="margin-top: 20px; display: ${_postResult ? "block" : "none"};">
          ${_postResult ? renderPostResultHtml(_postResult) : ""}
        </div>
      </div>
    `;

    // Bind Events
    container.querySelector("#ttKitSelect").onchange = function () {
      _selectedKit = this.value;
      renderComposeTab(container);
    };

    container.querySelector("#ttAccountSelect").onchange = function () {
      _selectedAccount = this.value;
    };

    container.querySelector("#ttProductTitle").oninput = function () {
      _productTitle = this.value;
    };

    container.querySelector("#ttProductPrice").oninput = function () {
      _productPrice = this.value;
    };

    container.querySelector("#ttCaption").oninput = function () {
      _caption = this.value;
    };

    container.querySelector("#chkMusic").onchange = function () {
      _autoAddMusic = this.checked;
    };

    container.querySelector("#chkCrop").onchange = function () {
      _autoCrop = this.checked;
    };

    container.querySelector("#chkDraft").onchange = function () {
      _isDraft = this.checked;
    };

    container.querySelector("#btnSaveKitAccount").onclick = async function () {
      var accId = container.querySelector("#ttAccountSelect").value;
      var accObj = accounts.find(a => a.id === accId);
      var accName = accObj ? (accObj.username || accObj.name) : "@seotrum";
      try {
        await api("/tiktok/kit-account", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            brand_kit: _selectedKit,
            account_id: accId,
            account_name: accName
          })
        });
        alert(`Đã lưu accountId ${accId} vào kit ${_selectedKit}!`);
        await loadStatus();
        renderTabBody();
      } catch (e) {
        alert("Lỗi lưu kit: " + e.message);
      }
    };

    container.querySelector("#btnPostTikTok").onclick = async function () {
      if (_posting) return;
      _posting = true;
      _postResult = null;
      renderComposeTab(container);

      try {
        var accId = container.querySelector("#ttAccountSelect").value;
        var res = await api("/tiktok/post", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            brand_kit: _selectedKit,
            account_id: accId,
            caption: _caption || undefined,
            product_title: _productTitle || undefined,
            product_price: _productPrice || undefined,
            auto_add_music: _autoAddMusic,
            draft: _isDraft
          })
        });
        _postResult = res;
      } catch (err) {
        _postResult = { ok: false, error: err.message };
      } finally {
        _posting = false;
        await loadStatus();
        renderComposeTab(container);
      }
    };
  }

  function renderPostResultHtml(res) {
    if (res.ok) {
      return `
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 16px;">
          <div style="display: flex; align-items: center; gap: 8px; color: #34d399; font-weight: 700; font-size: 15px; margin-bottom: 8px;">
            ✅ ${esc(res.message || "Đăng TikTok Carousel thành công!")}
          </div>
          <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
            <div>Mã định danh PostPeer: <code style="color:#fb7185;">${esc(res.postpeer_id || "Chờ xử lý")}</code></div>
            <div>Số ảnh đã gửi: <strong>${esc(res.photos_count || 0)} ảnh 9:16 dọc</strong></div>
            <div>Chế độ: <strong>${res.draft ? "Hộp thư nháp (Draft)" : "Đăng công khai (Published)"}</strong></div>
            ${res.tiktok_url ? `
              <div style="margin-top: 10px;">
                <a href="${esc(res.tiktok_url)}" target="_blank" rel="noopener" style="color: #38bdf8; text-decoration: underline; font-weight: 600;">
                  👉 Bấm vào đây để mở xem bài trên TikTok
                </a>
              </div>
            ` : `
              <div style="margin-top: 6px; font-size: 12px; color: #94a3b8;">
                (PostPeer đang đưa bài vào hàng đợi đăng TikTok. Sau vài giây kiểm tra TikTok @seotrum để thấy bài mới hoặc nháp).
              </div>
            `}
          </div>
        </div>
      `;
    } else {
      return `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 16px;">
          <div style="display: flex; align-items: center; gap: 8px; color: #f87171; font-weight: 700; font-size: 15px; margin-bottom: 6px;">
            ❌ Lỗi khi đăng TikTok qua PostPeer
          </div>
          <div style="font-size: 13px; color: #fca5a5;">
            ${esc(res.error || "Chi tiết lỗi không xác định")}
          </div>
        </div>
      `;
    }
  }

  // ==========================================
  // TAB 2: MEDIA & UPLOAD
  // ==========================================
  function renderMediaTab(container) {
    container.innerHTML = `
      <div class="tt-card">
        <h3 style="margin-top: 0; font-size: 16px; font-weight: 700; color: #fff;">
          Tải ảnh lên Thư viện 9:16 (_xuat-tiktok)
        </h3>
        <p style="font-size: 13px; color: #94a3b8; margin-top: -6px; margin-bottom: 20px;">
          Các ảnh trong thư mục này được cung cấp qua đường dẫn công khai HTTPS <code>https://trannhuy.online/tiktok-media/...</code> để PostPeer có thể nạp trực tiếp.
        </p>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
          <div class="tt-form-group">
            <label class="tt-label">Thư mục thương hiệu</label>
            <select id="ttUploadBrand" class="tt-select">
              <option value="bsn" ${_uploadBrand === "bsn" ? "selected" : ""}>_xuat-tiktok/bsn/ (Game BSN)</option>
              <option value="saoviet" ${_uploadBrand === "saoviet" ? "selected" : ""}>_xuat-tiktok/saoviet/ (Tin Học Sao Việt)</option>
            </select>
          </div>
          <div class="tt-form-group">
            <label class="tt-label">Chọn tệp hình ảnh</label>
            <input type="file" id="ttUploadFile" class="tt-input" accept="image/png,image/jpeg,image/webp">
          </div>
        </div>

        <div style="margin-bottom: 20px;">
          <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer;">
            <input type="checkbox" id="chkUploadCrop" checked>
            <span>Tự động crop tâm chuẩn 9:16 (1080x1920) ngay khi tải lên</span>
          </label>
        </div>

        <button id="btnDoUpload" class="tt-btn" ${_uploading ? "disabled" : ""}>
          ${_uploading ? "⏳ Đang tải lên & crop..." : "📤 Tải lên Thư viện"}
        </button>

        ${_uploadMsg ? `
          <div style="margin-top: 16px; padding: 12px; border-radius: 8px; background: rgba(255,255,255,0.05); font-size: 13px;">
            ${_uploadMsg}
          </div>
        ` : ""}
      </div>
    `;

    // Events
    container.querySelector("#ttUploadBrand").onchange = function () {
      _uploadBrand = this.value;
    };

    container.querySelector("#btnDoUpload").onclick = async function () {
      var fileInput = container.querySelector("#ttUploadFile");
      if (!fileInput.files || !fileInput.files[0]) {
        alert("Vui lòng chọn 1 tệp hình ảnh để tải lên!");
        return;
      }
      var file = fileInput.files[0];
      var crop = container.querySelector("#chkUploadCrop").checked;

      _uploading = true;
      _uploadMsg = "";
      renderMediaTab(container);

      try {
        var formData = new FormData();
        formData.append("file", file);
        formData.append("brand", _uploadBrand);
        formData.append("crop_9_16", crop ? "true" : "false");

        var res = await api("/tiktok/upload", {
          method: "POST",
          body: formData
        });

        _uploadMsg = `✅ Đã tải lên thành công: <strong>${esc(res.filename)}</strong><br>URL công khai: <a href="${esc(res.public_url)}" target="_blank" style="color:#38bdf8;">${esc(res.public_url)}</a>`;
      } catch (err) {
        _uploadMsg = `❌ Lỗi khi tải lên: ${esc(err.message)}`;
      } finally {
        _uploading = false;
        renderMediaTab(container);
      }
    };
  }

  // ==========================================
  // TAB 3: LOOP SETTINGS
  // ==========================================
  function renderLoopTab(container) {
    var loop = (_status && _status.loop) || { enabled: false, status: "Tắt" };

    container.innerHTML = `
      <div class="tt-card">
        <h3 style="margin-top: 0; font-size: 16px; font-weight: 700; color: #fff;">
          Vòng lặp đăng video & carousel tự động hàng ngày
        </h3>
        <p style="font-size: 13px; color: #94a3b8; margin-top: -6px; margin-bottom: 20px;">
          Tệp định nghĩa: <code>brains/Brain Default/Javis/dang-video-tiktok-hang-ngay.md</code>. Mặc định luôn là <strong>TẮT</strong> theo nguyên tắc an toàn của hệ thống.
        </p>

        <div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
            <div>
              <div style="font-size: 16px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px;">
                Trạng thái: 
                <span class="tt-badge ${loop.enabled ? "tt-badge-ok" : "tt-badge-off"}">
                  ${loop.enabled ? "ĐANG BẬT" : "ĐANG TẮT (MẶC ĐỊNH)"}
                </span>
              </div>
              <p style="font-size: 13px; color: #94a3b8; margin: 4px 0 0 0;">
                Mô tả: ${esc(loop.status || "Chưa kích hoạt")}
              </p>
            </div>

            <button id="btnToggleLoop" class="tt-btn ${loop.enabled ? "tt-btn-sec" : ""}">
              ${loop.enabled ? "🛑 Tắt Vòng Lặp Ngay" : "▶️ Bật Vòng Lặp Tự Động"}
            </button>
          </div>
        </div>

        <div style="font-size: 13px; color: #94a3b8; line-height: 1.6;">
          <strong>Quy chuẩn chạy tự động:</strong>
          <ul style="margin: 8px 0; padding-left: 20px;">
            <li>Đăng từ 4–6 ảnh 9:16 dọc từ kho xuất bản hoặc dataset có sẵn.</li>
            <li>Tự động gắn nhạc nền (autoAddMusic), không chọn đúng 1 bài cố định tránh trùng lặp.</li>
            <li>Sau mỗi lần chạy, ghi nhận kết quả và mã bài đăng vào <code>Javis/tiktok-posts.jsonl</code>.</li>
          </ul>
        </div>
      </div>
    `;

    container.querySelector("#btnToggleLoop").onclick = async function () {
      var nextState = !loop.enabled;
      if (nextState) {
        if (!confirm("Bạn có chắc chắn muốn BẬT vòng lặp đăng TikTok tự động hàng ngày?")) return;
      }
      try {
        await api("/tiktok/loop-toggle", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: nextState })
        });
        await loadStatus();
        renderTabBody();
      } catch (e) {
        alert("Lỗi đổi trạng thái loop: " + e.message);
      }
    };
  }

  // ==========================================
  // TAB 4: POSTS HISTORY
  // ==========================================
  function renderHistoryTab(container) {
    var posts = (_status && _status.recent_posts) || [];

    if (posts.length === 0) {
      container.innerHTML = `
        <div class="tt-card" style="text-align: center; padding: 48px 20px;">
          <div style="font-size: 32px; margin-bottom: 12px;">📭</div>
          <div style="font-size: 16px; font-weight: 700; color: #fff;">Chưa có bài đăng nào trong nhật ký</div>
          <p style="font-size: 13px; color: #94a3b8; max-width: 420px; margin: 6px auto 0 auto;">
            Các bài đăng thực tế qua PostPeer API sẽ được ghi nhận tại tệp <code>Javis/tiktok-posts.jsonl</code> và hiển thị tại đây.
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="tt-card" style="padding: 0; overflow: hidden;">
        <div style="padding: 16px 20px; border-bottom: 1px solid var(--border, rgba(255,255,255,0.08)); display: flex; justify-content: space-between; align-items: center;">
          <h3 style="margin: 0; font-size: 15px; font-weight: 700; color: #fff;">
            10 Bài Đăng Carousel Gần Nhất (tiktok-posts.jsonl)
          </h3>
          <span style="font-size: 12px; color: #94a3b8;">${posts.length} bài ghi nhận</span>
        </div>

        <div style="overflow-x: auto;">
          <table class="tt-table">
            <thead>
              <tr>
                <th>Thời gian</th>
                <th>Thương hiệu</th>
                <th>Tài khoản</th>
                <th>Số ảnh</th>
                <th>Trạng thái</th>
                <th>Caption tóm tắt</th>
                <th style="text-align: right;">Hành động</th>
              </tr>
            </thead>
            <tbody>
              ${posts.map(p => `
                <tr>
                  <td style="white-space: nowrap; color: #94a3b8; font-size: 12px;">
                    ${esc(p.datetime || formatTime(p.ts))}
                  </td>
                  <td>
                    <strong style="color: #fff;">${esc((p.brand || "BSN").toUpperCase())}</strong>
                    <div style="font-size: 11px; color: #64748b;">${esc(p.kit || "")}</div>
                  </td>
                  <td style="font-family: monospace; font-size: 12px; color: #fb7185;">
                    ${esc(p.username || `@${(p.accountId || "").substring(0,8)}`)}
                  </td>
                  <td>
                    <span class="tt-badge tt-badge-off">
                      ${p.photos_count || (p.urls && p.urls.length) || 0} ảnh 9:16
                    </span>
                  </td>
                  <td>
                    <span class="tt-badge ${p.draft ? "tt-badge-warn" : "tt-badge-ok"}">
                      ${p.draft ? "Hộp thư nháp" : "Đã xuất bản"}
                    </span>
                  </td>
                  <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #cbd5e1; font-size: 12px;">
                    ${esc(p.caption || "—")}
                  </td>
                  <td style="text-align: right; white-space: nowrap;">
                    ${p.tiktok_url ? `
                      <a href="${esc(p.tiktok_url)}" target="_blank" rel="noopener" style="color: #38bdf8; text-decoration: underline; font-size: 12px; font-weight: 600;">
                        Xem trên TikTok ↗
                      </a>
                    ` : `
                      <span style="color: #64748b; font-family: monospace; font-size: 11px;">
                        ID: ${(p.postpeer_id || "").substring(0, 10)}...
                      </span>
                    `}
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  window.JavisTikTok = {
    render: render
  };
})();
