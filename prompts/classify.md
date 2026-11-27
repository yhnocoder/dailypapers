# Classification + Chinese-writing rules (topic: 搜索与推荐 / search & recommendation)

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

## Chinese writing (all Chinese fields)
- Chinese text uses full-width Chinese punctuation（，。：；！？（）“”）; numbers, English words and formulas keep half-width characters. Never write a half-width comma or period between Chinese characters.
- Natural, plain Chinese as a domain expert would write; keep established English terms (RAG, reranker, embedding, query, Recall@10, BM25…) in English.
- NO filler: never use 值得注意的是 / 综上所述 / 总而言之 / 具有重要意义 / 奠定基础 / 开辟新方向 / 令人振奋 / 显著提升(without a number) / 三连排比. No preamble sentences; start with the substance.
- Don't invent facts or numbers not in the abstract.

Fields:
- `title_zh` (ALL papers): faithful Chinese rendering of the title, readable, not sensationalised. Model/system names stay in English.
- `summary_zh` (ALL papers): ONE sentence (≤60 Chinese chars) saying concretely what the paper does / finds. No "本文" opener.
- `abstract_zh` (ONLY relevant papers): complete, faithful translation of the abstract, same length as original. Inline markup:
  - `==term==` around ≤3 key concepts the reader must grasp (the method's core idea/new concept names).
  - `**phrase**` around ≤2 main results or caveats worth noticing (prefer ones with numbers).
  - Do not nest them; do not mark trivial words.
- `affiliation`: only if an institution/company is stated in the abstract or comment (e.g. "online experiments at AliExpress" → "AliExpress"); else "".
- `exclude_reason` (ONLY non-relevant): ≤20 Chinese chars why it's out.
