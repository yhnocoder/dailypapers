# dailypapers

每日 arXiv 论文日报：按主题全量阅读当日公布的论文，筛出相关论文、写中文摘要，挑出值得精读的论文写解读，并生成报纸样式的阅读页面。

- `topics/`：每个主题的配置，包括 arXiv 分类、cs.CV 过滤短语、方向分类、规则版本
- `prompts/`：筛选规则（`classify.md`）和写作规则（`writing.md`）
- `pipeline/`：抓取与组装脚本
- `site/`：页面（日报 `index.html` / `ink.html`，周报 `weekly.html`）和数据（`data/<topic>/<date>.json`、`data/<topic>/weekly/<YYYY-Www>.json`、`data/glossary.json`）

每周另出一期周报：不重读论文，从当周日报里重选必读、把不同日子的论文串成线索，流程见 `CLAUDE.md` 的「周报」一节。
