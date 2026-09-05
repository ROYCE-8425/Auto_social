/* Brand dataset: kit chung / kit tung page dang form + chon folder anh mac dinh + thu vien anh. */
(function () {
  "use strict";

  var KIT_DIR = "wiki/brand-kits";
  var IMG_DIR = "attachments/dataset";
  var TAGS_FILE = "wiki/brand-kits/_the-khoa-hoc.md";
  var IMG_RE = /\.(png|jpe?g|webp|gif|svg)$/i;
  var SYSTEM_DIRS = { chung: 1, _mau: 1, _xuat: 1 };

  var FOLDER_LABEL = { "chung": "chung", "_mau": "_mau", "_xuat": "_xuat" };
  var COURSE_FOLDERS = [];
  var COURSE_FOLDER_MAP = {};
  var courseTagsCache = null;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function brain() {
    try {
      return (window.currentBrainPath && window.currentBrainPath()) || "brain";
    } catch (e) {
      return "brain";
    }
  }

  var homeCache = {};
  async function getHome(b) {
    if (homeCache[b] != null) return homeCache[b];
    try {
      var r = await fetch("/files/list?brain=" + encodeURIComponent(b));
      var d = r.ok ? await r.json() : {};
      var h = (d && d.home) || "";
      homeCache[b] = h;
      return h;
    } catch (e) {
      return "";
    }
  }

  function ceilPath(home, brainRel) {
    var rel = String(brainRel || "").replace(/\\/g, "/").replace(/^\.?\//, "").replace(/\/+$/, "");
    var h = String(home || "").replace(/\\/g, "/").replace(/^\.?\//, "").replace(/\/+$/, "");
    if (!h || rel === h || rel.indexOf(h + "/") === 0) return rel;
    return h + "/" + rel;
  }

  function rawUrl(path) {
    return "/files/raw?brain=" + encodeURIComponent(brain()) + "&path=" + encodeURIComponent(path);
  }

  async function fetchFbPages() {
    try {
      var r = await fetch("/connect/facebook/pages");
      var d = r.ok ? await r.json() : {};
      return (d && d.ok && Array.isArray(d.pages)) ? d.pages : [];
    } catch (e) {
      return [];
    }
  }

  async function listPath(path) {
    var home = await getHome(brain());
    var full = ceilPath(home, path);
    var res = await fetch("/files/list?brain=" + encodeURIComponent(brain()) + "&path=" + encodeURIComponent(full));
    var d = await res.json();
    return d.items || [];
  }

  function parseTagTable(md) {
    var tags = [];
    String(md || "").split("\n").forEach(function (line) {
      var m = line.match(/^\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|/);
      if (!m) return;
      var id = m[1].trim();
      var label = m[2].trim();
      if (!id || /^id$/i.test(id) || /^-+$/.test(id.replace(/\s/g, ""))) return;
      tags.push({ id: id, label: label || id });
    });
    return tags;
  }

  function tagRegistryMarkdown(tags) {
    var today = new Date().toISOString().slice(0, 10);
    var rows = (tags || []).map(function (t) {
      return "| " + t.id + " | " + (t.label || t.id) + " |";
    }).join("\n");
    return "---\ntype: wiki\nupdated: " + today + "\n---\n" +
      "# Thẻ khoá học\n\n" +
      "Mỗi thẻ = 1 thư mục `attachments/dataset/<id>/`.\n" +
      "Default kit: `Thẻ khoá học: all`. Page kit liệt kê id, dấu phẩy.\n" +
      "Không có thẻ khớp chủ đề bài → không đăng page đó.\n\n" +
      "| id | Tên |\n| --- | --- |\n" + rows + "\n";
  }

  async function writeTextFile(rel, content) {
    var home = await getHome(brain());
    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", ceilPath(home, rel));
    fd.append("content", content);
    var res = await fetch("/files/write", { method: "POST", body: fd });
    return res.json();
  }

  async function mkdirDataset(name) {
    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", IMG_DIR);
    fd.append("name", name);
    try { await fetch("/files/mkdir", { method: "POST", body: fd }); } catch (e) {}
  }

  async function deleteDataset(name) {
    if (!name || SYSTEM_DIRS[name]) return { ok: false };
    var home = await getHome(brain());
    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", ceilPath(home, IMG_DIR + "/" + name));
    try {
      var res = await fetch("/files/delete", { method: "POST", body: fd });
      return await res.json();
    } catch (e) {
      return { ok: false, error: String(e) };
    }
  }

  function applyCourseTags(tags) {
    COURSE_FOLDERS = tags.slice();
    COURSE_FOLDER_MAP = {};
    tags.forEach(function (t) {
      COURSE_FOLDER_MAP[t.id] = t.label;
      COURSE_FOLDER_MAP[String(t.id).toLowerCase()] = t.label;
    });
    courseTagsCache = tags;
    return tags;
  }

  async function loadCourseTags(force) {
    if (courseTagsCache && !force) return courseTagsCache;
    var tags = [];
    try {
      var home = await getHome(brain());
      var full = ceilPath(home, TAGS_FILE);
      var res = await fetch("/files/read?brain=" + encodeURIComponent(brain()) + "&path=" + encodeURIComponent(full));
      var d = await res.json();
      tags = parseTagTable(d.content || "");
    } catch (e) {}
    var dirs = [];
    try {
      dirs = (await listPath(IMG_DIR)).filter(function (f) {
        return f.type === "dir" && !SYSTEM_DIRS[f.name];
      });
    } catch (e2) {}
    var dirSet = {};
    dirs.forEach(function (f) { dirSet[f.name] = true; });
    var have = {};
    var kept = [];
    tags.forEach(function (t) {
      if (!dirSet[t.id]) return;
      kept.push(t);
      have[t.id] = true;
    });
    dirs.forEach(function (f) {
      if (!have[f.name]) {
        kept.push({ id: f.name, label: f.name });
        have[f.name] = true;
      }
    });
    applyCourseTags(kept);
    if (kept.length !== tags.length) {
      try { await saveCourseTags(kept); } catch (e3) {}
    }
    return courseTagsCache;
  }

  async function saveCourseTags(tags) {
    applyCourseTags(tags);
    await writeTextFile(TAGS_FILE, tagRegistryMarkdown(tags));
  }

  function kitKind(name) {
    if (name.indexOf("_mac-dinh") === 0) return "default";
    if (name.charAt(0) === "_") return "he-thong";
    return "page";
  }

  /* Parse markdown cua mot brand kit page */
  function parsePageKit(content, fileName) {
    var md = content || "";
    var stem = fileName.replace(/\.md$/i, "");
    var out = {
      name: "",
      slug: stem,
      address: "",
      hotline: "",
      strengths: "",
      localAngle: "",
      folder: "",
      folders: [],
      tagsAll: false,
      hashtag: "",
      url: "",
      note: ""
    };

    var mName = md.match(/^[ \t]*[-*][ \t]*Tên Fanpage:[ \t]*(.*)$/m);
    if (mName && mName[1]) {
      out.name = mName[1].trim();
    } else {
      var mHead = md.match(/^# Kit trang(?: test)?:[ \t]*(.*)$/m);
      if (mHead && mHead[1]) out.name = mHead[1].trim();
    }

    var mSlug = md.match(/^[ \t]*[-*][ \t]*slug:[ \t]*(.*)$/m);
    if (mSlug && mSlug[1]) out.slug = mSlug[1].trim();

    var mAddr = md.match(/^[ \t]*[-*][ \t]*Cơ sở \/ địa chỉ[^:]*:[ \t]*(.*)$/m);
    if (mAddr && mAddr[1]) out.address = mAddr[1].trim();

    var mHot = md.match(/^[ \t]*[-*][ \t]*Hotline[^:]*:[ \t]*(.*)$/m);
    if (mHot && mHot[1]) out.hotline = mHot[1].trim();

    var mStr = md.match(/^[ \t]*[-*][ \t]*Khoá thế mạnh[^:]*:[ \t]*(.*)$/m);
    if (mStr && mStr[1]) out.strengths = mStr[1].trim();

    var mLoc = md.match(/^[ \t]*[-*][ \t]*Góc địa phương:[ \t]*(.*)$/m);
    if (mLoc && mLoc[1]) out.localAngle = mLoc[1].trim();

    var mFold = md.match(/^[ \t]*[-*][ \t]*(?:Thẻ khoá học|The khoa hoc|Folder anh[^:]*)[ \t]*:[ \t]*(.*)$/m);
    if (mFold && mFold[1]) {
      var raw = mFold[1].trim();
      if (/^(all|\*|full)$/i.test(raw)) {
        out.tagsAll = true;
        out.folders = [];
      } else {
        var parts = raw.split(/[,;|/]+/).map(function (s) { return s.trim(); }).filter(Boolean);
        out.folders = parts.map(function (id) {
          if (/^ve[\s_-]*ky[\s_-]*thuat$/i.test(id) || id === "VE KY THUAT") return "ve-ky-thuat";
          return id;
        });
        out.folder = parts[0] || "";
      }
    }

    var mHash = md.match(/^[ \t]*[-*][ \t]*Hashtag thêm:[ \t]*(.*)$/m);
    if (mHash && mHash[1]) out.hashtag = mHash[1].trim();

    var mUrl = md.match(/^[ \t]*[-*][ \t]*URL Fanpage:[ \t]*(.*)$/m);
    if (mUrl && mUrl[1]) out.url = mUrl[1].trim();

    var mPid = md.match(/^[ \t]*[-*][ \t]*(?:Page ID|page_id|ID Fanpage|ID Trang)[ \t]*:[ \t]*(.*)$/mi);
    if (mPid && mPid[1]) out.pageId = mPid[1].trim();
    else out.pageId = "";

    var mNote = md.match(/^[ \t]*[-*][ \t]*Ghi chú:[ \t]*(.*)$/m);
    if (mNote && mNote[1]) out.note = mNote[1].trim();

    function idLine(labels, fallback) {
      var i, m;
      for (i = 0; i < labels.length; i++) {
        m = md.match(new RegExp("^[ \\t]*[-*][ \\t]*" + labels[i] + ":[ \\t]*(.*)$", "m"));
        if (m && m[1] && m[1].trim()) return m[1].trim();
      }
      return fallback || "";
    }
    out.colorPrimary = idLine(["Màu chính", "Mau chinh"], "#6C3BFF");
    out.colorSecondary = idLine(["Màu phụ", "Mau phu"], "#00D4FF");
    out.fonts = idLine(["Font"], "Inter, Montserrat");
    out.logoMain = idLine(["Logo chính", "Logo chinh"], "attachments/dataset/chung/thsv-logo-2025.png");
    out.logoWhite = idLine(["Logo trắng", "Logo trang"], "attachments/dataset/chung/thsv-logo-big.png");
    out.logoIcon = idLine(["Icon"], "attachments/dataset/chung/thsv-logo-2025.png");
    out.imageStyle = idLine(["Phong cách hình ảnh", "Phong cach hinh anh"], "công nghệ, tối giản, premium");
    out.voice = idLine(["Tone of voice"], "chuyên nghiệp, trẻ, hiện đại");
    out.layout = idLine(["Quy tắc bố cục", "Quy tac bo cuc"], "logo góc trên, lề an toàn 8%, cover 16:9, không che mặt học viên");
    out.donts = idLine(["Điều không được làm", "Cam"], "đổi màu logo, bóp méo logo, dùng màu ngoài palette");

    return out;
  }

  function cleanPageLabel(rawName, fileName) {
    var stem = fileName.replace(/\.md$/i, "");
    if (stem === "_mac-dinh") return "Brand Kit Mặc Định (Default)";
    if (stem === "_index") return "Muc luc he thong";
    if (stem === "_van-hanh") return "Quy tac van hanh";
    if (stem === "_anh-da-dung") return "Anh da dung khi dang";
    if (stem === "_the-khoa-hoc") return "The khoa hoc";
    if (!rawName) return stem.replace(/^thsv-/, "").replace(/-/g, " ");
    var clean = rawName.split(/\s*\(hoặc/i)[0].trim();
    return clean || rawName;
  }

  function foldDiacritic(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  var FOLDER_KW = {
    "tin-hoc _ai": ["tin hoc", "word", "excel", "van phong", "mos", "powerpoint", "ai ", "chatgpt"],
    "ve-ky-thuat": ["autocad", "cad", "solidworks", "co khi", "ve ky thuat", "noi that", "ve ky thuat"],
    "VE KY THUAT": ["autocad", "cad", "solidworks", "co khi", "ve ky thuat", "noi that"],
    "ke-toan": ["ke toan", "chung tu", "so sach", "thue", "misa"],
    "do-hoa": ["do hoa", "photoshop", "illustrator", "corel"]
  };

  var PLACE_HINT = [
    { re: /vung tau/, angle: "Vung Tau", tag: "#TinHocVungTau" },
    { re: /bien hoa|dong nai/, angle: "Bien Hoa - Dong Nai", tag: "#TinHocBienHoa" },
    { re: /binh duong/, angle: "Binh Duong", tag: "#TinHocBinhDuong" },
    { re: /long thanh/, angle: "Long Thanh", tag: "#TinHocLongThanh" },
    { re: /quan 12|q12/, angle: "Quan 12, TPHCM", tag: "#TinHocQ12" },
    { re: /quan 6|q6/, angle: "Quan 6, TPHCM", tag: "#TinHocQ6" },
    { re: /binh thanh/, angle: "Binh Thanh, TPHCM", tag: "#TinHocBinhThanh" },
    { re: /tan binh/, angle: "Tan Binh, TPHCM", tag: "#TinHocTanBinh" }
  ];

  function guessFoldersFromText(text) {
    var hay = " " + foldDiacritic(text) + " ";
    var hit = [];
    COURSE_FOLDERS.forEach(function (opt) {
      var kws = (FOLDER_KW[opt.id] || []).concat([foldDiacritic(opt.id), foldDiacritic(opt.label)]);
      for (var i = 0; i < kws.length; i++) {
        if (kws[i] && hay.indexOf(kws[i]) >= 0) {
          hit.push(opt.id);
          return;
        }
      }
    });
    return hit;
  }

  function guessPlace(text) {
    var hay = foldDiacritic(text);
    for (var i = 0; i < PLACE_HINT.length; i++) {
      if (PLACE_HINT[i].re.test(hay)) return PLACE_HINT[i];
    }
    return null;
  }

  function parseUsedMap(md) {
    var map = {};
    var cur = null;
    String(md || "").split(/\n/).forEach(function (line) {
      line = line.trim();
      if (line.indexOf("## ") === 0) cur = line.slice(3).trim();
      else if (cur && line.indexOf("- ") === 0) {
        if (!map[cur]) map[cur] = [];
        map[cur].push(line.slice(2).trim().replace(/\\/g, "/"));
      }
    });
    return map;
  }

  function logLine(logEl, actor, text, kind) {
    if (!logEl) return;
    var row = document.createElement("div");
    row.className = "ds-ai-row" + (kind ? " ds-ai-" + kind : "");
    var t = new Date();
    var hh = String(t.getHours()).padStart(2, "0") + ":" + String(t.getMinutes()).padStart(2, "0");
    row.innerHTML =
      '<span class="ds-ai-time">' + hh + "</span>" +
      '<span class="ds-ai-who">' + esc(actor) + "</span>" +
      '<span class="ds-ai-msg">' + esc(text) + "</span>";
    logEl.appendChild(row);
    logEl.scrollTop = logEl.scrollHeight;
  }

  /* Cap nhat markdown dua tren gia tri form, giu nguyen cac phan khac */
  function updatePageKitMarkdown(origMd, formVals) {
    var md = origMd || "";

    function setField(pattern, replacement, insertAfterPat) {
      if (pattern.test(md)) {
        md = md.replace(pattern, replacement);
      } else if (insertAfterPat && insertAfterPat.test(md)) {
        md = md.replace(insertAfterPat, function (m) {
          return m + "\n" + replacement;
        });
      } else {
        md = md + "\n" + replacement;
      }
    }

    if (formVals.name) {
      setField(/^[ \t]*[-*][ \t]*Tên Fanpage:[^\r\n]*/m, "- Tên Fanpage: " + formVals.name, /^## Tuỳ biến trang/m);
      md = md.replace(/^# Kit trang(?: test)?:\s*.*$/m, function (m) {
        if (m.indexOf("test") >= 0) return "# Kit trang test: " + formVals.name;
        return "# Kit trang: " + formVals.name;
      });
    }

    if (formVals.pageId != null) {
      setField(/^[ \t]*[-*][ \t]*(?:Page ID|page_id|ID Fanpage|ID Trang)[ \t]*:[^\r\n]*/mi,
        "- Page ID: " + (formVals.pageId || ""),
        /^[ \t]*[-*][ \t]*slug:[^\r\n]*/m);
    }
    if (formVals.tagsLine != null) {
      setField(/^[ \t]*[-*][ \t]*(?:Thẻ khoá học|The khoa hoc|Folder anh[^:]*)[ \t]*:[^\r\n]*/m,
        "- Thẻ khoá học: " + formVals.tagsLine,
        /^[ \t]*[-*][ \t]*(?:Page ID|slug):[^\r\n]*/m);
    }
    setField(/^[ \t]*[-*][ \t]*Cơ sở \/ địa chỉ[^:]*:[^\r\n]*/m, "- Cơ sở / địa chỉ: " + (formVals.address || ""), /^[ \t]*[-*][ \t]*(?:Page ID|slug|Thẻ khoá học):[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Hotline[^:]*:[^\r\n]*/m, "- Hotline / Zalo: " + (formVals.hotline || ""), /^[ \t]*[-*][ \t]*Cơ sở \/ địa chỉ[^:]*:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Khoá thế mạnh[^:]*:[^\r\n]*/m, "- Khoá thế mạnh của page: " + (formVals.strengths || ""), /^[ \t]*[-*][ \t]*Hotline[^:]*:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Góc địa phương:[^\r\n]*/m, "- Góc địa phương: " + (formVals.localAngle || ""), /^[ \t]*[-*][ \t]*Khoá thế mạnh[^:]*:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Hashtag thêm:[^\r\n]*/m, "- Hashtag thêm: " + (formVals.hashtag || ""), /^[ \t]*[-*][ \t]*Góc địa phương:[^\r\n]*/m);

    if (md.indexOf("## Nhận diện thương hiệu") < 0 && md.indexOf("## Nhan dien thuong hieu") < 0) {
      md = md.replace(/^# .*$/m, function (h) {
        return h + "\n\n## Nhận diện thương hiệu\n- Màu chính: \n- Màu phụ: \n- Font: \n- Logo chính: \n- Logo trắng: \n- Icon: \n- Phong cách hình ảnh: \n- Tone of voice: \n- Quy tắc bố cục: \n- Điều không được làm: ";
      });
    }
    setField(/^[ \t]*[-*][ \t]*Màu chính:[^\r\n]*/m, "- Màu chính: " + (formVals.colorPrimary || ""), /^## Nhận diện thương hiệu/m);
    setField(/^[ \t]*[-*][ \t]*Màu phụ:[^\r\n]*/m, "- Màu phụ: " + (formVals.colorSecondary || ""), /^[ \t]*[-*][ \t]*Màu chính:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Font:[^\r\n]*/m, "- Font: " + (formVals.fonts || ""), /^[ \t]*[-*][ \t]*Màu phụ:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Logo chính:[^\r\n]*/m, "- Logo chính: " + (formVals.logoMain || ""), /^[ \t]*[-*][ \t]*Font:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Logo trắng:[^\r\n]*/m, "- Logo trắng: " + (formVals.logoWhite || ""), /^[ \t]*[-*][ \t]*Logo chính:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Icon:[^\r\n]*/m, "- Icon: " + (formVals.logoIcon || ""), /^[ \t]*[-*][ \t]*Logo trắng:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Phong cách hình ảnh:[^\r\n]*/m, "- Phong cách hình ảnh: " + (formVals.imageStyle || ""), /^[ \t]*[-*][ \t]*Icon:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Tone of voice:[^\r\n]*/m, "- Tone of voice: " + (formVals.voice || ""), /^[ \t]*[-*][ \t]*Phong cách hình ảnh:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Quy tắc bố cục:[^\r\n]*/m, "- Quy tắc bố cục: " + (formVals.layout || ""), /^[ \t]*[-*][ \t]*Tone of voice:[^\r\n]*/m);
    setField(/^[ \t]*[-*][ \t]*Điều không được làm:[^\r\n]*/m, "- Điều không được làm: " + (formVals.donts || ""), /^[ \t]*[-*][ \t]*Quy tắc bố cục:[^\r\n]*/m);
    return md;
  }

  async function render(el) {
    el.innerHTML =
      '<div class="cview-section ds-page">' +
      '<div class="ds-hero">' +
      '<div><h2 class="ds-title">Brand Kit Fanpage</h2>' +
      '<p class="ds-lead">Bộ nhận diện thương hiệu chuẩn (Màu sắc, Font, Logo, Voice, Bố cục) và cấu hình Fanpage.</p></div>' +
      '<div class="ds-tabs" role="tablist">' +
      '<button type="button" class="ds-tab sel" data-tab="kit">Brand kit</button>' +
      '<button type="button" class="ds-tab" data-tab="anh">Thư viện ảnh</button></div></div>' +
      '<div id="dsBody"></div></div>';

    var body = el.querySelector("#dsBody");
    el.querySelectorAll(".ds-tab").forEach(function (t) {
      t.onclick = function () {
        el.querySelectorAll(".ds-tab").forEach(function (x) { x.classList.remove("sel"); });
        t.classList.add("sel");
        if (t.dataset.tab === "anh") renderAnh(body);
        else renderKit(body);
      };
    });
    renderKit(body);
  }

  /* ============================================================
     TAB 1: BRAND KIT (FORM + PREVIEW)
     ============================================================ */
  async function renderKit(body) {
    body.innerHTML = '<p class="dim" style="padding:14px">Đang tải danh sách brand kit…</p>';
    await loadCourseTags(true);
    var rawItems = [];
    try {
      rawItems = (await listPath(KIT_DIR)).filter(function (f) {
        return f.type === "file" && /\.md$/i.test(f.name || "");
      });
    } catch (e) {
      body.innerHTML = '<p style="color:var(--red);padding:14px">Không đọc được thư mục wiki/brand-kits</p>';
      return;
    }

    /* Loai bo kit rac ten hi / hi.md */
    var items = rawItems.filter(function (f) {
      var stem = f.name.replace(/\.md$/i, "").toLowerCase().trim();
      return stem !== "hi" && stem !== "test-hi" && stem !== "thsv-hi";
    });

    /* Doc noi dung de lay thong tin cho tat ca kit */
    var readPromises = items.map(async function (f) {
      try {
        var home = await getHome(brain());
        var full = ceilPath(home, KIT_DIR + "/" + f.name);
        var res = await fetch("/files/read?brain=" + encodeURIComponent(brain()) + "&path=" + encodeURIComponent(full));
        var d = await res.json();
        f.content = d.content || "";
      } catch (err) {
        f.content = "";
      }
      f.parsed = parsePageKit(f.content, f.name);
      f.displayTitle = cleanPageLabel(f.parsed.name, f.name);
      f.kind = kitKind(f.name);
    });
    await Promise.all(readPromises);

    /* Sap xep: Default luon len dau tien -> tiep theo la Page -> cuoi cung la He thong */
    items.sort(function (a, b) {
      if (a.kind === "default" && b.kind !== "default") return -1;
      if (b.kind === "default" && a.kind !== "default") return 1;
      var order = { "default": 0, "page": 1, "he-thong": 2 };
      if (order[a.kind] !== order[b.kind]) return order[a.kind] - order[b.kind];
      return a.displayTitle.localeCompare(b.displayTitle, "vi");
    });

    body.innerHTML =
      '<div class="ds-split">' +
      '<aside class="ds-side">' +
      '<input class="ds-search" id="dsKitQ" placeholder="Tìm Brand Kit, Fanpage, slug…">' +
      '<div class="ds-side-scroll" id="dsKitList"></div>' +
      '<button type="button" class="s-btn ds-new" id="dsNewKit" title="Chọn Fanpage đã kết nối để tạo Brand Kit">Tạo kit từ Fanpage đã kết nối</button>' +
      '</aside>' +
      '<section class="ds-main" id="dsMainPanel">' +
      '<div class="ds-toolbar"><div><div class="ds-kicker" id="dsKitKind"></div>' +
      '<div class="ds-filename" id="dsKitMeta">Chọn kit bên trái</div></div>' +
      '<div class="ds-toolbar-right"><span id="dsKitStatus" class="ds-status-text"></span>' +
      '<button type="button" class="s-btn-ghost ds-btn-clone" id="dsCopyFromDefault" style="display:none" title="Sao chép toàn bộ nhận diện từ Default">Sao chép từ Default</button>' +
      '<button type="button" class="ds-btn-del" id="dsKitDelete" style="display:none" title="Xoá Brand Kit Page này">Xoá Page</button>' +
      '<button type="button" class="s-btn" id="dsKitSave" disabled>Lưu Brand Kit</button></div></div>' +
      '<div id="dsKitContentArea"></div>' +
      '</section></div>';

    var listEl = body.querySelector("#dsKitList");
    var activeItem = null;

    function paintList(q) {
      q = (q || "").toLowerCase().trim();
      listEl.innerHTML = "";

      var groups = [
        { "key": "default", "title": "BRAND KIT MẶC ĐỊNH (DEFAULT)", "items": [] },
        { "key": "page", "title": "Fanpage Chi Nhánh (" + items.filter(function (x) { return x.kind === "page"; }).length + ")", "items": [] },
        { "key": "he-thong", "title": "Tài Liệu Hệ Thống", "items": [] }
      ];

      items.forEach(function (f) {
        if (q) {
          var matchTitle = (f.displayTitle || "").toLowerCase().indexOf(q) >= 0;
          var matchSlug = (f.parsed.slug || f.name).toLowerCase().indexOf(q) >= 0;
          var matchColors = ((f.parsed.colorPrimary || "") + " " + (f.parsed.colorSecondary || "")).toLowerCase().indexOf(q) >= 0;
          if (!matchTitle && !matchSlug && !matchColors) return;
        }
        if (f.kind === "default") groups[0].items.push(f);
        else if (f.kind === "page") groups[1].items.push(f);
        else groups[2].items.push(f);
      });

      var renderedCount = 0;
      groups.forEach(function (grp) {
        if (!grp.items.length) return;
        var hdr = document.createElement("div");
        hdr.className = "ds-group-label";
        hdr.textContent = grp.title;
        listEl.appendChild(hdr);

        grp.items.forEach(function (f) {
          renderedCount++;
          var b = document.createElement("button");
          b.type = "button";
          var isDef = f.kind === "default";
          b.className = "ds-row" + (isDef ? " ds-row-default" : "") + (activeItem && activeItem.name === f.name ? " sel" : "");
          b.dataset.path = KIT_DIR + "/" + f.name;
          b.dataset.name = f.name;

          var badgeText = isDef ? "DEFAULT" : f.kind === "page" ? "Page" : "Hệ";
          var badgeClass = isDef ? "ds-badge ds-badge-default" : ("ds-badge ds-badge-" + f.kind);
          var subText = "";
          if (isDef) {
            subText = (f.parsed.colorPrimary || "#6C3BFF") + ", " + (f.parsed.colorSecondary || "#00D4FF") + " · " + (f.parsed.fonts || "Inter, Montserrat");
          } else if (f.kind === "page") {
            var tagTxt = f.parsed.tagsAll ? "thẻ all" : ((f.parsed.folders || []).length ? (f.parsed.folders.length + " thẻ") : "chưa thẻ");
            subText = (f.parsed.slug || "") + (f.parsed.pageId ? " · ID " + f.parsed.pageId : " · chưa Page ID")
              + " · " + tagTxt;
          } else {
            subText = f.name;
          }

          b.innerHTML =
            '<span class="' + badgeClass + '">' + badgeText + '</span>' +
            '<div class="ds-row-info">' +
            '<div class="ds-row-label">' + esc(f.displayTitle) + '</div>' +
            '<div class="ds-row-sub">' + esc(subText) + '</div>' +
            '</div>';

          b.onclick = function () {
            activeItem = f;
            openKit(body, f, b, items, paintList);
          };
          listEl.appendChild(b);
        });
      });

      if (!renderedCount) {
        listEl.innerHTML = '<div class="ds-empty-sm">Không có Brand Kit nào khớp tìm kiếm</div>';
      }
    }

    paintList("");
    body.querySelector("#dsKitQ").oninput = function () { paintList(this.value); };
    body.querySelector("#dsNewKit").onclick = function () { newKit(body, items, paintList); };

    /* Uu tien chon kit Default dau tien */
    var defBtn = listEl.querySelector('.ds-row[data-name="_mac-dinh.md"]');
    if (defBtn) {
      defBtn.click();
    } else {
      var firstBtn = listEl.querySelector(".ds-row");
      if (firstBtn) firstBtn.click();
    }
  }

  /* Sao chep toan bo nhan dien tu Default sang Page hien tai */
  function copyFromDefault(body, f, items) {
    var def = null;
    for (var i = 0; i < items.length; i++) {
      if (items[i].kind === "default" || items[i].name === "_mac-dinh.md") {
        def = items[i];
        break;
      }
    }
    if (!def || !def.parsed) {
      window.alert("Không tìm thấy Brand Kit mặc định (_mac-dinh.md)!");
      return;
    }
    var dp = def.parsed;
    var area = body.querySelector("#dsKitContentArea");
    if (!area) return;

    function setFieldVal(id, val) {
      var el = area.querySelector("#" + id);
      if (el) el.value = val || "";
    }

    setFieldVal("dsFldColorPri", dp.colorPrimary || "#6C3BFF");
    setFieldVal("dsColorPriPick", cleanHex(dp.colorPrimary, "#6C3BFF"));
    setFieldVal("dsFldColorSec", dp.colorSecondary || "#00D4FF");
    setFieldVal("dsColorSecPick", cleanHex(dp.colorSecondary, "#00D4FF"));
    setFieldVal("dsFldFonts", dp.fonts || "Inter, Montserrat");
    setFieldVal("dsFldLogoMain", dp.logoMain || "attachments/dataset/chung/thsv-logo-2025.png");
    setFieldVal("dsFldLogoWhite", dp.logoWhite || "attachments/dataset/chung/thsv-logo-big.png");
    setFieldVal("dsFldLogoIcon", dp.logoIcon || "attachments/dataset/chung/thsv-logo-2025.png");
    setFieldVal("dsFldImageStyle", dp.imageStyle || "công nghệ, tối giản, premium");
    setFieldVal("dsFldVoice", dp.voice || "chuyên nghiệp, trẻ, hiện đại");
    setFieldVal("dsFldLayout", dp.layout || "logo góc trên, lề an toàn 8%, cover 16:9, không che mặt học viên");
    setFieldVal("dsFldDonts", dp.donts || "đổi màu logo, bóp méo logo, dùng màu ngoài palette");

    /* Cap nhat logo thumbnails */
    var mThumb = area.querySelector("#dsThumbMain");
    if (mThumb) mThumb.innerHTML = '<img src="' + esc(rawUrl(dp.logoMain || "attachments/dataset/chung/thsv-logo-2025.png")) + '" alt="Logo chính">';
    var wThumb = area.querySelector("#dsThumbWhite");
    if (wThumb) wThumb.innerHTML = '<img src="' + esc(rawUrl(dp.logoWhite || "attachments/dataset/chung/thsv-logo-big.png")) + '" alt="Logo trắng">';
    var iThumb = area.querySelector("#dsThumbIcon");
    if (iThumb) iThumb.innerHTML = '<img src="' + esc(rawUrl(dp.logoIcon || "attachments/dataset/chung/thsv-logo-2025.png")) + '" alt="Icon">';

    /* Cap nhat gradient preview */
    var grad = area.querySelector("#dsColorGradientBar");
    if (grad) {
      grad.style.background = "linear-gradient(135deg, " + cleanHex(dp.colorPrimary, "#6C3BFF") + ", " + cleanHex(dp.colorSecondary, "#00D4FF") + ")";
    }

    var ta = area.querySelector("#dsKitText");
    var nameInp = area.querySelector("#dsFldPageName");
    var idInp = area.querySelector("#dsFldPageId");
    var ten = (nameInp && nameInp.value.trim()) || f.displayTitle || "";
    var pageId = (idInp && idInp.value.trim()) || (f.parsed && f.parsed.pageId) || "";
    var slug = (f.parsed && f.parsed.slug) || String(f.name || "").replace(/\.md$/i, "");
    if (ta) {
      var tagsLine = "all";
      if (f.kind !== "default") {
        var ids = [];
        area.querySelectorAll("#dsTagList input[data-tag]").forEach(function (c) {
          if (c.checked) ids.push(c.getAttribute("data-tag"));
        });
        tagsLine = ids.join(", ");
      }
      ta.value = cloneDefaultMarkdown(def.content || "", { ten: ten, slug: slug, pageId: pageId, tagsLine: tagsLine });
    }

    var st = body.querySelector("#dsKitStatus");
    if (st) {
      st.textContent = "Đã copy TOÀN BỘ markdown Default (pháp nhân, khóa học, cấm, chân trang…). Bấm Lưu Brand Kit.";
      st.className = "ds-status-text ds-ok";
      setTimeout(function () {
        if (st.textContent.indexOf("Đã copy TOÀN BỘ") >= 0) st.textContent = "";
      }, 5000);
    }
  }

  function cleanHex(c, fallback) {
    if (!c) return fallback;
    var s = c.trim();
    if (/^#[0-9A-Fa-f]{6}$/.test(s)) return s;
    if (/^[0-9A-Fa-f]{6}$/.test(s)) return "#" + s;
    return fallback;
  }

  /* Mo va hien thi form hoac editor cho mot kit */
  async function openKit(body, f, btn, items, paintList) {
    body.querySelectorAll(".ds-row").forEach(function (x) { x.classList.remove("sel"); });
    if (btn) btn.classList.add("sel");

    var path = KIT_DIR + "/" + f.name;
    var kind = f.kind;
    body.querySelector("#dsKitKind").textContent =
      kind === "default" ? "BRAND KIT MẶC ĐỊNH (GỐC TOÀN HỆ THỐNG)" :
      kind === "page" ? ("BRAND KIT FANPAGE: " + f.displayTitle.toUpperCase()) : "TÀI LIỆU HỆ THỐNG";
    body.querySelector("#dsKitMeta").textContent = path;

    var save = body.querySelector("#dsKitSave");
    var st = body.querySelector("#dsKitStatus");
    var area = body.querySelector("#dsKitContentArea");
    var btnCopy = body.querySelector("#dsCopyFromDefault");
    var btnDel = body.querySelector("#dsKitDelete");

    if (btnCopy) {
      if (kind === "page") {
        btnCopy.style.display = "inline-flex";
        btnCopy.onclick = function () {
          copyFromDefault(body, f, items);
        };
      } else {
        btnCopy.style.display = "none";
      }
    }

    if (btnDel) {
      if (kind === "page") {
        btnDel.style.display = "inline-flex";
        btnDel.disabled = false;
        btnDel.onclick = function () {
          deletePageKit(body, f, items, paintList);
        };
      } else {
        btnDel.style.display = "none";
      }
    }

    save.disabled = true;
    st.textContent = "Đang đọc…";
    st.className = "ds-status-text dim";

    /* Doc noi dung moi nhat tu server */
    try {
      var home = await getHome(brain());
      var full = ceilPath(home, path);
      var res = await fetch("/files/read?brain=" + encodeURIComponent(brain()) + "&path=" + encodeURIComponent(full));
      var d = await res.json();
      if (d.error) {
        st.textContent = d.error;
        st.className = "ds-status-text ds-err";
        return;
      }
      f.content = d.content || "";
      f.parsed = parsePageKit(f.content, f.name);
      f.displayTitle = cleanPageLabel(f.parsed.name, f.name);
      st.textContent = "";
    } catch (e) {
      st.textContent = "Không đọc được file";
      st.className = "ds-status-text ds-err";
      return;
    }

    save.disabled = false;
    if (kind === "page" || kind === "default") {
      await loadCourseTags();
      renderPageForm(body, f, items);
      save.onclick = function () { savePageKit(body, f, items); };
    } else {
      area.innerHTML =
        '<div class="ds-md-box">' +
        '<div class="ds-md-box-head">' +
        '<div class="ds-md-box-title">' + esc(f.displayTitle) + '</div>' +
        '<div class="ds-md-box-sub">' + esc(path) + '</div>' +
        '</div>' +
        '<textarea id="dsKitText" class="ds-md-editor" spellcheck="false" placeholder="Nội dung markdown kit…">' + esc(f.content) + '</textarea>' +
        '</div>';
      save.onclick = function () { saveRawKit(body, f); };
    }
  }

  /* Render form Brand Kit (tap trung 100% vao nhan dien thuong hieu + markdown truc tiep ben duoi) */
  function renderPageForm(body, f, items) {
    var p = f.parsed;
    var isDefault = f.kind === "default";
    var area = body.querySelector("#dsKitContentArea");

    var colorPri = p.colorPrimary || "#6C3BFF";
    var colorSec = p.colorSecondary || "#00D4FF";
    var fonts = p.fonts || "Inter, Montserrat";
    var logoMain = p.logoMain || "attachments/dataset/chung/thsv-logo-2025.png";
    var logoWhite = p.logoWhite || "attachments/dataset/chung/thsv-logo-big.png";
    var logoIcon = p.logoIcon || "attachments/dataset/chung/thsv-logo-2025.png";
    var imageStyle = p.imageStyle || "công nghệ, tối giản, premium";
    var voice = p.voice || "chuyên nghiệp, trẻ, hiện đại";
    var layout = p.layout || "logo góc trên, lề an toàn 8%, cover 16:9, không che mặt học viên";
    var donts = p.donts || "đổi màu logo, bóp méo logo, dùng màu ngoài palette";

    var defaultBannerHtml = isDefault
      ? '<div class="ds-default-banner"><b>Brand Kit Mặc Định:</b> Chứa bộ nhận diện chuẩn toàn hệ thống. Mọi Fanpage mới tạo hoặc bấm "Sao chép từ Default" sẽ kế thừa 100% cài đặt từ file này.</div>'
      : '';

    var pageId = p.pageId || "";
    var pageName = p.name || f.displayTitle || "";
    var pageSlug = p.slug || f.name.replace(/\.md$/i, "");
    var fbCard = isDefault ? "" :
      '<div class="ds-section-card">' +
      '<div class="ds-section-head">' +
      '<div class="ds-section-title">Fanpage Facebook (để đăng bài)</div>' +
      '<div class="ds-section-sub">Chọn Trang đã tick lúc kết nối Graph API — Javis dùng Page ID này khi đăng, không dùng slug</div>' +
      '</div>' +
      '<div class="ds-field" style="margin-bottom:10px">' +
      '<label class="ds-label" for="dsFldFbPick">Trang đã kết nối</label>' +
      '<select class="ds-input" id="dsFldFbPick"><option value="">Đang tải danh sách Trang…</option></select>' +
      '</div>' +
      '<div class="ds-form-row">' +
      '<div class="ds-field">' +
      '<label class="ds-label" for="dsFldPageName">Tên Fanpage</label>' +
      '<input type="text" class="ds-input" id="dsFldPageName" value="' + esc(pageName) + '" placeholder="Ví dụ: Royce Shop">' +
      '</div>' +
      '<div class="ds-field">' +
      '<label class="ds-label" for="dsFldPageId">Page ID</label>' +
      '<input type="text" class="ds-input" id="dsFldPageId" value="' + esc(pageId) + '" placeholder="Số ID, ví dụ 988656934325292" inputmode="numeric">' +
      '</div>' +
      '</div>' +
      '<div class="ds-field" style="margin-top:8px">' +
      '<label class="ds-label">Slug (tên file kit, không phải ID Facebook)</label>' +
      '<input type="text" class="ds-input" value="' + esc(pageSlug) + '" disabled>' +
      '</div>' +
      '</div>';

    var tags = COURSE_FOLDERS.slice();
    var selected = {};
    if (isDefault || p.tagsAll) {
      tags.forEach(function (t) { selected[t.id] = true; });
    } else {
      (p.folders || []).forEach(function (id) { selected[id] = true; });
    }
    var tagCard =
      '<div class="ds-section-card">' +
      '<div class="ds-section-head">' +
      '<div class="ds-section-title">Thẻ khoá học</div>' +
      '<div class="ds-section-sub">' +
      (isDefault
        ? "Default = FULL mọi thẻ. Thẻ mới thêm tự có trên Default. 1 ngày 1 bài: chỉ page có thẻ khớp mới được đăng."
        : "Tick ngành page này được đăng. Page đồ họa không nhận bài kế toán. Không thẻ → không đăng.") +
      "</div></div>" +
      (isDefault
        ? '<div class="ds-notice ds-notice-info" style="margin-bottom:10px">Default đang ở chế độ <b>all</b> — không bỏ thẻ từng cái. Dùng <b>Thêm thẻ</b> khi có khoá mới.</div>'
        : "") +
      '<div class="ds-tag-list" id="dsTagList">' +
      tags.map(function (t) {
        var on = !!selected[t.id];
        return '<label class="ds-tag' + (on ? " on" : "") + '">' +
          '<input type="checkbox" data-tag="' + esc(t.id) + '"' + (on ? " checked" : "") +
          (isDefault ? " disabled" : "") + ">" +
          esc(t.label) + " <span class=\"ds-tag-id\">" + esc(t.id) + "</span>" +
          '<button type="button" class="ds-tag-x" data-del-tag="' + esc(t.id) + '" title="Xoá thẻ và thư mục ảnh">×</button></label>';
      }).join("") +
      "</div>" +
      '<div class="ds-tag-add">' +
      '<input type="text" class="ds-input" id="dsNewTagName" placeholder="Thẻ mới, vd: Marketing">' +
      '<button type="button" class="s-btn-ghost" id="dsAddTag">Thêm thẻ</button>' +
      "</div></div>";

    area.innerHTML =
      '<div class="ds-form">' +
      defaultBannerHtml +
      fbCard +
      tagCard +

      /* CARD 1: MÀU THƯƠNG HIỆU & PHÔNG CHỮ */
      '<div class="ds-section-card">' +
      '<div class="ds-section-head">' +
      '<div class="ds-section-title">Màu thương hiệu &amp; Phông chữ</div>' +
      '<div class="ds-section-sub">Bảng màu và font chuẩn cho tiêu đề, nội dung, poster</div>' +
      '</div>' +
      '<div class="ds-color-grid">' +
      '<div class="ds-color-item">' +
      '<label class="ds-label" for="dsFldColorPri">Màu chính (Primary Color)</label>' +
      '<div class="ds-color-wrap">' +
      '<input type="color" class="ds-color-picker" id="dsColorPriPick" value="' + esc(cleanHex(colorPri, "#6C3BFF")) + '">' +
      '<input type="text" class="ds-input ds-color-hex" id="dsFldColorPri" value="' + esc(colorPri) + '" placeholder="Ví dụ: #6C3BFF">' +
      '</div>' +
      '</div>' +
      '<div class="ds-color-item">' +
      '<label class="ds-label" for="dsFldColorSec">Màu phụ (Secondary Color)</label>' +
      '<div class="ds-color-wrap">' +
      '<input type="color" class="ds-color-picker" id="dsColorSecPick" value="' + esc(cleanHex(colorSec, "#00D4FF")) + '">' +
      '<input type="text" class="ds-input ds-color-hex" id="dsFldColorSec" value="' + esc(colorSec) + '" placeholder="Ví dụ: #00D4FF">' +
      '</div>' +
      '</div>' +
      '</div>' +
      '<div class="ds-gradient-preview" id="dsColorGradientBar" style="background:linear-gradient(135deg,' + esc(cleanHex(colorPri, "#6C3BFF")) + ',' + esc(cleanHex(colorSec, "#00D4FF")) + ')"></div>' +
      '<div class="ds-field" style="margin-top:6px">' +
      '<label class="ds-label" for="dsFldFonts">Font thương hiệu (Tiêu đề & Nội dung)</label>' +
      '<input type="text" class="ds-input" id="dsFldFonts" value="' + esc(fonts) + '" placeholder="Ví dụ: Inter, Montserrat, Be Vietnam Pro">' +
      '</div>' +
      '</div>' +

      /* CARD 2: TÀI SẢN LOGO */
      '<div class="ds-section-card">' +
      '<div class="ds-section-head">' +
      '<div class="ds-section-title">Tài sản Logo</div>' +
      '<div class="ds-section-sub">Đường dẫn tệp và xem trước các phiên bản logo chính thống</div>' +
      '</div>' +
      '<div class="ds-logo-grid">' +
      /* Slot 1: Logo chinh */
      '<div class="ds-logo-card">' +
      '<div class="ds-logo-label">Logo chính</div>' +
      '<div class="ds-logo-thumb" id="dsThumbMain"><img src="' + esc(rawUrl(logoMain)) + '" alt="Logo chính" onerror="this.parentNode.innerHTML=\'<span class=\\\'ds-logo-thumb-empty\\\'>Chưa có ảnh</span>\'"></div>' +
      '<input type="text" class="ds-input ds-logo-input" id="dsFldLogoMain" value="' + esc(logoMain) + '" placeholder="Ví dụ: attachments/dataset/chung/...">' +
      '</div>' +
      /* Slot 2: Logo trang am ban */
      '<div class="ds-logo-card">' +
      '<div class="ds-logo-label">Logo trắng (Âm bản)</div>' +
      '<div class="ds-logo-thumb dark-bg" id="dsThumbWhite"><img src="' + esc(rawUrl(logoWhite)) + '" alt="Logo trắng" onerror="this.parentNode.innerHTML=\'<span class=\\\'ds-logo-thumb-empty\\\'>Chưa có ảnh</span>\'"></div>' +
      '<input type="text" class="ds-input ds-logo-input" id="dsFldLogoWhite" value="' + esc(logoWhite) + '" placeholder="Ví dụ: attachments/dataset/chung/...">' +
      '</div>' +
      /* Slot 3: Icon / Watermark */
      '<div class="ds-logo-card">' +
      '<div class="ds-logo-label">Icon / Watermark</div>' +
      '<div class="ds-logo-thumb" id="dsThumbIcon"><img src="' + esc(rawUrl(logoIcon)) + '" alt="Icon" onerror="this.parentNode.innerHTML=\'<span class=\\\'ds-logo-thumb-empty\\\'>Chưa có ảnh</span>\'"></div>' +
      '<input type="text" class="ds-input ds-logo-input" id="dsFldLogoIcon" value="' + esc(logoIcon) + '" placeholder="Ví dụ: attachments/dataset/chung/...">' +
      '</div>' +
      '</div>' +
      '</div>' +

      /* CARD 3: PHONG CÁCH HÌNH ẢNH & QUY TẮC BỐ CỤC */
      '<div class="ds-section-card">' +
      '<div class="ds-section-head">' +
      '<div class="ds-section-title">Phong cách hình ảnh &amp; Quy tắc bố cục</div>' +
      '<div class="ds-section-sub">Định hướng phong cách thị giác và vị trí căn chỉnh khi sinh ảnh</div>' +
      '</div>' +
      '<div class="ds-form-row">' +
      '<div class="ds-field">' +
      '<label class="ds-label" for="dsFldImageStyle">Phong cách hình ảnh</label>' +
      '<input type="text" class="ds-input" id="dsFldImageStyle" value="' + esc(imageStyle) + '" placeholder="Ví dụ: Công nghệ, tối giản, premium, học viên thực tế">' +
      '</div>' +
      '<div class="ds-field">' +
      '<label class="ds-label" for="dsFldLayout">Quy tắc bố cục</label>' +
      '<input type="text" class="ds-input" id="dsFldLayout" value="' + esc(layout) + '" placeholder="Ví dụ: Logo góc trên, lề an toàn 8%, cover 16:9">' +
      '</div>' +
      '</div>' +
      '</div>' +

      /* CARD 4: TONE OF VOICE & ĐIỀU CẤM KỴ */
      '<div class="ds-section-card">' +
      '<div class="ds-section-head">' +
      '<div class="ds-section-title">Tone of Voice &amp; Điều không được làm</div>' +
      '<div class="ds-section-sub">Giọng văn khi viết caption và các rào chắn tuyệt đối cấm vi phạm</div>' +
      '</div>' +
      '<div class="ds-form-row">' +
      '<div class="ds-field">' +
      '<label class="ds-label" for="dsFldVoice">Tone of voice (Giọng điệu bài viết)</label>' +
      '<textarea class="ds-input ds-textarea-sm" id="dsFldVoice" rows="2" placeholder="Ví dụ: Chuyên nghiệp, trẻ, hiện đại, thực chiến, đồng cảm">' + esc(voice) + '</textarea>' +
      '</div>' +
      '<div class="ds-field">' +
      '<label class="ds-label" for="dsFldDonts" style="color:var(--red,#ef4444)">Điều không được làm (Brand Don\'ts)</label>' +
      '<textarea class="ds-input ds-textarea-sm" id="dsFldDonts" rows="2" placeholder="Ví dụ: Đổi màu logo, bóp méo logo, dùng màu ngoài palette">' + esc(donts) + '</textarea>' +
      '</div>' +
      '</div>' +
      '</div>' +

      /* CARD 5: MARKDOWN CONTENT TRỰC TIẾP BÊN DƯỚI */
      '<div class="ds-md-box">' +
      '<div class="ds-md-box-head">' +
      '<div class="ds-md-box-title">Nội dung Markdown Brand Kit</div>' +
      '<div class="ds-md-box-sub">Tự động đồng bộ với các trường ở trên. Bạn có thể sửa trực tiếp Markdown hoặc thêm quy tắc riêng tại đây:</div>' +
      '</div>' +
      '<textarea id="dsKitText" class="ds-md-editor" spellcheck="false">' + esc(f.content) + '</textarea>' +
      '</div>' +

      '</div>';

    var ta = area.querySelector("#dsKitText");
    var pPick = area.querySelector("#dsColorPriPick");
    var pHex = area.querySelector("#dsFldColorPri");
    var sPick = area.querySelector("#dsColorSecPick");
    var sHex = area.querySelector("#dsFldColorSec");
    var gradBar = area.querySelector("#dsColorGradientBar");

    function updateGradient() {
      if (gradBar && pHex && sHex) {
        gradBar.style.background = "linear-gradient(135deg, " + cleanHex(pHex.value, "#6C3BFF") + ", " + cleanHex(sHex.value, "#00D4FF") + ")";
      }
    }

    function getFormVals() {
      return {
        name: (area.querySelector("#dsFldPageName") || {}).value || "",
        pageId: (area.querySelector("#dsFldPageId") || {}).value || "",
        tagsLine: (function () {
          if (f.kind === "default") return "all";
          var ids = [];
          area.querySelectorAll("#dsTagList input[data-tag]").forEach(function (c) {
            if (c.checked) ids.push(c.getAttribute("data-tag"));
          });
          return ids.join(", ");
        })(),
        colorPrimary: (area.querySelector("#dsFldColorPri") || {}).value || "",
        colorSecondary: (area.querySelector("#dsFldColorSec") || {}).value || "",
        fonts: (area.querySelector("#dsFldFonts") || {}).value || "",
        logoMain: (area.querySelector("#dsFldLogoMain") || {}).value || "",
        logoWhite: (area.querySelector("#dsFldLogoWhite") || {}).value || "",
        logoIcon: (area.querySelector("#dsFldLogoIcon") || {}).value || "",
        imageStyle: (area.querySelector("#dsFldImageStyle") || {}).value || "",
        voice: (area.querySelector("#dsFldVoice") || {}).value || "",
        layout: (area.querySelector("#dsFldLayout") || {}).value || "",
        donts: (area.querySelector("#dsFldDonts") || {}).value || ""
      };
    }

    function syncFormToMarkdown() {
      if (!ta) return;
      var vals = getFormVals();
      var newMd = updatePageKitMarkdown(ta.value, vals);
      ta.value = newMd;
      updateGradient();
    }

    if (pPick && pHex) {
      pPick.oninput = function () {
        pHex.value = this.value.toUpperCase();
        syncFormToMarkdown();
      };
      pHex.oninput = function () {
        var v = this.value.trim();
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) pPick.value = v;
        syncFormToMarkdown();
      };
    }
    if (sPick && sHex) {
      sPick.oninput = function () {
        sHex.value = this.value.toUpperCase();
        syncFormToMarkdown();
      };
      sHex.oninput = function () {
        var v = this.value.trim();
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) sPick.value = v;
        syncFormToMarkdown();
      };
    }

    function bindSyncInput(id) {
      var el = area.querySelector("#" + id);
      if (el) {
        el.oninput = function () { syncFormToMarkdown(); };
      }
    }
    bindSyncInput("dsFldFonts");
    bindSyncInput("dsFldImageStyle");
    bindSyncInput("dsFldLayout");
    bindSyncInput("dsFldVoice");
    bindSyncInput("dsFldDonts");
    bindSyncInput("dsFldPageName");
    bindSyncInput("dsFldPageId");
    area.querySelectorAll("#dsTagList input[data-tag]").forEach(function (c) {
      c.onchange = function () {
        var lab = c.closest(".ds-tag");
        if (lab) lab.classList.toggle("on", c.checked);
        syncFormToMarkdown();
      };
    });
    var addTagBtn = area.querySelector("#dsAddTag");
    if (addTagBtn) {
      addTagBtn.onclick = async function () {
        var inp = area.querySelector("#dsNewTagName");
        var label = ((inp && inp.value) || "").trim();
        if (!label) {
          window.alert("Nhập tên thẻ (vd: Marketing). Sẽ tạo folder attachments/dataset/<id>/ và ghi vào _the-khoa-hoc.md");
          return;
        }
        var id = slugFromPageName(label).replace(/-/g, "-");
        if (!id) id = "the-" + Date.now();
        var exists = COURSE_FOLDERS.some(function (t) {
          return t.id === id || foldDiacritic(t.label) === foldDiacritic(label);
        });
        if (exists) {
          window.alert("Thẻ này đã có.");
          return;
        }
        addTagBtn.disabled = true;
        await mkdirDataset(id);
        var next = COURSE_FOLDERS.concat([{ id: id, label: label }]);
        await saveCourseTags(next);
        if (inp) inp.value = "";
        addTagBtn.disabled = false;
        renderPageForm(body, f, items);
        var st2 = body.querySelector("#dsKitStatus");
        if (st2) {
          st2.textContent = "Đã thêm thẻ \"" + label + "\" → folder " + IMG_DIR + "/" + id + ". Default (all) tự có thẻ này. Lưu kit page nếu cần tick thẻ.";
          st2.className = "ds-status-text ds-ok";
        }
      };
    }
    area.querySelectorAll("[data-del-tag]").forEach(function (xbtn) {
      xbtn.onclick = async function (e) {
        e.preventDefault();
        e.stopPropagation();
        var id = xbtn.getAttribute("data-del-tag");
        if (!id || SYSTEM_DIRS[id]) return;
        if (!window.confirm('Xoá thẻ "' + id + '"?\nSẽ xoá thư mục ' + IMG_DIR + "/" + id + " và gỡ thẻ khỏi danh sách. Ảnh trong folder (nếu còn) cũng mất.")) return;
        xbtn.disabled = true;
        await deleteDataset(id);
        var next = COURSE_FOLDERS.filter(function (t) { return t.id !== id; });
        await saveCourseTags(next);
        courseTagsCache = next;
        renderPageForm(body, f, items);
        var st3 = body.querySelector("#dsKitStatus");
        if (st3) {
          st3.textContent = "Đã xoá thẻ " + id + ".";
          st3.className = "ds-status-text ds-ok";
        }
      };
    });

    var pick = area.querySelector("#dsFldFbPick");
    var idInp = area.querySelector("#dsFldPageId");
    var nameInp = area.querySelector("#dsFldPageName");
    if (pick) {
      fetchFbPages().then(function (pages) {
        if (!pick.parentNode) return;
        if (!pages.length) {
          pick.innerHTML = '<option value="">Chưa có Trang — vào Kết nối Facebook, tick Trang rồi mở lại kit</option>';
          return;
        }
        var cur = (idInp && idInp.value) ? String(idInp.value).trim() : "";
        pick.innerHTML = '<option value="">— Chọn Trang đã kết nối —</option>' +
          pages.map(function (pg) {
            var sel = String(pg.id) === cur ? " selected" : "";
            return '<option value="' + esc(pg.id) + '" data-name="' + esc(pg.name) + '"' + sel + ">"
              + esc(pg.name) + " · " + esc(pg.id) + "</option>";
          }).join("");
      });
      pick.onchange = function () {
        var opt = pick.options[pick.selectedIndex];
        if (!opt || !opt.value) return;
        if (idInp) idInp.value = opt.value;
        if (nameInp && opt.getAttribute("data-name")) nameInp.value = opt.getAttribute("data-name");
        syncFormToMarkdown();
      };
    }

    function syncLogo(inputSel, thumbSel) {
      var inp = area.querySelector(inputSel);
      var box = area.querySelector(thumbSel);
      if (!inp || !box) return;
      inp.oninput = function () {
        var val = this.value.trim();
        if (val) {
          box.innerHTML = '<img src="' + esc(rawUrl(val)) + '" alt="" onerror="this.parentNode.innerHTML=\'<span class=\\\'ds-logo-thumb-empty\\\'>Chưa có ảnh</span>\'">';
        } else {
          box.innerHTML = '<span class="ds-logo-thumb-empty">Chưa có ảnh</span>';
        }
        syncFormToMarkdown();
      };
    }
    syncLogo("#dsFldLogoMain", "#dsThumbMain");
    syncLogo("#dsFldLogoWhite", "#dsThumbWhite");
    syncLogo("#dsFldLogoIcon", "#dsThumbIcon");
  }

  /* Luu thong tin Brand Kit tu Form / Markdown */
  async function savePageKit(body, f, items) {
    var area = body.querySelector("#dsKitContentArea");
    var st = body.querySelector("#dsKitStatus");
    var save = body.querySelector("#dsKitSave");

    var ta = area.querySelector("#dsKitText");
    var contentToSave = (ta && ta.value) ? ta.value : f.content;

    st.textContent = "Đang lưu…";
    st.className = "ds-status-text dim";
    save.disabled = true;

    var path = KIT_DIR + "/" + f.name;
    var home = await getHome(brain());
    var ceil = ceilPath(home, path);
    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", ceil);
    fd.append("content", contentToSave);

    try {
      var res = await fetch("/files/write", { method: "POST", body: fd });
      var d = await res.json();
      if (d.ok) {
        f.content = contentToSave;
        f.parsed = parsePageKit(contentToSave, f.name);
        f.displayTitle = cleanPageLabel(f.parsed.name, f.name);

        /* Cap nhat lai nhan o cot trai */
        var rowBtn = body.querySelector('.ds-row[data-name="' + f.name + '"]');
        if (rowBtn) {
          var lbl = rowBtn.querySelector(".ds-row-label");
          if (lbl) lbl.textContent = f.displayTitle;
          var sub = rowBtn.querySelector(".ds-row-sub");
          if (sub) {
            if (f.kind === "default") {
              sub.textContent = (f.parsed.colorPrimary || "#6C3BFF") + ", " + (f.parsed.colorSecondary || "#00D4FF") + " · " + (f.parsed.fonts || "Inter, Montserrat");
            } else {
              sub.textContent = (f.parsed.slug || "") + (f.parsed.pageId ? " · ID " + f.parsed.pageId : " · chưa có Page ID")
                + " · " + (f.parsed.colorPrimary || "#6C3BFF") + ", " + (f.parsed.colorSecondary || "#00D4FF");
            }
          }
        }

        st.textContent = "Đã lưu Brand Kit thành công!";
        st.className = "ds-status-text ds-ok";
        setTimeout(function () {
          if (st.textContent === "Đã lưu Brand Kit thành công!") st.textContent = "";
        }, 3000);
      } else {
        st.textContent = d.error || "Lưu thất bại";
        st.className = "ds-status-text ds-err";
      }
    } catch (e) {
      st.textContent = "Lỗi kết nối khi lưu";
      st.className = "ds-status-text ds-err";
    } finally {
      save.disabled = false;
    }
  }

  /* Luu kit he thong (tu textarea markdown) */
  async function saveRawKit(body, f) {
    var ta = body.querySelector("#dsKitText");
    if (!ta) return;
    var val = ta.value;
    var save = body.querySelector("#dsKitSave");
    var st = body.querySelector("#dsKitStatus");
    save.disabled = true;
    st.textContent = "Đang lưu…";
    st.className = "ds-status-text dim";

    var path = KIT_DIR + "/" + f.name;
    var home = await getHome(brain());
    var ceil = ceilPath(home, path);
    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", ceil);
    fd.append("content", val);
    try {
      var res = await fetch("/files/write", { method: "POST", body: fd });
      var d = await res.json();
      if (d.ok) {
        f.content = val;
        f.parsed = parsePageKit(val, f.name);
        st.textContent = "Đã lưu thành công!";
        st.className = "ds-status-text ds-ok";
        setTimeout(function () {
          if (st.textContent === "Đã lưu thành công!") st.textContent = "";
        }, 3000);
      } else {
        st.textContent = d.error || "Lưu thất bại";
        st.className = "ds-status-text ds-err";
      }
    } catch (e) {
      st.textContent = "Lỗi kết nối khi lưu";
      st.className = "ds-status-text ds-err";
    } finally {
      save.disabled = false;
    }
  }

  /* Xoá Brand Kit Page (chỉ áp dụng cho Fanpage kit, bảo vệ Default và Hệ thống) */
  async function deletePageKit(body, f, items, paintList) {
    if (f.kind !== "page") {
      window.alert("Chỉ có thể xoá Brand Kit của Fanpage. Brand Kit Mặc Định và tài liệu hệ thống được bảo vệ an toàn.");
      return;
    }
    var pageTitle = f.displayTitle || f.name;
    var confirmMsg = 'Bạn có chắc chắn muốn xoá Brand Kit "' + pageTitle + '" không?\n\nFile sẽ bị xoá vĩnh viễn: ' + KIT_DIR + '/' + f.name + '\nThao tác này không thể hoàn tác.';
    if (!window.confirm(confirmMsg)) return;

    var st = body.querySelector("#dsKitStatus");
    var delBtn = body.querySelector("#dsKitDelete");
    var saveBtn = body.querySelector("#dsKitSave");
    if (st) {
      st.textContent = "Đang xoá…";
      st.className = "ds-status-text dim";
    }
    if (delBtn) delBtn.disabled = true;
    if (saveBtn) saveBtn.disabled = true;

    try {
      var path = KIT_DIR + "/" + f.name;
      var home = await getHome(brain());
      var ceil = ceilPath(home, path);
      var fd = new FormData();
      fd.append("brain", brain());
      fd.append("path", ceil);

      var res = await fetch("/files/delete", { method: "POST", body: fd });
      var d = await res.json();
      if (d.ok) {
        /* Xoá liên kết trong _index.md nếu có */
        try {
          var stem = f.name.replace(/\.md$/i, "");
          var idxPath = ceilPath(home, "wiki/brand-kits/_index.md");
          var idxRes = await fetch("/files/read?brain=" + encodeURIComponent(brain()) + "&path=" + encodeURIComponent(idxPath));
          var idxData = await idxRes.json();
          if (idxData && idxData.content) {
            var lines = idxData.content.split(/\r?\n/).filter(function (l) {
              return l.indexOf("brand-kits/" + stem) < 0;
            });
            var idxFd = new FormData();
            idxFd.append("brain", brain());
            idxFd.append("path", idxPath);
            idxFd.append("content", lines.join("\n"));
            await fetch("/files/write", { method: "POST", body: idxFd });
          }
        } catch (idxErr) {
          console.warn("[brand-kits] Cập nhật _index.md khi xoá:", idxErr);
        }

        /* Xoá khỏi mảng items local */
        var idx = items.indexOf(f);
        if (idx >= 0) items.splice(idx, 1);

        if (paintList) {
          var q = body.querySelector("#dsKitQ") ? body.querySelector("#dsKitQ").value : "";
          paintList(q);
        }

        /* Tự động chọn lại kit Default */
        var listEl = body.querySelector("#dsKitList");
        var defBtn = listEl ? (listEl.querySelector('.ds-row[data-name="_mac-dinh.md"]') || listEl.querySelector(".ds-row")) : null;
        if (defBtn) {
          defBtn.click();
        } else {
          var area = body.querySelector("#dsKitContentArea");
          if (area) area.innerHTML = '<div class="ds-empty-sm" style="padding:40px;text-align:center">Đã xoá Brand Kit thành công.</div>';
        }
      } else {
        if (st) {
          st.textContent = d.error || "Xoá thất bại";
          st.className = "ds-status-text ds-err";
        }
        window.alert(d.error || "Xoá Brand Kit thất bại.");
        if (delBtn) delBtn.disabled = false;
        if (saveBtn) saveBtn.disabled = false;
      }
    } catch (e) {
      if (st) {
        st.textContent = "Lỗi mạng khi xoá";
        st.className = "ds-status-text ds-err";
      }
      window.alert("Lỗi mạng khi xoá Brand Kit: " + (e.message || e));
      if (delBtn) delBtn.disabled = false;
      if (saveBtn) saveBtn.disabled = false;
    }
  }

  function defaultItemFromItems(items) {
    for (var i = 0; i < (items || []).length; i++) {
      if (items[i].kind === "default" || items[i].name === "_mac-dinh.md") return items[i];
    }
    return null;
  }

  function defaultParsedFromItems(items) {
    var defItem = defaultItemFromItems(items);
    return (defItem && defItem.parsed) ? defItem.parsed : {
      colorPrimary: "#6C3BFF",
      colorSecondary: "#00D4FF",
      fonts: "Inter, Montserrat",
      logoMain: "attachments/dataset/chung/thsv-logo-2025.png",
      logoWhite: "attachments/dataset/chung/thsv-logo-big.png",
      logoIcon: "attachments/dataset/chung/thsv-logo-2025.png",
      imageStyle: "công nghệ, tối giản, premium",
      voice: "chuyên nghiệp, trẻ, hiện đại",
      layout: "logo góc trên, lề an toàn 8%, cover 16:9, không che mặt học viên",
      donts: "đổi màu logo, bóp méo logo, dùng màu ngoài palette"
    };
  }

  function slugFromPageName(ten) {
    var s = String(ten || "").toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return s || "fanpage";
  }

  function uniqueKitSlug(base, items) {
    var name = base;
    var n = 2;
    function taken(s) {
      return items.some(function (x) {
        return (x.name || "").toLowerCase() === (s + ".md").toLowerCase();
      });
    }
    while (taken(name)) {
      name = base + "-" + n;
      n++;
    }
    return name;
  }

  function setMdLine(md, labels, replacement, insertAfter) {
    var pattern = new RegExp("^[ \\t]*[-*][ \\t]*(?:" + labels.join("|") + ")[ \\t]*:[^\\r\\n]*", "mi");
    if (pattern.test(md)) return md.replace(pattern, replacement);
    if (insertAfter && insertAfter.test(md)) {
      return md.replace(insertAfter, function (m) { return m + "\n" + replacement; });
    }
    return md + "\n" + replacement;
  }

  function cloneDefaultMarkdown(defMd, opts) {
    var ten = opts.ten || "";
    var slug = opts.slug || "";
    var pageId = opts.pageId || "";
    var md = String(defMd || "").replace(/\r\n/g, "\n");
    var today = new Date().toISOString().slice(0, 10);
    if (!md.trim()) {
      return "---\ntype: wiki\nupdated: " + today + "\n---\n# Kit trang: " + ten +
        "\n\n## Tuỳ biến trang\n- Tên Fanpage: " + ten + "\n- slug: " + slug + "\n- Page ID: " + pageId + "\n";
    }
    md = md.replace(/^updated:[^\n]*/m, "updated: " + today);
    md = md.replace(/^# .*$/m, "# Kit trang: " + ten);
    md = md.replace(
      /(^# Kit trang:[^\n]*\n+)[^\n#][^\n]*/,
      "$1Kế thừa `_mac-dinh.md`. Bản sao TOÀN BỘ markdown Default; chỉ đổi tên Fanpage, slug và Page ID."
    );
    md = setMdLine(md, ["Tên Fanpage"], "- Tên Fanpage: " + ten, /^## Tuỳ biến trang[^\n]*/m);
    md = setMdLine(md, ["slug"], "- slug: " + slug, /^[ \t]*[-*][ \t]*Tên Fanpage:[^\n]*/m);
    md = setMdLine(md, ["Page ID", "page_id", "ID Fanpage", "ID Trang"], "- Page ID: " + pageId, /^[ \t]*[-*][ \t]*slug:[^\n]*/m);
    var tagsLine = opts.tagsLine != null ? opts.tagsLine : "";
    md = setMdLine(md, ["Thẻ khoá học", "The khoa hoc", "Folder anh[^:]*"], "- Thẻ khoá học: " + tagsLine, /^[ \t]*[-*][ \t]*Page ID:[^\n]*/m);
    return md;
  }

  async function writePageKitFile(name, ten, tpl, items) {
    var home = await getHome(brain());
    var ceil = ceilPath(home, KIT_DIR + "/" + name + ".md");
    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", ceil);
    fd.append("content", tpl);
    var res = await fetch("/files/write", { method: "POST", body: fd });
    var d = await res.json();
    if (!d.ok) return d;
    try {
      var idxPath = ceilPath(home, "wiki/brand-kits/_index.md");
      var idxRes = await fetch("/files/read?brain=" + encodeURIComponent(brain()) + "&path=" + encodeURIComponent(idxPath));
      var idxData = await idxRes.json();
      if (idxData && idxData.content) {
        var idxContent = idxData.content;
        var linkStr = "[[brand-kits/" + name + "]]";
        if (idxContent.indexOf(linkStr) < 0) {
          var idxFd = new FormData();
          idxFd.append("brain", brain());
          idxFd.append("path", idxPath);
          idxFd.append("content", idxContent.trimEnd() + "\n- " + linkStr + " " + ten + "\n");
          await fetch("/files/write", { method: "POST", body: idxFd });
        }
      }
    } catch (idxErr) {}
    items.push({
      name: name + ".md",
      type: "file",
      content: tpl,
      kind: "page",
      parsed: parsePageKit(tpl, name + ".md"),
      displayTitle: ten
    });
    return { ok: true };
  }

  function kitHasFacebookPage(items, pg) {
    var pid = String(pg.id || "");
    var nm = foldDiacritic(pg.name || "");
    return items.some(function (x) {
      if (x.kind !== "page") return false;
      var haveId = String((x.parsed && x.parsed.pageId) || "").trim();
      if (pid && haveId && haveId === pid) return true;
      if (!haveId && nm && foldDiacritic(x.displayTitle || x.parsed.name || "") === nm) return true;
      return false;
    });
  }

  function closePagePicker(body) {
    var ov = body.querySelector("#dsPickFb");
    if (ov && ov.parentNode) ov.parentNode.removeChild(ov);
  }

  async function createKitsForPages(body, items, paintList, selected) {
    var st = body.querySelector("#dsKitStatus");
    var btn = body.querySelector("#dsNewKit");
    if (btn) btn.disabled = true;
    if (st) {
      st.textContent = "Đang tạo " + selected.length + " Brand Kit…";
      st.className = "ds-status-text dim";
    }
    var defItem = defaultItemFromItems(items);
    var defMd = (defItem && defItem.content) || "";
    var made = 0;
    for (var i = 0; i < selected.length; i++) {
      var pg = selected[i];
      if (kitHasFacebookPage(items, pg)) continue;
      var ten = String(pg.name || "").trim() || ("Fanpage " + pg.id);
      var slug = uniqueKitSlug(slugFromPageName(ten), items);
      var tpl = cloneDefaultMarkdown(defMd, { ten: ten, slug: slug, pageId: pg.id });
      var wr = await writePageKitFile(slug, ten, tpl, items);
      if (wr && wr.ok) made++;
    }
    if (btn) btn.disabled = false;
    paintList((body.querySelector("#dsKitQ") || {}).value || "");
    if (st) {
      st.textContent = made ? ("Đã tạo " + made + " Brand Kit (tên = tên Fanpage). Page không có kit sẽ không được đăng bài.") : "Không tạo được kit.";
      st.className = made ? "ds-status-text ds-ok" : "ds-status-text ds-err";
    }
  }

  async function openPagePicker(body, items, paintList) {
    closePagePicker(body);
    var st = body.querySelector("#dsKitStatus");
    if (st) {
      st.textContent = "Đang tải danh sách Fanpage đã kết nối…";
      st.className = "ds-status-text dim";
    }
    var pages = await fetchFbPages();
    if (st) st.textContent = "";
    if (!pages.length) {
      window.alert("Chưa lấy được Fanpage từ Kết nối Facebook. Kết nối lại, tick Trang, rồi bấm nút này.");
      return;
    }
    var host = body.querySelector(".ds-split") || body;
    host.style.position = host.style.position || "relative";
    var ov = document.createElement("div");
    ov.className = "ds-pick-overlay";
    ov.id = "dsPickFb";
    var rows = pages.map(function (pg, i) {
      var has = kitHasFacebookPage(items, pg);
      return '<label class="ds-pick-row' + (has ? " has-kit" : "") + '">' +
        '<input type="checkbox" data-i="' + i + '"' + (has ? " disabled" : " checked") + '>' +
        '<div><div class="ds-pick-name">' + esc(pg.name || "(không tên)") + '</div>' +
        '<div class="ds-pick-id">Page ID ' + esc(pg.id) + (pg.category ? " · " + esc(pg.category) : "") + "</div></div>" +
        (has ? '<span class="ds-pick-badge">Đã có kit — không tạo lại</span>' : "") +
        "</label>";
    }).join("");
    ov.innerHTML =
      '<div class="ds-pick-box">' +
      "<h3>Chọn Fanpage để tạo Brand Kit</h3>" +
      '<p class="ds-pick-lead">Tên kit = <b>đúng tên Fanpage</b>. Nội dung copy từ Default. ' +
      "<b>Page không có Brand Kit thì Javis không đăng bài lên page đó.</b></p>" +
      '<label class="ds-pick-all"><input type="checkbox" id="dsPickAll" checked> Chọn tất cả page chưa có kit</label>' +
      '<div class="ds-pick-list">' + rows + "</div>" +
      '<div class="ds-pick-foot">' +
      '<button type="button" class="s-btn-ghost" id="dsPickCancel">Hủy</button>' +
      '<button type="button" class="s-btn" id="dsPickGo">Tạo kit cho page đã chọn</button>' +
      "</div></div>";
    host.appendChild(ov);

    function enabledBoxes() {
      return Array.prototype.slice.call(ov.querySelectorAll('.ds-pick-row input[type="checkbox"]:not([disabled])'));
    }
    var all = ov.querySelector("#dsPickAll");
    all.onchange = function () {
      enabledBoxes().forEach(function (c) { c.checked = all.checked; });
    };
    enabledBoxes().forEach(function (c) {
      c.onchange = function () {
        var boxes = enabledBoxes();
        all.checked = boxes.length && boxes.every(function (x) { return x.checked; });
      };
    });
    ov.querySelector("#dsPickCancel").onclick = function () { closePagePicker(body); };
    ov.onclick = function (e) { if (e.target === ov) closePagePicker(body); };
    ov.querySelector("#dsPickGo").onclick = async function () {
      var selected = [];
      enabledBoxes().forEach(function (c) {
        if (c.checked) selected.push(pages[parseInt(c.getAttribute("data-i"), 10)]);
      });
      if (!selected.length) {
        window.alert("Chưa chọn page nào. Tick các Fanpage muốn tạo Brand Kit.");
        return;
      }
      closePagePicker(body);
      await createKitsForPages(body, items, paintList, selected);
    };
  }

  async function newKit(body, items, paintList) {
    return openPagePicker(body, items, paintList);
  }

  /* ============================================================
     TAB 2: THU VIEN ANH
     ============================================================ */
  async function renderAnh(body) {
    body.innerHTML = '<p class="dim" style="padding:14px">Đang tải thư viện ảnh…</p>';
    var folders = [];
    try {
      folders = (await listPath(IMG_DIR)).filter(function (f) { return f.type === "dir"; });
    } catch (e) {
      folders = [];
    }

    if (!folders.length) {
      await ensureFolders();
      try {
        folders = (await listPath(IMG_DIR)).filter(function (f) { return f.type === "dir"; });
      } catch (e2) {
        folders = [];
      }
    }
    folders.sort(function (a, b) {
      if (a.name === "chung") return -1;
      if (b.name === "chung") return 1;
      return a.name.localeCompare(b.name);
    });

    body.innerHTML =
      '<div class="ds-split">' +
      '<aside class="ds-side">' +
      '<div class="ds-kicker" style="padding:4px 8px 8px;font-weight:600">Thư mục chủ đề</div>' +
      '<div class="ds-side-scroll" id="dsFoldList"></div>' +
      '<button type="button" class="s-btn-ghost ds-new" id="dsNewFold">+ Thư mục mới</button>' +
      '</aside>' +
      '<section class="ds-main ds-drop" id="dsDrop">' +
      '<div class="ds-toolbar"><div><div class="ds-kicker" id="dsFoldKind">Chọn thư mục</div>' +
      '<div class="ds-filename" id="dsFoldMeta">attachments/dataset</div></div>' +
      '<div class="ds-toolbar-right">' +
      '<input class="ds-search" id="dsImgQ" placeholder="Tìm ảnh trong thư mục…" style="max-width:180px">' +
      '<span id="dsUploadStatus" class="ds-status-text"></span>' +
      '<label class="s-btn ds-upload">Tải ảnh lên<input type="file" id="dsFiles" accept="image/*" multiple hidden></label>' +
      '</div></div>' +
      '<div id="dsFoldNotice"></div>' +
      '<div class="ds-grid" id="dsGrid"></div>' +
      '</section></div>';

    var foldEl = body.querySelector("#dsFoldList");
    var current = "";
    folders.forEach(function (f, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "ds-row";
      b.dataset.name = f.name;
      b.innerHTML = '<span class="ds-row-label">' + esc(f.name) + '</span>';
      b.onclick = function () { openFolder(body, f.name, b); };
      foldEl.appendChild(b);
      if (i === 0) current = f.name;
    });

    body.querySelector("#dsNewFold").onclick = function () { newFolder(body); };

    var fileInput = body.querySelector("#dsFiles");
    fileInput.onchange = function () {
      if (this.files && this.files.length) {
        uploadFiles(body, body._dsCurrentFolder ? body._dsCurrentFolder() : current, this.files);
        this.value = "";
      }
    };

    var drop = body.querySelector("#dsDrop");
    drop.addEventListener("dragover", function (e) {
      e.preventDefault();
      drop.classList.add("over");
    });
    drop.addEventListener("dragleave", function () {
      drop.classList.remove("over");
    });
    drop.addEventListener("drop", function (e) {
      e.preventDefault();
      drop.classList.remove("over");
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
        uploadFiles(body, body._dsCurrentFolder ? body._dsCurrentFolder() : current, e.dataTransfer.files);
      }
    });

    body._dsCurrentFolder = function () { return current; };
    body._dsSetFolder = function (n) { current = n; };

    var first = foldEl.querySelector(".ds-row");
    if (first) {
      first.click();
    }
  }

  async function ensureFolders() {
    await loadCourseTags();
    var names = ["chung", "_mau", "_xuat"].concat(COURSE_FOLDERS.map(function (t) { return t.id; }));
    for (var i = 0; i < names.length; i++) {
      await mkdirDataset(names[i]);
    }
  }

  async function openFolder(body, name, btn) {
    body.querySelectorAll(".ds-row").forEach(function (x) { x.classList.remove("sel"); });
    if (btn) btn.classList.add("sel");
    if (body._dsSetFolder) body._dsSetFolder(name);

    body.querySelector("#dsFoldKind").textContent = name;
    body.querySelector("#dsFoldMeta").textContent = IMG_DIR + "/" + name;

    var noticeEl = body.querySelector("#dsFoldNotice");
    if (name === "chung") {
      noticeEl.innerHTML =
        '<div class="ds-notice ds-notice-warn">' +
        '<strong>Logo hệ thống:</strong> Thư mục này chỉ dùng làm watermark, góc ảnh hoặc tham chiếu thương hiệu. Cấm đăng logo trần làm ảnh chính của bài viết.' +
        '</div>';
    } else if (name === "_mau") {
      noticeEl.innerHTML =
        '<div class="ds-notice ds-notice-info">' +
        '<strong>Ảnh mẫu chuẩn:</strong> Mẫu Kiểu A (khoá học có ảnh gốc) và Kiểu B (lịch lễ tự gen). Dùng làm quy chuẩn đối chiếu hình ảnh.' +
        '</div>';
    } else if (name === "_xuat") {
      noticeEl.innerHTML =
        '<div class="ds-notice ds-notice-info">' +
        '<strong>Ảnh đã xuất:</strong> Thư mục lưu ảnh đã biên tập/sinh xong. Khi đăng bài, ảnh đầu (cover) bắt buộc lấy từ thư mục này.' +
        '</div>';
    } else {
      noticeEl.innerHTML =
        '<div class="ds-notice ds-notice-info">' +
        'Ảnh bài đăng trong thư mục <strong>' + esc(name) + '</strong> (<code>attachments/dataset/' + esc(name) + '</code>). Khi đăng bài, AI lấy ảnh trong thư mục này khớp chủ đề.' +
        '</div>';
    }

    var grid = body.querySelector("#dsGrid");
    grid.innerHTML = '<div class="dim" style="padding:20px;grid-column:1/-1">Đang tải danh sách ảnh…</div>';

    var items = [];
    try {
      items = await listPath(IMG_DIR + "/" + name);
    } catch (e) {
      items = [];
    }

    var imgs = items.filter(function (f) {
      return f.type === "file" && IMG_RE.test(f.name);
    });

    if (!imgs.length) {
      if (name === "chung") {
        grid.innerHTML =
          '<div class="ds-empty">' +
          '<strong>Thư mục logo trống</strong>' +
          '<p>Kéo thả logo hoặc banner hệ thống vào đây (dùng làm watermark góc ảnh).</p>' +
          '</div>';
      } else {
        grid.innerHTML =
          '<div class="ds-empty">' +
          '<strong>Chưa có ảnh trong thư mục này</strong>' +
          '<p>Kéo thả ảnh vào đây hoặc bấm "Tải ảnh lên". AI đăng bài sẽ chọn ảnh từ thư mục này, không lấy logo trần.</p>' +
          '</div>';
      }
      return;
    }

    function paintGrid(q) {
      q = (q || "").toLowerCase().trim();
      var filtered = imgs.filter(function (f) {
        return !q || f.name.toLowerCase().indexOf(q) >= 0;
      });
      if (!filtered.length) {
        grid.innerHTML = '<div class="ds-empty-sm" style="grid-column:1/-1">Không có ảnh nào khớp tìm kiếm</div>';
        return;
      }
      grid.innerHTML = "";
      filtered.forEach(function (f) {
        var filePath = IMG_DIR + "/" + name + "/" + f.name;
        var card = document.createElement("figure");
        card.className = "ds-card";
        card.innerHTML =
          '<div class="ds-card-thumb">' +
          '<img alt="' + esc(f.name) + '" src="' + esc(rawUrl(filePath)) + '" loading="lazy">' +
          '<button type="button" class="ds-card-del" title="Xoá ảnh này">×</button>' +
          '</div>' +
          '<figcaption title="' + esc(f.name) + '">' + esc(f.name) + '</figcaption>';

        var delBtn = card.querySelector(".ds-card-del");
        delBtn.onclick = function (ev) {
          ev.stopPropagation();
          deleteImage(body, name, f.name, filePath);
        };

        grid.appendChild(card);
      });
    }

    paintGrid("");
    var imgQ = body.querySelector("#dsImgQ");
    if (imgQ) {
      imgQ.value = "";
      imgQ.oninput = function () { paintGrid(this.value); };
    }
  }

  async function deleteImage(body, folder, fileName, filePath) {
    if (!window.confirm("Bạn có chắc chắn muốn xoá ảnh \"" + fileName + "\"?")) {
      return;
    }

    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", filePath);

    try {
      var res = await fetch("/files/delete", { method: "POST", body: fd });
      var d = await res.json();
      if (d.ok) {
        var sel = body.querySelector(".ds-row.sel");
        if (sel) openFolder(body, folder, sel);
      } else {
        window.alert(d.error || "Xoá ảnh thất bại");
      }
    } catch (e) {
      window.alert("Lỗi mạng khi xoá ảnh: " + e.message);
    }
  }

  async function uploadFiles(body, folder, fileList) {
    if (!folder) {
      window.alert("Vui lòng chọn thư mục trước khi tải ảnh");
      return;
    }

    var files = Array.prototype.slice.call(fileList).filter(function (f) {
      return IMG_RE.test(f.name);
    });

    if (!files.length) {
      window.alert("Vui lòng chọn các file định dạng ảnh (.png, .jpg, .webp, .gif, .svg)");
      return;
    }

    var st = body.querySelector("#dsUploadStatus");
    if (st) {
      st.textContent = "Đang tải " + files.length + " ảnh lên…";
      st.className = "ds-status-text dim";
    }

    var count = 0;
    var errors = [];

    for (var i = 0; i < files.length; i++) {
      var fd = new FormData();
      fd.append("brain", brain());
      fd.append("path", IMG_DIR + "/" + folder);
      fd.append("file", files[i]);
      try {
        var res = await fetch("/files/upload", { method: "POST", body: fd });
        var d = await res.json();
        if (d.ok) count++;
        else errors.push(files[i].name + ": " + (d.error || "Lỗi tải lên"));
      } catch (e) {
        errors.push(files[i].name + ": Lỗi mạng");
      }
    }

    if (st) {
      if (errors.length) {
        st.textContent = "Đã tải " + count + "/" + files.length + " ảnh (có lỗi)";
        st.className = "ds-status-text ds-err";
      } else {
        st.textContent = "Đã tải lên " + count + " ảnh";
        st.className = "ds-status-text ds-ok";
        setTimeout(function () {
          if (st.textContent.indexOf("Đã tải lên") >= 0) st.textContent = "";
        }, 3000);
      }
    }

    var sel = body.querySelector(".ds-row.sel");
    if (sel) openFolder(body, folder, sel);
  }

  async function newFolder(body) {
    var rawSlug = window.prompt("Tên thư mục mới (không dấu, vd: noi-that):");
    if (!rawSlug) return;
    var slug = rawSlug.trim().toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9-]/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");
    if (!slug) return;

    var fd = new FormData();
    fd.append("brain", brain());
    fd.append("path", IMG_DIR);
    fd.append("name", slug);

    try {
      var res = await fetch("/files/mkdir", { method: "POST", body: fd });
      var d = await res.json();
      if (d && d.error) {
        window.alert(d.error);
        return;
      }
      await loadCourseTags();
      if (!COURSE_FOLDERS.some(function (t) { return t.id === slug; })) {
        await saveCourseTags(COURSE_FOLDERS.concat([{ id: slug, label: rawSlug.trim() }]));
      }
      renderAnh(body);
    } catch (e) {
      window.alert("Lỗi khi tạo thư mục: " + e.message);
    }
  }

  window.JavisBrandKits = { render: render };
})();
