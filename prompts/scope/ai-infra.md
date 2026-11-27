# Scope: AI Infra (ai-infra)

## Is it relevant? (`relevant`: true/false)
TRUE when the paper's OWN research object is the systems side of AI — making models train, serve or run faster, cheaper, more reliably, at scale:
- training systems: data / tensor / pipeline / expert / sequence parallelism, fault tolerance and checkpointing, memory optimisation for training, RL post-training infrastructure (rollout engines, async RL, rollout–training disaggregation)
- inference serving: LLM / diffusion / multimodal serving, scheduling and batching, KV-cache management and offloading, prefill–decode disaggregation, speculative decoding *as a serving technique*, long-context serving, routing across models
- communication and networking for AI: collectives, NCCL/RDMA, topology and interconnect, communication compression, compute–communication overlap, cross-datacenter training
- kernels and compilers: CUDA / Triton / hardware kernels, attention implementations, operator fusion, ML compilers, autotuning
- quantization, sparsity, pruning, low-precision formats, efficient architectures *as efficiency methods* (accept even without hardware speedups; see ⭐ rule below)
- hardware and architecture for AI: accelerators, memory hierarchy, interconnect, in-/near-memory compute, energy
- cluster and resource management: GPU cluster scheduling, multi-tenancy, elasticity, cost and energy accounting
- agent infrastructure: agent runtimes and harnesses, sandboxes, tool-execution systems, agent serving and orchestration efficiency, agent memory/caching *as a systems problem*
- benchmarks, measurement and performance characterisation of AI systems
FALSE: papers about model accuracy/capabilities with no systems or efficiency contribution; pure ML algorithms; general distributed systems unrelated to AI; agent papers about reasoning/planning quality rather than infrastructure; using a GPU incidentally.

## Direction (`direction`, only if relevant) — exactly one code:
A 训练系统（并行 / 显存 / 容错 / RL 训练） · B 推理服务（调度 / KV Cache / 投机解码） · C 通信与网络（集合通信、NCCL/RDMA、网络拓扑与互联、通信压缩、计算通信重叠、跨机房训练） · D 算子与编译（Kernel / 编译器） · E 量化与高效推理 · F 硬件与体系结构 · G 集群与资源调度 · H Agent 基础设施 · I 评测与性能分析 · Z 其他

Agents: systems / runtime / efficiency side → H here. Agent capability, planning, training methods belong to the LLM topic instead (a paper may be tagged in both).

## `score` (0–1, only if relevant): how much an AI-infra engineer should care.
Weigh: measured on real hardware at meaningful scale (which GPUs, how many, which models); fair baselines (compared against strong mainstream implementations such as vLLM, SGLang, TensorRT-LLM, Megatron, DeepSpeed, FlashAttention — not a self-built weak baseline); production deployment; open-source system; findings that change common beliefs. Simulator-only or toy-scale ≈0.2–0.4; solid systems papers ≈0.5–0.7; ≥0.8 only for clearly outstanding ones.
`star_candidate`: true only if score ≥0.75 AND it's worth a full read; give `star_why` (≤40 Chinese chars, concrete).

## ⭐ (main session's final pick, 2–4 per day)
At least two of: core AI-infra problem; real-hardware measurement at meaningful scale with fair, mainstream baselines; production deployment or open-source system; a finding that changes common beliefs.
**Hard rule:** quantization / pruning / sparsity / low-precision papers can be ⭐ only if they report real speedups (latency, throughput or memory) measured on real hardware; accuracy-only or FLOPs-only results are listed but never starred.
