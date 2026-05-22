# Agents 页面设计（重要）

Agents 页面不应该只是：

```text
Agent 名称列表
```

而应该是：

```text
Agent Hub / Agent Profile
```

核心目标：

- 展示 agent 能力
- 展示 benchmark 表现
- 展示 agent evolution
- 展示 runtime 配置
- 展示安装与启动方式
- 展示 trace 风格
- 支持 compare

这是：

```text
Agent Evaluation Platform
```

非常核心的一部分。

---

# 一、推荐的信息架构

建议：

```text
Agents
 ├── Agent List
 └── Agent Detail
```

---

# 二、Agent List 页面（P0）

Agent 列表不应只是：

```text
opencode
claude
swe_agent
```

建议展示：

| Agent | Latest Accuracy | Best Accuracy | Benchmarks | Last Active |
|---|---|---|---|---|
| opencode | 57.1% | 61.2% | 4 | 2h ago |
| swe_agent | 44.4% | 48.7% | 3 | 1d ago |

并增加：

- logo
- tags
- capabilities

例如：

```text
[tool-use]
[multi-agent]
[sandboxed]
[planner]
```

---

# 三、Agent Detail 页面（核心）

点击：

```text
opencode
```

进入：

```text
/agents/opencode
```

---

# 四、Agent Detail 页面布局（推荐）

建议：

```text
┌─────────────────────────────────────┐
│ Agent Header                        │
├─────────────────────────────────────┤
│ Overview Metrics                    │
├─────────────────────────────────────┤
│ Benchmark History                   │
├─────────────────────────────────────┤
│ Cross-Benchmark Performance         │
├─────────────────────────────────────┤
│ Versions                            │
├─────────────────────────────────────┤
│ Runtime Configuration               │
├─────────────────────────────────────┤
│ Installation & Usage                │
├─────────────────────────────────────┤
│ Recent Runs                         │
├─────────────────────────────────────┤
│ Trace Samples                       │
└─────────────────────────────────────┘
```

---

# 五、Agent Header（重要）

顶部展示：

```text
OpenCode
```

以及：

- description
- github
- maintainer
- latest version
- runtime type

例如：

```text
OpenCode
Open-source coding agent focused on SWE-bench tasks.

Latest: v0.5.1
Maintainer: internal
Runtime: sandboxed shell
```

支持：

```text
[ Compare ]
[ Run Evaluation ]
```

---

# 六、Overview Metrics（推荐）

展示：

| Metric | Value |
|---|---|
| Latest Accuracy | 57.1% |
| Best Accuracy | 61.2% |
| Avg Runtime | 1h 42m |
| Avg Cost | $4.32 |
| Total Runs | 83 |

建议增加：

- trend arrow
- mini sparkline

例如：

```text
Accuracy
57.1%
↑ 4.2% this month
```

---

# 七、Benchmark History（非常重要）

支持：

```text
单个 agent 在某个 benchmark 上的历史表现
```

例如：

```text
OpenCode on SWE-bench Verified
```

折线图：

```text
accuracy over time
```

X轴：

```text
time / version
```

Y轴：

```text
accuracy
```

建议支持：

- latest run
- best run
- average run

切换。

---

# 八、Cross-Benchmark Performance（推荐）

展示：

```text
同一个 agent
在多个 benchmark 上的表现
```

例如：

| Dataset | Accuracy | Runtime | Cost |
|---|---|---|---|
| SWE-bench Verified | 57.1% | 1h 47m | $5.1 |
| HumanEval | 82.4% | 4m | $0.8 |
| GAIA | 31.2% | 42m | $2.7 |

这是：

```text
Agent Capability Profile
```

重要部分。

---

# 九、Version 页面（重要）

Agent 必须支持：

```text
versioning
```

例如：

| Version | Accuracy | Commit | Date |
|---|---|---|---|
| 0.5.1 | 57.1% | a1b2c3 | May 2026 |
| 0.5.0 | 54.2% | f4d5e6 | Apr 2026 |

