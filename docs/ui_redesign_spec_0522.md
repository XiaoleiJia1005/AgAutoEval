# 二十 UI fix
顶部切换数据集时，如果没数据显示空页面；当前切换后内容页面无变化；
all agents 列表显示具体agent而不是分类
表格中provider用图标代替，没有图标fallback文本，Launch Evaluation 页面步骤model也是
run详情页顶部：agent，provider/model，数据集三个维度分开，每个维度前加图标：agent 同机器人，model 用大脑，数据集用数据表
Runtime Configuration页面删除Temperature，Max Iterations

# 二十一、Trace Compare 页面（重要）

当前系统已经有：

```text
Run List
Run Detail
```

但对于 Agent Eval 平台来说：

```text
trace comparison
```

才是真正高级能力。

因为未来核心问题不是：

```text
哪个 agent 分高
```

而是：

```text
为什么这个 agent 更强
```

因此建议新增：

```text
Trace Compare
```

功能。

---

# 二十二、Trace Compare 功能定位

目标：

```text
对比两个（或多个）agent execution traces
```

从而分析：

- reasoning 差异
- tool use 差异
- retry 策略差异
- patch generation 差异
- planning 能力差异

本质是：

```text
Agent Observability
```

而不是：

```text
简单结果对比
```

---

# 二十三、Trace Compare 页面入口（重要）

建议提供三个入口。

---

## 入口 1：Run Detail 页面（推荐）

在：

```text
Run Detail
```

页面右上角增加：

```text
[ Compare Trace ]
```

点击后：

```text
打开 compare selector modal
```

用户可以：

- 选择对比 run
- 选择 compare baseline
- 选择 compare mode

这是最自然的入口。

---

## 入口 2：Run Table 多选（推荐）

在 run list table：

增加：

```text
checkbox selection
```

支持：

```text
☑ Run A
☑ Run B
```

之后顶部出现：

```text
[ Compare Selected ]
```

类似：

- GitHub compare
- Weights & Biases compare experiments

---

## 入口 3：Instance Detail 页面（高级）

在单个 instance：

```text
sympy__sympy-12345
```

页面中：

增加：

```text
Compare Other Runs
```

因为：

```text
同一个 issue
不同 agent 的执行路径
```

是最有价值的分析。

---

# 二十四、Trace Compare 的核心对比对象

建议支持：

---

## 1 Run vs Run（P0）

例如：

```text
OpenCode + Claude Sonnet 4.6
vs
swe_agent + GPT-4.1
```

对比：

- accuracy
- runtime
- traces
- retries
- patch quality

---

## 2 Same Instance Compare（非常重要）

例如：

```text
sympy issue #123
```

对比：

- Agent A 如何解决
- Agent B 为什么失败

这是：

```text
真正有研究价值的 compare
```

---

## 3 Same Agent Different Version（后面会提）

例如：

```text
opencode v0.4
vs
opencode v0.5
```

分析：

- regression
- planning improvements
- retry improvements

---

# 二十五、Trace Compare 页面布局（推荐）

推荐：

```text
┌──────────────────────────────────────┐
│ Compare Header                       │
├──────────────────────────────────────┤
│ Summary Metrics                      │
├──────────────────────────────────────┤
│ Trace Timeline (side-by-side)        │
├──────────────────────────────────────┤
│ Tool Usage Comparison                │
├──────────────────────────────────────┤
│ Patch Diff Comparison                │
├──────────────────────────────────────┤
│ Terminal Output Comparison           │
└──────────────────────────────────────┘
```

---

# 二十六、Summary Metrics（P0）

顶部首先展示：

```text
Agent A:
- resolved
- duration
- retries
- token cost

Agent B:
- resolved
- duration
- retries
- token cost
```

并高亮：

```text
winner
```

例如：

```text
+12% faster
-23% token usage
```

---

# 二十七、Trace Timeline Compare（最重要）

真正核心能力。

左右并排：

```text
Agent A                         Agent B
------------------------------------------------
Read parser.py                  Read parser.py
Run pytest                      Run pytest
Edit parser.py                  Edit parser.py
Retry test                      Retry test
Patch success                   Infinite retry
```

支持：

- synchronized scroll
- step highlight
- time alignment

类似：

```text
Chrome DevTools performance compare
```

体验。

