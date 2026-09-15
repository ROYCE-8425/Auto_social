/* Test engine Dataview lite (parse + chạy truy vấn trên chỉ mục giả). Chạy tay / CI:
     node dashboard/test_dataview.js
   KHÔNG cần trình duyệt: chỉ test hàm thuần parseQuery/execQuery/compile. */
const { parseQuery, execQuery, compile, matchFrom, fromScope, parseTasksQuery } = require("../../dashboard/dataview.js");

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok  " : "FAIL ") + name);
  if (!cond) fails++;
}

const today = new Date();
const pad = (n) => (n < 10 ? "0" : "") + n;
const TODAY = today.getFullYear() + "-" + pad(today.getMonth() + 1) + "-" + pad(today.getDate());

const FILES = [
  { path: "05 - Việc/du-an.md", name: "du-an.md", folder: "05 - Việc", mtime: 2,
    fm: { type: "project", status: "doing" }, tags: ["#duan", "#q3"],
    tasks: [
      { line: 8, raw: "- [ ] Gọi khách A 📅 2026-01-01 ⏫", text: "Gọi khách A", checked: false, due: "2026-01-01", priority: 1, tags: [] },
      { line: 9, raw: "- [x] Chốt báo giá", text: "Chốt báo giá", checked: true, priority: 3, tags: [] },
      { line: 10, raw: "- [ ] Soạn hợp đồng", text: "Soạn hợp đồng", checked: false, priority: 3, tags: ["#phap-ly"] },
    ] },
  { path: "notes/ghi-chu.md", name: "ghi-chu.md", folder: "notes", mtime: 1,
    fm: { type: "note", status: "idea" }, tags: ["#ban-hang"],
    tasks: [{ line: 3, raw: "- [ ] Việc lẻ", text: "Việc lẻ", checked: false, priority: 3, tags: [] }] },
  { path: "notes/trong.md", name: "trong.md", folder: "notes", mtime: 3, fm: {}, tags: [], tasks: [] },
];

// ---- parse ----
let q = parseQuery('TASK FROM "05 - Việc" WHERE !completed SORT due ASC LIMIT 5');
check("parse: TASK + FROM + WHERE + SORT + LIMIT", q.type === "TASK" && q.from && q.where === "!completed" && q.sort && !q.sort.desc && q.limit === 5);
check("parse: sai đầu câu -> lỗi", !!parseQuery("HELLO world").error);
check("parse: FROM [[link]] -> lỗi rõ ràng", !!parseQuery("LIST FROM [[abc]]").error);
q = parseQuery('TABLE WITHOUT ID file.name AS "Tên", status FROM "notes"');
check("parse: TABLE WITHOUT ID + cột AS", q.withoutId && q.columns.length === 2 && q.columns[0].name === "Tên" && q.columns[1].expr === "status");

// ---- matchFrom ----
q = parseQuery('LIST FROM "notes"');
check("from: thư mục", matchFrom(q.from, FILES[1]) && !matchFrom(q.from, FILES[0]));
q = parseQuery("LIST FROM #duan OR #ban-hang");
check("from: tag OR", matchFrom(q.from, FILES[0]) && matchFrom(q.from, FILES[1]) && !matchFrom(q.from, FILES[2]));
q = parseQuery('LIST FROM "notes" AND -#ban-hang');
check("from: AND + phủ định", !matchFrom(q.from, FILES[1]) && matchFrom(q.from, FILES[2]));

// ---- fromScope: suy phạm vi quét gửi server ----
q = parseQuery('TASK FROM "01 - Daily Log" OR "02 - Weekly Log"');
check("scope: gộp các thư mục", JSON.stringify(fromScope(q.from)) === JSON.stringify(["01 - Daily Log", "02 - Weekly Log"]));
q = parseQuery('TASK FROM "01 - Daily Log" OR #tag');
check("scope: nhánh OR chỉ có tag -> null (phải quét cả brain)", fromScope(q.from) === null);
q = parseQuery('TASK FROM "A" AND -"B"');
check("scope: bỏ qua phủ định, giữ thư mục dương", JSON.stringify(fromScope(q.from)) === JSON.stringify(["A"]));
q = parseQuery("TASK");
check("scope: không FROM -> null", fromScope(q.from) == null);

// ---- compile / WHERE ----
let f = compile("!completed");
check("expr: !completed", f({ completed: false }) === true && f({ completed: true }) === false);
f = compile('status = "doing"');
check("expr: so sánh chuỗi", f({ status: "doing" }) && !f({ status: "idea" }));
f = compile("due <= date(today)");
check("expr: date(today)", f({ due: "2020-01-01" }) === true && f({ due: "2999-01-01" }) === false);
check("expr: due null không nổ", compile("due < date(today)")({ due: null }) === false);
f = compile('contains(text, "khách")');
check("expr: contains chuỗi", f({ text: "Gọi khách A" }) && !f({ text: "Soạn hợp đồng" }));
f = compile('contains(tags, "#phap-ly")');
check("expr: contains mảng", f({ tags: ["#phap-ly"] }) && !f({ tags: [] }));
f = compile('(priority <= 1 OR due < date(today)) AND !completed');
check("expr: ngoặc + AND/OR", f({ priority: 1, completed: false }) === true && f({ priority: 3, completed: false, due: "2999-01-01" }) === false);
let threw = false;
try { compile("contains(text"); } catch (e) { threw = true; }
check("expr: cú pháp sai -> ném lỗi", threw);

