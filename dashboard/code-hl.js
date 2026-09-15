/* code-hl.js - Tô màu cú pháp cho Ô SỬA CODE (textarea), dùng chung cho trình sửa đính
   (console.js) và khung sửa bung giữa màn hình (file-editor.js).

   window.JavisCodeHL = { attach(textarea, lang), langFromPath(path), highlight(code, lang) }

   Cách làm: KHÔNG thay textarea bằng contenteditable (mất undo của trình duyệt, mất gõ
   tiếng Việt bằng bộ gõ ngoài, mất mọi phím tắt quen tay). Thay vào đó lồng một thẻ <pre>
   đã tô màu NẰM DƯỚI, còn textarea ở trên với chữ trong suốt và con trỏ vẫn thấy. Người
   dùng gõ vào textarea thật như cũ, chỉ khác là nhìn thấy màu bên dưới. Muốn hai lớp trùng
   khít thì font, cỡ chữ, dòng cao, padding và luật xuống dòng phải Y HỆT - CSS ép cả hai
   bằng cùng một bộ thuộc tính trong style.css (.jvhl-view và .jvhl-ta).

   Vì sao có bộ tô màu riêng thay vì dùng lại `highlight` của chat-render.js: bộ đó viết cho
   khối code trong chat, coi mọi thứ là ngôn ngữ kiểu C nên đọc HTML ra rất sai (tô "class"
   thành từ khoá, tên thẻ và tên thuộc tính thì không tô gì). HTML lại đúng là thứ người dùng
   mở ra sửa nhiều nhất. Nên ở đây có bộ đọc riêng cho markup, CSS và JSON; các ngôn ngữ còn
   lại vẫn giao lại cho bộ chung, không chép lại logic.

   Ghi chú: KHÔNG dùng ký tự em dash ở bất kỳ đâu. */
