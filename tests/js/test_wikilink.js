/* Test wkResolve - bo tim file dich cho wikilink [[..]] (chat-render.js). Chay tay / CI:
       node dashboard/test_wikilink.js
   KHONG can trinh duyet lan server: stub global.fetch gia lap /files/list + /files/search. */
"use strict";

// ---- stub fetch TRUOC khi require (chat-render chi goi fetch luc click, nhung cho chac) ----
const HOME = "My Bullet Journal";
let FILES = [];   // danh sach file gia lap trong vault: path tinh theo TRAN (co tien to HOME)
global.fetch = (url) => {
  const u = String(url);
  const ok = (body) => Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
  if (u.indexOf("/files/list") === 0) return ok({ home: HOME, items: [] });
  if (u.indexOf("/files/search") === 0) {
    // giong server that (_fold_accents): khop TEN khong phan biet dau tieng Viet
    const fold = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[đĐ]/g, "d").toLowerCase();
    const q = decodeURIComponent((/[?&]q=([^&]*)/.exec(u) || [])[1] || "").toLowerCase();
    const items = FILES.filter((p) => {
      const name = p.split("/").pop();
      return name.toLowerCase().indexOf(q) >= 0 || fold(name).indexOf(fold(q)) >= 0;
    })
      .map((p) => {
        const name = p.split("/").pop();
        const i = name.lastIndexOf(".");
        return { path: p, name, ext: i >= 0 ? name.slice(i).toLowerCase() : "", snippet: "", line: 0, match: "name" };
      });
    return ok({ items, q });
  }
  return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
};

const { wkResolve } = require("../../dashboard/chat-render.js");

let fails = [];
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails.push(name);
}

(async () => {
  // ---- 1. Wikilink co thu muc, khong duoi .md -> khop DUOI duong dan (kieu Obsidian) ----
  FILES = [
    HOME + "/07 - Wiki/business/Danh Muc Du An Dang Lam - Minh Quy.md",
    HOME + "/06 - Sources/khac.md",
  ];
  let hit = await wkResolve("business/Danh Muc Du An Dang Lam - Minh Quy");
  check("duoi path: tim thay", !!hit);
  check("duoi path: dung file", hit && hit.ceil === FILES[0]);
  check("duoi path: rel bo tien to home", hit && hit.rel === "07 - Wiki/business/Danh Muc Du An Dang Lam - Minh Quy.md");

  // ---- 2. Chi TEN note (khong thu muc), file nam sau trong cay ----
  FILES = [HOME + "/07 - Wiki/_entities/Chi Nga - Khach Coaching Performance Ads.md"];
  hit = await wkResolve("Chi Nga - Khach Coaching Performance Ads");
  check("ten note: tim thay o thu muc sau", !!hit && hit.rel.indexOf("_entities/") >= 0);

  // ---- 3. Khong phan biet HOA thuong + dau tieng Viet ----
  FILES = [HOME + "/07 - Wiki/Chị Nga - Khách Coaching.md"];
  hit = await wkResolve("chi nga - khach coaching");
  check("khong dau: van khop ten co dau", !!hit);

  // ---- 4. Ten note co DAU CHAM (N.bk) khong bi tuong nham la duoi file ----
  FILES = [HOME + "/07 - Wiki/business/Job Ads N.bk - TK1 Digital Wave.md"];
  hit = await wkResolve("business/Job Ads N.bk - TK1 Digital Wave");
  check("ten co dau cham: van tim thay", !!hit);

  // ---- 5. Uu tien .md khi trung ten voi file khac duoi ----
  FILES = [HOME + "/notes/abc.txt", HOME + "/notes/abc.md"];
  hit = await wkResolve("abc");
  check("uu tien .md", !!hit && hit.ext === ".md");

  // ---- 6. Target co duoi that (anh) -> mo dung file anh ----
  FILES = [HOME + "/attachments/nuoc-mam.jpg"];
  hit = await wkResolve("attachments/nuoc-mam.jpg");
  check("duoi that: tim thay file anh", !!hit && hit.ext === ".jpg");

  // ---- 7. Khong co file -> null (va khong no) ----
  FILES = [];
  hit = await wkResolve("khong ton tai dau nhe");
  check("khong thay: tra null", hit === null || hit === undefined || !hit);

  // ---- 8. [[note#heading]] -> bo phan heading khi tim ----
  FILES = [HOME + "/07 - Wiki/ghi chu.md"];
  hit = await wkResolve("ghi chu#Muc 2");
  check("co #heading: van tim thay note", !!hit && hit.name === "ghi chu.md");

  if (fails.length) {
    console.log("\nFAIL - " + fails.length + " test: " + fails.join(", "));
    process.exit(1);
  }
  console.log("\nOK - test_wikilink: tat ca pass");
})();
