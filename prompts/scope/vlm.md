# Scope: VLM / 多模态 (vlm)

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
Same scale as other topics: rigour, scale, open release, major lab reports, belief-changing findings. Single-dataset tweaks ≈0.2–0.4; solid ≈0.5–0.7; ≥0.8 outstanding.
`star_candidate`: score ≥0.75 AND worth a full read; `star_why` ≤40 Chinese chars.

## ⭐
At least two of: core multimodal question; rigorous large-scale evidence; open model/data/code or a major technical report; a finding that changes common beliefs.
