# dailypapers

每日 arXiv 论文日报。页面部署在 GitHub Pages（`site/` → https://yhnocoder.github.io/dailypapers/）。

## 每日流程（一个主题、一个 arXiv 公布日）

工作目录 `WORK` 放在会话的 scratchpad 里，不要放进仓库。

1. **抓取**：`python3 pipeline/fetch_arxiv.py topics/search-rec.json <YYYY-MM-DD> WORK/all.json`
   日期以 arXiv **公布日**为准，脚本会自动换算对应的提交时间窗口。
2. **分批**：把 `all.json` 按每 64 篇切成 `WORK/batches/b0.json …`，每篇只保留 id、title、cat、cats、comment、abstract 字段。
3. **筛选**：用 Workflow 并行跑 Sonnet subagent（每批一个，`model: 'sonnet'`）。每个 agent 读 `prompts/classify.md` 和一批论文，把每篇的 `{id, relevant, direction, score, star_candidate, star_why, title_zh, summary_zh, abstract_zh, affiliation, exclude_reason}` 写到 `WORK/out/b<i>.json`，并用 python 校验 JSON。每篇候选论文都要有结果。
4. **选 ⭐**：主会话参考 `star_candidate` 和 `score` 做最终决定，通常每天 2–4 篇，宁缺毋滥。标准是至少满足两条：核心搜推问题、工业或真实规模验证、方法完整可复现或开源、结论改变已有认知。
5. **精读**：再用一个 Workflow，每篇 ⭐ 论文一个 agent（不指定模型）。先为每篇写 `WORK/star/<id>.in.json`，内容是元数据加 Sonnet 的 `title_zh`、`abstract_zh`、`direction`。agent 把 PDF 下载到 `WORK/star/pdf_<id>/`，用 `pdftotext -layout` 提取全文并读完，按 `prompts/writing.md` 写 `WORK/star/<id>.out.json`，字段为 `{id, title_zh, analysis[], abstract_zh, affiliation, code, star_reasons[], glossary_new[]}`。主会话逐篇审改，尤其是标题和保留意见。
5b. **全文翻译（tongtu）**：选完 ⭐ 后，在后台对每篇运行 `tongtu run <id> --mode fast`，模式见 `topics/search-rec.json` 的 `translations.tongtu_mode`，和第 5 步的精读并行。如果 `tongtu` 不存在，先执行 `uv tool install git+https://github.com/yhnocoder/tongtu` 和 `tongtu doctor`。全部跑完后执行 `python3 pipeline/upload_translations.py topics/search-rec.json WORK <id> …`，把译文上传到 Cloudflare R2，并生成 `WORK/translations.json`。某篇失败不阻塞日报，在 PR 描述和最终汇报里写明原因。译文只存在 R2，不进仓库，说明见 `worker/README.md`。
6. **导读**：主会话按 `prompts/writing.md` 写 `WORK/overview.json`，格式为 `{"guide": ["⭐ 段落", "非 ⭐ 段落"]}`，最多 2 段、约 400 字以内。
7. **组装**：`python3 pipeline/assemble.py topics/search-rec.json <date> WORK`。这一步会更新 `site/data/<topic>/<date>.json`、`site/data/topics.json`、`site/data/glossary.json`。
8. **本地检查**：`cd site && python3 -m http.server 8766`，用 Playwright 在 1280 和 400 宽度下打开页面，确认没有 pageerror、`scrollWidth` 等于视口宽度、每个 `.term` 都能对应到术语表。

## 提交约定

- 不直接 push 到 `main`。每次改动都新建分支，提 PR，然后 **squash merge**。
- 分支命名：每日更新用 `daily/search/<YYYY-MM-DD>`（前缀见 `topics/search-rec.json` 的 `branch_prefix`）；改规则或模板用 `chore/…` / `feat/…`。
- 会话里 `gh pr create` 用不了（GraphQL 被拦截），改用 REST：
  - 建 PR：`gh api repos/yhnocoder/dailypapers/pulls -f title=… -f head=<branch> -f base=main -F body=@pr.md`
  - 合并（必须带上提交信息，否则署名会丢）：
    ```
    gh api -X PUT repos/yhnocoder/dailypapers/pulls/<n>/merge -f merge_method=squash \
      -f commit_title="<PR 标题> (#<n>)" \
      -f commit_message="<一句话说明>

    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    ```
- push 用 `git -c push.negotiate=true push -u origin <branch>`。
- 日报 PR 描述里写：漏斗数字、⭐ 论文和入选理由、新增的术语。
- commit 信息末尾必须原样带上这一行（squash merge 时也放进合并后的提交信息）：
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```
- 仓库已开启 merge 后自动删除分支，会话里不需要也无法删除分支。
- merge 后由 `.github/workflows/pages.yml` 自动部署。合并后用 `gh run list` 确认部署成功；如果失败，用 `gh run rerun <id>` 重跑一次。

## 规则

- 筛选与中文写作规则：`prompts/classify.md`
- 精读与导读写作规则：`prompts/writing.md`（汇总了读者的反馈，修改要谨慎）
- 方向分类固定在 `topics/<topic>.json` 中，改动时要升级 `taxonomy_version`；改筛选规则时要升级 `rules_version`。
- 术语表 `site/data/glossary.json` 全局共享，只增不重复。
- tongtu 译文不放进本仓库：arXiv 论文的许可证不一定允许公开再分发。
