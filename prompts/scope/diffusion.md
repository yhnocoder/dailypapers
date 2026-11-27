# Scope: Diffusion / 生成 (diffusion)

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

## `score` (0–1)
Rigour and scale, open release, major-lab model reports, strong human/automatic evaluation, belief-changing findings. Narrow tweaks ≈0.2–0.4; solid ≈0.5–0.7; ≥0.8 outstanding.
`star_candidate`: score ≥0.75 AND worth a full read; `star_why` ≤40 Chinese chars.

## ⭐
At least two of: core generative-modelling question; rigorous large-scale evidence; open model/code or a major technical report; a finding that changes common beliefs.
