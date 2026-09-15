/* Test bo to mau cu phap cho o sua code (dashboard/code-hl.js). Chay tay / CI:
       node tests/js/test_code_hl.js

   Rang buoc QUAN TRONG NHAT o day khong phai "mau co dep khong" ma la GO BO THE DI THI PHAI
   RA LAI DUNG CHUOI GOC. Lop mau nam CHONG KHIT duoi textarea; chi can bo to mau nuot mot ky
   tu, them mot ky tu, hay doi mot khoang trang la tu do tro di moi dong deu lech - chu mau mot
   noi, con tro mot neo. Loi kieu do khong bao gio nem exception nen chi co test nay bat duoc. */
"use strict";

global.window = {};   // co window -> module gan window.JavisCodeHL; van giu module.exports
const HL = require("../../dashboard/code-hl.js");

let fails = [];
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails.push(name);
}

// Bo the + doi thuc the ve lai chu goc, de so voi dau vao.
function stripHtml(s) {
  return String(s)
    .replace(/<span class="tok-[a-z]">/g, "")
    .replace(/<\/span>/g, "")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
}
function roundTrip(name, code, lang) {
  check(name, stripHtml(HL.highlight(code, lang)) === code);
}

// ---------------------------------------------------------------- ngon ngu theo duoi file
check("html -> html", HL.langFromPath("bao-cao/trang.html") === "html");
check("htm cung la html", HL.langFromPath("a.htm") === "html");
check("svg doc nhu xml", HL.langFromPath("icon.SVG") === "xml");
check("css", HL.langFromPath("style.css") === "css");
check("json", HL.langFromPath("data.json") === "json");
check("py", HL.langFromPath("tool.py") === "py");
check("md KHONG to mau (trinh soan WYSIWYG tu chen chu, lop mau se lech)",
      HL.langFromPath("ghi-chu.md") === "");
check("txt khong to mau", HL.langFromPath("a.txt") === "");
check("file khong duoi -> khong to mau", HL.langFromPath("Makefile") === "");
check("duong dan rong khong no", HL.langFromPath("") === "");
check("duoi la doi tuong la khong lam sap (chuoi rong)", HL.langFromPath("a.khongbietlagi") === "");

// ---------------------------------------------------------------- HTML
const HTML = [
  "<!DOCTYPE html>",
  "<!-- ghi chu <b>khong phai the</b> -->",
  '<div class="hop" data-id=\'7\' hidden>',
  '  <img src="a.png" alt="a > b">',
  "  Chu thuong &amp; ky tu dac biet < >",
  "</div>",
  "<style>.a{color:#fff;margin:4px}/* xong */</style>",
  "<script>var x = 1;<\/script>",
].join("\n");
const outHtml = HL.highlight(HTML, "html");

check("ten the vao tok-t", outHtml.indexOf('<span class="tok-t">&lt;div</span>') >= 0);
check("the dong cung tok-t", outHtml.indexOf('<span class="tok-t">&lt;/div</span>') >= 0);
check("ten thuoc tinh vao tok-a", outHtml.indexOf('<span class="tok-a">class</span>') >= 0);
check("gia tri thuoc tinh vao tok-s", outHtml.indexOf('<span class="tok-s">"hop"</span>') >= 0);
check("gia tri nhay don cung tok-s", outHtml.indexOf("<span class=\"tok-s\">'7'</span>") >= 0);
check("thuoc tinh khong co gia tri van la tok-a", outHtml.indexOf('<span class="tok-a">hidden</span>') >= 0);
check("chu thich HTML vao tok-c", /<span class="tok-c">&lt;!-- ghi chu/.test(outHtml));
check("DOCTYPE vao tok-k", /<span class="tok-k">&lt;!DOCTYPE html&gt;<\/span>/.test(outHtml));
check("dau > trong chuoi KHONG cat the som", outHtml.indexOf('<span class="tok-s">"a &gt; b"</span>') >= 0);
check("ruot <style> doc theo luat CSS", outHtml.indexOf('<span class="tok-a">color</span>') >= 0);
check("chu thich trong <style> van la chu thich", outHtml.indexOf('<span class="tok-c">/* xong */</span>') >= 0);
check("chu thuong khong bi boc the", outHtml.indexOf("Chu thuong &amp;amp; ky tu dac biet &lt; &gt;") >= 0);
roundTrip("HTML: go the di ra lai dung chuoi goc", HTML, "html");

// Cac dang HTML gay bay: the chua dong, dau < don doc, the tu dong.
roundTrip("HTML the con dang go dang do", '<div class="a', "html");
roundTrip("HTML dau < don doc giua chu", "1 < 2 va 3 > 2", "html");
roundTrip("HTML the tu dong", '<br/><input type="text" />', "html");
roundTrip("HTML <style> khong dong", "<style>.a{color:red}", "html");
roundTrip("HTML rong", "", "html");
check("HTML rong tra chuoi rong", HL.highlight("", "html") === "");

// ---------------------------------------------------------------- ruot <script> giao cho bo chung
global.window.JavisHighlight = function (code) { return "[[JS:" + code + "]]"; };
check("ruot <script> giao cho bo to mau chung",
      HL.highlight("<script>var x=1;<\/script>", "html").indexOf("[[JS:var x=1;]]") >= 0);
