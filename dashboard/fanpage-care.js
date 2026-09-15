// ============================================================
// Javis OS - Chăm sóc Fanpage (Fanpage Care)
// Quản lý hộp thư bình luận, Messenger và CRM khách hàng đa Trang.
// docs/dev/2026-09-16-fanpage-care-ui-plan.md
// ============================================================
(function () {
  "use strict";

  const LOC = () => (window.JavisI18n && JavisI18n.locale()) || "vi-VN";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function redactPhone(phone) {
    if (!phone) return "";
    var p = String(phone).replace(/\s+/g, "");
    if (p.length >= 7) {
      return p.substring(0, 3) + "****" + p.substring(p.length - 3);
    }
    return p;
  }

  function formatTime(ts) {
    if (!ts) return "";
    try {
      var d = typeof ts === "number" ? new Date(ts > 1e11 ? ts : ts * 1000) : new Date(ts);
      var now = new Date();
      var isToday = d.toDateString() === now.toDateString();
      var timeStr = d.toLocaleTimeString(LOC(), { hour: "2-digit", minute: "2-digit" });
      if (isToday) return timeStr;
      return d.toLocaleDateString(LOC(), { day: "2-digit", month: "2-digit" }) + " " + timeStr;
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
      throw new Error((d && (d.error || d.detail)) || ("Lỗi HTTP " + r.status));
    }
    return d;
  }

  let _hostEl = null;
  let _activeTab = "comments"; // "comments" | "messenger" | "crm"
  let _state = null;
  let _inbox = { events: [], drafts: [], stats: {} };
  let _customers = [];
  let _conversations = [];
  let _filterPage = "";
  let _filterClass = "";
  let _crmQuery = "";
  let _pollInterval = null;
  let _showFullPhones = {};

  const CLASS_LABELS = {
    lead: { label: "Lead (SĐT)", color: "var(--ok, #10b981)", bg: "rgba(16, 185, 129, 0.15)" },
    faq: { label: "FAQ", color: "#3b82f6", bg: "rgba(59, 130, 246, 0.15)" },
    spam: { label: "Spam", color: "var(--danger, #ef4444)", bg: "rgba(239, 68, 68, 0.15)" },
    khen: { label: "Khen", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.15)" },
    ky_thuat: { label: "Kỹ thuật", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    ambiguous: { label: "Mơ hồ", color: "#eab308", bg: "rgba(234, 179, 8, 0.15)" },
    bo_qua: { label: "Bỏ qua", color: "var(--text3, #888)", bg: "rgba(128, 128, 128, 0.15)" },
  };

  const MODE_INFOS = {
    suggest: {
      name: "Chỉ nháp",
      desc: "Không gửi Facebook. Bạn bấm Gửi trên từng nháp.",
      label: "Đang bật — Chỉ nháp",
    },
    auto: {
      name: "Tự FAQ",
      desc: "Tự trả lời comment học phí/địa chỉ/lịch. Không Messenger.",
      label: "Đang bật — Tự FAQ",
    },
    full: {
      name: "Tự động + tin",
      desc: "FAQ + AI câu khó + Messenger (cửa sổ 24h).",
      label: "Đang bật — Tự động",
    },
  };

  async function loadState() {
    try {
      _state = await api("/fanpage-care/state");
    } catch (e) {
      console.error("[Care] loadState error:", e);
    }
  }

  async function loadInbox() {
    try {
      var q = new URLSearchParams();
      if (_filterPage) q.append("page_id", _filterPage);
      if (_filterClass) q.append("class_name", _filterClass);
      q.append("limit", "50");
      _inbox = await api("/fanpage-care/inbox?" + q.toString());
    } catch (e) {
      console.error("[Care] loadInbox error:", e);
    }
  }

  async function loadCustomers() {
    try {
      var q = new URLSearchParams();
      if (_crmQuery) q.append("q", _crmQuery);
      q.append("limit", "50");
      var res = await api("/fanpage-care/customers?" + q.toString());
      _customers = res.customers || [];
    } catch (e) {
      console.error("[Care] loadCustomers error:", e);
    }
  }

  async function loadConversations() {
    try {
      var res = await api("/fanpage-care/conversations");
      _conversations = res.conversations || [];
    } catch (e) {
      console.error("[Care] loadConversations error:", e);
    }
  }

  function startAutoPoll() {
    stopAutoPoll();
    _pollInterval = setInterval(async function () {
      if (!_hostEl || !_hostEl.isConnected) {
        stopAutoPoll();
        return;
      }
      if (_activeTab === "comments") {
        await loadInbox();
        renderTabContent();
      } else if (_activeTab === "messenger") {
        await loadConversations();
        renderTabContent();
      }
    }, 5000);
  }

  function stopAutoPoll() {
    if (_pollInterval) {
      clearInterval(_pollInterval);
      _pollInterval = null;
    }
  }

  function render(container) {
    _hostEl = container;
    _hostEl.innerHTML = `
      <div class="care-wrapper">
        <div id="careChecklistSlot"></div>
        <div id="careStatsSlot"></div>
        <div id="careToolbarSlot"></div>
        <div class="care-tabs-nav">
          <button class="care-tab-btn active" data-tab="comments" id="tabBtnComments">
            <span>Bình luận & Bản nháp</span>
            <span class="care-badge" id="careDraftCount" style="display:none;">0</span>
            <span class="care-time-muted" id="careEventsCount"></span>
          </button>
          <button class="care-tab-btn" data-tab="messenger" id="tabBtnMessenger">
            <span>Messenger</span>
            <span class="care-tag-dev">Development</span>
          </button>
          <button class="care-tab-btn" data-tab="crm" id="tabBtnCrm">
            <span>Khách hàng (CRM)</span>
            <span class="care-time-muted" id="careCustCount"></span>
          </button>
        </div>
        <div id="careTabContent" class="care-tab-content"></div>
      </div>
      <div id="careModal" class="care-modal-backdrop" style="display:none;"></div>
    `;

    bindTabEvents();
    initData();
  }

  async function initData() {
    await loadState();
    await loadInbox();
    renderHeader();
    renderTabContent();
    startAutoPoll();
  }

  function bindTabEvents() {
    _hostEl.querySelectorAll(".care-tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var t = this.getAttribute("data-tab");
        if (t === _activeTab) return;
        switchTab(t);
      });
    });
  }

  function switchTab(tabId) {
    _activeTab = tabId;
    _hostEl.querySelectorAll(".care-tab-btn").forEach(b => {
      b.classList.toggle("active", b.getAttribute("data-tab") === _activeTab);
    });
    if (_activeTab === "crm") {
      loadCustomers().then(renderTabContent);
    } else if (_activeTab === "messenger") {
      loadConversations().then(renderTabContent);
    } else {
      renderTabContent();
    }
  }

  function renderHeader() {
    if (!_hostEl || !_state) return;

    var cfg = _state.config || {};
    var stats = _state.stats || {};
    var eligiblePages = _state.eligible_pages || [];
    var perm = _state.connection_perm || "readonly";
    var fbConnected = !!_state.facebook_connected;
    var fbLabel = _state.facebook_label || "Facebook Trang";
    var enabled = !!cfg.enabled;
    var mode = cfg.mode || "suggest";
    var kill = !!cfg.kill_switch;
    var isQuiet = !!_state.is_quiet;
    var events24h = stats.events_24h || 0;
    var pendingDrafts = stats.pending_drafts || 0;
    var totalCust = stats.total_customers || 0;
    var leads24h = stats.leads_24h || 0;

    // 1. Tầng A - Checklist 3 bước (chỉ hiện khi chưa hoàn tất cả 3 và chưa có event)
    var chkSlot = _hostEl.querySelector("#careChecklistSlot");
    var step1Done = fbConnected && perm === "full";
    var step2Done = enabled;
    var step3Done = events24h > 0;
    var needsSetup = !step1Done || !step2Done || !step3Done;

    var killBanner = kill
      ? `<div class="care-banner care-banner-danger" style="margin-bottom:10px;">
           <div class="care-banner-icon">&#9940;</div>
           <div class="care-banner-body">
             <strong>Đã dừng mọi lệnh gửi.</strong> Vẫn nhận bình luận và CRM.
           </div>
         </div>`
      : "";

    if (needsSetup) {
      chkSlot.innerHTML = `
        ${killBanner}
        <div class="care-setup">
          <div class="care-setup-head">
            <span>Các bước sẵn sàng vận hành</span>
            <span class="care-time-muted">Hoàn thành 3 bước để Javis bắt đầu chăm sóc</span>
          </div>

          <div class="care-setup-step ${step1Done ? "is-done" : "is-todo"}">
            <div class="care-step-info">
              <div class="care-step-num">${step1Done ? "&#10003;" : "1"}</div>
              <div class="care-step-texts">
                <div class="care-step-title">1. Facebook Toàn quyền</div>
                <div class="care-step-desc">
                  ${step1Done
                    ? `Đã kết nối Toàn quyền (${esc(fbLabel)}).`
                    : `Facebook chưa Toàn quyền. Care chỉ ghi nhận, không trả lời được. Vào Kết nối, thẻ Facebook Trang &rarr; Kết nối lại / nâng Toàn quyền.`}
                </div>
              </div>
            </div>
            ${step1Done ? "" : `<button id="careBtnOpenConn" class="care-btn care-btn-sm care-btn-sec">Mở Kết nối &rarr;</button>`}
          </div>

          <div class="care-setup-step ${step2Done ? "is-done" : "is-todo"}">
            <div class="care-step-info">
              <div class="care-step-num">${step2Done ? "&#10003;" : "2"}</div>
              <div class="care-step-texts">
                <div class="care-step-title">2. Bật Chăm sóc Fanpage</div>
                <div class="care-step-desc">
                  ${step2Done
                    ? `Hệ thống đang hoạt động.`
                    : `Công tắc bên dưới. Lần đầu để <strong>Chỉ nháp</strong> &mdash; không gửi ra Facebook.`}
                </div>
              </div>
            </div>
          </div>

          <div class="care-setup-step ${step3Done ? "is-done" : "is-todo"}">
            <div class="care-step-info">
              <div class="care-step-num">${step3Done ? "&#10003;" : "3"}</div>
              <div class="care-step-texts">
                <div class="care-step-title">3. Quét kiểm tra bình luận</div>
                <div class="care-step-desc">
                  ${step3Done
                    ? `Đã thu nạp ${events24h} sự kiện.`
                    : `Bấm <strong>Quét ngay</strong>. Hoặc comment thử trên 1 Fanpage (cơ sở ở đâu / học phí / để SĐT).`}
                </div>
              </div>
            </div>
            ${step3Done ? "" : `<button id="careBtnStepPoll" class="care-btn care-btn-sm care-btn-pri">&#8635; Quét ngay</button>`}
          </div>
        </div>
      `;

      var btnConn = chkSlot.querySelector("#careBtnOpenConn");
      if (btnConn) {
        btnConn.onclick = function () {
          if (window.JavisNav && JavisNav.go) JavisNav.go("mcp");
        };
      }
      var btnStepPoll = chkSlot.querySelector("#careBtnStepPoll");
      if (btnStepPoll) {
        btnStepPoll.onclick = triggerPoll;
      }
    } else {
      chkSlot.innerHTML = killBanner;
    }

    // 2. Tầng B - 4 Thẻ Số
    var statsSlot = _hostEl.querySelector("#careStatsSlot");
    statsSlot.innerHTML = `
      <div class="care-stats">
        <div class="care-stat" id="statCardPages" title="Số Fanpage có brand kit trong Brain">
          <div class="care-stat-val">${eligiblePages.length}</div>
          <div class="care-stat-lbl">Fanpage có kit</div>
        </div>
        <div class="care-stat" id="statCardComments" title="Tổng số bình luận trong 24 giờ qua">
          <div class="care-stat-val">${events24h}</div>
          <div class="care-stat-lbl">Bình luận 24h</div>
        </div>
        <div class="care-stat" id="statCardDrafts" title="Bản nháp phản hồi đang chờ bạn duyệt">
          <div class="care-stat-val ${pendingDrafts > 0 ? "is-accent" : ""}">${pendingDrafts}</div>
          <div class="care-stat-lbl">Nháp chờ duyệt</div>
        </div>
        <div class="care-stat" id="statCardCrm" title="Khách hàng ghi nhận trong CRM Brain">
          <div class="care-stat-val">
            <span>${totalCust}</span>
            ${leads24h > 0 ? `<span class="care-stat-sub">+${leads24h} lead</span>` : ""}
          </div>
          <div class="care-stat-lbl">Khách / lead</div>
        </div>
      </div>
    `;

    statsSlot.querySelector("#statCardComments").onclick = () => switchTab("comments");
    statsSlot.querySelector("#statCardDrafts").onclick = () => {
      switchTab("comments");
      setTimeout(() => {
        var dSection = _hostEl.querySelector(".care-drafts-list");
        if (dSection) dSection.scrollIntoView({ behavior: "smooth" });
      }, 100);
    };
    statsSlot.querySelector("#statCardCrm").onclick = () => switchTab("crm");

    // 3. Tầng C - Thanh Điều Khiển
    var tbSlot = _hostEl.querySelector("#careToolbarSlot");
    var modeInfo = MODE_INFOS[mode] || MODE_INFOS.suggest;
    var toggleLabel = enabled ? modeInfo.label : "Đang tắt Care";

    var quietPill = isQuiet
      ? `<span class="care-pill care-pill-quiet" title="21h&ndash;7h không gửi, vẫn ghi CRM">&#127769; Giờ im lặng (${esc(cfg.quiet_hours || "21-07")})</span>`
      : `<span class="care-pill care-pill-sec" title="21h&ndash;7h không gửi, vẫn ghi CRM">&#128344; ${esc(cfg.quiet_hours || "21-07")}</span>`;

    tbSlot.innerHTML = `
      <div class="care-controls-card">
        <div class="care-ctl-left">
          <div class="care-switch-wrap">
            <label class="care-toggle">
              <input type="checkbox" id="careToggleEnabled" ${enabled ? "checked" : ""}>
              <span class="care-toggle-slider"></span>
            </label>
            <span class="care-toggle-lbl"><strong>${toggleLabel}</strong></span>
          </div>

          <div style="display:flex; flex-direction:column; gap:2px;">
            <div class="care-segment" id="careModeSegment">
              <button data-mode="suggest" class="${mode === "suggest" ? "active" : ""}">Chỉ nháp</button>
              <button data-mode="auto" class="${mode === "auto" ? "active" : ""}">Tự FAQ</button>
              <button data-mode="full" class="${mode === "full" ? "active" : ""}">Tự động + tin</button>
            </div>
            <div class="care-mode-subtext" id="careModeSubtext">${esc(modeInfo.desc)}</div>
          </div>

          ${quietPill}
        </div>

        <div class="care-ctl-right">
          <button id="careBtnPollNow" class="care-btn care-btn-pri" title="Quét bình luận ngay lập tức">
            <span>&#8635; Quét ngay</span>
          </button>
          <button id="careBtnKill" class="${kill ? "care-btn-kill-on" : "care-btn-kill-off"}" title="Dừng khẩn cấp toàn bộ lệnh gửi Graph">
            <span>${kill ? "Đang dừng gửi &mdash; bấm để mở lại" : "Dừng gửi &mdash; Kill"}</span>
          </button>
        </div>
      </div>
    `;

    // Bind Controls
    tbSlot.querySelector("#careToggleEnabled").onchange = async function () {
      var n = this.checked;
      try {
        await api("/fanpage-care/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: n }),
        });
        await loadState();
        renderHeader();
      } catch (e) {
        alert("Lỗi lưu cài đặt: " + e.message);
        this.checked = !n;
      }
    };

    tbSlot.querySelectorAll("#careModeSegment button").forEach(b => {
      b.onclick = async function () {
        var newMode = this.getAttribute("data-mode");
        if (newMode === mode) return;

        if (newMode !== "suggest" && perm === "full") {
          var ok = confirm("Bạn có chắc muốn chuyển sang chế độ tự động trả lời công khai trên Facebook?");
          if (!ok) return;
        }

        try {
          await api("/fanpage-care/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: newMode }),
          });
          await loadState();
          renderHeader();
        } catch (e) {
          alert("Lỗi lưu chế độ: " + e.message);
        }
      };
    });

    tbSlot.querySelector("#careBtnPollNow").onclick = triggerPoll;

    tbSlot.querySelector("#careBtnKill").onclick = async function () {
      var nextKill = !kill;
      if (nextKill) {
        if (!confirm("Dừng khẩn cấp mọi lệnh gửi ra Facebook? Hệ thống vẫn tiếp tục nhận bình luận và lưu CRM.")) return;
      }
      try {
        await api("/fanpage-care/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kill_switch: nextKill }),
        });
        await loadState();
        renderHeader();
      } catch (e) {
        alert("Lỗi Kill Switch: " + e.message);
      }
    };
  }

  async function triggerPoll() {
    var btns = _hostEl.querySelectorAll("#careBtnPollNow, #careBtnStepPoll, #careBtnEmptyPoll");
    btns.forEach(b => {
      b.disabled = true;
      b.innerHTML = "Đang quét...";
    });

    try {
      var res = await api("/fanpage-care/poll-now", { method: "POST" });
      var r = res.result || {};
      if (r.status === "skipped") {
        if (r.reason === "disabled") {
          alert("Care đang tắt. Bật công tắc rồi quét lại.");
        } else if (r.reason === "no_eligible_pages") {
          alert("Chưa có Fanpage nào có brand kit trong brain.");
        } else {
          alert("Bỏ qua quét: " + (r.reason || "đang bận"));
        }
      }
      await loadState();
      await loadInbox();
      renderHeader();
      renderTabContent();
    } catch (e) {
      alert("Quét lỗi: " + e.message);
    } finally {
      btns.forEach(b => {
        b.disabled = false;
        b.innerHTML = "<span>&#8635; Quét ngay</span>";
      });
    }
  }

  function renderTabContent() {
    var el = _hostEl.querySelector("#careTabContent");
    if (!el) return;

    var drafts = (_inbox && _inbox.drafts) || [];
    var events = (_inbox && _inbox.events) || [];
    var badge = _hostEl.querySelector("#careDraftCount");
    if (badge) {
      if (drafts.length > 0) {
        badge.textContent = drafts.length;
        badge.style.display = "inline-flex";
      } else {
        badge.style.display = "none";
      }
    }

    var evCnt = _hostEl.querySelector("#careEventsCount");
    if (evCnt) {
      evCnt.textContent = `(${events.length})`;
    }

    var custCnt = _hostEl.querySelector("#careCustCount");
    if (custCnt && _state && _state.stats) {
      custCnt.textContent = `(${_state.stats.total_customers || 0})`;
    }

    if (_activeTab === "comments") {
      renderCommentsTab(el);
    } else if (_activeTab === "messenger") {
      renderMessengerTab(el);
    } else if (_activeTab === "crm") {
      renderCrmTab(el);
    }
  }

  // ===================== TAB 1: COMMENTS =====================
  function renderCommentsTab(container) {
    var drafts = (_inbox && _inbox.drafts) || [];
    var events = (_inbox && _inbox.events) || [];
    var pages = (_state && _state.eligible_pages) || [];
    var enabled = !!(_state && _state.config && _state.config.enabled);

    // 1. Nháp chờ duyệt (trên cùng nếu có)
    var draftsSection = "";
    if (drafts.length > 0) {
      var draftCards = drafts.map(d => {
        var page = pages.find(p => p.page_id === d.page_id) || { name: d.page_id };
        return `
          <div class="care-draft-card" data-draft-id="${d.id}">
            <div class="care-draft-head">
              <div>
                <span class="care-page-tag">${esc(page.name)}</span>
                <span class="care-class-chip" style="color:#3b82f6; background:rgba(59,130,246,0.15);">${esc(d.class || "draft")}</span>
                <span class="care-time-muted">${formatTime(d.created_at || "")}</span>
              </div>
              <div class="care-draft-actions">
                <button class="care-btn care-btn-sm care-btn-pri btn-send-draft" data-id="${d.id}">Gửi ngay</button>
                <button class="care-btn care-btn-sm care-btn-sec btn-reject-draft" data-id="${d.id}">Bỏ qua</button>
              </div>
            </div>
            <div class="care-draft-body">
              <div class="care-draft-label">Đề xuất trả lời:</div>
              <div class="care-draft-text">${esc(d.proposed || "")}</div>
            </div>
          </div>
        `;
      }).join("");

      draftsSection = `
        <div class="care-section-title">
          <span>Cần bạn duyệt (${drafts.length})</span>
        </div>
        <div class="care-drafts-list">${draftCards}</div>
      `;
    }

    // 2. Bộ lọc & Quick Chips
    var pageOptions = '<option value="">Mọi Fanpage</option>';
    pages.forEach(p => {
      pageOptions += `<option value="${esc(p.page_id)}" ${_filterPage === p.page_id ? "selected" : ""}>${esc(p.name)}</option>`;
    });

    var classOptions = `
      <option value="">Mọi loại</option>
      <option value="lead" ${_filterClass === "lead" ? "selected" : ""}>Lead (SĐT / Đăng ký)</option>
      <option value="faq" ${_filterClass === "faq" ? "selected" : ""}>FAQ (Học phí, Lịch, Địa chỉ)</option>
      <option value="spam" ${_filterClass === "spam" ? "selected" : ""}>Spam</option>
      <option value="khen" ${_filterClass === "khen" ? "selected" : ""}>Khen ngợi</option>
      <option value="ambiguous" ${_filterClass === "ambiguous" ? "selected" : ""}>Mơ hồ</option>
      <option value="ky_thuat" ${_filterClass === "ky_thuat" ? "selected" : ""}>Kỹ thuật</option>
    `;

    var filtersBar = `
      <div class="care-filters-bar">
        <div class="care-filter-item">
          <select id="careFilterPage" class="care-select">${pageOptions}</select>
        </div>
        <div class="care-filter-item">
          <select id="careFilterClass" class="care-select">${classOptions}</select>
        </div>
        <div class="care-quick-chips">
          <button class="care-chip ${_filterClass === "" ? "active" : ""}" data-c="">Tất cả</button>
          <button class="care-chip ${_filterClass === "lead" ? "active" : ""}" data-c="lead">Lead</button>
          <button class="care-chip ${_filterClass === "faq" ? "active" : ""}" data-c="faq">FAQ</button>
          <button class="care-chip ${_filterClass === "spam" ? "active" : ""}" data-c="spam">Spam</button>
        </div>
      </div>
    `;

    // 3. Danh sách Cards (hoặc Empty Hero)
    var contentHtml = "";
    if (events.length === 0) {
      contentHtml = `
        <div class="care-empty-hero">
          <div class="care-empty-icon">&#128172;</div>
          <h3>Chưa có bình luận</h3>
          <p>
            ${enabled
              ? "Chưa thấy bình luận 24 giờ qua. Bấm Quét ngay, hoặc comment thử trên Page (ở đâu / học phí / để SĐT)."
              : "Bật Care ở bước 2, rồi Quét ngay."}
          </p>
          <button id="careBtnEmptyPoll" class="care-btn care-btn-pri" style="margin-top:6px;">&#8635; Quét ngay</button>
        </div>
      `;
    } else {
      var cardsHtml = events.map(ev => {
        var pInfo = pages.find(p => p.page_id === ev.page_id) || { name: ev.page_id };
        var clsMeta = CLASS_LABELS[ev.class] || { label: ev.class || "Khác", color: "#888", bg: "rgba(128,128,128,0.15)" };
        var rawPhone = "";
        try {
          var extra = JSON.parse(ev.extra_json || "{}");
          if (extra.phones && extra.phones.length > 0) rawPhone = extra.phones.join(", ");
        } catch (e) {}

        var phoneDisplay = "";
        if (rawPhone) {
          var isShown = _showFullPhones[ev.id];
          phoneDisplay = `
            <span class="care-phone-badge" title="Bấm để ẩn/hiện" data-ev-id="${ev.id}">
              &#128222; ${esc(isShown ? rawPhone : redactPhone(rawPhone))}
            </span>
          `;
        }

        return `
          <div class="care-comment-card">
            <div class="care-card-head">
              <div class="care-card-meta">
                <span class="care-class-chip" style="color:${clsMeta.color}; background:${clsMeta.bg};">${clsMeta.label}</span>
                <span class="care-time-muted">${formatTime(ev.created_time || ev.created_ts)}</span>
                <span class="care-page-tag">${esc(pInfo.name)}</span>
              </div>
            </div>
            <div class="care-card-body">
              <span class="care-card-user">${esc(ev.from_name || "Ẩn danh")}:</span>
              <span>${esc(ev.body || "")}</span>
            </div>
            <div class="care-card-foot">
              <div>${phoneDisplay || `<span class="care-text-muted">Không có SĐT</span>`}</div>
              <button class="care-btn care-btn-xs care-btn-sec btn-ev-task" 
                data-ev-id="${ev.id}" 
                data-page="${esc(pInfo.name)}" 
                data-user="${esc(ev.from_name || 'Ẩn danh')}" 
                data-msg="${esc(ev.body || '')}" 
                data-phone="${esc(rawPhone)}">
                <span>&#128203; Tạo việc</span>
              </button>
            </div>
          </div>
        `;
      }).join("");

      contentHtml = `<div class="care-comment-list">${cardsHtml}</div>`;
    }

    container.innerHTML = `
      ${draftsSection}
      ${filtersBar}
      ${contentHtml}
    `;

    // Bind event handlers
    container.querySelector("#careFilterPage").onchange = function () {
      _filterPage = this.value;
      loadInbox().then(renderTabContent);
    };

    container.querySelector("#careFilterClass").onchange = function () {
      _filterClass = this.value;
      loadInbox().then(renderTabContent);
    };

    container.querySelectorAll(".care-quick-chips button").forEach(b => {
      b.onclick = function () {
        _filterClass = this.getAttribute("data-c");
        loadInbox().then(renderTabContent);
      };
    });

    var btnEmptyPoll = container.querySelector("#careBtnEmptyPoll");
    if (btnEmptyPoll) btnEmptyPoll.onclick = triggerPoll;

    container.querySelectorAll(".btn-send-draft").forEach(b => {
      b.onclick = async function () {
        var id = this.getAttribute("data-id");
        this.disabled = true;
        this.textContent = "Đang gửi...";
        try {
          await api("/fanpage-care/drafts/" + id + "/send", { method: "POST" });
          await loadInbox();
          renderTabContent();
        } catch (e) {
          alert("Lỗi gửi draft: " + e.message);
          this.disabled = false;
          this.textContent = "Gửi ngay";
        }
      };
    });

    container.querySelectorAll(".btn-reject-draft").forEach(b => {
      b.onclick = async function () {
        var id = this.getAttribute("data-id");
        try {
          await api("/fanpage-care/drafts/" + id + "/reject", { method: "POST" });
          await loadInbox();
          renderTabContent();
        } catch (e) {
          alert("Lỗi: " + e.message);
        }
      };
    });

    container.querySelectorAll(".care-phone-badge").forEach(b => {
      b.onclick = function () {
        var evId = this.getAttribute("data-ev-id");
        _showFullPhones[evId] = !_showFullPhones[evId];
        renderTabContent();
      };
    });

    container.querySelectorAll(".btn-ev-task").forEach(b => {
      b.onclick = async function () {
        var page = this.getAttribute("data-page");
        var user = this.getAttribute("data-user");
        var msg = this.getAttribute("data-msg");
        var phone = this.getAttribute("data-phone");
        var evId = this.getAttribute("data-ev-id");

        var title = prompt("Tiêu đề việc cần giao:", "Chăm sóc khách FB: " + user + (phone ? " (" + phone + ")" : ""));
        if (!title) return;

        try {
          await api("/fanpage-care/handoff", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: title,
              intent: "Phản hồi khách tại trang " + page + ". Nội dung: " + msg + (phone ? ". SĐT: " + phone : ""),
              priority: phone ? 1 : 2,
              comment_id: evId,
            }),
          });
          alert("Đã tạo việc Kanban thành công (chế độ suggest cho nhân viên)!");
        } catch (e) {
          alert("Lỗi tạo việc: " + e.message);
        }
      };
    });
  }

  // ===================== TAB 2: MESSENGER =====================
  function renderMessengerTab(container) {
    var pages = (_state && _state.eligible_pages) || [];
    var threads = _conversations || [];

    var devBanner = `
      <div class="care-banner care-banner-info" style="margin-bottom:14px;">
        <div class="care-banner-icon">&#9432;</div>
        <div class="care-banner-body">
          <strong>Chế độ Messenger đang trong giai đoạn Development (thử nghiệm Meta).</strong><br>
          Tin nhắn tự động chỉ gửi khi mode là 'Tự động + tin' (full) và trong cửa sổ 24 giờ của Meta.
        </div>
      </div>
    `;

    var contentHtml = "";
    if (threads.length === 0) {
      contentHtml = `
        <div class="care-empty-hero">
          <div class="care-empty-icon">&#128172;</div>
          <h3>Chưa có tin Messenger</h3>
          <p>
            Cần Kết nối lại Facebook (quyền nhắn tin) và khách nhắn Page.<br>
            Không HTTPS thì webhook không tới &mdash; comment vẫn vào tab Bình luận nhờ poll 5 phút.
          </p>
        </div>
      `;
    } else {
      var cardsHtml = threads.map(th => {
        var page = pages.find(p => p.page_id === th.page_id) || { name: th.page_id };
        var psidStr = String(th.psid || "");
        var psidShort = psidStr.length > 4 ? "..." + psidStr.slice(-4) : psidStr;

        var lastUserTs = th.last_user_ts || 0;
        var nowSec = Date.now() / 1000;
        var in24h = (nowSec - lastUserTs) <= 24 * 3600;
        var windowChip = in24h
          ? `<span class="care-tag" style="color:var(--ok); border-color:rgba(16,185,129,0.3); background:rgba(16,185,129,0.1);">Trong cửa sổ 24h</span>`
          : `<span class="care-tag" style="color:var(--text3); border-color:var(--hairline);">Hết cửa sổ 24h</span>`;

        var takeoverUntil = th.takeover_until || 0;
        var isTakeover = takeoverUntil > nowSec;
        var takeoverChip = "";
        var releaseBtn = "";

        if (isTakeover) {
          var leftMin = Math.ceil((takeoverUntil - nowSec) / 60);
          takeoverChip = `<span class="care-tag" style="color:#f59e0b; border-color:rgba(245,158,11,0.3); background:rgba(245,158,11,0.1);">Nhân viên đang trả lời (${leftMin}p)</span>`;
          releaseBtn = `
            <button class="care-btn care-btn-xs care-btn-pri btn-release-takeover" data-pid="${esc(th.page_id)}" data-psid="${esc(th.psid)}">
              Javis nhận lại
            </button>
          `;
        }

        return `
          <div class="care-thread-card">
            <div class="care-thread-info">
              <div style="display:flex; align-items:center; gap:8px;">
                <strong>${esc(page.name)}</strong>
                <span class="care-time-muted">PSID: <code>${esc(psidShort)}</code></span>
              </div>
              <div style="display:flex; align-items:center; gap:6px; margin-top:4px;">
                ${windowChip}
                ${takeoverChip}
                <span class="care-time-muted">Khách nhắn: ${formatTime(lastUserTs)}</span>
              </div>
            </div>
            <div class="care-thread-actions">
              ${releaseBtn}
            </div>
          </div>
        `;
      }).join("");

      contentHtml = `<div class="care-threads-list">${cardsHtml}</div>`;
    }

    container.innerHTML = `
      ${devBanner}
      ${contentHtml}
    `;

    container.querySelectorAll(".btn-release-takeover").forEach(b => {
      b.onclick = async function () {
        var pid = this.getAttribute("data-pid");
        var psid = this.getAttribute("data-psid");
        this.disabled = true;
        this.textContent = "Đang xử lý...";
        try {
          await api("/fanpage-care/conversations/release-takeover", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ page_id: pid, psid: psid }),
          });
          await loadConversations();
          renderTabContent();
        } catch (e) {
          alert("Lỗi: " + e.message);
          this.disabled = false;
          this.textContent = "Javis nhận lại";
        }
      };
    });
  }

  // ===================== TAB 3: CRM =====================
  function renderCrmTab(container) {
    var cfg = (_state && _state.config) || {};
    var backupCrm = cfg.backup_crm !== false;

    var custRows = "";
    if (_customers.length === 0) {
      custRows = `<tr><td colspan="7" class="care-empty">Chưa có khách. Lead (có SĐT trên comment) sẽ hiện ở đây sau khi Quét.</td></tr>`;
    } else {
      custRows = _customers.map(c => {
        var tags = (c.tags || "").split(",").filter(Boolean).map(t => `<span class="care-tag">${esc(t.trim())}</span>`).join(" ");
        return `
          <tr>
            <td><code>${esc(c.crm_id)}</code></td>
            <td><strong>${esc(c.name || "Ẩn danh")}</strong></td>
            <td>${c.phone ? `<strong>${esc(c.phone)}</strong>` : '<span class="care-text-muted">Chưa có</span>'}</td>
            <td>${esc(c.campus || "")}</td>
            <td>${esc(c.course_interest || "")}</td>
            <td>${tags}</td>
            <td class="care-td-act">
              <button class="care-btn care-btn-xs care-btn-sec btn-crm-view" data-id="${esc(c.crm_id)}">Xem hồ sơ</button>
              <button class="care-btn care-btn-xs care-btn-sec btn-crm-merge" data-id="${esc(c.crm_id)}" data-name="${esc(c.name || '')}">Gộp</button>
              <button class="care-btn care-btn-xs care-btn-danger btn-crm-del" data-id="${esc(c.crm_id)}">Xoá (PDPD)</button>
            </td>
          </tr>
        `;
      }).join("");
    }

    container.innerHTML = `
      <div class="care-crm-top">
        <div class="care-search-box">
          <input type="text" id="careCrmSearch" class="care-input" placeholder="Tìm theo tên, SĐT, ngành học..." value="${esc(_crmQuery)}">
          <button id="careBtnCrmSearch" class="care-btn care-btn-sec">Tìm kiếm</button>
        </div>

        <div class="care-backup-opt">
          <label class="care-checkbox-lbl" title="Bảo vệ quyền riêng tư dữ liệu cá nhân (PDPD)">
            <input type="checkbox" id="careChkBackupCrm" ${backupCrm ? "checked" : ""}>
            <span>Đồng bộ <code>crm/</code> vào Git backup</span>
          </label>
          <div class="care-help-note">
            Tắt thì lần sync sau không đẩy crm/. Lịch sử GitHub đã push vẫn còn &mdash; xoá repo/rotate nếu cần (PDPD).
          </div>
        </div>
      </div>

      <div class="care-table-wrap">
        <table class="care-table">
          <thead>
            <tr>
              <th style="width:130px;">Mã CRM</th>
              <th style="width:160px;">Tên khách hàng</th>
              <th style="width:130px;">Số điện thoại</th>
              <th style="width:150px;">Cơ sở quan tâm</th>
              <th>Khoá học</th>
              <th style="width:120px;">Thẻ</th>
              <th style="width:180px;">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            ${custRows}
          </tbody>
        </table>
      </div>
    `;

    // Bind CRM actions
    container.querySelector("#careBtnCrmSearch").onclick = function () {
      _crmQuery = container.querySelector("#careCrmSearch").value.trim();
      loadCustomers().then(renderTabContent);
    };

    container.querySelector("#careCrmSearch").onkeydown = function (e) {
      if (e.key === "Enter") {
        _crmQuery = this.value.trim();
        loadCustomers().then(renderTabContent);
      }
    };

    container.querySelector("#careChkBackupCrm").onchange = async function () {
      var val = this.checked;
      try {
        await api("/fanpage-care/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ backup_crm: val }),
        });
        await loadState();
      } catch (e) {
        alert("Lỗi: " + e.message);
        this.checked = !val;
      }
    };

    container.querySelectorAll(".btn-crm-view").forEach(b => {
      b.onclick = async function () {
        var id = this.getAttribute("data-id");
        try {
          var res = await api("/fanpage-care/customers/" + encodeURIComponent(id));
          openModal(`
            <div class="care-modal-box">
              <div class="care-modal-head">
                <h3>Hồ sơ khách hàng: ${esc(res.customer.name || id)}</h3>
                <button class="care-modal-close">&times;</button>
              </div>
              <div class="care-modal-body">
                <div class="care-md-preview"><pre>${esc(res.markdown || "Chưa có file markdown")}</pre></div>
              </div>
            </div>
          `);
        } catch (e) {
          alert("Lỗi đọc hồ sơ: " + e.message);
        }
      };
    });

    container.querySelectorAll(".btn-crm-merge").forEach(b => {
      b.onclick = async function () {
        var primId = this.getAttribute("data-id");
        var primName = this.getAttribute("data-name");
        var secId = prompt("Nhập Mã CRM phụ cần gộp vào khách '" + primName + "' (" + primId + "):");
        if (!secId || secId.trim() === primId) return;
        secId = secId.trim();

        if (!confirm("Xác nhận gộp dữ liệu từ " + secId + " vào " + primId + "? Thao tác này không thể hoàn tác.")) return;

        try {
          await api("/fanpage-care/customers/merge", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ primary_crm_id: primId, secondary_crm_id: secId }),
          });
          alert("Đã gộp khách hàng thành công!");
          loadCustomers().then(renderTabContent);
        } catch (e) {
          alert("Lỗi gộp: " + e.message);
        }
      };
    });

    container.querySelectorAll(".btn-crm-del").forEach(b => {
      b.onclick = async function () {
        var id = this.getAttribute("data-id");
        if (!confirm("XOÁ KHÁCH HÀNG (PDPD): Xoá toàn bộ định danh liên kết và thay thế hồ sơ bằng bản ghi rỗng tuân thủ PDPD. Bạn có chắc chắn không?")) return;
        try {
          await api("/fanpage-care/customers/" + encodeURIComponent(id), { method: "DELETE" });
          alert("Đã xoá khách hàng thành công!");
          loadCustomers().then(renderTabContent);
        } catch (e) {
          alert("Lỗi xoá: " + e.message);
        }
      };
    });
  }

  function openModal(html) {
    var m = _hostEl.querySelector("#careModal");
    if (!m) return;
    m.innerHTML = html;
    m.style.display = "flex";
    var closeBtn = m.querySelector(".care-modal-close");
    if (closeBtn) closeBtn.onclick = closeModal;
    m.onclick = function (e) {
      if (e.target === m) closeModal();
    };
  }

  function closeModal() {
    var m = _hostEl.querySelector("#careModal");
    if (!m) return;
    m.style.display = "none";
    m.innerHTML = "";
  }

  window.JavisFanpageCare = {
    render: render,
  };
})();