// ---- execQuery ----
let h = execQuery(parseQuery('TASK FROM "05 - Việc" WHERE !completed'), FILES);
check("task: lọc chưa xong", h.includes("Gọi khách A") && h.includes("Soạn hợp đồng") && !h.includes("Chốt báo giá"));
check("task: checkbox mang path + line", h.includes('data-dv-path="05 - Việc/du-an.md"') && h.includes('data-dv-line="8"'));
check("task: badge quá hạn", h.includes("dv-over"));
h = execQuery(parseQuery("TASK WHERE contains(tags, \"#phap-ly\")"), FILES);
check("task: lọc theo tag của task", h.includes("Soạn hợp đồng") && !h.includes("Việc lẻ"));
h = execQuery(parseQuery("TASK LIMIT 1 SORT priority ASC"), FILES);
check("task: LIMIT + SORT priority", h.includes("Gọi khách A") && !h.includes("Việc lẻ"));

h = execQuery(parseQuery('LIST FROM "notes"'), FILES);
check("list: 2 note, có link vault", h.includes("ghi-chu") && h.includes("trong") && h.includes('data-vault-path="notes/ghi-chu.md"'));
h = execQuery(parseQuery('LIST WHERE type = "project"'), FILES);
check("list: WHERE frontmatter", h.includes("du-an") && !h.includes("ghi-chu"));

h = execQuery(parseQuery('TABLE status, file.folder AS "Thư mục" WHERE type != ""'), FILES);
check("table: cột frontmatter + file.*", h.includes("<th>File</th>") && h.includes("<th>Thư mục</th>") && h.includes("<td>doing</td>") && h.includes("<td>notes</td>"));
h = execQuery(parseQuery('TABLE WITHOUT ID file.name FROM "notes"'), FILES);
check("table: WITHOUT ID bỏ cột File", !h.includes("<th>File</th>") && h.includes("<td>ghi-chu</td>"));

h = execQuery(parseQuery('LIST FROM "khong-ton-tai"'), FILES);
check("rỗng: báo không có kết quả", h.includes("Không có kết quả"));

// ---- ngôn ngữ obsidian-tasks (khối ```tasks) ----
let tq = parseTasksQuery("not done\ndue before today\nsort by due\nlimit 20");
check("tasks: dịch not done + due before today", tq.type === "TASK" &&
  tq.where === "(!completed) AND (due < date(today))" && tq.sort && tq.sort.expr === "due" && !tq.sort.desc && tq.limit === 20);
h = execQuery(tq, FILES);
check("tasks: quá hạn ra đúng việc", h.includes("Gọi khách A") && !h.includes("Việc lẻ") && !h.includes("Chốt báo giá"));
h = execQuery(parseTasksQuery("not done\nno due date"), FILES);
check("tasks: no due date", h.includes("Soạn hợp đồng") && h.includes("Việc lẻ") && !h.includes("Gọi khách A"));
h = execQuery(parseTasksQuery("done"), FILES);
check("tasks: done", h.includes("Chốt báo giá") && !h.includes("Gọi khách A"));
h = execQuery(parseTasksQuery("description includes khách"), FILES);
check("tasks: description includes", h.includes("Gọi khách A") && !h.includes("Việc lẻ"));
h = execQuery(parseTasksQuery("tag includes phap-ly"), FILES);
check("tasks: tag includes (tự thêm #)", h.includes("Soạn hợp đồng") && !h.includes("Việc lẻ"));
h = execQuery(parseTasksQuery("priority is high"), FILES);
check("tasks: priority is high", h.includes("Gọi khách A") && !h.includes("Soạn hợp đồng"));
h = execQuery(parseTasksQuery("not done\npath includes notes"), FILES);
check("tasks: path includes", h.includes("Việc lẻ") && !h.includes("Gọi khách A"));
tq = parseTasksQuery("not done\nfilter by function task.x\nhide backlink");
check("tasks: dòng lạ -> cảnh báo, dòng hide -> bỏ qua im lặng",
  tq.warn.length === 1 && tq.warn[0].includes("filter by function") && tq.where === "(!completed)");
tq = parseTasksQuery("sort by priority reverse\nlimit to 5 tasks");
check("tasks: sort reverse + limit to N tasks", tq.sort.expr === "priority" && tq.sort.desc && tq.limit === 5);

// XSS: nội dung task/frontmatter phải được escape
const XSS = [{ path: "x.md", name: "x.md", folder: "", mtime: 0, fm: { status: '<img src=x onerror=1>' }, tags: [],
  tasks: [{ line: 1, raw: '- [ ] <script>alert(1)</script>', text: '<script>alert(1)</script>', checked: false, priority: 3, tags: [] }] }];
h = execQuery(parseQuery("TASK"), XSS);
check("xss: task text được escape", !h.includes("<script>") && h.includes("&lt;script&gt;"));
h = execQuery(parseQuery("TABLE status"), XSS);
check("xss: cell bảng được escape", !h.includes("<img src=x"));

console.log("");
if (fails) { console.log(fails + " test FAIL"); process.exit(1); }
console.log("Tất cả test dataview OK");