(function () {
  "use strict";

  // File to hơn ngần này thì bỏ tô màu: mỗi lần gõ là dựng lại cả cây HTML, file vài trăm
  // nghìn ký tự sẽ giật. Sửa vẫn bình thường, chỉ là chữ một màu.
  var MAX_CHARS = 300000;
  // Trên ngưỡng này thì hoãn tô lại theo hẹn giờ thay vì mỗi khung hình.
  var DEBOUNCE_FROM = 60000;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function span(cls, text) {
    return '<span class="tok-' + cls + '">' + esc(text) + "</span>";
  }

  // ---------------------------------------------------------------- ngôn ngữ theo đuôi file
  var BY_EXT = {
    html: "html", htm: "html", xhtml: "html",
    xml: "xml", svg: "xml", rss: "xml", xsl: "xml",
    css: "css", scss: "css", less: "css",
    js: "js", mjs: "js", cjs: "js", jsx: "js", ts: "js", tsx: "js",
    json: "json", jsonc: "json", webmanifest: "json",
    py: "py", pyw: "py",
    yaml: "yaml", yml: "yaml",
    toml: "ini", ini: "ini", conf: "ini", cfg: "ini", env: "ini", properties: "ini",
    sh: "sh", bash: "sh", zsh: "sh",
    sql: "sql", go: "go", rs: "rust", java: "java", c: "c", h: "c", cpp: "c", hpp: "c",
    cs: "cs", php: "php", rb: "ruby", lua: "lua", ps1: "ps1", bat: "bat", cmd: "bat",
  };

  /** Đuôi file -> tên ngôn ngữ, hoặc "" nếu không nên tô màu (.md, .txt, .csv, .log...).
      .md cố ý KHÔNG tô: nó mở bằng trình soạn WYSIWYG có thanh công cụ tự chèn chữ vào
      textarea mà không bắn sự kiện input, lớp màu sẽ lệch với nội dung thật. */
  function langFromPath(path) {
    var base = String(path || "").replace(/\/+$/, "").split("/").pop();
    var i = base.lastIndexOf(".");
    if (i < 0) return "";
    return BY_EXT[base.slice(i + 1).toLowerCase()] || "";
  }

  // ---------------------------------------------------------------- markup (html, xml, svg)
  function hlAttrs(s) {
    var re = /([^\s=/>"']+)|(=)|("[^"]*"|'[^']*')|([\s\S])/g;
    var out = "", m, choValue = false;
    while ((m = re.exec(s)) !== null) {
      if (m[1] != null) {
        out += choValue ? span("s", m[1]) : span("a", m[1]);
        choValue = false;
      } else if (m[2] != null) {
        out += "=";
        choValue = true;
      } else if (m[3] != null) {
        out += span("s", m[3]);
        choValue = false;
      } else {
        out += esc(m[4]);
      }
    }
    return out;
  }

  function hlMarkup(code) {
    var out = "", i = 0, n = code.length;
    while (i < n) {
      var lt = code.indexOf("<", i);
      if (lt < 0) { out += esc(code.slice(i)); break; }
      out += esc(code.slice(i, lt));
      if (code.substr(lt, 4) === "<!--") {
        var endC = code.indexOf("-->", lt + 4);
        endC = endC < 0 ? n : endC + 3;
        out += span("c", code.slice(lt, endC));
        i = endC;
        continue;
      }
      if (code.substr(lt, 9).toLowerCase() === "<!doctype" || code.substr(lt, 2) === "<?") {
        var endD = code.indexOf(">", lt);
        endD = endD < 0 ? n : endD + 1;
        out += span("k", code.slice(lt, endD));
        i = endD;
        continue;
      }
      var m = /^<(\/?)([a-zA-Z][\w:.-]*)/.exec(code.slice(lt, lt + 80));
      if (!m) { out += "&lt;"; i = lt + 1; continue; }
      // Tìm dấu ">" đóng thẻ, BỎ QUA dấu nằm trong chuỗi (vd alt="a > b").
      var j = lt + m[0].length, nhay = "";
      while (j < n) {
        var ch = code.charAt(j);
        if (nhay) { if (ch === nhay) nhay = ""; }
        else if (ch === '"' || ch === "'") nhay = ch;
        else if (ch === ">") break;
        j++;
      }
      var hetThe = j < n ? j + 1 : n;
      out += span("t", "<" + m[1] + m[2]);
      out += hlAttrs(code.slice(lt + m[0].length, j));
      out += span("t", code.slice(j, hetThe));
      i = hetThe;
      // Ruột <style> và <script> là ngôn ngữ KHÁC, đọc bằng bộ tương ứng thay vì coi là chữ.
      var ten = m[2].toLowerCase();
      if (!m[1] && (ten === "style" || ten === "script") && code.charAt(j) === ">") {
        var dong = code.toLowerCase().indexOf("</" + ten, i);
        if (dong < 0) dong = n;
        var ruot = code.slice(i, dong);
        out += (ten === "style" ? hlCss(ruot) : hlChung(ruot, "js"));
        i = dong;
      }
    }
    return out;
  }

  // ---------------------------------------------------------------- CSS
  // Thu tu cac nhanh la CO Y, doi cho la sai ngay:
  //   - nhanh "ten thuoc tinh" (co nhin truoc dau ":") phai dung TRUOC nhanh dinh danh, khong
  //     thi "top" bi nuot thanh chu thuong va mat mau.
  //   - nhanh "dinh danh" phai dung TRUOC nhanh so, de "h1" va ".col-12" duoc an nguyen cum.
  //     Bo nhanh nay di thi "-12" trong ".col-12" hien ra mot manh mau cam giua ten lop.
  //   - `-?\b\d` chu khong phai `\b-?\d`: dat \b truoc dau tru thi "-4px" khong khop, vi dau
  //     tru lan khoang trang deu la ky tu khong-tu nen giua chung khong co ranh gioi tu.
  var RE_CSS = /(\/\*[\s\S]*?\*\/)|("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(@[\w-]+)|([-\w]+)(?=\s*:)|(#[0-9a-fA-F]{3,8}\b)|(-?[A-Za-z_][\w-]*)|(-?\b\d*\.?\d+(?:px|em|rem|%|vh|vw|s|ms|deg|fr|ch|pt)?\b)|([\s\S])/g;
  function hlCss(code) {
    RE_CSS.lastIndex = 0;
    var out = "", m;
    while ((m = RE_CSS.exec(code)) !== null) {
      if (m[1] != null) out += span("c", m[1]);
      else if (m[2] != null) out += span("s", m[2]);
      else if (m[3] != null) out += span("k", m[3]);
      else if (m[4] != null) out += span("a", m[4]);
      else if (m[5] != null) out += span("n", m[5]);
      else if (m[6] != null) out += esc(m[6]);
      else if (m[7] != null) out += span("n", m[7]);
      else out += esc(m[8]);
      if (RE_CSS.lastIndex === m.index) RE_CSS.lastIndex++;
    }
    return out;
  }

  // ---------------------------------------------------------------- JSON
  var RE_JSON = /("(?:\\.|[^"\\])*")(\s*:)?|(-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b)|(\btrue\b|\bfalse\b|\bnull\b)|([\s\S])/g;
  function hlJson(code) {
    RE_JSON.lastIndex = 0;
    var out = "", m;
    while ((m = RE_JSON.exec(code)) !== null) {
      if (m[1] != null) {
        // Chuỗi đứng ngay trước dấu ":" là TÊN TRƯỜNG, tô khác giá trị cho dễ dò.
        out += m[2] != null ? span("a", m[1]) + esc(m[2]) : span("s", m[1]);
      } else if (m[3] != null) out += span("n", m[3]);
      else if (m[4] != null) out += span("k", m[4]);
      else out += esc(m[5]);
      if (RE_JSON.lastIndex === m.index) RE_JSON.lastIndex++;
    }
    return out;
  }

  // ---------------------------------------------------------------- các ngôn ngữ còn lại
  // Giao lại cho bộ tô màu của chat-render.js (đã dùng cho khối code trong chat) để một
  // luật chỉ nằm ở một chỗ. Chưa nạp được thì trả chữ trơ, không nổ.
  function hlChung(code, lang) {
    var f = null;
    if (typeof window !== "undefined" && typeof window.JavisHighlight === "function") f = window.JavisHighlight;
    if (!f) return esc(code);
    try { return f(code, lang); } catch (e) { return esc(code); }
  }

  function highlight(code, lang) {
    code = String(code == null ? "" : code);
    lang = String(lang || "").toLowerCase();
    if (lang === "html" || lang === "xml") return hlMarkup(code);
    if (lang === "css") return hlCss(code);
    if (lang === "json") return hlJson(code);
    return hlChung(code, lang);
  }

  // ---------------------------------------------------------------- gắn vào textarea
  /** Bọc textarea bằng lớp tô màu. Trả về {refresh, detach} hoặc null nếu bỏ qua
      (không có ngôn ngữ, file quá to, hoặc đã gắn rồi). */
  function attach(ta, lang) {
    if (!ta || !ta.parentNode || ta.__jvhl) return null;
    if (!lang) return null;
    if ((ta.value || "").length > MAX_CHARS) return null;
    if (typeof document === "undefined") return null;

    var cha = ta.parentNode;
    var wrap = document.createElement("div");
    wrap.className = "jvhl";
    var view = document.createElement("pre");
    view.className = "jvhl-view";
    view.setAttribute("aria-hidden", "true");
    cha.insertBefore(wrap, ta);
    wrap.appendChild(view);
    wrap.appendChild(ta);
    ta.classList.add("jvhl-ta");

    // Ô cha thường tự cuộn (.ne-src có overflow:auto). Giờ phần cuộn nằm trong textarea,
    // để cha cuộn nữa thì có hai thanh cuộn lồng nhau. Nhớ giá trị cũ để gỡ ra trả lại.
    var chaOverflowCu = cha.style.overflow;
    cha.style.overflow = "hidden";

    var cho = 0, hen = 0;
    function ve() {
      view.innerHTML = highlight(ta.value, lang) + "\n";   // "\n" thừa: giữ chỗ cho dòng cuối
      dongBo();
    }
    function dongBo() {
      view.scrollTop = ta.scrollTop;
      view.scrollLeft = ta.scrollLeft;
    }
    function henVe() {
      if ((ta.value || "").length >= DEBOUNCE_FROM) {
        clearTimeout(hen);
        hen = setTimeout(ve, 120);
        return;
      }
      if (cho) return;
      cho = requestAnimationFrame(function () { cho = 0; ve(); });
    }

    ta.addEventListener("input", henVe);
    ta.addEventListener("change", henVe);
    ta.addEventListener("scroll", dongBo);
    ve();

    var api = {
      refresh: ve,
      detach: function () {
        ta.removeEventListener("input", henVe);
        ta.removeEventListener("change", henVe);
        ta.removeEventListener("scroll", dongBo);
        clearTimeout(hen);
        if (cho) cancelAnimationFrame(cho);
        ta.classList.remove("jvhl-ta");
        delete ta.__jvhl;
        cha.style.overflow = chaOverflowCu;
        if (wrap.parentNode) wrap.parentNode.insertBefore(ta, wrap);
        if (wrap.parentNode) wrap.parentNode.removeChild(wrap);
      },
    };
    ta.__jvhl = api;
    return api;
  }

  if (typeof window !== "undefined") {
    window.JavisCodeHL = { attach: attach, langFromPath: langFromPath, highlight: highlight };
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { langFromPath: langFromPath, highlight: highlight };
  }
})();
