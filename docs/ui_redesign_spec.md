一、当前最大问题：SWE-bench Verified 被“写死”

现在顶部：

[SWE-bench Verified]

视觉上像：

当前产品 = SWE-bench dashboard

但实际上：

SWE-bench 只是 dataset/provider

这会导致未来扩展：

GAIA
BrowserArena
HumanEval
internal tasks
agent trajectories

时架构别扭。

二、正确的产品结构（重要）

你应该把产品抽象成：

AgAutoEval
 ├── Benchmarks
 ├── Runs
 ├── Datasets
 ├── Agents
 ├── Models
 └── Leaderboards

而不是：

AgAutoEval
 └── SWE-bench
三、顶部导航改造（优先级 P0）

现在：

AgAutoEval   [SWE-bench Verified]

建议改成：

AgAutoEval
Benchmarks
Runs
Datasets
Agents
Leaderboard

类似：

Weights & Biases
LangSmith
OpenAI Evals

结构。

四、Benchmark Selector（替代 SWE-bench Badge）

现在：

[SWE-bench Verified]

应该改成：

Benchmark: [ SWE-bench Verified ▼ ]

支持切换：

SWE-bench Lite
SWE-bench Verified
HumanEval
GAIA
Internal Eval
Browser Tasks
五、Create Run（最应该新增）

你现在缺少：

“入口”

现在页面像：

只读 dashboard

但 benchmark 平台核心其实是：

launch experiment
六、Create Run 按钮（P0）

建议放右上角：

+ New Run

或者：

Run Evaluation

视觉：

Primary button
蓝色 glow
有“启动实验”的感觉

例如：

[ + Launch Run ]
七、Create Run Modal / Page（核心）

不要只做：

form

应该做成：

Experiment Configuration

感觉。

八、推荐 Create Run UI（很重要）

建议分步骤：

Step 1 — Select Benchmark
Choose Benchmark

( ) SWE-bench Verified
( ) SWE-bench Lite
( ) HumanEval
( ) BrowserArena
( ) Custom Dataset

并显示：

task count
difficulty
language
avg runtime
Step 2 — Select Agent
Choose Agent

[opencode]
[swe_agent]
[claude]
[custom]

支持：

version
capabilities
tool-use enabled
Step 3 — Select Model
Provider:
[Anthropic ▼]

Model:
[Claude Sonnet 4.6 ▼]
Step 4 — Runtime Config（很关键）

这里才体现：

Agent Infra

能力。

建议：

Max Iterations
Timeout
Parallelism
Sandbox Mode
Retry Strategy
Temperature
Allowed Tools

例如：

Max Runtime: 90 min
Parallel Workers: 8
Tool Permissions: sandboxed
Step 5 — Eval Config

例如：

Run subset only
Limit instances
Random seed
Enable replay
Enable trace recording
Enable patch grading
Step 6 — Review + Launch

最终：

Benchmark: SWE-bench Verified
Agent: opencode
Model: Claude Sonnet 4.6
Instances: 50
Estimated Cost: $14.20

然后：

[ Launch Evaluation ]
九、非常建议增加：Run Queue 页面

现在 industry trend 很明显：

eval = job system

因此建议：

Runs
 ├── Running
 ├── Queued
 ├── Completed
 ├── Failed
十、Run 状态增强（重要）

现在左边绿点：

●

信息量太少。

建议：

状态	UI
queued	gray
provisioning	blue pulse
running	green pulse
evaluating	yellow
failed	red
timeout	orange
cancelled	muted

并增加：

live elapsed time

例如：

Running · 32m
十一、最值得增加：Live Run Detail（强烈推荐）

这是你产品能明显拉开差距的地方。

点击 run：

进入：

Experiment Dashboard
十二、Run Detail 应该长什么样

推荐布局：

┌─────────────────────┬────────────────────┐
│ Run Timeline        │ Live Agent Trace  │
├─────────────────────┼────────────────────┤
│ Instance List       │ Terminal Output   │
└─────────────────────┴────────────────────┘
十三、Agent Trace（非常重要）

你现在还是：

benchmark result

但未来应该变成：

agent observability

展示：

Thought
Tool Call
File Edit
Shell
Retry
Patch
Test

类似：

LangSmith
OpenTelemetry
OpenAI tracing
十四、Dataset 管理（后续会非常重要）

未来你一定会有：

多个 benchmark

因此建议：

Datasets

独立页面。

支持：

upload dataset
split
tags
difficulty
expected runtime
十五、Leaderboard（非常值得）

现在 benchmark 产品的“社交传播性”来自：

排行榜

建议：

Top Models
Top Agents
Cheapest
Fastest
十六、现在还缺少“实验感”

目前页面还是：

dashboard

而不是：

research platform

建议增加：

1 Trend Charts

例如：

accuracy over time
2 Cost Analytics

现在大家很关心：

accuracy / $
3 Parallel Workers Visualization

例如：

8 workers running

动态图。

4 Token Usage

例如：

12.4M input tokens
4.8M output tokens
十七、很推荐：Command Palette

现在 AI tooling 几乎标配：

Cmd + K

支持：

Search runs
Launch eval
Open dataset
Compare models

会明显高级。

十八、当前视觉层面的几个问题
1 KPI card 太空

建议：

增加 mini sparkline
增加 trend

例如：

46.6%
↑ 4.2% this week
2 顶部导航太 sparse

左边太空。

建议：

AgAutoEval
[Benchmark ▼]
[Search]
3 Table 行高略高

当前有点：

cursor dashboard 风

但 benchmark table 更适合：

slightly denser
4 色彩层级不够丰富

现在：

全是蓝 + 黄

建议：

running 用 cyan
success 用 green
failed 用 red
queue 用 gray

增加状态辨识度。

十九、未来真正高级的方向（很重要）

未来 agent eval 最大价值会从：

accuracy leaderboard

变成：

agent execution intelligence

即：

为什么失败
哪一步失败
tool use patterns
retry effectiveness
planning quality
patch quality

因此：

trace/replay

会越来越核心。

二十、我认为你现在最优先做的（P0）

按收益排序：

P0
必须立即做
Create Run
Benchmark selector
Run status system
Run detail page
Better top nav
P1
明显提升专业度
Live trace
Charts
Leaderboard
Compare view
P2
高级平台能力
Replay
Failure analytics
Cost intelligence
Trace search
Tool observability