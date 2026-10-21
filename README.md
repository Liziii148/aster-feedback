# 萤火虫紫菀 Aster 2.1.0 反馈分析 · GitHub 版

网站由GitHub Pages托管，采集测试由GitHub Actions手动启动，无需本机安装Python。研究起始日固定为2026-10-15，预置用户提供的两条测试链接。

## 明确能力边界

此包完成了可提交GitHub的页面和工作流配置，尚未部署、尚未在GitHub Actions跑通真实小红书数据。采集器仅尝试读取无需登录即可显示的网页文本，受登录、验证或访问限制时停止或报告失败；它不是完整的小红书搜索/评论采集服务。GitHub Actions无法在运行时让用户扫码登录，本包不收集Cookie，不绕过限制，也不支持云端登录。之前Windows版的交互扫码功能不适用于GitHub云端。

当前云端采集仅支持config.json内的帖子链接，不运行关键词自动发现，不识别图片视频，不保证全部评论或楼中楼。config.json中的keywords为后续接口接入预留，当前不使用。获得可用的数据服务权限后，可进一步替换采集层以实现搜索及完整分页。

## 部署

1. 在GitHub新建仓库，默认分支main，将此包的全部内容提交到根目录。注意保留隐藏的 `.github/workflows` 文件夹。不要只上传ZIP。
2. Settings → Pages → Build and deployment → Source 选择 GitHub Actions。
3. Actions → 发布反馈分析网站 → Run workflow。成功后在部署任务中打开GitHub返回的网址。
4. Actions → 手动采集小红书公开页面 → Run workflow。任务完成后打开该次运行，下载Artifacts中的firefly-feedback压缩包。
5. 解压下载结果，将feedback.json导入网站，检查report.json的覆盖情况。
6. 在网站中复核日期、升级版本和分类后计数；所有新采集原声均为待复核，不自动纳入统计。

首次Pages部署可能因为设置尚未开启而失败；完成第2步后重新手动运行发布任务即可。Pages权限、Actions配额及私有仓库支持取决于GitHub账户套餐。

## 原声保密

Actions的结果会存放在GitHub的运行产物中7天，不会自动提交到代码仓库或发布到网站。产物访问取决于仓库权限，公开仓库的产物不应视为私密。机密研究请用符合访问要求的私有仓库运行采集；如果账户套餐不支持该私有仓库的Pages，可单独用另一个仓库托管不含原声的页面代码。

网站导入在浏览器中处理，不上传原文；默认刷新后丢失，需导出备份或主动开启浏览器保存。它没有共享数据库。采集后的下载和导入目前仍是人工步骤，网页内不能直接启动Actions，避免在前端保存GitHub访问令牌。

## 采集失败不代表“零反馈”

report.json中的status可能是partial、login_required、body_unavailable、verification_or_access_limited、navigation_or_extraction_failed等。complete始终为false；没有抓到内容时工作流失败并保留报告，不能将空数据当成全平台零反馈。少量结果也只能称为可见样本。默认只处理10篇，每篇最多12轮滚动。

原声日期无法从编辑时间确认时保持空值；相对日期仅推算。网站从10月15日起筛选时会排除空日期，需人工核实。第二条测试帖作者后续称售后判断为摄像头故障，因此不得自动解释成系统升级导致。

Python语法与复用数据处理逻辑检查通过；GitHub部署、云端页面读取及浏览器页面呈现尚未实测。新建仓库并授权后应先测试这两条链接，再决定是否需要授权数据接口。
