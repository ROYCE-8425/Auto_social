/* Test timelapse "cuộc đời brain" (graph.js). Chạy tay / CI:
     node dashboard/test_graph_timelapse.js
   KHÔNG cần trình duyệt: stub ForceGraph chỉ ghi lại các lần đổ graphData. */
global.window = global;                     // graph.js gắn class vào window
global.document = { createElement: () => ({ getContext: () => null }) };
const _events = [];
global.window.dispatchEvent = (e) => { _events.push(e && e.type); };

require("../../dashboard/graph.js");
const JavisGraph = window.JavisGraph;

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok  " : "FAIL ") + name);
  if (!cond) fails++;
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// Stub ForceGraph: nhớ MỌI lần graphData(set) để soi trình tự chiếu phim
const frames = [];
function stubGraph(initial) {
  let cur = initial;
  return {
    graphData(d) {
      if (d === undefined) return cur;
      cur = d; frames.push({ nodes: d.nodes.slice(), links: d.links.slice() });
      return this;
    },
    warmupTicks() { return this; },
  };
}

// Vault giả: 6 note với mốc ra đời t xáo trộn + link chéo
const N = (id, t) => ({ id, label: id, t, links: 0 });
const nodes = [N("e", 50), N("a", 10), N("c", 30), N("f", 60), N("b", 20), N("d", 40)];
const links = [
  { source: "a", target: "b" },
  { source: "a", target: "f" },
  { source: "c", target: "d" },
  { source: "e", target: "b" },
];

(async () => {
  const g = new JavisGraph({}, {});
  g.graph = stubGraph({ nodes, links });

  check("chưa chạy: timelapseRunning=false", g.timelapseRunning === false);
  // Nhịp CỐ ĐỊNH mỗi note (test dùng 60ms cho nhanh) → 6 note = 6 nhịp, não dày phim dài
  check("startTimelapse trả true", g.startTimelapse(60) === true);
  check("đang chạy: timelapseRunning=true", g.timelapseRunning === true);
  check("khung đầu tiên là não trống", frames[0].nodes.length === 0 && frames[0].links.length === 0);
  check("gọi start lần 2 khi đang chạy → false", g.startTimelapse(60) === false);

  await sleep(800);   // đợi hết phim (6 nhịp x 60ms + dư an toàn)

  check("hết phim: timelapseRunning=false", g.timelapseRunning === false);
  check("bắn sự kiện javis-timelapse-end", _events.includes("javis-timelapse-end"));

  // Trình tự thời gian: mỗi khung node phải là PREFIX của [a,b,c,d,e,f] (xếp theo t tăng)
  const wantOrder = ["a", "b", "c", "d", "e", "f"];
  const growing = frames.slice(1, -1);   // bỏ khung trống đầu + khung khôi phục cuối
  check("mỗi nhịp đúng MỘT note (6 note = 6 khung)", growing.length === 6);
  check("khung sau nhiều hơn khung trước đúng 1 node",
    growing.every((f, i) => f.nodes.length === i + 1));
  check("node hiện dần đúng thứ tự ra đời",
    growing.every(f => f.nodes.every((n, i) => n.id === wantOrder[i])));
  check("link chỉ hiện khi CẢ HAI đầu đã ra đời",
    growing.every(f => {
      const present = new Set(f.nodes.map(n => n.id));
      return f.links.every(l => present.has(l.source) && present.has(l.target));
    }));
  // Nhịp cụ thể: sau nhịp 2 có a,b → link a-b phải xuất hiện, link a-f thì CHƯA
  const step2 = growing.find(f => f.nodes.length === 2);
  check("nhịp 2 (a,b): có link a-b, chưa có a-f",
    !!step2 && step2.links.some(l => l.source === "a" && l.target === "b")
            && !step2.links.some(l => l.target === "f"));

  const last = frames[frames.length - 1];
  check("khung cuối khôi phục ĐỦ mạng (6 node, 4 link)",
    last.nodes.length === 6 && last.links.length === 4);
  check("node được xoá toạ độ để d3 dựng lại từ đầu (fx/fy=null)",
    nodes.every(n => n.fx === null && n.fy === null));

  // Bấm dừng giữa chừng: chạy lại (nhịp chậm để chưa kịp hết) rồi stop ngay → khôi phục đủ mạng
  _events.length = 0;
  g.startTimelapse(10000);
  await sleep(200);
  g.stopTimelapse();
  const afterStop = g.graph.graphData();
  check("dừng giữa chừng: trả lại đủ mạng ngay", afterStop.nodes.length === 6 && afterStop.links.length === 4);
  check("dừng giữa chừng: có sự kiện end", _events.includes("javis-timelapse-end"));
  check("dừng xong: timelapseRunning=false", g.timelapseRunning === false);

  console.log();
  if (fails) { console.log(`FAIL ${fails} test`); process.exit(1); }
  console.log("TẤT CẢ PASS");
})();
