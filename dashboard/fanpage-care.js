// ============================================================
// Javis OS - Chăm sóc Fanpage (Fanpage Care)
// Quản lý hộp thư bình luận, Messenger và CRM khách hàng đa Trang.
// docs/dev/2026-09-16-fanpage-care-design.md
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
  let _filterPage = "";
  let _filterClass = "";
  let _filterStatus = "";
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

  function startAutoPoll() {
    stopAutoPoll();
    _pollInterval = setInterval(async function () {
      if (_activeTab === "comments") {
        await loadInbox();
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
        <div id="careHeader"></div>
        <div class="care-tabs-nav">
          <button class="care-tab-btn" data-tab="comments" id="tabBtnComments">
            <span>Bình luận & Bản nháp</span>
            <span class="care-badge" id="careDraftCount" style="display:none;">0</span>
          </button>
          <button class="care-tab-btn" data-tab="messenger" id="tabBtnMessenger">
            <span>Messenger</span>
            <span class="care-tag-dev">Development</span>
          </button>
          <button class="care-tab-btn" data-tab="crm" id="tabBtnCrm">
            <span>Khách hàng (CRM)</span>
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
        _activeTab = t;
        _hostEl.querySelectorAll(".care-tab-btn").forEach(b => b.classList.remove("active"));
        this.classList.add("active");
        if (_activeTab === "crm") {
          loadCustomers().then(renderTabContent);
        } else {
          renderTabContent();
        }
      });
    });
  }

  function renderHeader() {
    var hdr = _hostEl.querySelector("#careHeader");
    if (!hdr || !_state) return;

    var cfg = _state.config || {};
    var perm = _state.connection_perm || "readonly";
    var isFull = perm === "full";
    var enabled = !!cfg.enabled;
    var mode = cfg.mode || "suggest";
    var kill = !!cfg.kill_switch;
    var isQuiet = !!_state.is_quiet;

    var permBanner = "";
    if (!isFull) {
      permBanner = `
        <div class="care-banner care-banner-warn">
          <div class="care-banner-icon">&#9888;</div>
          <div class="care-banner-body">
            <strong>Kết nối Facebook đang ở chế độ '${esc(perm)}'</strong>. 
            Care chỉ ghi nhận sự kiện và cập nhật CRM, không thực hiện hành động ghi (reply, hide) ra Graph.
          </div>
        </div>
      `;
    }

    var killBanner = "";
    if (kill) {
      killBanner = `
        <div class="care-banner care-banner-danger">
          <div class="care-banner-icon">&#9940;</div>
          <div class="care-banner-body">
            <strong>KILL SWITCH ĐANG BẬT</strong>: Mọi lệnh gửi ra Facebook bị dừng ngay lập tức. 
            Hệ thống vẫn nhận bình luận và lưu trữ CRM.
          </div>
        </div>
      `;
    }

    var quietIndicator = isQuiet
      ? `<span class="care-pill care-pill-quiet" title="Đang trong khung giờ im lặng: không gửi reply ra Graph">&#127769; Giờ im lặng (${esc(cfg.quiet_hours || "21-07")})</span>`
      : "";

    hdr.innerHTML = `
      ${permBanner}
      ${killBanner}
      <div class="care-controls-card">
        <div class="care-ctl-left">
          <div class="care-switch-wrap">
            <label class="care-toggle">
              <input type="checkbox" id="careToggleEnabled" ${enabled ? "checked" : ""}>
              <span class="care-toggle-slider"></span>
            </label>
            <span class="care-toggle-lbl"><strong>${enabled ? "Đang bật Care" : "Đang tắt Care"}</strong></span>
          </div>

          <div class="care-field-group">
            <label>Chế độ:</label>
            <select id="careModeSelect" class="care-select">
              <option value="suggest" ${mode === "suggest" ? "selected" : ""}>suggest (Gợi ý nháp, duyệt tay)</option>
              <option value="auto" ${mode === "auto" ? "selected" : ""}>auto (Tự gửi template FAQ & Lead)</option>
              <option value="full" ${mode === "full" ? "selected" : ""}>full (Tự động + AI grounded)</option>
            </select>
          </div>

          ${quietIndicator}
        </div>

        <div class="care-ctl-right">
          <button id="careBtnPollNow" class="care-btn care-btn-sec" title="Quét bình luận ngay lập tức">
            <span>&#8635; Quét ngay</span>
          </button>
          <button id="careBtnKill" class="care-btn ${kill ? "care-btn-danger-active" : "care-btn-danger"}" title="Dừng khẩn cấp toàn bộ gửi Graph">
            <span>${kill ? "Tắt Kill Switch" : "Kill Switch"}</span>
          </button>
        </div>
      </div>
    `;

    // Bind controls
    hdr.querySelector("#careToggleEnabled").onchange = async function () {
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

    hdr.querySelector("#careModeSelect").onchange = async function () {
      var newMode = this.value;
      if (newMode !== "suggest" && isFull) {
        var ok = confirm(
          "Kết nối Facebook đang Toàn quyền; Care " + newMode + " sẽ trả lời CÔNG KHAI trên bình luận Fanpage.\n\nBạn có chắc chắn muốn chuyển sang chế độ này không?"
        );
        if (!ok) {
          this.value = mode;
          return;
        }
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
        alert("Lỗi lưu mode: " + e.message);
        this.value = mode;
      }
    };

    hdr.querySelector("#careBtnKill").onclick = async function () {
      var nextKill = !kill;
      if (nextKill) {
        if (!confirm("BẬT KILL SWITCH? Toàn bộ Graph gửi ra sẽ bị khoá ngay lập tức.")) return;
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
        alert("Lỗi: " + e.message);
      }
    };

    hdr.querySelector("#careBtnPollNow").onclick = async function () {
      this.disabled = true;
      this.innerHTML = "Đang quét...";
      try {
        var res = await api("/fanpage-care/poll-now", { method: "POST" });
        await loadInbox();
        renderTabContent();
      } catch (e) {
        alert("Quét lỗi: " + e.message);
      } finally {
        this.disabled = false;
        this.innerHTML = "<span>&#8635; Quét ngay</span>";
      }
    };
  }

  function renderTabContent() {
    var el = _hostEl.querySelector("#careTabContent");
    if (!el) return;

    // Update draft count badge
    var drafts = (_inbox && _inbox.drafts) || [];
    var badge = _hostEl.querySelector("#careDraftCount");
    if (badge) {
      if (drafts.length > 0) {
        badge.textContent = drafts.length;
        badge.style.display = "inline-flex";
      } else {
        badge.style.display = "none";
      }
    }

    _hostEl.querySelectorAll(".care-tab-btn").forEach(b => {
      if (b.getAttribute("data-tab") === _activeTab) b.classList.add("active");
      else b.classList.remove("active");
    });

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

    var pageOptions = '<option value="">-- Mọi Fanpage --</option>';
    pages.forEach(p => {
      pageOptions += `<option value="${esc(p.page_id)}" ${_filterPage === p.page_id ? "selected" : ""}>${esc(p.name)}</option>`;
    });

    var draftsSection = "";
    if (drafts.length > 0) {
      var draftRows = drafts.map(d => {
        var page = pages.find(p => p.page_id === d.page_id) || { name: d.page_id };
        return `
          <div class="care-draft-card" data-draft-id="${d.id}">
            <div class="care-draft-head">
              <div>
                <span class="care-page-tag">${esc(page.name)}</span>
                <span class="care-class-chip" style="color:#3b82f6; background:rgba(59,130,246,0.15);">${esc(d.class || "draft")}</span>
                <span class="care-time-muted">${esc(d.created_at || "")}</span>
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
          <span>Bản nháp chờ duyệt (${drafts.length})</span>
        </div>
        <div class="care-drafts-list">${draftRows}</div>
      `;
    }

    var eventRows = "";
    if (events.length === 0) {
      eventRows = `<tr><td colspan="6" class="care-empty">Chưa có bình luận nào trong 24 giờ qua.</td></tr>`;
    } else {
      eventRows = events.map(ev => {
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

        var actions = `
          <button class="care-btn-icon btn-ev-task" title="Tạo việc Kanban cho nhân viên" data-ev-id="${ev.id}" data-page="${esc(pInfo.name)}" data-user="${esc(ev.from_name || 'Ẩn danh')}" data-msg="${esc(ev.body || '')}" data-phone="${esc(rawPhone)}">&#128203;</button>
        `;

        return `
          <tr>
            <td class="care-td-time">${esc(ev.created_time ? ev.created_time.substring(11, 19) : "")}</td>
            <td class="care-td-page"><strong>${esc(pInfo.name)}</strong></td>
            <td class="care-td-user">${esc(ev.from_name || "Ẩn danh")} ${phoneDisplay}</td>
            <td class="care-td-msg">${esc(ev.body || "")}</td>
            <td class="care-td-class">
              <span class="care-class-chip" style="color:${clsMeta.color}; background:${clsMeta.bg};">${clsMeta.label}</span>
            </td>
            <td class="care-td-act">${actions}</td>
          </tr>
        `;
      }).join("");
    }

    container.innerHTML = `
      ${draftsSection}
      <div class="care-filters-bar">
        <div class="care-filter-item">
          <select id="careFilterPage" class="care-select">${pageOptions}</select>
        </div>
        <div class="care-filter-item">
          <select id="careFilterClass" class="care-select">
            <option value="">-- Mọi phân loại --</option>
            <option value="lead" ${_filterClass === "lead" ? "selected" : ""}>Lead (SĐT / Đăng ký)</option>
            <option value="faq" ${_filterClass === "faq" ? "selected" : ""}>FAQ (Học phí, Lịch, Địa chỉ)</option>
            <option value="spam" ${_filterClass === "spam" ? "selected" : ""}>Spam</option>
            <option value="khen" ${_filterClass === "khen" ? "selected" : ""}>Khen ngợi</option>
            <option value="ambiguous" ${_filterClass === "ambiguous" ? "selected" : ""}>Mơ hồ</option>
            <option value="ky_thuat" ${_filterClass === "ky_thuat" ? "selected" : ""}>Kỹ thuật</option>
          </select>
        </div>
      </div>

      <div class="care-table-wrap">
        <table class="care-table">
          <thead>
            <tr>
              <th style="width:80px;">Thời gian</th>
              <th style="width:160px;">Trang</th>
              <th style="width:180px;">Người gửi</th>
              <th>Nội dung</th>
              <th style="width:120px;">Phân loại</th>
              <th style="width:80px;">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            ${eventRows}
          </tbody>
        </table>
      </div>
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
    container.innerHTML = `
      <div class="care-banner care-banner-info">
        <div class="care-banner-icon">&#9432;</div>
        <div class="care-banner-body">
          <strong>Chế độ Messenger đang trong giai đoạn Development</strong><br>
          Theo chính sách Meta, ứng dụng đang phát triển chỉ gửi/nhận tin với tài khoản có vai trò Quản trị viên/Tester trên App Facebook.
          Khi chuyển sang Live, cần xin quyền <code>pages_messaging</code> qua App Review.
        </div>
      </div>

      <div class="care-msg-preview-card">
        <div class="care-msg-empty-state">
          <div style="font-size:36px; margin-bottom:12px;">&#128172;</div>
          <h3>Hộp thư Messenger đa Trang</h3>
          <p style="color:var(--text2); max-width:480px; margin:8px auto 20px auto;">
            Hỗ trợ quản lý tin nhắn tập trung, cửa sổ phản hồi chuẩn 24 giờ, 
            và cơ chế tự động tạm dừng (Human Takeover 4 giờ) khi nhân viên trả lời trực tiếp trên Facebook.
          </p>
          <span class="care-pill care-pill-sec">Sẵn sàng ở bản cập nhật tiếp theo</span>
        </div>
      </div>
    `;
  }

  // ===================== TAB 3: CRM =====================
  function renderCrmTab(container) {
    var cfg = (_state && _state.config) || {};
    var backupCrm = cfg.backup_crm !== false;

    var custRows = "";
    if (_customers.length === 0) {
      custRows = `<tr><td colspan="7" class="care-empty">Chưa có khách hàng nào phù hợp.</td></tr>`;
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
            Tắt thì lần sync sau không đẩy crm/. Lịch sử GitHub đã push vẫn còn — xoá repo/rotate nếu cần (PDPD).
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
