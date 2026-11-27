# dailypapers

每日 arXiv 论文日报。页面部署在 GitHub Pages（`site/` → https://yhnocoder.github.io/dailypapers/），只有一个页面 `site/index.html`，读 `site/data/`。

## 结构

两类运行，各自是一个定时任务、一个独立会话，一次只做一件事：

- **入库**（每天一次）：抓取当天 arXiv 批次（所有主题分类的并集）和 HF / HN 的热门论文，Sonnet 每篇读一次，打上所有主题的标签，存成论文池 `data/papers/<batch>.json`；同时存一份热度快照 `data/heat/<date>.json`（只存数据，页面暂不展示）。
- **出刊**（每个主题按自己的频率）：从论文池取本主题的论文，选出前 N 篇、⭐ 精读、配图、tongtu 全文翻译、导读，产出 `site/data/<topic>/<key>.json`。

论文池和热度快照放在仓库根目录的 `data/`，不部署到 Pages（每天约 2 MB，Pages 站点上限 1 GB）；页面只读 `site/data/` 里每期的数据，那里已经带上了要显示的全部内容。

批次 = arXiv 截稿日（America/New_York），也是分支名和页面里用的日期。一期（issue）可以覆盖一个或多个批次，`key` 是它最后一个批次的日期；`site/data/topics.json` 里每个主题的 `issues[key]` 记录这一期覆盖了哪些批次。

| 主题 | `<topic>` | 频率 | 定时（ET） | 每期上限 | ⭐ | 分支前缀 |
|---|---|---|---|---|---|---|
| —（入库） | — | 每天 | 周日–周四 21:07 | — | — | `daily/ingest` |
| AI Infra | `ai-infra` | 每天 | 周日–周四 21:47 | 15 | 2–4 | `daily/infra` |
| LLM | `llm` | 每天 | 周日–周四 22:17 | 15 | 2–4 | `daily/llm` |
| Search & Rec | `search-rec` | 周三、周日 | 22:47 | 20 | 3–5 | `daily/search` |
| VLM | `vlm` | 周三、周日 | 23:17 | 20 | 3–5 | `daily/vlm` |
| Diffusion | `diffusion` | 周三、周日 | 23:47 | 20 | 3–5 | `daily/diffusion` |
| Embodied AI | `embodied` | 周日 | 22:32 | 20 | 3–5 | `daily/embodied` |

配置：`topics/_ingest.json`（入库）、`topics/<topic>.json`（分类、方向、频率 `cadence.run_days`、上限 `issue_cap`、相关的最低分 `min_score`（默认 0.45，低于它的算「未收录」）、⭐ 数量 `stars`、`start_date`、分支前缀）。范围说明：`prompts/scope/<topic>.md`。

工作目录 `WORK` 放在会话的 scratchpad 里，不要放进仓库。**每个批次、每一期各用一个新目录**：入库用 `<scratchpad>/ingest-<batch>`，出刊用 `<scratchpad>/<topic>-<key>`，不要复用上一个批次或上一期的目录（`assemble.py` 会读目录里所有的 ⭐ 精读稿）。

arXiv 不公布的日子（感恩节等）列在 `topics/_ingest.json` 的 `no_announce` 里：这些日期不算批次，投稿并入下一个批次。arXiv 公布了年底的假期安排后要补进去（https://info.arxiv.org/help/availability.html）。

## 入库流程

