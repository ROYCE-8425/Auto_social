/* Test phần thuần của task-suggest.js (gợi ý task kiểu obsidian-tasks). Chạy tay / CI:
     node dashboard/test_task_suggest.js
   KHÔNG cần trình duyệt: chỉ test tsTaskStart (nhận diện khung "- [ ]") và
   tsDateOptions (tính ngày Hôm nay / Ngày mai / Cuối tuần / Tuần sau). */
const { tsDateOptions, tsTaskStart } = require("../../dashboard/task-suggest.js");

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok  " : "FAIL ") + name);
  if (!cond) fails++;
}

// ---- tsTaskStart ----
check("start: '- [ ]' chuẩn", tsTaskStart("- [ ] "));
check("start: '- []' thiếu cách trong ngoặc vẫn nhận", tsTaskStart("- []"));
check("start: '- [x]' đã tick", tsTaskStart("- [x] "));
check("start: '* [ ]' dấu sao", tsTaskStart("* [ ]"));
check("start: nbsp của contenteditable", tsTaskStart("- [ ] "));
check("start: thiếu cách sau gạch -> không nhận", !tsTaskStart("-[ ]"));
check("start: có chữ phía sau -> không nhận (đã thành task rồi)", !tsTaskStart("- [ ] mua sữa"));
check("start: câu thường -> không nhận", !tsTaskStart("hello world"));

// ---- tsDateOptions (2026-07-28 là thứ 3) ----
const opts = tsDateOptions(new Date(2026, 6, 28));
const by = {};
opts.forEach((o) => { by[o.label] = o; });
check("date: hôm nay", by["Hôm nay"].date === "2026-07-28");
check("date: ngày mai", by["Ngày mai"].date === "2026-07-29");
check("date: cuối tuần = thứ 7 gần nhất", by["Cuối tuần (thứ 7)"].date === "2026-08-01");
check("date: tuần sau = thứ 2 kế tiếp", by["Tuần sau (thứ 2)"].date === "2026-08-03");
check("date: có mục chọn ngày tay", opts.some((o) => o.pick));

// đứng ĐÚNG thứ 7 thì "cuối tuần" phải là thứ 7 TUẦN SAU (không phải hôm nay)
const sat = tsDateOptions(new Date(2026, 7, 1));   // 2026-08-01 là thứ 7
const sby = {};
sat.forEach((o) => { sby[o.label] = o; });
check("date: đứng thứ 7 -> cuối tuần nhảy tuần kế", sby["Cuối tuần (thứ 7)"].date === "2026-08-08");
// đứng thứ 2 -> "tuần sau" là thứ 2 tuần kế
const mon = tsDateOptions(new Date(2026, 7, 3));   // 2026-08-03 là thứ 2
const mby = {};
mon.forEach((o) => { mby[o.label] = o; });
check("date: đứng thứ 2 -> tuần sau nhảy tuần kế", mby["Tuần sau (thứ 2)"].date === "2026-08-10");

console.log("");
if (fails) { console.log(fails + " test FAIL"); process.exit(1); }
console.log("Tất cả test task-suggest OK");
