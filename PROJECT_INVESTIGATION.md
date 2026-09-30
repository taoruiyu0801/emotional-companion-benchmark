# 数字人综合情感陪伴对话模型：任务调查报告

调查日期：2026-09-25。调查范围：本文件夹全部原始资料，包括两个 README、全部脚本与配置、训练/验证数据及 Schema、测试样例，以及平台 DOCX 的正文和 9 张截图。

本文区分三种结论：**已确认**表示直接来自本地资料或全量统计；**建议**表示据此提出的实施方案；**待确认**表示资料不足，不能当作正式比赛规则。此次没有训练模型、下载模型或测得模型成绩，原始数据和参赛脚本未修改。

## 1. 先回答最关心的几个问题

| 问题 | 调查结论 |
|---|---|
| 这是做什么的任务？ | 给定一段中文多轮对话历史，预测下一轮助手回复，同时识别最新用户消息的情绪、提取用户画像，输出规定的 JSON。 |
| benchmark 是什么？ | 本地材料体现的是**比赛自定义的对话生成＋结构化标签预测＋推理耗时评测**。没有独立的官方质量评分器、总分公式、指标权重或已发布基线成绩。不能把它等同于某个已有通用榜单。 |
| 应该跑分优先，还是做完整产品？ | **建议按比赛评测优先组织工作，同时优化回复本身的体验。**主办方明确通过批量命令行入口运行；现有材料没有要求网页聊天、数字人形象、语音、动画等产品功能。 |
| 聊天可以直接命令行吗？ | 可以作为开发和展示方案。正式入口本身是“读 JSONL、批量写结果”，并不是交互聊天；如需人工试聊，再增加一个很薄的命令行聊天工具即可。 |
| 只是训练出一个强大的 `.pt` 吗？ | **应交付可离线运行的模型与推理包。**参考加载方式需要模型配置、tokenizer、权重等组成的模型目录；一个任意命名的 `.pt` 权重文件通常不能直接满足接口。 |
| 一定需要从零训练吗？ | 材料没有要求从零预训练。建议先建立已有模型基线，再决定是否进行监督微调、参数高效微调以及推理优化。模型体积更大也不等于本任务更优。 |
| 现在有哪些东西能直接用？ | 数据、标签规范、统一启动入口、两种推理后端、输出清洗与计时工具。**没有模型权重、训练流程、数据转换器和质量评分器。** |