1. **待入库的批次**：`python3 pipeline/ingest.py plan`。列出最近 7 天里还没有论文池、且不早于 `start_date` 的工作日批次，从旧到新。为空就跳到第 6 步。下面每个批次各做一遍，**每个批次一个分支 `daily/ingest/<batch>`、一个 PR**。
2. **抓取**：`python3 pipeline/ingest.py fetch <batch> WORK`。退出码 3 表示 arXiv 候选少于 `min_candidates`（150），这一批多半还没公布（不在 `no_announce` 里的临时停发，或 API 还没更新）：跳过这个批次、不提 PR，在汇报里说明，下次再试；如果确认是 arXiv 的假期，把日期加进 `no_announce`（单独提一个 `chore/…` PR）。报错「returned 2000 results」表示某组分类的结果被截断了，不要继续，在汇报里说明。
3. **分批**：`python3 pipeline/ingest.py split WORK` → `WORK/batches/b<i>.json`（每批 64 篇）。
4. **打标签**：用 Workflow 并行跑 Sonnet subagent（每批一个，`model: 'sonnet'`）。每个 agent 读 `prompts/classify.md` 和 `prompts/scope/` 下所有范围说明，把每篇的 `{id, title_zh, summary_zh, affiliation, tags}` 组成一个 **JSON 数组**写到 `WORK/out/b<i>.json`（`tags` 是以主题 id 为键的对象），并用 python 校验 JSON。
5. **合成论文池**：`python3 pipeline/ingest.py build <batch> WORK`。缺结果会直接报错，按提示补跑对应的批次；有 WARNING 时检查一下。
6. **热度快照**（每次运行做一次，不管处理了几个批次）：`python3 pipeline/heat.py`，和最后一个批次放在同一个 PR 里；没有批次时单独提一个 `daily/ingest/heat-<date>` 的 PR。
7. **提交**：按「提交约定」提 PR 并 squash merge。PR 描述写：批次、候选数（arXiv / 热门补充）、每个主题打上标签的篇数、热度快照的条数。

## 出刊流程（一个主题）

1. **要出哪几期**：`python3 pipeline/issue_plan.py --topic <topic>`，每行一个 `{"key", "batches"}`，从旧到新。为空就结束。
   - 如果它提示「最新批次还没有论文池」，说明入库还在跑或失败了：每 5 分钟 `git pull` 一次，最多等 45 分钟，再重新运行 `issue_plan.py`；仍然没有就照常处理已有的批次，并在汇报里说明。
   - 每天出刊的主题每个批次一期；其他主题只在运行日出一期，覆盖所有还没出过的批次。
   - 下面每一期各做一遍，**每期一个分支 `<branch_prefix>/<key>`、一个 PR**，按从旧到新的顺序合并。
2. **选出本期的论文**：`python3 pipeline/select.py topics/<topic>.json WORK <batch> …`，产出 `WORK/selection.json`（前 `issue_cap` 篇 `shown`，其余相关的 `others` 折叠显示）和 `WORK/abstract_in.json`。
3. **中文摘要**：用 Workflow 跑 Sonnet subagent（每 10 篇一个），按 `prompts/abstract.md` 翻译 `abstract_in.json` 里的论文，合并成 `WORK/abstracts.json`（`[{id, abstract_zh}]`）。
4. **选 ⭐**：主会话在 `shown` 里做最终决定，数量见主题配置的 `stars`，宁缺毋滥；`select.py` 打印的 `star hints` 是 Sonnet 的提名，只作参考。标准见 `prompts/scope/<topic>.md` 的「⭐」一节（AI Infra：量化、剪枝类论文必须有真实硬件上的加速数据才能 ⭐）。
5. **精读**：再用一个 Workflow，每篇 ⭐ 一个 agent（不指定模型）。先为每篇写 `WORK/star/<id>.in.json`（论文池里的元数据 + `abstracts.json` 里的中文摘要 + 本主题的 `direction` + `headline`：本期 ⭐ 里主题分数最高的那篇为 `true`，它是头条，篇幅更长）。agent 把 PDF 下载到 `WORK/star/pdf_<id>/`，用 `pdftotext -layout` 提取全文并读完，按 `prompts/writing.md` 写 `WORK/star/<id>.out.json`：`{id, title_zh, analysis[], abstract_zh, affiliation, code, star_reasons[], glossary_new[], figures[]}`。配图从论文的 arXiv HTML 版里挑（见 `prompts/writing.md`「配图」）。主会话逐篇审改：没读过论文的人能不能顺着读懂、数字有没有对上原文的实验组、agent 自己的推测有没有用「我怀疑」标明。审改后决定不给 ⭐ 的论文，要删掉它的 `out.json`（⭐ 以 `star/<id>.out.json` 是否存在为准）。
5b. **全文翻译（tongtu）**：选完 ⭐ 后，在后台对每篇运行 `tongtu run <id> --mode fast`（模式见主题配置 `translations.tongtu_mode`），每篇间隔 20 秒启动，避免 arXiv 限流，和第 5 步并行。`tongtu` 不存在时先执行 `uv tool install git+https://github.com/yhnocoder/tongtu` 和 `tongtu doctor`。全部跑完后执行 `python3 pipeline/upload_translations.py topics/<topic>.json WORK <id> …`，生成 `WORK/translations.json`。某篇失败先原地重跑一次（会从失败的阶段继续）；仍然失败就放弃这篇的译文，不阻塞日报，在 PR 描述和汇报里写明失败的阶段和原因。
   **只要某篇翻译失败过（包括重跑后成功的），都要把它的 tongtu 工作目录打包发给用户调试**：工作目录用 `tongtu status <id> --json` 的 `workdir` 字段取得（形如 `/root/.tongtu/papers/2611.34366v1/`，里面有 `logs/`、`build/manifests/`、`last_run.json` 等），打成 `tongtu_<idv>_<key>.zip` 放在 scratchpad，用发文件的工具（SendUserFile）在会话里发出来，并在汇报里注明。译文只存在 R2，不进仓库，见 `worker/README.md`。
