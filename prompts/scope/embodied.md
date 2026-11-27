# Scope: Embodied AI (embodied)

## Is it relevant? (`relevant`)
TRUE when the research object is learning-based embodied agents and robots:
- vision-language-action (VLA) models: architecture, training, technical reports
- manipulation (grasping, dexterous hands, bimanual, imitation learning)
- navigation and mobile manipulation (vision-language navigation)
- world models and simulation for robots, sim-to-real
- data collection, teleoperation systems, robot datasets and data mixtures
- robot reinforcement learning, policy learning, motor control
- humanoids, legged and whole-body control
- embodied benchmarks and real-robot evaluation
FALSE: classical robotics without learning (pure planning/control theory, SLAM without learning), autonomous driving perception stacks unless framed as embodied policy learning, GUI agents (VLM topic).

## Direction — exactly one code:
A VLA 模型 · B 操作 · C 导航与移动 · D 世界模型与仿真 · E 数据与遥操作 · F 强化学习与控制 · G 人形与全身控制 · H 评测与 Benchmark · Z 其他

## `score` (0–1): how much someone working on robot learning should care.
Weigh: real-robot experiments at meaningful scale, many tasks, strong baselines, open models/data/hardware, belief-changing findings.

Use the whole range and two decimals (0.62, not 0.6): the score orders the issue, so papers of one batch should not pile up on the same value. Score from what the abstract and comment actually state; evidence that is not stated (scale, baselines, release) counts as absent.

| Score | Meaning | Typical paper |
|---|---|---|
| 0.85–1.00 | People in this field need to know about it this week. Rare: most batches have none. | A generalist policy or large dataset from a major lab with extensive real-robot evaluation and an open release; or a finding that changes how VLAs are trained or evaluated. |
| 0.70–0.84 | Strong: rigorous evidence at real scale plus something reusable or surprising. `star_candidate` starts at 0.75. | Real-robot results across many tasks or embodiments against strong current baselines (π-series, OpenVLA-class), with models, data or hardware released. |
| 0.55–0.69 | Solid and complete, but incremental. | A complete method with real-robot results on a handful of tasks, or thorough simulation plus a real-robot check. |
| 0.45–0.54 | Relevant, with narrow scope or thin evidence. Shown only if the issue has room. | Simulation only, one or two tasks, or weak baselines. |
| 0.20–0.44 | Marginal. Not shown as related. | Narrow simulation tweaks, classical control without learning, surveys without new evidence. |

`star_candidate`: score ≥0.75 AND worth a full read; `star_why` ≤40 Chinese chars.

## ⭐
At least two of: core embodied-learning question; real-robot evidence at meaningful scale; open model/data/hardware; a finding that changes common beliefs.
