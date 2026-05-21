# Agent Eval Dashboard UI Redesign Spec

目标：把当前界面从“内部工具列表页”升级为“专业 AI Benchmark 平台”。

当前问题：
- 信息密度低，但视觉层级也弱
- 所有 run 都长得一样，没有重点
- 缺少 benchmark / eval 的“实验感”
- 缺少 trend / comparison / filtering 的高级能力
- 缺少对 resolved rate 的视觉强化
- 暗色主题过于平，没有层次
- 缺少实时感（agent 正在运行）
- 没有体现 AI Agent 的 workflow 特征

---

# 一、整体视觉方向

建议风格：

```txt
Linear + Vercel + Cursor + Weights & Biases
```

目标气质：

```txt
AI Infra / Research Platform
```

而不是：

```txt
普通后台管理系统
```

---

# 二、顶部 Header 改造

当前：

```txt
AgAutoEval
Runs
```

问题：
- 太空
- 品牌感弱
- 没有状态信息

建议：

## 新 Header 结构

左侧：
- Logo
- 项目名
- 当前 benchmark

中间：
- 全局搜索
- command palette

右侧：
- Live queue 状态
- Running agents 数量
- Theme switch
- User avatar

---

## 示例布局

```txt
┌───────────────────────────────────────────────┐
│ ◉ AgAutoEval        Search runs...      🔔  │
│ SWE-bench Verified   12 Running   GPU 82%   │
└───────────────────────────────────────────────┘
```

---

# 三、增加 KPI Summary Cards（最重要）

当前页面最大问题：

```txt
缺少 overview
```

进入页面后应该先看到：

- 当前 benchmark 整体成功率
- 平均 duration
- Top model
- 当前 running jobs
- Token cost
- Pass trend

---

## 建议新增顶部 KPI 区域

```txt
┌─────────┬─────────┬─────────┬─────────┐
│ Success │ Avg Dur │ Running │ Cost    │
│ 48.2%   │ 31 min  │ 12      │ $82.4   │
└─────────┴─────────┴─────────┴─────────┘
```

---

## 视觉要求

- 大号数字
- 小 label
- subtle border
- hover elevation
- 微渐变背景

推荐：

```txt
rounded-2xl
backdrop blur
border-white/10
bg-white/3
```

---

# 四、Run Table 改造成真正的 Benchmark Table

当前 table 太像：

```txt
数据库 admin table
```

建议增加：

## 1 行 hover 状态

当前 hover 不明显。

建议：

- hover 背景变化
- 左侧 accent bar
- shadow 提升

例如：

```txt
hover:bg-white/5
hover:border-l-green-400
```

---

## 2 Accuracy 改成 Progress Bar

当前：

```txt
50.0%
```

太弱。

建议：

```txt
████████░░ 50%
```

颜色：

- >60% 绿色
- 40-60 黄色
- <40 红色

增加视觉反馈。

---

## 3 Duration 增加趋势信息

当前：

```txt
1h 53m
```

建议增加：

```txt
1h 53m
↑ 12% slower
```

或者：

```txt
⚡ Fast
🐢 Slow
```

---

## 4 Model 显示 provider icon

现在：

```txt
claude-sonnet-4-6
```

太 plain。

建议：

```txt
[Anthropic Icon] Claude Sonnet 4.6
```

OpenAI / DeepSeek 也一样。

---

## 5 Agent 增加类型 tag

例如：

```txt
opencode        Tool-use
claude          Native Agent
swe_agent       Research Agent
```

可以增加：

- tool use
- multi-agent
- shell enabled
- sandboxed

这种 metadata。

---

## 6 状态字段（重要）

当前没有状态。

应该新增：

```txt
Queued
Running
Evaluating
Completed
Failed
Timeout
```

并增加 live animation：

```txt
● Running
```

带 pulse 动画。

---

# 五、增加 Run Detail Page（非常关键）

当前最大缺失：

```txt
没有实验细节页
```

点击 View 后应该进入：

```txt
真正的 experiment dashboard
```

---

## Run Detail 页面建议

### 1 顶部 Summary

```txt
Run #20260521_220000
OpenCode + Claude Sonnet 4.6
Resolved 4 / 8
```

---

### 2 Timeline（强烈推荐）

展示：

```txt
Task Started
↓
Environment Setup
↓
Agent Reasoning
↓
Patch Generated
↓
Tests Running
↓
Evaluation Complete
```

很有 agent infra 感。

---

### 3 Instance 列表

每个 SWE-bench instance：

- repo
- issue
- patch diff
- test logs
- token usage
- duration

---

### 4 Patch Viewer

一定要做。

