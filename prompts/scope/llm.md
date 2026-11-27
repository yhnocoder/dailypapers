# Scope: LLM (llm)

## Is it relevant? (`relevant`)
TRUE when the paper's own research object is (text) large language models: how they are built, trained, aligned, reason, act, are understood, evaluated or made safe.
- technical reports and model releases of LLMs; large end-to-end training reports
- pre-training recipes, data mixture/cleaning, synthetic data, scaling laws
- architectures: attention variants, linear attention, state-space models, MoE design, looped/recurrent-depth models
- long context: context extension, length extrapolation, long-context evaluation, context compression and memory
- post-training and alignment: SFT, preference optimisation (DPO/KTO…), reward models, safety training
- RL and reasoning: RLVR, chain-of-thought, test-time scaling, math/code reasoning
- agents (capability side): planning, tool use, memory, multi-agent collaboration, agent training methods
- interpretability and mechanism analysis; evaluation, benchmarks, LLM-as-judge, contamination; safety and reliability (hallucination, jailbreaks and defences, privacy, watermarking, robustness)
FALSE: papers that merely *use* an LLM as a tool for a domain application without contributing to LLMs themselves; pure systems/serving work with no model-side contribution (that is AI Infra); multimodal-first work (VLM topic) unless the language-model side is the contribution.

## Direction — exactly one code:
A 技术报告与模型发布 · B 预训练与数据 · C 架构 · D 长上下文 · E 后训练与对齐 · F 强化学习与推理 · G Agent · H 可解释性与机制分析 · I 评测与 Benchmark · J 安全与可靠性 · Z 其他
Agents: capability / planning / training → G here; runtime and efficiency → AI Infra H (both tags allowed). RL training *systems* → AI Infra A; RL *algorithms* → F here.

## `score` (0–1): how much an LLM researcher/engineer should care.
Weigh: scale and rigour (real models at meaningful size, multiple seeds/benchmarks, strong baselines); released weights/data/code; technical reports from major labs; findings that change common beliefs; clear, reusable recipes. Incremental prompt tricks or single-benchmark gains ≈0.2–0.4; solid papers ≈0.5–0.7; ≥0.8 only for outstanding ones.
`star_candidate`: score ≥0.75 AND worth a full read; `star_why` ≤40 Chinese chars.

## ⭐ (main session's final pick)
At least two of: core LLM question; rigorous large-scale evidence; open weights/data/code or a major technical report; a finding that changes common beliefs.
