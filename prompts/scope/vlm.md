# Scope: VLM (vlm)

## Is it relevant? (`relevant`)
TRUE when the research object is models that understand vision (images/video/documents/screens) together with language:
- VLM architectures, vision encoders, connectors/alignment, multimodal pre-training and instruction tuning, VLM technical reports
- multimodal reasoning (visual math/chart reasoning, visual chain-of-thought, multimodal RL)
- video understanding (long video, temporal grounding, streaming video)
- documents, OCR, tables, charts, GUI screenshots
- visual grounding and perception with VLMs (referring, detection/segmentation-style VLMs, spatial understanding)
- GUI agents and computer use
- unified understanding-and-generation models
- multimodal benchmarks, hallucination detection/mitigation
FALSE: pure vision models with no language component (classic detection/segmentation/tracking), pure image/video generation without understanding (Diffusion topic), robotics/VLA (Embodied topic), audio-only work.

## Direction — exactly one code:
A 架构与训练（含多模态技术报告） · B 多模态推理 · C 视频理解 · D 文档与 OCR · E 视觉 Grounding 与感知 · F GUI Agent / Computer Use · G 统一理解与生成 · H 评测与幻觉 · Z 其他

## `score` (0–1): how much a multimodal researcher/engineer should care.
Weigh: rigour, scale, open release, major-lab reports, belief-changing findings.

Use the whole range and two decimals (0.62, not 0.6): the score orders the issue, so papers of one batch should not pile up on the same value. Score from what the abstract and comment actually state; evidence that is not stated (scale, baselines, release) counts as absent.

| Score | Meaning | Typical paper |
|---|---|---|
| 0.85–1.00 | People in this field need to know about it this week. Rare: most batches have none. | A flagship multimodal model's technical report from a major lab; or a diagnosis of how VLMs fail that holds across many open and closed models and comes with released data and code. |
| 0.70–0.84 | Strong: rigorous evidence at real scale plus something reusable or surprising. `star_candidate` starts at 0.75. | A new architecture, training recipe or benchmark validated on several current VLMs with controlled comparisons and released artifacts; an audit showing that reported gains are not what they seem. |
| 0.55–0.69 | Solid and complete, but incremental. | A sound method or benchmark with standard baselines on a few models. |
| 0.45–0.54 | Relevant, with narrow scope or thin evidence. Shown only if the issue has room. | A single-dataset or single-model tweak, a narrow domain benchmark, small models only. |
| 0.20–0.44 | Marginal. Not shown as related. | Application papers that only call a VLM, surveys without new evidence. |

`star_candidate`: score ≥0.75 AND worth a full read; `star_why` ≤40 Chinese chars.

## ⭐
At least two of: core multimodal question; rigorous large-scale evidence; open model/data/code or a major technical report; a finding that changes common beliefs.
