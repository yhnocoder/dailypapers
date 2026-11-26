# dailypapers

每日 arXiv 论文日报：按主题全量阅读当日公布的论文，筛出相关论文、写中文摘要，挑出值得精读的论文写解读，并生成报纸样式的阅读页面。

- `topics/`：每个主题的配置，包括 arXiv 分类、cs.CV 过滤短语、方向分类、规则版本
- `prompts/`：筛选规则（`classify.md`）和写作规则（`writing.md`）
- `pipeline/`：抓取与组装脚本
- `site/`：页面（`index.html`）和数据（`data/<topic>/<date>.json`、`data/glossary.json`）
