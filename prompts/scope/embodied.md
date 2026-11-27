# Scope: 具身智能与 VLA (embodied)

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

## `score` (0–1)
Real-robot experiments at meaningful scale, many tasks, strong baselines, open models/data/hardware, belief-changing findings. Simulation-only narrow tweaks ≈0.2–0.4; solid ≈0.5–0.7; ≥0.8 outstanding.
`star_candidate`: score ≥0.75 AND worth a full read; `star_why` ≤40 Chinese chars.

## ⭐
At least two of: core embodied-learning question; real-robot evidence at meaningful scale; open model/data/hardware; a finding that changes common beliefs.