支持：

```text
Compare Versions
```

用于：

- regression 分析
- prompt 对比
- runtime config 对比

---

# 十、Runtime Configuration（非常重要）

这是很多 benchmark 平台缺失的能力。

应该展示：

```text
agent 实际运行配置
```

例如：

```yaml
Model:
  claude-sonnet-4.6

Tool Policy:
  sandboxed

Max Iterations:
  200

Parallelism:
  8

Retry Strategy:
  enabled

Patch Strategy:
  minimal-edit

Planner:
  hierarchical
```

这是：

```text
可复现 benchmark
```

关键能力。

---

# 十一、Installation & Usage（推荐）

非常建议支持：

```text
agent 安装与启动文档
```

例如：

```bash
npm install -g opencode-ai
```

```bash
opencode run "fix failing tests"
```

以及：

- required env
- provider config
- docker setup
- sandbox setup

因为未来：

```text
Agent Marketplace
```

是可能的发展方向。

---

# 十二、Launch Config Examples（推荐）

展示：

```text
benchmark 推荐启动方式
```

例如：

```bash
opencode run \
  --model claude-sonnet-4.6 \
  --sandbox docker \
  --max-iterations 200
```

以及：

- best known config
- fastest config
- cheapest config

---

# 十三、Recent Runs（推荐）

展示：

```text
最近 benchmark runs
```

例如：

| Run | Benchmark | Accuracy | Date |
|---|---|---|---|
| #123 | SWE-bench | 57.1% | 2h ago |
| #118 | GAIA | 31.2% | 1d ago |

支持：

```text
View Run
```

---

# 十四、Trace Samples（非常推荐）

展示：

```text
代表性的 trace
```

例如：

- fastest solve
- best reasoning
- longest retry
- failed interesting case

这是：

```text
展示 agent 风格
```

的重要部分。

---

# 十五、Agent Compare（重要）

支持：

```text
Compare Agents
```

例如：

```text
OpenCode vs swe_agent
```

对比：

- benchmark
- retries
- patch size
- tool usage
- runtime
- token cost

---

# 十六、推荐增加 Capabilities 标签

例如：

```text
[tool-use]
[multi-agent]
[sandbox]
[browser]
[planner]
[self-reflection]
```

帮助理解：

```text
agent 类型
```

---

# 十七、未来很重要：Agent Evolution

未来真正高级的能力不是：

```text
当前最准
```

而是：

```text
agent 如何演化
```

例如：

```text
v0.4 → v0.5
accuracy +6%
runtime -18%
retry -42%
```

这是：

```text
Agent DevOps
```

方向。

---

# 十八、推荐增加 Benchmark Breakdown

展示：

```text
agent 在不同 repo/category 上表现
```

例如：

| Category | Accuracy |
|---|---|
| Django | 62% |
| SymPy | 44% |
| Flask | 71% |

帮助分析：

```text
agent strengths
```

---

# 十九、未来高级方向：Agent Registry

长期来看：

```text
Agents 页面
```

可以演化成：

```text
Agent Registry / Agent Marketplace
```

支持：

- publish agent
- benchmark agent
- share configs
- compare traces
- reproducible evals

类似：

```text
HuggingFace for Agents
```

---

# 二十、我认为最值得优先做的（P0）

## 必须立即做

1. Agent Detail 页面
2. Benchmark History 图表
3. Version 系统
4. Runtime Config 展示
5. Recent Runs

---

## P1

1. Cross-benchmark view
2. Install & Usage
3. Agent compare
4. Trace samples

---

## P2

1. Agent evolution analytics
2. Agent registry
3. Publish/share
4. Community leaderboard

---

# 二十一、一个非常关键的定位

不要把：

```text
Agents 页面
```

做成：

```text
配置页
```

而应该做成：

```text
Agent Identity + Capability + Evolution
```

这是整个 Agent Eval 平台最核心的对象之一。