支持：

- syntax highlight
- unified diff
- split diff
- collapse unchanged

类似 GitHub PR。

---

### 5 Agent Trace（最重要）

这是 AI Agent benchmark 和普通 benchmark 最大区别。

展示：

```txt
Thought
Tool Call
Shell Command
File Edit
Test Output
Retry
```

甚至可以：

```txt
step-by-step replay
```

非常有价值。

---

# 六、增加 Compare View（很重要）

现在 benchmark 最大需求之一：

```txt
模型对比
```

应该支持：

## Compare Runs

```txt
Claude Sonnet 4.6
vs
GPT-4.1
vs
DeepSeek-V4
```

---

## 对比维度

- success rate
- avg duration
- avg retries
- avg token cost
- shell usage
- test retries
- patch size

---

## 图表建议

### 1 Pass Rate Trend

折线图。

### 2 Duration Distribution

柱状图。

### 3 Radar Chart

比较：

- reasoning
- coding
- debugging
- cost
- speed

---

# 七、增加 Live Run Experience

现在太静态。

Agent Eval 应该有：

```txt
正在运行 AI Agent
```

的感觉。

---

## 建议新增

### 1 Live Terminal Stream

```txt
> pytest tests/parser_test.py
FAILED
```

实时输出。

---

### 2 Running Animation

例如：

```txt
Thinking...
Executing...
Retrying...
```

---

### 3 Agent Tool Activity

```txt
Read file parser.py
Run pytest
Edit parser.py
```

像 Cursor background agent。

---

# 八、Filter / Search 升级

当前 filter 太基础。

建议支持：

## 多维 filter

- provider
- model
- benchmark
- repo
- resolved only
- failed only
- duration range
- token cost

---

## Full-text search

支持：

```txt
sympy
parser
django
```

搜索 instance。

---

## 快捷 filter chips

```txt
[High Accuracy]
[Fastest]
[Cheapest]
[Claude]
```

---

# 九、视觉层次优化（非常重要）

当前最大视觉问题：

```txt
整个页面亮度一致
```

没有 focus。

---

## 建议

### 1 增加 surface 层级

页面：

```txt
background
↓
panel
↓
card
↓
hover
```

层层递进。

---

### 2 暗色不要纯黑

推荐：

```txt
bg-[#0B1020]
```

而不是：

```txt
#000
```

---

### 3 增加 subtle glow

例如：

- active run
- selected row
- running agent

增加：

```txt
shadow-[0_0_20px_rgba(...)]
```

---

### 4 Typography

当前字体层级太弱。

建议：

- 大标题更大
- metric 数字更粗
- secondary text 降低 opacity

---

# 十、真正值得做的高级功能

---

## 1 Agent Replay（非常酷）

像：

```txt
Cursor Replay
```

展示 agent：

- 思考
- 编辑
- shell
- retry

时间轴回放。

---

## 2 Token Cost Analytics

现在大家越来越关注：

```txt
accuracy / dollar
```

建议增加：

```txt
$ per resolved issue
```

---

## 3 Failure Analysis

自动聚类：

```txt
Environment failure
Test timeout
Patch invalid
Syntax error
```

非常适合 benchmark。

---

## 4 Leaderboard

```txt
Top Performing Models
```

像 LMSYS。

---

# 十一、前端技术建议

---

## UI Library

推荐：

```txt
shadcn/ui
```

原因：

- AI tooling 风格匹配
- modern
- 可组合

---

## Chart

推荐：

```txt
recharts
```

---

## Table

推荐：

```txt
TanStack Table
```

支持：

- virtualization
- sorting
- filtering
- pin columns

---

## Motion

推荐：

```txt
framer-motion
```

用于：

- hover
- live pulse
- loading
- transitions

---

# 十二、最优先改造顺序（重要）

如果时间有限：

---

## P0（必须先做）

1. KPI Summary Cards
2. Accuracy Progress Bar
3. Better Table Hover
4. Status Column
5. Run Detail Page

---

## P1（明显提升质感）

1. Live terminal stream
2. Charts
3. Compare view
4. Patch viewer

---

## P2（高级能力）

1. Agent replay
2. Failure analytics
3. Cost analytics
4. Timeline visualization

---

# 十三、你这个产品真正应该强调什么

不要把它做成：

```txt
后台管理系统
```

而应该做成：

```txt
AI Agent Research Platform
```

核心关键词：

- experiments
- traces
- orchestration
- execution
- evaluation
- benchmarking

因为：

```txt
Agent Eval 的真正价值
不只是最终 accuracy
而是 agent execution process
```

这个方向会明显比普通 dashboard 更高级。

