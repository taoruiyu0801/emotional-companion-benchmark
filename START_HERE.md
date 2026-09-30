# 数字人综合情感陪伴对话模型：规划阅读入口

这是比赛资料与调查结果仓库，用于让网页端模型审阅并规划后续实现。**目前没有模型权重、训练实现或官方质量 scorer，也没有实测模型成绩。**

## 给 6 Pro 使用

1. 将 [PLANNING_PROMPT.md](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/PLANNING_PROMPT.md) 中分隔线后的正文复制到网页端聊天。正文已包含仓库和原始文本链接。
2. 要求模型实际读取文件后再规划；打不开时应报告具体缺口。若网页端无法读取 GitHub，下载下面三份 TXT 并作为附件上传，再使用上传版提示词。
3. 让模型输出 `PROJECT_PLAN.md`，再交给 Codex 按阶段实施。

| 阅读顺序 | 内容 | 页面 | 纯文本 |
|---|---|---|---|
| 1 | 已有调查报告，属于助手分析，需对照源文件核验 | [报告](PROJECT_INVESTIGATION.md) | [01_investigation.txt](https://raw.githubusercontent.com/taoruiyu0801/emotional-companion-benchmark/main/planning/01_investigation.txt) |
| 2 | 两份 README、完整代码、配置、Schema、3 条测试样例、平台文档正文 | [源码阅读包](planning/02_sources.txt) | [02_sources.txt](https://raw.githubusercontent.com/taoruiyu0801/emotional-companion-benchmark/main/planning/02_sources.txt) |
| 3 | 全量统计、2 条完整原始记录、20 个正常预测点案例、4 个错位点证据 | [数据阅读包](planning/03_data_samples.txt) | [03_data_samples.txt](https://raw.githubusercontent.com/taoruiyu0801/emotional-companion-benchmark/main/planning/03_data_samples.txt) |

## 项目已知情况

- 任务：根据中文对话历史生成回复，同时输出最新用户情绪、用户画像和记忆引用。
- 训练：8,338 段对话、18,657 个标注预测点；验证：900 段对话、2,354 个预测点。
- 运行：`bash /root/participant/start.sh TEST_FILE RESULT_DIR`。
- 固定产物：`submission.jsonl` 和 `performance_report.json`。
- 当前参考提示词要求 `memory_refs=[]`，因为未提供测试记忆库。
- 官方质量评分公式、指标权重和最终提交渠道不在已有资料中。平台演示硬件不是正式硬件承诺。
- 已发现的数据对齐、重复、标签分布、Schema 以及计时问题详见调查报告。

## 原始文件

原始 [README.md](README.md)、[participant](participant)、[完整训练与验证数据](训练-验证-数据集)、[测试样例](test_inference_data.jsonl)、平台 DOCX 和原始中文调查报告都已保留。原始文件的字节数与 SHA-256 见 [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)。

完整训练文件约 69.6 MB、验证文件约 6.1 MB；若 GitHub 网页不显示完整大文件，可从仓库下载后读取。首次做技术规划通常先读上面的文本阅读包；定向案例不代表总体分布，不应用来报告模型成绩。

## 本次公开范围

按资料提供者要求，此公共仓库包含完整原始目录，包括完整训练集、验证集和平台文档。新增的调查报告、上传阅读包和提示词是辅助材料，不是主办方新增规则。未补写原始资料没有提供的模型/数据许可证。

此仓库仅准备资料与规划入口，不表示已完成训练、参赛模型提交或质量评测。
