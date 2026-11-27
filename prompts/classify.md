# Classification + Chinese-writing rules (shared by all topics)

Read the topic's scope file first (`scope_prompt` in `topics/<topic>.json`, e.g. `prompts/scope/search-rec.md`): it defines `relevant`, `direction`, `score` and `star_candidate` for that topic. This file defines everything else.

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
