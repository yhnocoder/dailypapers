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
Weigh: closeness to core search/rec problems; industrial / real-scale validation (online A/B, real logs, millions of items); complete, reusable method (open code/models/data, full training recipe); findings that change common beliefs; strong venue acceptance in comment. Pure app papers ≈0.2–0.35; solid method papers ≈0.5–0.7; ≥0.8 only for clearly outstanding ones.
`star_candidate`: true only if score ≥0.75 AND it's worth a full read; give `star_why` (≤40 Chinese chars, concrete).

## ⭐ (main session's final pick, 2–4 per day)
At least two of: core search/rec problem; industrial or real-scale validation; complete, reproducible or open-source method; a finding that changes common beliefs.
