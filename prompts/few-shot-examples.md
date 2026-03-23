# LLM Few-Shot 示例库

> **状态**: 📋 骨架文档 — 第二阶段 LLM 联调时，将经过验证的 Prompt-Response 对添加至此
>
> **用途**: 将部分示例嵌入 System Prompt 或 User Prompt 以提升输出稳定性

---

## 如何使用此文件

在 `prompts/system-prompt.md` 的结尾，可以将以下验证通过的示例以 Few-Shot 形式追加：

```
## 参考示例（Few-Shot）

以下是你历史上做出的正确判断，请参考此风格输出：

### 示例 1
[输入告警] → [正确 JSON 输出]

### 示例 2
[输入告警] → [正确 JSON 输出]
```

---

## 示例库

> **TODO**: 以下每个槽位在实际联调时，将真实的告警输入和 LLM 输出填入

### 场景 1: Pod CPU 持续高负载 → 滚动重启

**输入告警 (Alertmanager Payload)**:
```json
{
  "TODO": "第二阶段填写真实触发了此场景的告警 JSON"
}
```

**LLM 期望输出**:
```json
{
  "TODO": "第二阶段填写经过人工验证正确的 LLM JSON 输出"
}
```

**备注**: `TODO: 记录 Prompt 版本、LLM 模型、是否需要人工调整`

---

### 场景 2: Pod 频繁重启 (CrashLoopBackOff) → 回滚

**输入告警**:
```json
{
  "TODO": "待填写"
}
```

**LLM 期望输出**:
```json
{
  "TODO": "待填写"
}
```

---

### 场景 3: 内存使用率过高 → 扩容

**输入告警**:
```json
{
  "TODO": "待填写"
}
```

**LLM 期望输出**:
```json
{
  "TODO": "待填写"
}
```

---

### 场景 4: 服务不可用 (0 副本 Ready) → 调查

**输入告警**:
```json
{
  "TODO": "待填写"
}
```

**LLM 期望输出**:
```json
{
  "TODO": "待填写，置信度应低于阈值，action 为 investigate"
}
```

---

### 场景 5: 节点 CPU 满载 → Cordon 节点

**输入告警**:
```json
{
  "TODO": "待填写"
}
```

**LLM 期望输出**:
```json
{
  "TODO": "待填写"
}
```

---

## 反例（导致误操作的 Prompt，需要避免）

> **TODO**: 记录在测试中发现的、会让 LLM 做出错误决策的输入，用于 Prompt 防御性优化

| 场景 | 错误输出 | 原因分析 | 修复方式 |
|:---|:---|:---|:---|
| TODO | TODO | TODO | TODO |