global.window.JavisHighlight = function () { throw new Error("hong"); };
check("bo chung nem loi thi khong keo sap ca file",
      HL.highlight("<script>var x=1;<\/script>", "html").indexOf("var x=1;") >= 0);
delete global.window.JavisHighlight;

// ---------------------------------------------------------------- CSS
const CSS = ".hop, #id { color: #ff8800; margin: 12px 0; }\n/* chu thich */\n@media (max-width:700px){ .a{display:none} }";
const outCss = HL.highlight(CSS, "css");
check("thuoc tinh CSS vao tok-a", outCss.indexOf('<span class="tok-a">color</span>') >= 0);
check("ma mau vao tok-n", outCss.indexOf('<span class="tok-n">#ff8800</span>') >= 0);
check("so kem don vi vao tok-n", outCss.indexOf('<span class="tok-n">12px</span>') >= 0);
check("@media vao tok-k", outCss.indexOf('<span class="tok-k">@media</span>') >= 0);
check("chu thich CSS vao tok-c", outCss.indexOf('<span class="tok-c">/* chu thich */</span>') >= 0);
check("so AM van vao tok-n", HL.highlight("a{margin:-4px}", "css").indexOf('<span class="tok-n">-4px</span>') >= 0);
check("so trong TEN khong bi to (h1, .col-12)",
      HL.highlight("h1,.col-12{top:0}", "css").indexOf('class="tok-n"') === HL.highlight("h1,.col-12{top:0}", "css").lastIndexOf('class="tok-n"'));
roundTrip("CSS: go the di ra lai dung chuoi goc", CSS, "css");
roundTrip("CSS so am giu nguyen chuoi", "a{margin:-4px;left:-.5em}", "css");

// ---------------------------------------------------------------- JSON
const JSON_SRC = '{\n  "ten": "Javis",\n  "so": -12.5,\n  "bat": true,\n  "trong": null\n}';
const outJson = HL.highlight(JSON_SRC, "json");
check("ten truong JSON vao tok-a", outJson.indexOf('<span class="tok-a">"ten"</span>') >= 0);
check("gia tri chuoi JSON vao tok-s", outJson.indexOf('<span class="tok-s">"Javis"</span>') >= 0);
check("so am co phan thap phan vao tok-n", outJson.indexOf('<span class="tok-n">-12.5</span>') >= 0);
check("true/null vao tok-k", outJson.indexOf('<span class="tok-k">true</span>') >= 0
      && outJson.indexOf('<span class="tok-k">null</span>') >= 0);
roundTrip("JSON: go the di ra lai dung chuoi goc", JSON_SRC, "json");

// ---------------------------------------------------------------- an toan
check("dau nhon trong chu bi thoat (khong chen duoc the)",
      HL.highlight('<p>a<script>alert(1)<\/script>', "xml").indexOf("<script>alert") < 0);
check("ngon ngu la thi giao bo chung, khong no", typeof HL.highlight("abc", "khonghieu") === "string");
check("code null khong no", HL.highlight(null, "html") === "");

// ---------------------------------------------------------------- da dau day chua
// Bo to mau chay dung chi khi CA BA cho cung khop nhau. Moi cho deu im lang khi hong: quen
// the <script> thi window.JavisCodeHL khong ton tai va ca hai trinh sua nuot loi trong
// try/catch; quen goi attach thi o sua van sua duoc, chi la khong co mau. Khong ai nhan ra.
const fs = require("fs");
const path = require("path");
const goc = path.join(__dirname, "..", "..");
const doc = (p) => fs.readFileSync(path.join(goc, p), "utf8");

const indexHtml = doc("dashboard/index.html");
check("index.html co nap code-hl.js", /<script src="\/static\/code-hl\.js\?v=/.test(indexHtml));
check("code-hl.js nap SAU chat-render.js (can window.JavisHighlight)",
      indexHtml.indexOf("/static/code-hl.js") > indexHtml.indexOf("/static/chat-render.js"));
check("chat-render.js phoi window.JavisHighlight", /window\.JavisHighlight\s*=/.test(doc("dashboard/chat-render.js")));
check("trinh sua dinh (console.js) goi attach", /JavisCodeHL\.attach\(/.test(doc("dashboard/console.js")));
check("khung sua bung giua (file-editor.js) goi attach", /JavisCodeHL\.attach\(/.test(doc("dashboard/file-editor.js")));
check("khung sua bung giua co nut Mo tab moi", /function openLink\(/.test(doc("dashboard/file-editor.js")));

const css = doc("dashboard/style.css");
check("style.css co lop phu .jvhl", css.indexOf(".jvhl-view, .jvhl .jvhl-ta") >= 0);
check("style.css chua du cho thanh cuon o ca hai lop", /scrollbar-gutter:\s*stable/.test(css));
check("style.css co bien mau the va thuoc tinh (ca hai giao dien)",
      (css.match(/--tok-t:/g) || []).length >= 2 && (css.match(/--tok-a:/g) || []).length >= 2);
check("chu trong o sua phai TRONG SUOT (de lo lop mau ben duoi)", /\.jvhl-ta \{[^}]*color: transparent/.test(css));

console.log();
if (fails.length) { console.log(fails.length + " loi: " + fails.join(", ")); process.exit(1); }
console.log("Tat ca OK");
