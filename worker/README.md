# 译稿存储（Cloudflare R2 + Workers + Access）

tongtu 生成的中文 PDF 和 out 目录不放进 git，存在 Cloudflare R2，只有你本人能看。

```
每日会话 ──PUT（Bearer token）──▶ dailypapers-upload ──┐
                                                      ├──▶ R2 存储桶 dailypapers-zh
你的浏览器 ──GET（Cloudflare Access 登录）──▶ dailypapers-files ──┘
```

- `upload.js`：只接受带正确 token 的 PUT，只能写 `papers/<id>/<file>`，不能读也不能删。
- `read.js`：前面挂 Cloudflare Access，Worker 自己再校验一遍 Access 的 JWT。Access 没配好时一律返回 403，不会意外公开。PDF 以 inline 方式返回，浏览器直接打开；zip 作为下载。

## 一次性配置（在你自己的电脑上执行）

需要 Node.js。以下命令在本目录（`worker/`）执行。

1. 登录并创建存储桶

   ```bash
   npx wrangler login
   ```

   ```bash
   npx wrangler r2 bucket create dailypapers-zh
   ```

2. 部署读取 Worker

   ```bash
   npx wrangler deploy -c wrangler.read.toml
   ```

3. 给读取 Worker 开启 Cloudflare Access
   - 第一次使用时，先在 Worker 的 **Access** 标签页点 **Set up Zero Trust**：填团队名（决定登录域名 `<团队名>.cloudflareaccess.com`），套餐选 Free。
   - 回到 `dailypapers-files` → **Access** 标签页 → Manage Worker access：
     - **Scope 选 All traffic**。选 Previews only 时，正式地址不经过 Access，Worker 拿不到 Access 凭证，会一直返回 403。
     - **Authentication policy**：默认的 Cloudflare account（这个 Cloudflare 账号的成员可以访问），或者按邮箱放行（One-time PIN，必须能收到邮箱里的验证码）。
     - Session duration 按需要调，比如 1 周。
   - 在 Zero Trust → Access → Applications 里打开这个 Worker 对应的应用，复制 **Application Audience (AUD) Tag**。
   - 把团队域名和 AUD 填进 `wrangler.read.toml` 的 `ACCESS_TEAM_DOMAIN` 和 `ACCESS_AUD`，重新部署（之后每次 `wrangler deploy` 都会用 toml 里的值覆盖后台的变量）：

     ```bash
     npx wrangler deploy -c wrangler.read.toml
     ```

   这两个值不是密钥，可以提交到仓库。

4. 部署上传 Worker 并设置 token

   ```bash
   npx wrangler deploy -c wrangler.upload.toml
   ```

   ```bash
   openssl rand -hex 32
   ```

   ```bash
   npx wrangler secret put UPLOAD_TOKEN -c wrangler.upload.toml
   ```

   把上一步生成的随机串粘贴进去，同时自己保存一份。**不要**提交到仓库，也不要发在对话里。

5. 把两个 `*.workers.dev` 地址告诉 Claude（不要发 token）。Claude 会：
   - 把地址写进 `topics/search-rec.json` 的 `translations.upload_base` / `files_base`；
   - 申请把上传地址加入会话环境的网络白名单，并弹出安全表单，你在表单里粘贴 token。之后代理会在请求上传地址时自动带上这个 token。

## 自检

浏览器打开 `https://dailypapers-files.<你的子域>.workers.dev/papers/x/y.pdf`：应先跳到 Access 登录页；登录后返回 404（文件不存在），说明链路通了。不登录直接 curl 应该拿到 Access 的登录页或 403。