主要依据：[推理工具说明](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/README.md#L80)、[任务提示词](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/run_inference.py#L35)、[模型加载代码](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/run_inference.py#L345)。

## 2. Benchmark：可以确认到什么程度

### 2.1 输入、预测任务与输出

测试样例的每行包含 `id`、`conversation_id`、`target_user_turn_id`、`history`。`history` 是截止目标用户消息的历史，每条消息带 `turn_id`、`role`、`content`。

实际推理脚本的最低读取要求是字符串 `id` 和数组 `history`；随后检查历史消息的角色及内容。它没有用 `conversation_id` 建立持久会话，也没有依靠 `target_user_turn_id` 自动截断测试历史，传入的 `history` 必须预先正确准备。

模型生成四个字段，脚本额外加上输入的 `id`：

| 字段 | 任务类型 | 当前要求 |
|---|---|---|
| `response_text` | 中文条件文本生成 | 自然、贴合上下文和用户偏好。提示词要求非空。 |
| `emotion_label` | 16 类单标签分类 | 判断**最新用户消息**的情绪，不是助手语气，也不是整段对话的平均情绪。 |
| `user_profile.personality_traits` | 多标签分类/提取 | 从 10 个性格标签中选择，可为空。 |
| `user_profile.interests` | 多标签分类/提取 | 从 12 个兴趣标签中选择，可为空。 |
| `user_profile.style` | 多标签分类/提取 | 从 11 个风格标签中选择，可为空。 |
| `memory_refs` | 记忆引用接口 | 当前参考提示词明确要求 `[]`，理由是测试集没有公开 memory bank。 |

因此，本任务不只考“聊得像不像人”。它同时要求回复得体、分类准确、画像有依据、结构正确，并在约束环境下及时完成推理。各项是否以及如何折算总分，仍须以未提供的评分细则为准。

### 2.2 正式入口与固定产物

主办方说明的唯一运行命令是：

```bash
bash /root/participant/start.sh TEST_FILE RESULT_DIR
```

这里的 `/root/participant` 是比赛 Linux 容器路径，不是本机 Windows 路径。命令必须接受测试文件和结果目录两个位置参数，完成全部样本，输出：

```text
RESULT_DIR/
├── submission.jsonl          # 每条测试记录的预测结果
└── performance_report.json  # 本轮推理耗时及运行摘要
```

结果目录可预先存在；参考实现覆盖这两个同名文件，不清理其他文件。没有人工聊天步骤，也没有要求评委打开网页。

### 2.3 当前计时的精确含义

依据 [推理主循环与报告](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/run_inference.py#L411)：

| 项目 | 实际行为 |
|---|---|
| 样本遍历 | 对文件内全部样本逐条、串行推理。 |
| 计时样本 | 记录文件前 `performance_rounds` 条；当前配置为 **100**，README 也明确写前 100 条。不是同一问题重复跑 100 次。 |
| Transformers 计时 | 包括 tokenization、输入张量送入设备、生成、解码、JSON 解析与字段清洗、结束时 CUDA 同步；模型加载不计入。 |
| API 计时 | 包括 HTTP 请求、服务端推理、响应解码、JSON 解析与字段清洗；服务启动不计入。 |
| 共同不计入的部分 | 测试文件读取、对话文本拼装、结果落盘、报告写入与文件哈希等；Transformers 的 chat template 文本渲染也发生在计时前。 |
| 预热 | 脚本没有单独的预热样本或丢弃第一条计时逻辑。 |
| 报告内容 | 平均、中位、P95、最小、最大耗时，逐条耗时列表，硬件标签，输入/输出 SHA-256，样本数，JSON 解析失败数量和 ID。 |
| 没有记录 | 正式质量分、首 token 延迟、tokens/s、峰值显存、并发吞吐。 |

报告中的 `complete` 只检查是否收集够规定的计时条数，不等于“所有预测字段正确”或“质量达标”。用附带的 3 条样例成功运行时，默认会得到 `rounds=3`、`required_rounds=100`、`complete=false`；这是样例不足 100 条造成的，不能据此认定脚本失败。

由于实际只做单请求串行推理，优化时要看这一调用模式下的延迟，不能只拿高并发吞吐成绩替代。正式评测应保留要求的计时口径，不能靠缩短计时样本数制造成绩。

### 2.4 目前没有的评分信息

本目录没有给出以下内容：

- 回复使用参考答案相似度、规则、人工评审还是模型裁判评分，以及裁判提示词。
- 情绪使用 accuracy、macro-F1 还是其他指标。
- 画像按标签 F1、集合完全匹配还是其他规则评分；正确空集合如何计分。
- 记忆字段在本轮是否免评、占多少分，是否会另行提供记忆库。
- 质量与速度的权重、延迟门槛、超时/失败的总分处罚、正式硬件限制。
- 可否使用外部数据、蒸馏、集成、检索、量化，能修改参赛脚本的哪些部分。

`participant/README.md` 提到缺失或不合规字段置空且该项不获得命中分，但这不是完整评分公式。**`performance_report.json` 是耗时报告，不是综合 benchmark 成绩单；脚本打印 `PASS` 也不代表模型质量通过。**

## 3. 数据集：类型、规模与训练方式

### 3.1 全量统计

以下数字来自对两个 JSONL 文件逐行解析和全部预测点遍历；不是抽样估计。这里的“消息数”把一次 user 或 assistant 发言各算一条，避免与一问一答的“轮”混淆。

| 指标 | 训练集 | 验证集 |
|---|---:|---:|
| 文件字节数 | 69,575,005 | 6,078,596 |
| 对话数，即 JSONL 记录数 | 8,338 | 900 |
| 消息总数 | 117,902 | 11,732 |
| 用户消息数 | 58,951 | 5,866 |
| **有完整标签的预测点数** | **18,657** | **2,354** |
| 每段对话消息数：中位数 / 最大值 | 12 / 50 | 10 / 50 |
| 每个预测点历史消息数：中位数 / P95 / 最大值 | 9 / 27 / 49 | 7 / 25 / 49 |
| 历史内容字符数：中位数 / P95 / 最大值 | 803 / 4,500 / 40,003 | 740 / 3,058 / 14,092 |
| 参考回复字符数：中位数 / P95 / 最大值 | 129 / 806 / 1,809 | 98.5 / 510 / 1,754 |
| 没有预测点的对话数 | 5 | 0 |

历史字符数为历史各消息 `content` 的 Python `len()` 之和，不包含系统提示、角色前缀、样本 ID 或 chat template，**不是 tokenizer token 数**。实际训练和部署需要用选定模型的 tokenizer 重算长度，不能直接把 40,003 字符当作 40,003 tokens。

另有 `test_inference_data.jsonl`：只有 **3 个无答案预测样例，来自 2 段对话**，用途是检查推理链路能否运行；它不是足够规模的质量验证集，也不是完整的正式测试集。

### 3.2 数据类型与结构

这是一套以中文文本为内容的、多轮情感陪伴对话监督数据。公开字段没有图片、音频、视频、数字人动作，也没有偏好对、奖励分数或 DPO 所需的 chosen/rejected 对。

每行训练/验证记录有三个顶层字段：

```text
conversation_id
turns[]
  └─ turn_id、role、content
prediction_points[]
  ├─ target_user_turn_id
  ├─ assistant_response_turn_id
  └─ target
       ├─ response_text
       ├─ emotion_label
       ├─ user_profile {personality_traits, interests, style}
       └─ memory_refs
```

对话抽读可见求职、学业、关系、兴趣、压力与陪伴等场景。数据的原始来源、是否合成、标注人员和标注一致性没有说明，不应根据文风自行认定来源。

### 3.3 不能直接把原始 train/val 文件交给推理脚本

原始 train/val 是“完整对话＋多个预测点”，而推理器要求“`id`＋截断后的 `history`”。直接运行会因缺少测试输入字段而失败。需要先做数据转换。

正常预测点的转换关系为：

```text
对话 turns + 一个 prediction_point
    ↓ 检查用户/助手轮次、角色和答案对应关系
输入：只取 turn_id <= target_user_turn_id 的历史
输出：该 prediction_point 的 target JSON
```

例：目标用户轮次为 9、助手回复轮次为 10，则只输入 1～9 的消息；第 10 条以及后面的所有消息都不能进入该样本输入。

建议转换时：

1. 保留原始对话 ID、目标轮次和来源行号，方便追溯、去重及按对话分组。
2. 推理输入与参考答案分开保存，验证时推理程序只读输入。
3. 为本地验证生成唯一 ID 并保留映射；真实测试输出始终原样保留输入 ID。
4. 训练输出只包含模型负责生成的四个字段；`id` 由推理包装器添加。
5. 输入组织与推理器保持一致：当前实现是 system prompt，加上一个包含 `user:`/`assistant:` 文本历史的 user message，并非原样把所有历史作为 API 多轮 messages 传入。
6. 当前无记忆库版本可在**派生训练目标**中将 `memory_refs` 统一为 `[]`，保留原始文件；不要训练模型猜不具备可用映射的记忆 ID。

同一对话的不同预测点共享大量历史。若另划内部开发集，必须按对话分组，并处理完全重复对话，不能把展开后的样本随意随机切分。

58,951 条训练用户消息不等于 58,951 条完整多任务标签。没有 `prediction_point` 的普通助手回复最多用于额外的回复生成训练，不能凭空补出情绪和画像真值。

### 3.4 情绪类别明显不均衡

| 情绪标签 | 训练预测点数 | 验证预测点数 |
|---|---:|---:|
| anxiety | 6,340 | 751 |
| relaxed | 2,819 | 409 |
| helplessness | 1,575 | 142 |
| fear | 1,388 | 124 |
| sadness | 1,085 | 131 |
| mixed | 945 | 177 |
| loneliness | 876 | 115 |
| anger | 855 | 115 |
| shame | 752 | 118 |
| gratitude | 695 | 118 |
| neutral | 654 | 53 |
| pride | 234 | 40 |
| joy | 171 | 20 |
| disgust | 125 | 21 |
| care | 79 | 11 |
| surprise | 64 | 9 |

例如训练中 `anxiety` 占 33.98%，验证中占 31.90%；只报 accuracy 容易掩盖小类别表现。建议本地同时记录 macro-F1、逐类召回和混淆矩阵，特别检查 `anxiety/fear/helplessness`、`relaxed/gratitude/mixed` 等容易混淆的情况。这些是建议的诊断指标，不是已经证实的官方计分指标。

### 3.5 用户画像是稀疏标签，不应逢句就推断人格

| 画像子项为空的比例 | 训练 | 验证 |
|---|---:|---:|
| personality_traits | 56.24% | 61.85% |
| interests | 69.24% | 74.89% |
| style | 46.80% | 51.74% |
| 三项同时为空 | 36.63% | 37.17% |

画像标签空间为：

- 性格：`extroverted, introverted, open, conservative, high_conscientiousness, casual, agreeable, assertive, emotionally_stable, sensitive`。
- 兴趣：`study_exam, programming_technology, reading_writing, film_animation, music, games, sports_fitness, travel_outdoor, pets, social, career_development, art_design`。
- 风格：`brief, detailed, colloquial, formal, direct, indirect, humorous, rational, high_emotional_expression, low_emotional_expression, emoji_user`。

训练中 `low_emotional_expression` 仅出现 3 次，`emoji_user` 出现 27 次，两者在验证标签中均未出现；因此公开验证集也不能完整证明每个稀有标签的能力。建议按标签、子项分别分析误报和漏报，并对无证据时的空集合保持保守。最新一句有焦虑不等于人格一定 `sensitive`；提到一项活动也不自动代表稳定兴趣。

### 3.6 记忆字段的实际边界

训练和验证确实含有 `mem_XXXXXX` 引用：训练有 38,417 次引用、26,883 个不同 ID；验证有 4,789 次引用、3,301 个不同 ID。训练 437 个预测点、验证 41 个预测点的记忆列表为空。

但是文件夹没有 ID 对应的记忆内容库，测试样例也没有候选记忆。因此，不能据此直接实施“从记忆库检索正确 ID”的训练或评测。

当前提示词要求空数组，但 `normalize_prediction()` 只是校验 ID 格式，不会强制把合法非空列表清空。也就是说，**这是提示词约定，不是程序层面的强制保证**。后续应让训练目标和输出策略一致，并向主办方确认记忆计分安排。对话上下文里的信息仍然要记住和使用；空记忆引用不意味着可以忽略历史。

## 4. 已发现的数据与工具问题

### 4.1 四个预测点存在回复轮次错位，必须先隔离

全量检查发现以下训练预测点把目标助手回复指向了最新用户消息**之前**：

| 原始 JSONL 行号 | conversation_id | target_user_turn_id | assistant_response_turn_id |
|---:|---|---:|---:|
| 628 | train_conv_000628 | 15 | 14 |
| 817 | train_conv_000817 | 33 | 32 |
| 3,644 | train_conv_003644 | 7 | 6 |
| 3,695 | train_conv_003695 | 9 | 8 |

位置：[628 行](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/train/train_public.jsonl#L628)、[817 行](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/train/train_public.jsonl#L817)、[3644 行](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/train/train_public.jsonl#L3644)、[3695 行](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/train/train_public.jsonl#L3695)。

这些 `target.response_text` 均确实等于所指向的旧助手消息。如果机械截取到目标用户轮次，答案已经在输入里，造成答案泄漏和错误的续写目标。**建议先剔除这 4 个预测点，保留对应对话的其他正常预测点；人工复核后再决定是否修复。**不能只改一个 turn ID，因为回复、情绪和画像可能需要一起重新对应。

### 4.2 重复、空记录与跨集重合

按完整消息的 `(role, content)` 序列比较，忽略对话 ID：

- 训练集存在 **202 条超出首次出现的重复对话记录**；这是重复记录数，不是重复组数。
- 展开预测点后，训练存在 **508 条超出首次出现的重复历史**；按“历史＋完整原始 target”比较，也有 508 条重复。
- 验证集没有上述精确重复；训练和验证之间没有完全相同的对话或预测历史。
- 训练/验证有 18 个完全相同的回复文本值；仅回复相同不能证明跨集泄漏，尤其是通用短回复。
- 训练第 77、284、325、691、767 行没有预测点，展开多任务训练时自然产生 0 个样本。

建议先在派生数据中处理重复，并记录保留策略，不直接覆盖原始数据。这次只检查精确重复，**没有完成语义近重复检测**，不能据此宣称彻底排除了数据污染。

两个数据文件全部记录通过各自 JSON Schema 校验；所有引用轮次都存在，角色匹配，参考文本与其引用的助手消息一致，消息轮次连续且 user/assistant 交替。上述四个错位问题说明：Schema 合法不等于语义对齐正确。

### 4.3 样例 ID 与提交 Schema 冲突

[提交 Schema](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/templates/submission_schema.json#L7) 要求：

```text
^test_[0-9]{6}_t[0-9]+$
```

但是三个测试样例 ID 分别是 `test1_000001_t5`、`test1_000001_t7`、`test1_000002_t5`。用原样 ID 构造其他字段合规的提交记录后，三条都会被这个 Schema 的 ID 正则拒绝。

实际推理器不调用这个 Schema，只检查输入 ID 是字符串且不重复，并在输出中原样保留。因此样例可以经过程序，但未必通过外部严格校验。建议向主办方确认正式 ID 规范；**不要为了匹配模板自行改写真实测试 ID**，否则可能无法与参考答案对齐。

### 4.4 解析成功不代表字段合格

`parse_failure_count` 只统计“没有解析出 JSON object”，不统计 object 内部的字段错误。已用纯函数检查确认：合法 JSON 即使 `emotion_label` 不在枚举中，`parse_failed` 仍为 false，情绪被清成空字符串；画像数组只要含一个非法标签或重复项，该子项整个置空，不是只删除坏标签。

因此后续本地评估应额外统计：回复为空率、情绪非法/为空率、画像原始字段错误率、输出截断率，而不能只盯 `parse_failure_count=0`。画像的合法空数组本身并不等于失败，应结合原始字段和参考标签判断。

JSON 格式出错有恢复逻辑，但模型加载错误、API 请求失败、OOM 等异常没有同样的逐条容错保证，可能直接终止整批任务。

### 4.5 环境与实现上的注意事项

- `start.sh` 在开头固定执行 `source activate conda_env`；纯 Windows PowerShell 不能按比赛命令直接运行，正式验收应在对应 Linux/conda 环境进行。
- vLLM 启动参数当前写死 `--tensor-parallel-size 2`；单卡环境需调整，不能假定一份脚本无论硬件如何都能启动。
- `requirements.txt` 只有 `torch>=2.1`、`transformers>=4.40`、`accelerate>=0.29`，没有列 vLLM，也没有训练相关依赖。vLLM 模式依赖镜像已有环境或另行准备。
- Python 代码会导入 `AutoModelForImageTextToText` 及相关映射。依赖文件给出的宽泛下限不保证任意允许安装的版本都兼容，部署前要验证并固定实际可运行版本。
- `hardware_label` 还是 `fill-in-before-official-run`。通过现有 `start.sh` 的环境变量默认表达式，也不能保证它会自动变成真实硬件说明，正式运行前应显式填写。
- 输入没有显式 token 长度检查或截断策略，长尾历史可能触发上下文超限或显存不足。
- 当前贪心生成：`do_sample=false`；API 后端因此把 temperature 设为 0。配置中的 `temperature=1.0` 不代表当前在随机采样。
- 情绪枚举来自 Python set，拼接提示词时未排序；跨进程可能顺序不同。画像枚举已经排序。若规则允许修改，稳定情绪枚举顺序有利于复现。

## 5. 文件和脚本分别负责什么

| 文件 | 内容与职责 | 不负责什么 |
|---|---|---|
| [根 README](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/README.md) | 资料总览、平台准备、模型放置和示例运行命令。 | 没有训练教程与评分公式。 |
| [participant/README.md](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/README.md) | 后端选择、环境变量、唯一运行接口、固定产物、计时和失败处理。 | 没有质量评测实现。 |
| [start.sh](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/start.sh) | 激活环境、验证参数、选择后端；Transformers 模式直接运行 Python；API 模式启动本地 vLLM、等待健康检查、运行推理、退出时停止服务。 | 不训练、不下载模型；选 API 后端时并非仅连接任意已有服务。 |
| [run_inference.py](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/run_inference.py) | 加载模型或调用接口；构造提示；逐条生成；解析与清洗；计时；写提交和报告。 | 不读取 train/val 的参考标签评分，不执行反向传播、不更新权重。 |
| [inference_config.json](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/configs/inference_config.json) | 默认使用 Transformers、`./model`、自动设备/精度、最多 1,200 个新 tokens、100 条计时；也包含 API 配置。 | 不是训练超参数配置；1,200 是生成上限，不是目标回复长度。 |
| [requirements.txt](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/requirements.txt) | 基础推理依赖。 | 不构成完整的训练或 vLLM 环境锁定文件。 |
| [submission_template.json](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/templates/submission_template.json) | 一条输出样板。 | 不是测试集或标准答案。 |
| [submission_schema.json](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/participant/templates/submission_schema.json) | 输出字段、枚举、数组唯一性与 ID 规范。 | Python 推理流程并未实际调用它。 |
| [train_public.jsonl](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/train/train_public.jsonl) / [train Schema](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/train/train_public.schema.json) | 完整训练对话与标注预测点、格式定义。 | 不是已整理好的逐样本训练输入。 |
| [val_public.jsonl](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/val/val_public.jsonl) / [val Schema](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E8%AE%AD%E7%BB%83-%E9%AA%8C%E8%AF%81-%E6%95%B0%E6%8D%AE%E9%9B%86/val/val_public.schema.json) | 有答案的验证对话与预测点。 | 不含官方评价函数。 |
| [test_inference_data.jsonl](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/test_inference_data.jsonl) | 3 条无答案的运行样例。 | 不能给出可靠综合跑分。 |
| [咪咕仝学平台实例创建demo V1.docx](https://github.com/taoruiyu0801/emotional-companion-benchmark/blob/main/%E5%92%AA%E5%92%95%E4%BB%9D%E5%AD%A6%E5%B9%B3%E5%8F%B0%E5%AE%9E%E4%BE%8B%E5%88%9B%E5%BB%BAdemo%20V1.docx) | 创建算力实例、选择 vLLM 公有镜像、进入容器、上传模型和脚本、运行并得到结果的操作图示。 | 不是完整比赛章程；没有评分权重。 |

`run_inference.py` 内部可按以下阶段理解：

1. `read_jsonl / validate_test_file / load_config`：读输入、检查参数和后端配置，应用环境变量覆盖。
2. `conversation_text / SYSTEM_PROMPT`：将整个可见历史变成文本，加入固定任务指令和标签枚举。
3. Transformers 分支：从本地配置选择加载器，加载 tokenizer/权重，使用 chat template 和 `generate()`。
4. `request_chat_completion`：用 Python 标准库发送 OpenAI 兼容 HTTP 请求；不是必须调用云端 OpenAI 服务。
5. `extract_object / recover_response_text / normalize_prediction`：去思考标签、尝试提取 JSON、失败时保留可恢复的回复、清洗字段。
6. 主循环：每条生成一次，收集指定前缀样本耗时，输出结果与 SHA-256 摘要。

若要使用已经启动的兼容服务，应按 README 示例直接运行 Python 推理器并设置 API 配置。统一 `start.sh` 的 API 分支会自行启动 vLLM，并设置客户端地址和模型名。

平台 DOCX 截图展示过 RTX 4090 24G×2 实例及 vLLM 镜像，另一张实例列表也出现 4 卡实例。**这些是操作示例，不能据此断言正式比赛必定使用双卡 4090。**正式 GPU、显存和资源上限仍需确认。

## 6. 建议的 scope 与最终交付

### 6.1 当前应纳入工作范围

| 范围 | 优先程度 | 交付目标 |
|---|---|---|
| 复现固定推理入口 | 必须 | 给定测试文件能完整、离线、稳定产出两个结果文件。 |
| 数据转换与质量检查 | 必须 | 无答案泄漏、无轮次错位、可追溯的训练/验证样本。 |
| 本地质量评估 | 必须 | 能比较候选模型和优化前后的实际变化。 |
| 中文情感陪伴回复、情绪、画像 | 核心优化 | 同时提升文本质量和结构化标签能力。 |
| 延迟、显存、输出可靠性 | 核心优化 | 在正式资源限制内运行，并控制延迟与失败率。 |
| 模型微调 | 由基线决定，建议重点验证 | 用此任务数据改善领域与标签适配，验证收益后采用。 |
| 命令行交互聊天 | 可选且成本低 | 人工抽查体验，查看回复与标签。 |
| 网页/App、语音、数字人渲染 | 当前低优先 | 本地资料没有对应评测和交付要求，除非后续章程另有规定。 |

“体验”在本任务中主要体现为回复行为：记住历史事实、听从“简短一点”“先听我说”“给我具体步骤”等要求，识别情绪变化，避免重复说教或用户已结束时继续追问。这些是文本模型自身要改善的能力，与是否制作漂亮界面是不同层面的工作。

### 6.2 最终产物应如何理解

部署包建议沿用现有结构，其中 `model/` 目前不存在，需要后续补齐：

```text
/root/participant/
├── start.sh
├── run_inference.py
├── configs/inference_config.json
├── requirements.txt
└── model/
    ├── config.json
    ├── tokenizer_config.json
    ├── tokenizer 文件 / chat template 等模型所需资源
    ├── 模型权重：例如 model.safetensors 或分片及其索引
    └── generation_config.json 等按模型需要提供的文件
```

这里是目录组织示意，不是要求每个模型都有完全相同的文件名。标准是选定后端能够从本地完整加载，并执行正确的模板和生成逻辑。

如果使用 LoRA/QLoRA，训练阶段可以保存 adapter，但部署时还必须有完整、可验证的基座与 adapter 加载方案，或导出合并后的完整模型。参考脚本没有显式的 PEFT 装载/合并流程；不能只交一个 adapter 文件就假定现有两种后端都会正常加载。

除部署包外，建议保留训练代码、参数、数据处理记录、验证结果、运行环境版本与模型来源，便于复现和迭代。正式是否要求提交这些附加文件，现有资料未说明。

## 7. 接下来具体优化什么

### 阶段 A：先建立可信基线

1. 获取正式评分规则和硬件约束；同时完成不依赖这些答案的数据准备。
2. 新增数据转换工具，按预测点构造训练样本及验证输入/答案，隔离 4 个错位点，处理重复并保留审计记录。
3. 用能够在目标环境运行的已有中文指令模型，先跑通 3 条样例，再运行展开后的 2,354 条验证样本。
4. 保存原始模型输出、清洗后输出、配置、模型版本、质量指标和耗时。调试产物应与正式固定产物区分保存。

这一阶段的价值是确认主要瓶颈究竟在回复、情绪、画像、格式，还是硬件与推理速度，而不是先默认必须大规模训练。

### 阶段 B：补上本地质量评估

没有官方 scorer 时，先建立诊断指标，**不要把它们命名为官方总分**：

| 维度 | 建议本地记录 | 用途 |
|---|---|---|
| 情绪 | accuracy、macro-F1、每类 F1/召回、混淆矩阵 | 看主流类与稀有类，定位情绪混淆。 |
| 画像 | 三个子项分别计算 micro/macro-F1、precision/recall、集合完全匹配；单列空集合样本 | 看过度推断和漏报，避免只靠大量空标签得到表面好成绩。 |
| 回复 | 固定样本人工盲评：情境贴合、用户要求、情绪回应、前后一致、冗余程度 | 开放式回复往往有多个好答案，不能只用全文完全匹配衡量。 |
| 格式 | JSON 可解析率、各字段原始合规率、回复非空率、截断率 | 区分格式问题与模型能力问题。 |
| 性能 | 按现有口径的前 100 条平均/P95 延迟；另记录完整验证集运行耗时与显存 | 与正式入口行为对应，帮助选择可部署方案。 |

若以后拿到官方 evaluator，应优先复现官方指标；本地诊断指标用于解释变化，而不是擅自替代比赛规则。

### 阶段 C：微调，让模型学会任务输出和判断边界

建议首先验证联合监督微调：

```text
输入：任务提示词 + 截止当前用户的对话历史
训练目标：回复 + 单个情绪标签 + 三组画像标签 + 空记忆引用
```

可先尝试参数高效微调，而不从零训练；是否采用、模型大小和训练资源都由基线结果与硬件预算决定。建议只对目标 assistant 输出计算监督损失，并保持训练与推理的序列组织一致。

优先关注：

- 情绪：判断当前用户的变化，不被历史长期情绪带偏。
- 画像：有证据才输出；对显式风格要求和历史稳定偏好保持敏感。
- 回复：区分用户需要倾听、具体帮助、轻松聊天还是结束对话；按要求控制长度。
- 标签：学习英文枚举及 JSON 格式，减少正文生成很好、结构化字段却失分的情况。
- 数据：稀有类别采样或损失加权必须通过验证比较，不能假定过采样一定改善总表现。

初版建议一次生成完整 JSON，以匹配现有接口并控制延迟。是否拆分为多个分类器、加入检索或使用多次模型调用，应在规则允许且收益足以抵消成本时再评估。

### 阶段 D：在质量可接受后优化推理

- 测量实际输入/输出 token 长度，再设置上下文与生成上限。不能为了加速把长样本静默截断或将 JSON 截坏。
- 比较同一模型在 Transformers 与本地 vLLM 下的实际串行延迟，不能预设某后端必然更快。
- 按真实 GPU 数、显存和上下文需求配置张量并行、精度与量化；量化后重新检查质量。
- 若服务支持且规则允许，验证 JSON/Schema 约束输出是否减少字段错误，并检查其延迟影响。
- 如采用有思考模式的模型，明确思考输出策略；客户端去掉 `<think>` 不会退回已经花费的生成时间。
- 固定 prompt、依赖和生成参数，保存每次实验的可复现记录；一次只改变有明确目的的因素。

### 阶段 E：按比赛入口验收

最终检查应覆盖：模型离线加载、固定路径与环境名称、完整样本输出、ID 一一对应、字段合规、无 OOM/超时、报告计时条数正确、硬件描述真实、服务正常退出。对 API/加载失败另做清晰日志记录，不要把失败结果当有效成绩。

可新增的工具建议如下；**这些脚本目前均不存在，本次调查也没有实现它们**：

| 建议文件 | 职责 |
|---|---|
| `prepare_data.py` | 转换、对齐检查、去重、长度统计和溯源。 |
| `evaluate_local.py` | 比较预测与答案，报告分类、画像、格式与回复检查结果。 |
| `train_sft.py` | 执行任务监督微调并保存实验配置。 |
| `export_model.py` | 按实际训练方案导出可部署模型，必要时合并 adapter。 |
| `chat_cli.py` | 可选的人工交互试聊，复用正式提示与输出解析。 |

## 8. 启动训练前需要补齐的外部信息

| 优先级 | 需要确认的问题 | 影响 |
|---|---|---|
| 最高 | 正式质量指标、权重、延迟折算规则与 scorer 是否提供 | 决定模型与速度的取舍。 |
| 最高 | 正式 GPU 数量、型号、显存、上下文/运行时限 | 决定候选模型、精度与并行配置。 |
| 最高 | `memory_refs` 是否免评或另发记忆库 | 决定空列表策略是否为正式约定。 |
| 高 | 正式测试 ID 规范，样例与 Schema 冲突如何处理 | 避免提交因格式或对齐失败。 |
| 高 | 允许修改哪些脚本部分，计时逻辑能否改动 | 明确提示、后处理、批处理与推理引擎的优化范围。 |
| 高 | 模型、外部数据、蒸馏、联网与许可限制 | 决定训练数据和模型来源；API 接口支持不等于允许云端模型。 |
| 中 | 最终提交模型目录、环境镜像还是结果文件，是否要求演示/答辩 | 确定工程打包和展示投入。 |

在这些答案到来之前，数据清理、无泄漏转换、本地诊断评估和现有模型基线仍然可以先做。

## 9. 调查核验记录

本次已执行：完整目录检查；两份 README 和全部源代码/配置阅读；两个数据集全部 JSON 解析及 JSON Schema 校验；预测轮次/角色/文本对应检查；标签与长度统计；精确重复和跨集精确重合检查；三个测试样例的 ID/Schema 一致性检查；输出解析与非法字段清洗的纯函数检查；平台 DOCX 正文及全部 9 张截图阅读。

数据文件 SHA-256：

```text
train_public.jsonl
184a47471f8d6f70fa21b9265b0a4d4e51c3748ba25af39a801884a2da35341a

val_public.jsonl
097c0639ef7370a18a54670ec3c8390ce5dc87c1ed95f436cef07b68dfed7668
```

此次未测得真实模型的回复质量、准确率或 GPU 延迟，因为目录没有模型；也未完成近重复语义排查或全部样本的人工标注复审。建议据本文先补齐“数据转换＋本地评估＋可运行基线”，再决定微调与部署优化方案。
