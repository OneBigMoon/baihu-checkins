# 白虎签到应用

适配白虎面板声明式应用规范 v1 的四个签到应用，源码与凭据分离。

| 应用 | 配置 | 默认任务 |
| --- | --- | --- |
| 携程 | CTRIP_COOKIE | 每天 09:10 签到 |
| 天翼云盘 | CLOUD189_USERNAME、CLOUD189_PASSWORD | 每天 09:10 签到 |
| 百度贴吧 | TIEBA_COOKIE、TIEBA_FORUMS | 每天 09:10 按列表签到 |
| 什么值得买 | SMZDM_COOKIE | 每天 09:20 浏览与领奖；签到任务默认关闭 |

## 安装

在白虎面板“应用市场 → 导入应用”填写对应的清单地址：

- 携程每日签到：`https://raw.githubusercontent.com/OneBigMoon/baihu-checkins/v1.0.1/apps/ctrip-checkin/app.yaml`
- 天翼云盘每日签到：`https://raw.githubusercontent.com/OneBigMoon/baihu-checkins/v1.0.1/apps/cloud189-checkin/app.yaml`
- 百度贴吧每日签到：`https://raw.githubusercontent.com/OneBigMoon/baihu-checkins/v1.0.1/apps/tieba-checkin/app.yaml`
- 什么值得买签到与任务奖励：`https://raw.githubusercontent.com/OneBigMoon/baihu-checkins/v1.0.1/apps/smzdm-checkin/app.yaml`

安装表单只填写本人的账号凭据。Cookie 从对应官网已登录页面的网络请求读取，不要提交到仓库、Issue 或聊天中。

如果面板已经有相同签到任务，安装后先停用旧任务再启用新任务，避免同一天重复触发。清单使用六段 Cron，第一段为秒；具体运行时间可在面板中修改。

## 配置与结果

- 贴吧列表使用英文逗号分隔，例如 `吧名一,吧名二`。程序去重后只签到指定列表，不自动关注贴吧。错误码 1011 计为跳过；全部跳过或存在其他失败时返回非零退出码。
- 天翼云盘的表单提供独立账号、密码字段。脚本仍兼容旧的 `CLOUD189_ACCOUNT` JSON；如填写了新字段，需同时填写账号和密码。
- 什么值得买签到可能返回 110202 验证码错误，因此默认关闭；在官网完成验证并确认接口可用后再启用。奖励任务只处理支持的浏览和领奖；评论、关注、爆料、笔记和文章由本人完成。
- 所有应用默认不自动重试。登录失效、验证码和网络错误会保留为失败，避免反复请求。

## 本地运行与验证

Python 3.9 以上可运行源码，面板清单使用镜像预装的 Python 3.13.12。只有天翼脚本需要额外依赖：

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

测试模拟接口响应，不读取真实账号环境、不发送网络请求。覆盖缺少凭据、过期登录、已签到、验证码、贴吧部分跳过和人工任务边界；不代表平台接口长期可用。

华住会和恩山论坛暂未纳入这次发布：前者最近返回 HTTP 401，后者尚未完成当前接口的验证。

许可证：MIT。
