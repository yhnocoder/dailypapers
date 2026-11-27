# Scope: Search & Rec (search-rec)

## Is it relevant? (`relevant`: true/false)
TRUE when the paper's OWN research object is search or recommendation:
- web/vertical/e-commerce search engines, search agents, deep research agents, agentic search
- retrieval models: dense/sparse/multi-vector/multimodal embeddings *for retrieval*, cross-lingual retrieval
- ranking: reranking, learning to rank, relevance modeling, LLM rankers
- query understanding / rewriting / expansion
- RAG where the paper studies the retrieval side or the retrieval–generation pipeline (not just "we use RAG in app X" — pure application papers that only plug in a stock RAG are FALSE unless they contribute a retrieval method or evaluation)
- recommender systems (any kind: sequential, generative/semantic-ID, CTR, multimodal, cross-domain, LLM-based rec, evaluation of recsys)
- indexing/ANN/vector search/quantization for retrieval, search systems efficiency
- evaluation/benchmarks of search/retrieval/recsys/RAG/deep-research, generative engines (GEO, AI search behaviour)
FALSE when "retrieval" is incidental: agent memory used as a component, linear-attention "associative recall", phase retrieval (physics), robot demo retrieval, generic LLM/RL/agent work, hallucination work without a retrieval contribution, KG construction without retrieval, generic text classification, etc.

## Direction (`direction`, only if relevant) — exactly one code:
A 搜索 Agent / Deep Research · B 检索模型（Embedding / 多模态检索） · C 排序与相关性 · D Query 理解 · E RAG / GraphRAG · F 推荐系统 · G 索引与检索系统（ANN / 量化） · H 评测 / Benchmark / 生成式引擎 · Z 其他

## `score` (0–1, only if relevant): how much a search/rec practitioner should care.
Weigh: closeness to core search/rec problems; industrial / real-scale validation (online A/B, real logs, millions of items); complete, reusable method (open code/models/data, full training recipe); findings that change common beliefs; strong venue acceptance in comment.

Use the whole range and two decimals (0.62, not 0.6): the score orders the issue, so papers of one batch should not pile up on the same value. Score from what the abstract and comment actually state; evidence that is not stated (scale, baselines, release) counts as absent.

| Score | Meaning | Typical paper |
|---|---|---|
| 0.85–1.00 | People in this field need to know about it this week. Rare: most batches have none. | A production system at a major platform with online A/B results and enough detail to reproduce; or a released embedding / reranking model or benchmark that becomes the new reference. |
| 0.70–0.84 | Strong: rigorous evidence at real scale plus something reusable or surprising. `star_candidate` starts at 0.75. | A core retrieval / ranking / recommendation method with online A/B or real-log validation at scale, or a rigorous study that contradicts a common practice, with code or models released. |
| 0.55–0.69 | Solid and complete, but incremental. | A complete method on standard public benchmarks (BEIR, MTEB, Amazon, MovieLens-scale and above) with strong baselines. |
| 0.45–0.54 | Relevant, with narrow scope or thin evidence. Shown only if the issue has room. | Small or dated datasets only, weak baselines, or a RAG pipeline variation evaluated on one QA set. |
| 0.20–0.44 | Marginal. Not shown as related. | Pure application papers that use retrieval or recommendation as a component, surveys without new evidence. |

`star_candidate`: true only if score ≥0.75 AND it's worth a full read; give `star_why` (≤40 Chinese chars, concrete).

## ⭐ (main session's final pick, 2–4 per day)
At least two of: core search/rec problem; industrial or real-scale validation; complete, reproducible or open-source method; a finding that changes common beliefs.