---

# 二十八、Tool Usage Compare（推荐）

展示：

| Tool | Agent A | Agent B |
|---|---|---|
| Read File | 32 | 18 |
| Edit File | 9 | 21 |
| Bash | 14 | 6 |
| Retry | 3 | 11 |

帮助分析：

```text
agent behavior pattern
```

---

# 二十九、Patch Compare（非常重要）

支持：

```text
side-by-side diff
```

例如：

```text
Agent A:
minimal patch

Agent B:
large refactor
```

帮助分析：

- patch quality
- over-editing
- risky edits

---

# 三十、Reasoning Compare（高级）

如果支持 reasoning trace：

可以：

```text
Thought A
vs
Thought B
```

例如：

```text
Agent A:
Root cause identified quickly

Agent B:
Long exploratory reasoning
```

这是：

```text
research value 非常高
```

的能力。

---

# 三十一、Compare Mode（重要）

建议支持：

---

## 1 Full Run Compare

对比：

```text
整个 run
```

---

## 2 Same Instance Compare（推荐）

只对比：

```text
同一个 benchmark instance
```

例如：

```text
django__django-12345
```

这是最有价值的。

---

## 3 Failed Only Compare

只对比：

```text
失败 case
```

帮助分析：

- regression
- weakness
- flaky behavior

---

# 三十二、Agent Version 系统（非常重要）

当前系统里：

```text
agent = opencode
```

是不够的。

因为：

```text
agent 本身会不断迭代
```

未来必须支持：

```text
Agent Version
```

例如：

```text
opencode@0.4.1
opencode@0.5.0
claude-agent@2026.05
```

否则：

```text
历史 benchmark 无法分析
```

---

# 三十三、Agent Version 数据模型（重要）

推荐：

```text
Agent
 ├── id
 ├── name
 └── versions
      ├── version
      ├── git_commit
      ├── prompt_version
      ├── tool_policy
      ├── runtime_config
      └── created_at
```

重点：

```text
run 必须绑定 agent_version
```

而不是：

```text
run 只绑定 agent_name
```

---

# 三十四、Run 数据结构修改（前后端）

当前可能：

```json
{
  "agent": "opencode"
}
```

建议升级：

```json
{
  "agent": {
    "name": "opencode",
    "version": "0.5.1",
    "commit": "a1b2c3",
    "prompt_version": "planner-v2",
    "tool_policy": "sandboxed"
  }
}
```

因为：

```text
agent 行为变化
不仅来自代码
还来自：
- prompt
- tool policy
- runtime config
```

---

# 三十五、Create Run 页面增加 Version Selector

新增：

```text
Agent:
[ opencode ▼ ]

Version:
[ 0.5.1 ▼ ]
```

支持：

- latest
- pinned version
- git commit

---

# 三十六、Agent Detail 页面（非常推荐）

新增：

```text
Agent Detail
```

页面。

例如：

```text
/opencode
```

展示：

- 所有版本
- performance trend
- datasets coverage
- regression history

---

# 三十七、Agent History View（重要）

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
accuracy over versions
```

支持：

- best run
- latest run
- average run

---

# 三十八、Agent Cross-Benchmark View（推荐）

支持：

```text
单个 agent 固定版本
在所有 benchmark 上的表现
```

例如：

| Dataset | Accuracy |
|---|---|
| SWE-bench | 57% |
| HumanEval | 82% |
| GAIA | 31% |

这是：

```text
Agent Capability Radar
```

核心能力。

---

# 三十九、Latest vs Best Run（重要）

建议支持切换：

```text
View:
( ) Latest Run
( ) Best Run
( ) Average
```

因为：

```text
benchmark 有随机性
```

不能只看单次 run。

---

# 四十、Leaderboard 也必须支持 Version

否则：

```text
排行榜不可复现
```

建议：

```text
opencode@0.5.1
```

而不是：

```text
opencode
```

---

# 四十一、未来真正重要的能力

未来 Agent Eval 的核心会逐渐从：

```text
accuracy ranking
```

变成：

```text
agent evolution tracking
```

即：

- agent 如何变强
- 哪个改动导致 regression
- prompt 是否有效
- tool policy 是否有效
- retry strategy 是否有效

因此：

```text
trace compare + version system
```

会成为核心基础设施能力。