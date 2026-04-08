const pptxgen = require("pptxgenjs");

// ====== 颜色与字体常量 ======
const C = {
  navy: "0F172A", navyLight: "1E293B", slate: "334155",
  accent: "6366F1", accentLight: "818CF8", cyan: "06B6D4",
  emerald: "10B981", amber: "F59E0B", rose: "F43F5E",
  white: "F8FAFC", gray: "94A3B8", grayDark: "64748B",
  cardBg: "1E293B", cardBorder: "334155",
};
const FONT_H = "Calibri";
const FONT_B = "Calibri Light";

// ====== 工具函数 ======
const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.25 });

function addPageNum(slide, num, total) {
  slide.addText(`${num} / ${total}`, {
    x: 8.8, y: 5.2, w: 1, h: 0.3, fontSize: 9,
    color: C.grayDark, fontFace: FONT_B, align: "right",
  });
}

function addFooter(slide) {
  slide.addShape("rect", { x: 0, y: 5.3, w: 10, h: 0.325, fill: { color: C.accent, transparency: 85 } });
  slide.addText("KubeSentinel | Kubernetes AIOps", {
    x: 0.5, y: 5.35, w: 5, h: 0.25, fontSize: 8, color: C.grayDark, fontFace: FONT_B,
  });
}

// 添加带左侧色条的卡片
function addCard(slide, x, y, w, h, accentColor, title, bullets, opts = {}) {
  slide.addShape("rect", { x, y, w, h, fill: { color: C.cardBg }, shadow: makeShadow() });
  slide.addShape("rect", { x, y, w: 0.06, h, fill: { color: accentColor } });
  if (title) {
    slide.addText(title, {
      x: x + 0.2, y: y + 0.08, w: w - 0.3, h: 0.35,
      fontSize: 13, fontFace: FONT_H, color: C.white, bold: true, margin: 0,
    });
  }
  if (bullets && bullets.length) {
    const textArr = bullets.map((b, i) => ({
      text: b, options: { bullet: true, breakLine: i < bullets.length - 1, fontSize: 11, color: C.gray },
    }));
    slide.addText(textArr, {
      x: x + 0.2, y: y + (title ? 0.4 : 0.1), w: w - 0.3, h: h - (title ? 0.5 : 0.2),
      fontFace: FONT_B, valign: "top", paraSpaceAfter: 4,
    });
  }
}

// 添加大号指标卡
function addStatCard(slide, x, y, w, h, num, label, color) {
  slide.addShape("rect", { x, y, w, h, fill: { color: C.cardBg }, shadow: makeShadow() });
  slide.addShape("rect", { x, y: y + h - 0.05, w, h: 0.05, fill: { color } });
  slide.addText(num, { x, y: y + 0.1, w, h: 0.5, fontSize: 28, fontFace: FONT_H, color, align: "center", bold: true, margin: 0 });
  slide.addText(label, { x, y: y + 0.55, w, h: 0.3, fontSize: 10, fontFace: FONT_B, color: C.gray, align: "center", margin: 0 });
}

