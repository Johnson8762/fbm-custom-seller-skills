# Etsy 图片规则（平台 + 本技能附加规则）

## 平台（Etsy 官方）
- **至少 1 张未修图实拍**：Listing Image Requirements（https://www.etsy.com/legal/policy/listing-image-requirements/253962679005 ，页面写 Last updated on Oct 22, 2026）原文 "Unedited Photo: For most products, you must include at least one unedited photo of the actual item against a real background." 不补可能被下架；屡次违规处罚升级。
- **个性化商品首图**：Creativity Standards（https://www.etsy.com/legal/creativity ）要求首图是 "a finished, customized item rather than the blank product or placeholder text"。
- **首图**：横图或方图；最短边至少 635 px，建议 ≥2000 px（https://help.etsy.com/hc/en-us/articles/115015628707 ：低于建议值只是提示，可以继续发布）。**官方没有"推荐 4:3"**，不要写。
- **数量**：单个 listing 最多 20 张图、2 个视频（3–15 秒、≤100 MB、上传后静音）。
- **Alt text**：每张都写，≤250 字符；终图出来后对着实际画面写，不提前写。
- **AI**：效果图可以用，描述里必须写明哪些是数字/AI 效果图；若使用了 AI 生成图，按后台实际选项勾选，并在描述里披露。
- 生产合作方/发货地：如实披露；文案不写发货地，运费模板如实填写。

## 本技能附加规则
1. AI 效果图可以展示成品效果，但每条 listing 至少 1 张未修图实拍，描述注明 AI 图。
2. **03 号位留空**给使用者上传未修图实拍，不传占位图。
3. 人物形象抱枕的生活场景图里，**抱抱枕的人要和抱枕上印的是同一个人**。不要使用使用者未同意公开的客户照片；已同意上架的产品照不要擅自打码。
4. 不做 3D Hug / 张开双臂拥抱造型，图、文案、tags 都不出现。
5. 纪念款风格克制，不要流程图、纯文字图、示意简图。
6. 没有实拍的款不出"成品图"冒充实物；只有一两张工厂照也能做整套：原图只裁剪留作实拍，其余抠图校色后入场景或做图文图。
7. 主图不放字、≥2000 px；备用主图与主图同一主体；AI 出图强制写防白边（无白边款）、不出无关人脸。
8. 交付格式：先总目录 → 每张图的来源（用了哪张实拍、改了什么、有没有用 AI）→ 一张图一个 alt 复制框。
9. 汇率用 `etsy-listing-writer/data/etsy_fees.json` 里的示例规划汇率，并注明来源；不编数据。

## 逐图验收（2026-11-08 增补，借鉴 etsy-tony-full-photo-15）
- 每张图必须有**独立用途**（job），且相对前面的图**提供新信息**；重复信息的图删掉。
- 方案里声称的差异必须**画面里看得出来**：镜像（不能用对称人物，否则看不出是镜像，只靠标签不算）、尺寸差（10–70 cm 要拉开对比，不能三个差不多大）、白边宽度（与实物一致，不能画得比实物宽）。
- 工艺一致：轮廓、白边、印刷面、变形按 manufacturing-checklist.md，不画实物做不到的效果。
- 手机端：缩到 340 px 仍能看清卖点；主图在搜索小图里认得出产品；美国站用 inch/lb（可附 cm）。
- 不通过的图：重做或删掉，并在方案里记录重做次数与原因。
