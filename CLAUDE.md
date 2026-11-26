# dailypapers

每日 arXiv 论文日报。页面部署在 GitHub Pages（`site/` → https://yhnocoder.github.io/dailypapers/）。

## 每日流程（一个主题、一个 arXiv 公布日）

1. 抓取：`python3 pipeline/fetch_arxiv.py topics/<topic>.json <YYYY-MM-DD> WORK/all.json`
   日期以 arXiv **公布日**为准，脚本会自动换算对应的提交时间窗口。
2. 筛选：把 `all.json` 每 ~64 篇切成一批，由 Sonnet subagent 按 `prompts/classify.md` 并行处理，结果写到 `WORK/out/b*.json`。每篇候选论文都要有结果，未收录的也要写一句话中文摘要。
3. 选 ⭐：参考 Sonnet 提名（`star_candidate`）和分数，由主会话做最终决定，通常每天 2–4 篇，宁缺毋滥。
4. 精读：每篇 ⭐ 论文交给一个 subagent 读完整 PDF，按 `prompts/writing.md` 写 `WORK/star/<id>.out.json`。主会话逐篇审改，尤其是标题和保留意见。
5. 导读：主会话按 `prompts/writing.md` 写 `WORK/overview.json`，只写非 ⭐ 论文。
6. 组装：`python3 pipeline/assemble.py topics/<topic>.json <date> WORK`。这一步会更新 `site/data/<topic>/<date>.json`、`site/data/topics.json`、`site/data/glossary.json`。
7. 本地检查：`cd site && python3 -m http.server`，用 Playwright 在 1280 / 400 宽度下截图，确认没有报错、没有横向滚动。

## 提交约定

- 不直接 push 到 `main`。每次改动都新建分支，提 PR，再 merge。
- 分支命名：日报用 `digest/<topic>-<date>`，改规则或模板用 `chore/…` / `feat/…`。
- 日报 PR 描述里写：漏斗数字、⭐ 论文和入选理由、新增的术语。
- merge 后由 `.github/workflows/pages.yml` 自动部署。

## 规则

- 筛选与中文写作规则：`prompts/classify.md`
- 精读与导读写作规则：`prompts/writing.md`（汇总了读者的反馈，修改要谨慎）
- 方向分类固定在 `topics/<topic>.json` 中，改动时要升级 `taxonomy_version`；改筛选规则时要升级 `rules_version`。
- 术语表 `site/data/glossary.json` 全局共享，只增不重复。
- tongtu 译文不放进本仓库：arXiv 论文的许可证不一定允许公开再分发。