6. **导读**：主会话按 `prompts/writing.md` 写 `WORK/overview.json`：`{"guide": ["段落", …]}`，2–3 段、约 600 字，按话题组织（不按 ⭐ / 非 ⭐ 分段）。⭐ 论文全部提到，非 ⭐ 只写本期 `shown` 里的论文。
7. **组装**：`python3 pipeline/assemble.py topics/<topic>.json <key> WORK`。更新 `site/data/<topic>/<key>.json`、`site/data/topics.json`（`dates`、`issues`）、`site/data/glossary.json`。
8. **本地检查**：`cd site && python3 -m http.server 8766`，用 Playwright 在 1280 和 400 宽度下打开 `index.html#<topic>-<key>`，确认没有 pageerror、`scrollWidth` 等于视口宽度、每个 `.term` 都能对应到术语表、导读里的论文链接都能跳到对应论文。

## 提交约定

- 不直接 push 到 `main`。每次改动都新建分支，提 PR，然后 **squash merge**。
- 分支命名：入库 `daily/ingest/<batch>`；出刊 `<branch_prefix>/<key>`（如 `daily/llm/2026-11-25`）；改规则或模板用 `chore/…` / `feat/…`。
- 会话里 `gh pr create` 用不了（GraphQL 被拦截），改用 REST：
  - 建 PR：`gh api repos/yhnocoder/dailypapers/pulls -f title=… -f head=<branch> -f base=main -F body=@pr.md`
  - 合并（必须带上提交信息，否则署名会丢）：
    ```
    gh api -X PUT repos/yhnocoder/dailypapers/pulls/<n>/merge -f merge_method=squash \
      -f commit_title="<PR 标题> (#<n>)" \
      -f commit_message="<一句话说明>

    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    ```
- push 用 `git -c push.negotiate=true push -u origin <branch>`。合并前 main 已经前进（入库和多个主题会先后合并）时，`git pull --rebase origin main` 后再推；冲突一般只在 `site/data/topics.json` / `site/data/glossary.json`：先用 `git checkout origin/main -- site/data/topics.json site/data/glossary.json` 取 main 的版本，`git add` 后 `git rebase --continue`，再重新运行第 7 步的 `assemble.py`（它会把本期加回去）并另提交一次，不要手工合并 JSON。
- 出刊 PR 描述里写：漏斗数字、⭐ 论文和入选理由、配图与译文情况、新增的术语。
- commit 信息末尾必须原样带上这一行（squash merge 时也放进合并后的提交信息）：
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```
- 仓库已开启 merge 后自动删除分支，会话里不需要也无法删除分支。
- merge 后由 `.github/workflows/pages.yml` 自动部署（只在 `site/` 有改动时触发，所以入库 PR 不会部署，也不用检查）。出刊 PR 合并后用 `gh run list --workflow pages.yml` 确认这次合并触发的部署成功；如果失败，用 `gh run rerun <id>` 重跑一次。

## 规则

- 入库打标签：`prompts/classify.md`（通用）+ `prompts/scope/<topic>.md`（各主题的范围、方向、打分、⭐ 标准）；中文摘要：`prompts/abstract.md`。
- 精读、配图与导读写作规则：`prompts/writing.md`（汇总了读者的反馈，修改要谨慎）。
- 方向分类固定在 `topics/<topic>.json` 中，改动时要升级 `taxonomy_version`；改范围或打分规则时要升级 `rules_version`。
- 术语表 `site/data/glossary.json` 全局共享，只增不重复。
- tongtu 译文不放进本仓库：arXiv 论文的许可证不一定允许公开再分发。
