# AI 绘画提示词输入方案

这是基于 Windows 小狼毫（Rime）扩展的离线绘画提示词输入方案，需要先安装小狼毫，再挂载本方案：输入中文拼音，选中英文 tag 或通用颜色/配色短语，直接填入绘画提示词。

## 解决什么问题

知道中文概念，却记不住绘画标签的写法？例如“双马尾”希望得到 Danbooru 标签 **twintails**，通用翻译可能给出 **twin ponytails**。本方案通过词典查找标签，减少反复查词和切换翻译工具的操作；标签在具体模型上的效果仍取决于模型。

| 输入拼音 | 中文概念 | 选词输出（默认带逗号与空格） |
|---|---|---|
| shuangmawei | 双马尾 | `twintails, ` |
| guoxiwa | 过膝袜 | `thighhighs, ` |
| baifa / baitoufa / baimao | 白发 | `white_hair, ` |
| huangse | 黄色〔通用短语〕 | `yellow, ` |
| huangbaipeise | 黄＋白配色〔通用短语〕 | `yellow and white color scheme, ` |

## 版本与验收

0.2.2 新增通用颜色与双色配色短语，并将 Ctrl＋Shift＋逗号改为只切换逗号后的空格。原有 tag 数据保留；默认与扩展库均通过 librime 回归和全部通用词拼音映射检查。独立安装器使用隔离目录验证；本版未追加维护者实机验收。上述输入与输出展示方案的使用方式；本页未附实机截图。词库覆盖和模型效果的边界见下文。

## 安装