const TOTAL = 14;

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "KubeSentinel Team";
  pres.title = "KubeSentinel - Kubernetes AIOps Platform";

  // ========== 1. 封面 ==========
  let slide = pres.addSlide();
  slide.background = { color: C.navy };
  // 装饰圆
  slide.addShape("oval", { x: -1.5, y: -1, w: 5, h: 5, fill: { color: C.accent, transparency: 90 } });
  slide.addShape("oval", { x: 7, y: 2, w: 4, h: 4, fill: { color: C.cyan, transparency: 90 } });
  slide.addText("KubeSentinel", {
    x: 0.8, y: 1.2, w: 8.5, h: 1, fontSize: 44, fontFace: FONT_H, color: C.white, bold: true, margin: 0,
  });
  slide.addText([
    { text: "Kubernetes ", options: { color: C.accentLight } },
    { text: "AIOps ", options: { color: C.cyan } },
    { text: "Platform", options: { color: C.accentLight } },
  ], { x: 0.8, y: 2.1, w: 8.5, h: 0.5, fontSize: 22, fontFace: FONT_H, margin: 0 });
  slide.addText("基于大语言模型的 Kubernetes 智能自愈与 AIOps 平台", {
    x: 0.8, y: 2.7, w: 8, h: 0.4, fontSize: 14, fontFace: FONT_B, color: C.gray, margin: 0,
  });
  slide.addShape("rect", { x: 0.8, y: 3.3, w: 2.5, h: 0.04, fill: { color: C.accent } });
  slide.addText("毕业设计答辩", {
    x: 0.8, y: 3.6, w: 4, h: 0.35, fontSize: 13, fontFace: FONT_B, color: C.grayDark, margin: 0,
  });
  slide.addText("2026 年 4 月", {
    x: 0.8, y: 3.95, w: 4, h: 0.3, fontSize: 11, fontFace: FONT_B, color: C.grayDark, margin: 0,
  });

  // ========== 2. 目录 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 2, TOTAL);
  slide.addText("CONTENTS", { x: 0.8, y: 0.4, w: 4, h: 0.5, fontSize: 28, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addText("目录", { x: 0.8, y: 0.85, w: 2, h: 0.3, fontSize: 12, fontFace: FONT_B, color: C.grayDark, margin: 0 });
  const tocItems = [
    ["01", "研究背景与意义"], ["02", "研究目的与目标"], ["03", "国内外研究现状"],
    ["04", "关键技术分析"], ["05", "系统总体架构"], ["06", "核心模块设计"],
    ["07", "OODA 智能闭环"], ["08", "前端可视化展示"], ["09", "n8n 工作流编排"],
    ["10", "混沌工程验证"], ["11", "创新点与贡献"], ["12", "总结与展望"],
  ];
  tocItems.forEach(([num, title], i) => {
    const col = i < 6 ? 0 : 1;
    const row = i % 6;
    const bx = 0.8 + col * 4.5;
    const by = 1.45 + row * 0.6;
    slide.addText(num, { x: bx, y: by, w: 0.45, h: 0.4, fontSize: 16, fontFace: FONT_H, color: C.accent, bold: true, margin: 0 });
    slide.addText(title, { x: bx + 0.55, y: by, w: 3.5, h: 0.4, fontSize: 13, fontFace: FONT_B, color: C.white, margin: 0 });
    slide.addShape("rect", { x: bx + 0.55, y: by + 0.38, w: 3, h: 0.01, fill: { color: C.cardBorder } });
  });

  // ========== 3. 研究背景与意义 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 3, TOTAL);
  slide.addText("01  研究背景与意义", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  addStatCard(slide, 0.5, 1.2, 2.1, 0.95, "30min+", "平均故障恢复时间", C.rose);
  addStatCard(slide, 2.8, 1.2, 2.1, 0.95, "100+", "告警风暴日均条数", C.amber);
  addStatCard(slide, 5.1, 1.2, 2.1, 0.95, "80%", "重复手动操作占比", C.cyan);
  addStatCard(slide, 7.4, 1.2, 2.1, 0.95, "< 3s", "目标自愈响应时间", C.emerald);

  addCard(slide, 0.5, 2.4, 4.3, 2.6, C.rose, "行业痛点", [
    "微服务架构指数级膨胀，告警风暴频发",
    "SRE 需在 Grafana/Kibana/Terminal 间切换排查",
    "MTTR 严重依赖个人经验，居高不下",
    "静态阈值告警无法发现缓慢性能衰退",
    "人工 7x24 值班成本高昂，效率低下",
  ]);
  addCard(slide, 5.2, 2.4, 4.3, 2.6, C.emerald, "研究意义", [
    "将 LLM 推理能力引入 SRE 排障链路",
    "实现从告警到修复的全自动化闭环",
    "降低 MTTR 至秒级，减少人工干预",
    "提供可解释、可审计的 AI 决策过程",
    "探索 AIOps 与 Kubernetes Operator 融合范式",
  ]);

  // ========== 4. 研究目的与目标 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 4, TOTAL);
  slide.addText("02  研究目的与目标", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  slide.addText("核心目标", { x: 0.5, y: 1.15, w: 3, h: 0.35, fontSize: 14, fontFace: FONT_H, color: C.accentLight, bold: true, margin: 0 });
  slide.addText("构建一套基于大语言模型的 Kubernetes 集群智能自愈平台，实现告警接收、AI 根因分析、安全门控、自动修复的完整 OODA 闭环。", {
    x: 0.5, y: 1.5, w: 9, h: 0.6, fontSize: 12, fontFace: FONT_B, color: C.gray, margin: 0,
  });

  const goals = [
    [C.accent, "LLM 根因分析引擎", "集成 GLM-5/DeepSeek 大模型，通过 Chain-of-Thought 和 Tool Calling 实现自主推理式故障诊断"],
    [C.cyan, "ML 异常预测模块", "基于 IsolationForest 对 CPU/内存多维指标进行无监督异常检测，提前发现性能衰退"],
    [C.emerald, "Kubernetes Operator", "使用 Go + Kubebuilder 实现 HealingRule CRD 控制器，执行滚动重启、扩缩容、回滚等 8 种自愈动作"],
    [C.amber, "n8n 审批工作流", "高风险操作自动触发可视化审批流，支持飞书/钉钉通知，实现人机协同"],
    [C.rose, "全栈可视化平台", "Vue 3 玻璃拟态暗黑大屏 + AI Copilot 副驾驶，实时 WebSocket 推送"],
    [C.accentLight, "MCP 协议扩展", "通过 FastMCP Server 暴露 AI 诊断能力，支持 Cursor/Claude Desktop 直连"],
  ];
  goals.forEach(([color, title, desc], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const cx = 0.5 + col * 4.65;
    const cy = 2.3 + row * 1.0;
    addCard(slide, cx, cy, 4.45, 0.88, color, title, [desc]);
  });

  // ========== 5. 国内外研究现状 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 5, TOTAL);
  slide.addText("03  国内外研究现状", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  // 表格
  const headerOpts = { fill: { color: C.accent }, color: "FFFFFF", bold: true, fontSize: 11, fontFace: FONT_H, align: "center", valign: "middle" };
  const cellOpts = { fill: { color: C.cardBg }, color: C.gray, fontSize: 10, fontFace: FONT_B, valign: "middle", border: { pt: 0.5, color: C.cardBorder } };
  slide.addTable([
    [
      { text: "方向", options: headerOpts },
      { text: "代表工作", options: headerOpts },
      { text: "局限性", options: headerOpts },
      { text: "本项目改进", options: headerOpts },
    ],
    [
      { text: "传统 AIOps", options: cellOpts },
      { text: "MOOGSOFT, BigPanda", options: cellOpts },
      { text: "基于统计规则，缺乏语义理解", options: cellOpts },
      { text: "引入 LLM 语义推理能力", options: cellOpts },
    ],
    [
      { text: "K8s Operator", options: cellOpts },
      { text: "Node Problem Detector", options: cellOpts },
      { text: "仅检测不修复，缺少 AI 决策", options: cellOpts },
      { text: "AI 决策 + Operator 自动执行", options: cellOpts },
    ],
    [
      { text: "LLM for DevOps", options: cellOpts },
      { text: "K8sGPT, Holmes", options: cellOpts },
      { text: "主要做诊断建议，不闭环执行", options: cellOpts },
      { text: "诊断-审批-执行全闭环", options: cellOpts },
    ],
    [
      { text: "ML 异常检测", options: cellOpts },
      { text: "Prometheus + ML", options: cellOpts },
      { text: "单维度阈值，误报率高", options: cellOpts },
      { text: "多维隔离森林 + LLM 二次验证", options: cellOpts },
    ],
  ], { x: 0.5, y: 1.15, w: 9, colW: [1.5, 2.2, 2.8, 2.5] });

  slide.addText("本项目创新定位", { x: 0.5, y: 3.6, w: 4, h: 0.35, fontSize: 13, fontFace: FONT_H, color: C.accentLight, bold: true, margin: 0 });
  slide.addText([
    { text: "区别于现有方案仅停留在 \"诊断建议\" 层面，KubeSentinel 实现了从 LLM 诊断、安全门控、人机审批到 Kubernetes 原生 Operator 物理执行的完整闭环。", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "这是国内首个将 LLM + CRD Operator + n8n DAG 审批融合为一体的开源 AIOps 自愈平台原型。", options: { fontSize: 11, color: C.amber } },
  ], { x: 0.5, y: 3.95, w: 9, h: 1.1, fontFace: FONT_B, valign: "top" });

  // ========== 6. 关键技术分析 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 6, TOTAL);
  slide.addText("04  关键技术分析", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  const techs = [
    [C.accent, "FastAPI + asyncpg + Redis", ["全异步非阻塞后端架构", "PostgreSQL 持久化 + Redis 冷却缓存", "WebSocket 实时事件推送"]],
    [C.cyan, "GLM-5 / DeepSeek LLM", ["Chain-of-Thought 推理链", "Tool Calling 自主调用 K8s API", "结构化 JSON 输出约束"]],
    [C.emerald, "Go Kubebuilder Operator", ["controller-runtime 控制器框架", "HealingRule CRD 自定义资源", "8 种自愈动作的原生执行"]],
    [C.amber, "Isolation Forest ML", ["scikit-learn 无监督异常检测", "CPU/内存多维特征聚类", "主动预测性能衰退趋势"]],
    [C.rose, "Vue 3 + ECharts", ["玻璃拟态 Glassmorphism UI", "Element Plus 组件库", "AI Copilot 自然语言交互"]],
    [C.accentLight, "n8n + FastMCP", ["零代码 DAG 审批工作流", "飞书/钉钉 Webhook 通知集成", "MCP 协议 AI 能力暴露"]],
  ];
  techs.forEach(([color, title, items], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    addCard(slide, 0.5 + col * 3.1, 1.15 + row * 2.15, 2.9, 1.95, color, title, items);
  });

  // ========== 7. 系统总体架构 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 7, TOTAL);
  slide.addText("05  系统总体架构", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  // 五层架构
  const layers = [
    { label: "前端展示层", tech: "Vue 3  |  Element Plus  |  ECharts  |  WebSocket", color: C.accent, y: 1.1 },
    { label: "智能决策层", tech: "FastAPI  |  LLM Service  |  Prometheus/Loki Query  |  PostgreSQL/Redis", color: C.cyan, y: 1.98 },
    { label: "工作流编排层", tech: "n8n Webhook  |  Switch 审批  |  飞书/钉钉通知  |  Callback", color: C.amber, y: 2.86 },
    { label: "自愈执行层", tech: "Go Operator  |  HealingRule CRD  |  controller-runtime", color: C.emerald, y: 3.74 },
    { label: "可观测基础层", tech: "Prometheus  |  Alertmanager  |  Loki  |  Grafana  |  kube-state-metrics", color: C.rose, y: 4.62 },
  ];
  layers.forEach((l) => {
    slide.addShape("rect", { x: 0.5, y: l.y, w: 9, h: 0.75, fill: { color: C.cardBg }, shadow: makeShadow() });
    slide.addShape("rect", { x: 0.5, y: l.y, w: 0.06, h: 0.75, fill: { color: l.color } });
    slide.addText(l.label, { x: 0.7, y: l.y + 0.05, w: 2, h: 0.35, fontSize: 13, fontFace: FONT_H, color: l.color, bold: true, margin: 0 });
    slide.addText(l.tech, { x: 0.7, y: l.y + 0.38, w: 8.5, h: 0.3, fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0 });
  });
  // 箭头
  for (let i = 0; i < 4; i++) {
    slide.addText("\u25BC", { x: 4.7, y: layers[i].y + 0.7, w: 0.6, h: 0.35, fontSize: 14, color: C.grayDark, align: "center", fontFace: FONT_B, margin: 0 });
  }

  // ========== 8. 核心模块设计 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 8, TOTAL);
  slide.addText("06  核心模块设计", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  addCard(slide, 0.5, 1.1, 4.35, 1.9, C.accent, "LLM 诊断引擎 (llm_service.py)", [
    "System Prompt 注入 Senior SRE 角色身份",
    "支持 DashScope / OpenAI 双供应商切换",
    "3 层 JSON 解析策略 (直接/去Markdown/大括号匹配)",
    "最多 3 次重试 + 安全 fallback 兜底",
  ]);
  addCard(slide, 5.15, 1.1, 4.35, 1.9, C.emerald, "Go Operator (healingrule_controller.go)", [
    "Watch HealingRule CRD 变更事件",
    "Reconcile 状态机: Pending -> Executing -> Completed/Failed",
    "8 种动作: restart/scale/rollback/cordon/evict/hpa...",
    "Best-effort HTTP callback 回调后端",
  ]);
  addCard(slide, 0.5, 3.2, 4.35, 1.9, C.cyan, "告警处理主链路 (api/alerts.py)", [
    "接收 Alertmanager POST Webhook",
    "Redis 冷却去重 + Prometheus/Loki 上下文采集",
    "LLM 分析 -> 安全门控 (置信度/风险级别判定)",
    "低风险直接创建 CRD，高风险触发 n8n 审批",
  ]);
  addCard(slide, 5.15, 3.2, 4.35, 1.9, C.amber, "AIOps ML 引擎 (aiops_service.py)", [
    "Prometheus 时序数据范围查询",
    "Pandas DataFrame 多维特征对齐",
    "IsolationForest 拟合 + 异常点标记",
    "异常结果作为 LLM 诊断的上下文增强",
  ]);

  // ========== 9. OODA 智能闭环 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 9, TOTAL);
  slide.addText("07  OODA 智能自愈闭环", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  const ooda = [
    { letter: "O", title: "Observe", sub: "观察神经网", desc: "kube-state-metrics + node-exporter 遥测采集\nPrometheus 时序存储 + Alertmanager 告警触发", color: C.cyan, x: 0.5 },
    { letter: "O", title: "Orient", sub: "定位哨兵站", desc: "Alertmanager Webhook 推送\nML IsolationForest 多维异常检测\n冷却去重 + 上下文聚合", color: C.amber, x: 2.85 },
    { letter: "D", title: "Decide", sub: "参谋决策层", desc: "LLM Chain-of-Thought 根因推理\nTool Calling 自主调查\n安全门控: 置信度/风险/审批", color: C.accent, x: 5.2 },
    { letter: "A", title: "Act", sub: "特种执行队", desc: "HealingRule CRD 下发\nGo Operator Reconcile 执行\n滚动重启/扩缩容/回滚/驱逐", color: C.emerald, x: 7.55 },
  ];
  ooda.forEach((o) => {
    slide.addShape("rect", { x: o.x, y: 1.15, w: 2.15, h: 3.8, fill: { color: C.cardBg }, shadow: makeShadow() });
    slide.addShape("rect", { x: o.x, y: 1.15, w: 2.15, h: 0.06, fill: { color: o.color } });
    slide.addText(o.letter, { x: o.x, y: 1.3, w: 2.15, h: 0.6, fontSize: 36, fontFace: FONT_H, color: o.color, align: "center", bold: true, margin: 0 });
    slide.addText(o.title, { x: o.x, y: 1.85, w: 2.15, h: 0.35, fontSize: 14, fontFace: FONT_H, color: C.white, align: "center", bold: true, margin: 0 });
    slide.addText(o.sub, { x: o.x, y: 2.15, w: 2.15, h: 0.3, fontSize: 10, fontFace: FONT_B, color: C.grayDark, align: "center", margin: 0 });
    slide.addShape("rect", { x: o.x + 0.3, y: 2.5, w: 1.55, h: 0.01, fill: { color: C.cardBorder } });
    slide.addText(o.desc, { x: o.x + 0.15, y: 2.6, w: 1.85, h: 2.2, fontSize: 10, fontFace: FONT_B, color: C.gray, valign: "top", margin: 0 });
  });

  // ========== 10. 前端可视化 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 10, TOTAL);
  slide.addText("08  前端可视化展示", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  addCard(slide, 0.5, 1.1, 4.4, 2.0, C.accent, "Dashboard (Dashboard.vue)", [
    "4 项实时统计卡片: 告警数/自愈次数/成功率/待审批",
    "ECharts 趋势折线图 + 故障类型饼图 + 成功率仪表盘",
    "模拟告警一键触发",
    "Glassmorphism 暗黑玻璃拟态设计美学",
  ]);
  addCard(slide, 5.1, 1.1, 4.4, 2.0, C.cyan, "Alerts (Alerts.vue)", [
    "告警列表: 实时展示告警状态与 AI 分析结果",
    "审批操作: 一键授权/拒绝高风险动作",
    "AI 分析详情展开: 根因、置信度、建议动作",
    "状态标签: 待审批/已执行/已拒绝/无需动作",
  ]);
  addCard(slide, 0.5, 3.3, 4.4, 1.7, C.emerald, "AI Copilot (AICopilot.vue)", [
    "右侧悬浮智能副驾驶助手",
    "自然语言提问: \"为什么订单服务挂了?\"",
    "WebSocket 流式输出诊断报告",
    "Tool Calling: 自主查日志、事件、PromQL",
  ]);
  addCard(slide, 5.1, 3.3, 4.4, 1.7, C.amber, "History (History.vue)", [
    "历史告警时间线回溯",
    "审计日志: 记录所有 AI 决策与人工操作",
    "操作追溯: 谁在什么时间做了什么",
    "完整的可审计性保障",
  ]);

  // ========== 11. n8n 工作流 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 11, TOTAL);
  slide.addText("09  n8n 工作流编排", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  // 流程
  const flowSteps = [
    { label: "Webhook\n接收告警", color: C.accent },
    { label: "Switch\n风险分级", color: C.amber },
    { label: "飞书/钉钉\n通知审批", color: C.cyan },
    { label: "Wait\n等待响应", color: C.grayDark },
    { label: "Callback\n回传结果", color: C.emerald },
  ];
  flowSteps.forEach((s, i) => {
    const fx = 0.5 + i * 1.95;
    slide.addShape("rect", { x: fx, y: 1.2, w: 1.6, h: 0.9, fill: { color: C.cardBg }, shadow: makeShadow() });
    slide.addShape("rect", { x: fx, y: 1.2, w: 1.6, h: 0.05, fill: { color: s.color } });
    slide.addText(s.label, { x: fx, y: 1.3, w: 1.6, h: 0.75, fontSize: 11, fontFace: FONT_H, color: C.white, align: "center", valign: "middle", margin: 0 });
    if (i < flowSteps.length - 1) {
      slide.addText("\u25B6", { x: fx + 1.6, y: 1.45, w: 0.35, h: 0.4, fontSize: 12, color: C.grayDark, align: "center", fontFace: FONT_B, margin: 0 });
    }
  });

  addCard(slide, 0.5, 2.4, 4.35, 2.7, C.accent, "工作流设计要点", [
    "零代码 DAG 可视化编排，无需 Python 硬编码",
    "Webhook 节点接收后端 JSON payload",
    "Switch 节点按 risk_level 分流高/中/低风险",
    "HTTP Request 节点发送飞书/钉钉卡片消息",
    "Wait 节点等待人工审批响应",
    "Callback 节点将审批结果回传后端 API",
  ]);
  addCard(slide, 5.15, 2.4, 4.35, 2.7, C.emerald, "安全门控策略", [
    "置信度 < 0.6: 强制人工审批 + investigate",
    "置信度 0.6~0.75: 可执行但需人工确认",
    "置信度 > 0.75: 允许自动执行",
    "risk_level = high: 无论置信度均需审批",
    "冷却机制: 300s 内同目标不重复处理",
    "飞书/钉钉双通道通知保障到达率",
  ]);

  // ========== 12. 混沌工程验证 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 12, TOTAL);
  slide.addText("10  混沌工程验证", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  addCard(slide, 0.5, 1.1, 4.35, 2.0, C.rose, "混沌注入工具 (chaos-inject.sh)", [
    "CPU Stress: stress-ng 打满容器 CPU",
    "Memory Leak: 持续分配内存模拟 OOM",
    "Network Delay: 注入网络延迟和丢包",
    "Pod Kill: 随机杀死目标 Pod 测试自愈",
    "支持 --target / --type / --duration 参数化",
  ]);
  addCard(slide, 5.15, 1.1, 4.35, 2.0, C.emerald, "验证流程与预期结果", [
    "1. 注入 CPU 压力 -> Prometheus 告警触发",
    "2. Alertmanager Webhook 推送至后端",
    "3. LLM 分析并返回 rolling_restart 决策",
    "4. Go Operator 执行滚动重启",
    "5. 前端大屏实时展示自愈全过程",
  ]);
  addCard(slide, 0.5, 3.3, 9, 1.7, C.cyan, "端到端测试 (Playwright)", [
    "e2e_frontend.py: 使用 Playwright 自动化测试前端 Dashboard、Alerts、AI Copilot 页面",
    "setup-cluster.sh: 一键部署 kube-prometheus-stack 监控底座",
    "validate-setup.sh: 验证集群中所有组件健康状态",
    "simulate-alert.py: Python 脚本模拟 Alertmanager Webhook 推送测试告警",
  ]);

  // ========== 13. 创新点 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addFooter(slide); addPageNum(slide, 13, TOTAL);
  slide.addText("11  创新点与贡献", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  const innovations = [
    [C.accent, "LLM + Operator 融合闭环", "首次将大语言模型的推理能力与 Kubernetes Operator 的物理执行能力结合，实现从告警到修复的全自动化闭环，超越了 K8sGPT 等仅提供诊断建议的方案。"],
    [C.cyan, "可解释可审计的 AI 决策", "LLM 决策全程落库并附带分析推理过程、置信度评分和风险等级，实现完整的审计链路，满足金融等行业的合规要求。"],
    [C.emerald, "多维异常检测增强 LLM", "IsolationForest 在 LLM 调用前提供数据驱动的异常判定，减少 LLM 幻觉，提高诊断准确性。"],
    [C.amber, "人机协同安全门控", "高风险操作通过 n8n 零代码审批流实现人机协同，在自动化效率与安全可控之间取得平衡。"],
    [C.rose, "MCP 协议生态扩展", "通过 FastMCP 暴露 AI 诊断能力，使 Cursor/Claude Desktop 等客户端可直接接入，拓展了 AIOps 平台的边界。"],
  ];
  innovations.forEach(([color, title, desc], i) => {
    const iy = 1.15 + i * 0.82;
    slide.addShape("rect", { x: 0.5, y: iy, w: 9, h: 0.72, fill: { color: C.cardBg }, shadow: makeShadow() });
    slide.addShape("rect", { x: 0.5, y: iy, w: 0.06, h: 0.72, fill: { color } });
    slide.addText(`0${i + 1}`, { x: 0.7, y: iy + 0.05, w: 0.4, h: 0.3, fontSize: 16, fontFace: FONT_H, color, bold: true, margin: 0 });
    slide.addText(title, { x: 1.15, y: iy + 0.05, w: 2.5, h: 0.3, fontSize: 13, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
    slide.addText(desc, { x: 1.15, y: iy + 0.33, w: 8.1, h: 0.35, fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0 });
  });

  // ========== 14. 总结与展望 ==========
  slide = pres.addSlide();
  slide.background = { color: C.navy };
  addPageNum(slide, 14, TOTAL);
  slide.addShape("oval", { x: 6.5, y: -1, w: 5, h: 5, fill: { color: C.accent, transparency: 90 } });
  slide.addShape("oval", { x: -2, y: 3, w: 5, h: 5, fill: { color: C.cyan, transparency: 90 } });

  slide.addText("12  总结与展望", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, margin: 0 });
  slide.addShape("rect", { x: 0.5, y: 0.82, w: 1.8, h: 0.04, fill: { color: C.accent } });

  addCard(slide, 0.5, 1.1, 4.35, 2.5, C.accent, "项目总结", [
    "构建了完整的 LLM + Operator AIOps 自愈平台",
    "实现了 OODA 闭环: 观察-定位-决策-执行",
    "采用全异步 FastAPI + Go Operator 双语言架构",
    "IsolationForest ML 实现主动异常预测",
    "n8n 零代码审批流保障高危操作安全",
    "Vue 3 暗黑科技风大屏 + AI Copilot 交互",
  ]);
  addCard(slide, 5.15, 1.1, 4.35, 2.5, C.emerald, "未来展望", [
    "部署至真实 Kubernetes 生产集群验证",
    "引入 RAG 增强 LLM 的领域知识深度",
    "接入更多可观测数据源 (Jaeger/ OpenTelemetry)",
    "支持多集群联邦管理与跨集群自愈",
    "扩展 CRD 动作库: 金丝雀发布/流量切换",
    "企业级 RBAC 权限与多租户支持",
  ]);

  slide.addText("感谢各位老师的指导与评审!", {
    x: 0.5, y: 4.2, w: 9, h: 0.5, fontSize: 16, fontFace: FONT_H, color: C.accentLight, align: "center", bold: true, margin: 0,
  });
  slide.addText("Q & A", {
    x: 0.5, y: 4.7, w: 9, h: 0.5, fontSize: 28, fontFace: FONT_H, color: C.white, align: "center", bold: true, margin: 0,
  });

  // ====== 写入文件 ======
  const outPath = "docs/KubeSentinel-GraduationDefense.pptx";
  await pres.writeFile({ fileName: outPath });
  console.log(`PPT generated: ${outPath}`);
}

main().catch(console.error);
