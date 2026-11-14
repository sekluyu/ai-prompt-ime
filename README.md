# AI 绘画提示词输入法

输入中文拼音，选出英文提示词，直接填进 ComfyUI、Stable Diffusion WebUI 或其他绘图软件。基于 Windows 小狼毫（Rime），词库离线运行，不需要 API Key，也不用开翻译网页。

**当前版本：[v0.2.12](https://github.com/sekluyu/ai-prompt-ime/releases/tag/v0.2.12)** · 收录 **279,161 条拼音映射**。一个英文词可以有多个中文入口，这个数字不是独立词汇数量，也不代表所有常用词都已覆盖。

## 下载和安装

先安装[小狼毫输入法](https://github.com/rime/weasel/releases)，再选择下面任意一种安装包：

| 下载 | 说明 |
|---|---|
| [独立安装器](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.12/ai-prompt-ime-0.2.12-setup.exe) | 下载后直接运行，不需要 Python、Go 或 .NET |
| [ZIP 安装包](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.12/ai-prompt-ime-0.2.12.zip) | 包含相同安装器、词库和使用说明 |
| [校验文件](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.12/SHA256SUMS.txt) | 用于核对下载文件的 SHA-256 |

1. 运行安装器。安装前会备份需要替换的文件，不创建桌面快捷方式。
2. 右键小狼毫托盘图标，点击“重新部署”。
3. 按 F4 或 Ctrl＋反引号，切换到“绘画提示词”。
4. 输入 `danren`，按空格即可得到 `solo, `。

默认安装到 `%APPDATA%\Rime`。更换目录、手动安装和回滚方法见[安装与回滚](docs/安装与回滚.md)。

## 怎么输入

| 想输入的内容 | 拼音 | 英文输出 |
|---|---|---|
| 单人 | `danren` | `solo, ` |
| 双马尾 | `shuangmawei` | `twintails, ` |
| 低马尾 | `dimawei` | `low_ponytail, ` |
| 长尾巴 | `changweiba` | `long_tail, ` |
| 多根尾巴 | `duogenweiba` | `multiple_tails, ` |
| 错误的腹肌 | `cuowudefuji` | `bad abs, ` |
| 黄白配色 | `huangbaipeise` | `yellow and white color scheme, ` |
| 左手扶腰 | `zuoshoufuyao` | `left hand resting on hip, ` |

空格选第一项，数字键选择其他候选；`=` 翻到下一页，`-` 返回上一页，Esc 取消。默认在每次选词后加英文逗号和空格，**Ctrl＋Alt＋F9 可以开关逗号后的空格**。日常聊天时切回原来的中文方案即可。

中文入口以完整拼音为主，暂不支持任意中文句子翻译。词库中的英文标签、空格短语和中文别名会一起显示，最终输出相同的候选只显示一次。

## 随机皮毛颜色和物种

输入下面的拼音，候选中会显示本次抽中的具体英文。选中后直接填入绘图软件。

| 拼音 | 用途 | 输出示例 |
|---|---|---|
| `suijidansepimao` | 随机单色皮毛 | `blue fur, ` |
| `suijishuangsepimao` | 随机双色皮毛 | `black and white fur, ` |
| `suijiwuzhong` | 随机物种 | `fox, ` |

单色从16种颜色中抽取，双色使用两种不同颜色；物种包含24种常见兽类及幻想物种，包括龙、飞龙、狮鹫和独角兽。提交后再次输入可以重新抽取，也可能抽到重复结果。`suijiyansepimao` 和 `suijipimaoyanse` 也能查找随机单色皮毛。

抽取发生在输入法中，最终输入具体颜色或物种，不依赖模型理解 `random`。模型对具体词的表现仍取决于所用模型。

## 一次输入一组常用词

输入 `zhengmian`，选择基础正面、动漫正面、写实正面、兽人毛发或自然肌肉。输入 `fumian`，选择基础负面、身体结构负面或腹肌负面。基础组合排在第一项，按空格就能一次输入整串。

基础正面：

```text
high quality, best quality, ultra-detailed, fine details, sharp focus,
```

基础负面：

```text
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad proportions, extra limbs, missing limbs, extra fingers, missing fingers, fused fingers, watermark, signature, text,
```

也可以输入 `dongmanzhengmian`、`xieshizhengmian`、`shourenmaofa`、`ziranjirou`、`shentijiegoufumian` 或 `fujifumian`，直接查找对应组合。[查看所有组合和本次新增词](docs/词库更新-0.2.9.md)。

请先点选绘图软件的正面或负面输入框，再选词。输入法不会自动切换输入框。这些组合是方便起步的常用写法，具体效果取决于所用模型；自然肌肉和腹肌负面中也有尚未做出图对比的描述短语。

## 姿势、位置与可续写短语

完整姿势可以直接选，例如 `tuifangping` 输出 `sitting with legs extended forward, `，表示坐着把腿向前伸直。`zuotuifangping`、`youtuifangping` 和 `shuangtuifangping` 分别指定左腿、右腿、双腿。[查看基础姿势清单](docs/基础姿势补充.md)。

物体位置可以留给自己填写：输入 `zuotuifangzai`，选中后先输出 `left leg resting on `，再补具体物体。半句只留一个空格，不加逗号；完整词条照常加分隔符。[查看可续写短语](docs/可续写短语.md)。

位置关系要先选，再补物体。例如“脚在浴缸左侧”：

1. 输入 `jiaofangzaizuoce`，按空格选出 `one foot positioned to the left of `。
2. 输入 `yugang`，按空格选出 `bathtub, `。

按“脚放在 → 浴缸 → 左侧”逐段选择不会自动换序。[查看浴缸连接例子](docs/浴缸位置连接.md)。

人物位置也分两种：`renwuzhanzaipangbian` 输出可续写的 `character standing beside `；`renwuzaihuamianzuoce` 则直接输出完整的 `character on the left side of the frame, `。[查看空间与人物位置](docs/空间与人物位置.md)。

左右腿、左右脚指角色自身；某物左侧、画面左侧分别描述物体关系和构图位置。腿脚放置、基础姿势、人物位置和半句用法一并纳入 v0.2.11；v0.2.10 只保留源码标签，没有单独发布安装包。

详细变化见[更新记录](CHANGELOG.md)，固定物体上的腿脚放置见[腿脚放置](docs/腿脚放置.md)。遇到不合适的词，可在 [Issues](https://github.com/sekluyu/ai-prompt-ime/issues) 中附上输入拼音、候选中文和实际英文。

## 可选：截图识图

[AI Prompt Vision](https://github.com/sekluyu/ai-prompt-vision) 可以读取图片、框选截图并生成标签，支持 SwinV2 和 EVA02。它是独立程序，模型不进入 Rime，也不参与输入法按键处理。

建议识图截图快捷键用 Ctrl＋Alt＋F8，输入法保留 Ctrl＋Alt＋F9。只使用输入法时，无需安装识图程序或下载模型。

## 来源与许可

项目代码采用 MIT 许可，维护者：sekluyu，开发协助：GPT（Codex）、DeepSeek。词库参考 ffdkj、n714、Physton、e621 标签归档及 MTT，并包含本项目整理的中文别名和短语。各来源许可见 [licenses](licenses)，数据来源见[来源说明](docs/补充词库来源.md)。词库包含成人相关标签。

开发和重建方法见[项目手册](docs/项目手册.md)。
