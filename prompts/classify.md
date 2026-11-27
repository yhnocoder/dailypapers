# Ingest tagging rules (shared paper pool, all topics at once)

Each paper in the pool is read once and tagged for every topic it belongs to. Before tagging, read every scope file in `prompts/scope/` (search-rec, ai-infra, llm, vlm, diffusion, embodied): each defines, for its topic, what is relevant, the direction codes, how to score, and when to set `star_candidate`.

A paper can belong to several topics (e.g. a GPU vector index → search-rec and ai-infra; a GUI agent → vlm and llm). Tag every topic whose scope says TRUE; tag none if it fits no topic. Judge each topic independently against its own scope and scoring scale.

## Chinese writing (all Chinese fields)
- Chinese text uses full-width Chinese punctuation（，。：；！？（）“”）; numbers, English words and formulas keep half-width characters. Never write a half-width comma or period between Chinese characters.
- Natural, plain Chinese as a domain expert would write; keep established English terms (RAG, reranker, embedding, query, Recall@10, BM25…) in English.
- NO filler: never use 值得注意的是 / 综上所述 / 总而言之 / 具有重要意义 / 奠定基础 / 开辟新方向 / 令人振奋 / 显著提升(without a number) / 三连排比. No preamble sentences; start with the substance.
- Don't invent facts or numbers not in the abstract.

Fields (one JSON object per paper):
- `id`
- `title_zh` (ALL papers): faithful Chinese rendering of the title, readable, not sensationalised. Model/system names stay in English.
- `summary_zh` (ALL papers): ONE sentence (≤60 Chinese chars) saying concretely what the paper does / finds. No "本文" opener.
- `affiliation`: only if an institution/company is stated in the abstract or comment (e.g. "online experiments at AliExpress" → "AliExpress"); else "".
- `tags`: object keyed by topic id, only for topics the paper belongs to, e.g.
  `{"llm": {"direction": "F", "score": 0.62, "star_candidate": false, "star_why": ""}, "ai-infra": {...}}`.
  `{}` when it belongs to no topic. `star_why` (≤40 Chinese chars, concrete) only when `star_candidate` is true.

Do not translate the abstract here: full Chinese abstracts are written later, only for the papers an issue actually shows (`prompts/abstract.md`).
