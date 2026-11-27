# Scope: Diffusion (diffusion)

## Is it relevant? (`relevant`)
TRUE when the research object is *visual* generative modelling: diffusion, flow matching, autoregressive or other generators of images, video, 3D/4D content and world models.
- image generation and editing, controllable generation, personalisation
- video generation and editing, long video
- 3D / 4D generation (assets, scenes, Gaussian-splatting generation, dynamic scenes)
- world models (interactive, game/driving scene generation)
- theory and training methods (diffusion/flow theory, distillation, consistency models, objectives), technical reports of generation models
- sampling acceleration (few-step sampling, caching, inference speedups)
- evaluation and safety of generation (quality metrics, copyright, watermarking, harmful content)
FALSE: audio/speech/music generation, molecules/proteins and other non-visual generation; diffusion used only as a component for a non-generative task; pure reconstruction without generation.

## Direction — exactly one code:
A 图像生成 · B 视频生成 · C 3D / 4D 生成 · D 世界模型 · E 理论与训练方法 · F 采样加速 · G 评测与安全 · Z 其他

## `score` (0–1): how much someone working on generative models should care.
Weigh: rigour and scale, open release, major-lab model reports, strong human/automatic evaluation, belief-changing findings.

Use the whole range and two decimals (0.62, not 0.6): the score orders the issue, so papers of one batch should not pile up on the same value. Score from what the abstract and comment actually state; evidence that is not stated (scale, baselines, release) counts as absent.

| Score | Meaning | Typical paper |
|---|---|---|
| 0.85–1.00 | People in this field need to know about it this week. Rare: most batches have none. | A flagship image / video / world model report from a major lab with released weights; or a result that changes how these models are trained or sampled, shown at scale. |
| 0.70–0.84 | Strong: rigorous evidence at real scale plus something reusable or surprising. `star_candidate` starts at 0.75. | A method validated on current large models (not only small class-conditional ImageNet or CIFAR setups) with human or strong automatic evaluation and released code or weights. |
| 0.55–0.69 | Solid and complete, but incremental. | A complete method with standard metrics and baselines at moderate scale. |
| 0.45–0.54 | Relevant, with narrow scope or thin evidence. Shown only if the issue has room. | A narrow tweak, small-scale or single-dataset evaluation, qualitative results only. |
| 0.20–0.44 | Marginal. Not shown as related. | Application papers that only use an off-the-shelf generator, surveys without new evidence. |

`star_candidate`: score ≥0.75 AND worth a full read; `star_why` ≤40 Chinese chars.

## ⭐
At least two of: core generative-modelling question; rigorous large-scale evidence; open model/code or a major technical report; a finding that changes common beliefs.
