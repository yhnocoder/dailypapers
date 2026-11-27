# Chinese abstract translation (issue stage)

For each paper given (id, title, abstract), write `abstract_zh`: a complete, faithful Chinese translation of the English abstract, same length as the original — do not summarise.

## Chinese writing (all Chinese fields)
- Chinese text uses full-width Chinese punctuation（，。：；！？（）“”）; numbers, English words and formulas keep half-width characters. Never write a half-width comma or period between Chinese characters.
- Natural, plain Chinese as a domain expert would write; keep established English terms (RAG, reranker, embedding, query, Recall@10, BM25…) in English.
- NO filler: never use 值得注意的是 / 综上所述 / 总而言之 / 具有重要意义 / 奠定基础 / 开辟新方向 / 令人振奋 / 显著提升(without a number) / 三连排比. No preamble sentences; start with the substance.
- Don't invent facts or numbers not in the abstract.

Inline markup in `abstract_zh`:
- `==term==` around ≤3 key concepts the reader must grasp (the method's core idea / new concept names).
- `**phrase**` around ≤2 main results or caveats worth noticing (prefer ones with numbers).
- Do not nest them; do not mark trivial words.

Output: a JSON array of `{"id", "abstract_zh"}`, same order as the input.