前置条件：Windows 10/11 x64、已安装的[小狼毫](https://github.com/rime/weasel/releases)。**普通用户无需安装 Python、.NET、Go 或其他运行环境，安装过程无需联网。** 本方案不需要 API key、LLM 或在线服务。

从 [v0.2.2 Release](https://github.com/sekluyu/ai-prompt-ime/releases/tag/v0.2.2) 下载[默认独立安装器](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/ai-prompt-ime-0.2.2-setup.exe)，单独这个 EXE 即可安装；也可以下载[默认 ZIP 包](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/ai-prompt-ime-0.2.2.zip)，完整解压后使用包内的 EXE。默认词库够日常使用；扩展词库与词库追溯包见下文。

1. 安装小狼毫并确认能正常输入中文。
2. 双击 **`ai-prompt-ime-0.2.2-setup.exe`**，或 ZIP 解压目录里的 **`安装绘画提示词.exe`**。方案文件和词库均已内置，不依赖旁边的脚本或数据文件，不需要管理员权限。
3. 看到安装成功提示后，右键托盘小狼毫图标，选择“重新部署”。
4. 部署完成后切到小狼毫，按 **F4** 打开方案菜单，选“绘画提示词”，输入 `shuangmawei`，选词后得到 `twintails, `。

安装器默认使用 `%APPDATA%\Rime`，先备份同名方案文件及方案列表，再添加绘画方案；不安装或替换小狼毫。自定义用户目录、错误处理与备份位置见[安装与回滚](docs/安装与回滚.md)。

仓库源码仍提供 `tools/install.py`，需要 Python 3；它是可选的源码安装入口。词库转换、构建及开发测试所需的 Python/Go 不属于普通用户安装依赖。

## 使用

1. 切到小狼毫，按 **F4** 打开方案菜单，选“绘画提示词”。F4若被系统/应用占用，可用 **Ctrl＋反引号**；自定义过热键时以自己的配置为准。
2. 输入连续小写无声调拼音，ü输入v；候选框显示英文 tag 和中文释义。空格选首项，数字键选对应项，`=` 下一页、`-` 上一页，Esc取消。
3. 逐词输入并选中。例如女孩、单人、白发可组成 `1girl, solo, white_hair, `。**Ctrl＋Shift＋逗号**只切换是否在逗号后添加空格，逗号保留：开启时如 `yellow, white, `，关闭时如 `yellow,white,`；末尾多余分隔符可手动删掉。
4. 日常聊天时通过方案菜单切回原中文方案。本方案不根据窗口或网址自动启停。

通用词支持红、橙、黄、绿、青、蓝、紫、粉、黑、白、灰、棕、金、银及粉红/褐别名；双色输入如“黄白配色”“黄色白色配色”“黄色与白色”。候选注释带“〔通用短语〕”，它们是项目维护的固定英文表达，不是上游 Danbooru 标签，也不是整句翻译。

详细行为见[使用说明](docs/使用说明.md)，实机操作见[人工验收清单](docs/人工验收清单.md)。

## 回滚

在安装器所在目录打开 PowerShell，运行 `.\ai-prompt-ime-0.2.2-setup.exe --rollback-latest`；使用 ZIP 内安装器时，运行 `.\安装绘画提示词.exe --rollback-latest`。看到恢复成功后重新部署小狼毫。自定义用户目录需要再带同一个 `--user-dir` 参数。新安装器兼容 0.2.0 Python 安装器的备份格式。回滚只撤销最近一次方案挂载/更新，不卸载小狼毫；若文件安装后被手工改过或删除，会停止并报告冲突，避免覆盖后续改动。旧备份和手动回滚步骤见[安装与回滚](docs/安装与回滚.md)。

## 词库与下载内容

数据来自 [ffdkj Danbooru 中英对照表](https://github.com/ffdkj/ffdkj-Danbooru_Tag-Chinese-English-Translation-Table)，固定 commit 为 `d232b4ee431f13c6f34c7f31c35b937b26bb56c2`，另加项目维护的少量中文别名与拼音覆盖。

| 内容 | 来源 tag＋通用表达 / 拼音映射数 | 获取位置 |
|---|---:|---|
| 默认常用库 | 20002＋196 / 20834 | [独立 EXE](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/ai-prompt-ime-0.2.2-setup.exe) / [ZIP 包](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/ai-prompt-ime-0.2.2.zip)；源码中的 rime 目录 |
| 扩展可检索库 | 81359＋196 / 82191 | [独立 EXE](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/ai-prompt-ime-0.2.2-searchable-setup.exe) / [ZIP 包](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/ai-prompt-ime-0.2.2-searchable.zip)，词库更大，替换默认库使用 |
| 完整来源与处理记录 | 336155条来源记录 | [词库追溯包](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/ai-prompt-ime-0.2.2-dictionary.zip)，约 45 MiB，用于数据溯源，不需要安装 |

两个独立 EXE 与三个 ZIP 的 SHA-256 校验值见 [SHA256SUMS.txt](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.2/SHA256SUMS.txt)；每个 ZIP 内另附所含文件的校验清单。独立 EXE 内置项目、词库和 Go 运行时的许可，可运行 `安装器文件名.exe --license` 查看。

通用颜色层包含196条不同英文表达、771条拼音映射；默认与扩展包都加载同一通用层。它来自项目维护的 `data/general_colors.tsv`，独立于 ffdkj 来源统计。

默认库的来源层为一般类可检索词按源热度取前20000个，再加核心别名所需的额外2个 tag；不是逐条人工精选。完整来源已遍历归档，但254796个 tag 仍无可用拼音映射，主要涉及混合文本或读音处理，未盲目去字符猜译。**两万常用词不等于全量标签都能输入。** 自动拼音也未全部人工审读。

仓库只保留方案、默认词库、脚本和文档。全量SQLite、异常/元数据、开发引擎、临时构建目录和ZIP不进入Git；大文件通过Release附件提供，校验值随附件提供。更多数字与边界见[词库交付说明](docs/词库交付说明.md)。

仓库不含 `dictionary/` 全量目录和原始 `tag.sqlite`。重建全量词库需要自行从上述 ffdkj 仓库的固定 commit 拉取来源数据，按转换脚本要求放入 `dictionary/source/d232b4ee431f13c6f34c7f31c35b937b26bb56c2/`；词库追溯包提供同一固定快照和项目别名覆盖，复现时应一并保留。具体依赖与步骤见[开发与发布](docs/开发与发布.md)。

## 许可

第三方词库采用 **MIT**，完整声明保留在 [licenses/ffdkj-LICENSE.txt](licenses/ffdkj-LICENSE.txt)。小狼毫与librime由使用者自行安装，本仓库和方案ZIP不捆绑其二进制。

本项目自有 YAML、Lua、Python 和 Go 代码采用 **MIT License**，完整文本见根目录 [LICENSE](LICENSE)。第三方数据与依赖保留各自版权及许可声明，见[第三方许可](docs/第三方许可.md)。

## 开发与维护署名

开发由 **GPT（Codex）和 DeepSeek** 完成；**sekluyu** 负责项目目标、发布决策与本机实机验收。

## 已知边界

- 当前只交付并验收 Windows 小狼毫方案，未验收macOS或手机端。
- 逐词选 tag 或固定的通用颜色/配色短语，支持别名；不提供任意整句中文语义转换或LLM兜底。
- 以SDXL/Pony常见标签使用场景为起点，不保证任意模型能识别每个词；同音词需要人工选候选。
- 默认词库和扩展词库均未按成人内容做筛除，源数据含成人相关标签。
- 仓库不含 librime 引擎。运行 `tests/engine_test.py` 需要自备 Windows x64 librime 及配套头文件，并按[开发与发布](docs/开发与发布.md)配置路径与依赖；未准备引擎时会因无法加载 `rime.dll` 报错。这不影响已安装小狼毫的用户安装方案。

构建、可选测试和发布顺序见[开发与发布](docs/开发与发布.md)；版本发布审核项目见[发布检查清单](docs/发布检查清单.md)。
