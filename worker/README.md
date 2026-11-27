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
   - Cloudflare 后台 → Workers & Pages → `dailypapers-files` → Settings → Domains & Routes → `workers.dev` 那一行 → 开启 Cloudflare Access。
   - 打开 Zero Trust → Access → Applications，找到自动生成的应用，把策略改成只允许你的邮箱。
   - 在这个应用的 Overview 里复制 **Application Audience (AUD) Tag**；在 Zero Trust → Settings 里找到团队域名（形如 `xxx.cloudflareaccess.com`）。
   - 把两个值填进 `wrangler.read.toml` 的 `ACCESS_AUD` 和 `ACCESS_TEAM_DOMAIN`，重新部署：

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
