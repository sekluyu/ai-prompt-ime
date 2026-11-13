# AI 绘画提示词输入方案

这是基于 Windows 小狼毫（Rime）扩展的离线绘画提示词输入方案，需要先安装小狼毫，再挂载本方案：输入中文拼音，选中英文 tag、质量词、皮毛描述或配色短语，直接填入绘画提示词。

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

**当前版本：[v0.2.3](https://github.com/sekluyu/ai-prompt-ime/releases/tag/v0.2.3)。** 完整词库为唯一默认版本，共276,472条拼音映射。已接入n714、Physton、e621与MTT的固定文本快照，补充质量、皮肤、皮毛、兽人和色调短语；来源边界见[补充词库来源](docs/补充词库来源.md)。

本版合并23条同码同英文的重复映射，保留原有检索入口，并在候选列表按最终英文去重。不同英文可能共享中文入口，空格/下划线写法也继续保留，见[候选展示说明](docs/已知问题.md)。数据、Lua检查及历史引擎基线的范围见[词库交付说明](docs/词库交付说明.md)，方案ZIP附带对应报告。

| 输入拼音 | 中文概念 | 输出内容（省略分隔符） |
|---|---|---|
| zhilianggenggao / gaozhiliang | 质量更高／高质量 | `high quality` |
| jiezuo / dashiji | 杰作／大师级 | `masterpiece` |
| zuijiazhiliang / zuijiahuazhi | 最佳质量／最佳画质 | `best quality` |
| zhenshipifu | 真实皮肤 | `realistic skin` |
| zhenshipimao / zhenshimaopi | 真实皮毛／真实毛皮 | `realistic fur` |
| jinchengse / naiyouse | 金橙色／奶油色 | `golden orange` / `cream` |
| jinchengyunaiyousepimao | 金橙与奶油色皮毛 | `golden orange and cream fur` |

## 安装

从[v0.2.3 Release](https://github.com/sekluyu/ai-prompt-ime/releases/tag/v0.2.3)下载[独立安装器](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/ai-prompt-ime-0.2.3-setup.exe)，单个EXE即可安装；也可下载[方案ZIP](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/ai-prompt-ime-0.2.3.zip)，完整解压后使用包内`安装绘画提示词.exe`。两种形式内容相同，完整词库为唯一默认，不再区分默认/扩展版。

前置条件：Windows 10/11 x64、已安装的[小狼毫](https://github.com/rime/weasel/releases)。**普通用户无需安装Python、.NET、Go或其他运行环境，安装过程无需联网。** 本方案不需要API key、LLM或在线服务。

1. 安装小狼毫并确认能正常输入中文。
2. 双击 **`ai-prompt-ime-0.2.3-setup.exe`**，或 ZIP 解压目录里的 **`安装绘画提示词.exe`**。方案文件和词库均已内置，不依赖旁边的脚本或数据文件，不需要管理员权限。
3. 看到安装成功提示后，右键托盘小狼毫图标，选择“重新部署”。
4. 部署完成后切到小狼毫，按 **F4** 打开方案菜单，选“绘画提示词”，输入 `shuangmawei`，选词后得到 `twintails, `。

安装器默认使用 `%APPDATA%\Rime`，先备份同名方案文件及方案列表，再添加绘画方案；不安装或替换小狼毫。自定义用户目录、错误处理与备份位置见[安装与回滚](docs/安装与回滚.md)。

仓库源码仍提供 `tools/install.py`，需要 Python 3；它是可选的源码安装入口。词库转换、构建及开发测试所需的 Python/Go 不属于普通用户安装依赖。

## 使用

1. 切到小狼毫，按 **F4** 打开方案菜单，选“绘画提示词”。F4若被系统/应用占用，可用 **Ctrl＋反引号**；自定义过热键时以自己的配置为准。
2. 输入连续小写无声调拼音，ü输入v；候选框显示英文 tag 和中文释义。空格选首项，数字键选对应项，`=` 下一页、`-` 上一页，Esc取消。
3. 逐词输入并选中。例如女孩、单人、白发可组成 `1girl, solo, white_hair, `。**Ctrl＋Alt＋F9**只切换是否在逗号后添加空格，逗号保留：开启时如 `yellow, white, `，关闭时如 `yellow,white,`；末尾多余分隔符可手动删掉。
4. 日常聊天时通过方案菜单切回原中文方案。本方案不根据窗口或网址自动启停。

0.2.3支持25种颜色及别名，新增金橙、奶油、象牙、米色、米白、黄褐、深浅棕、深浅灰和金黄。整体配色输出 `color scheme`，皮毛配色输出 `fur`。质量词、材质词、兽人词、光照词和负面词分别标注类别；负面词需要自行填入绘图软件的负面提示词框，输入法不识别当前输入框。

质量词是常见表达，不保证添加后一定提高画质；先提供中文检索，不按主模型版本屏蔽词条。
详细行为见[使用说明](docs/使用说明.md)，实机操作见[人工验收清单](docs/人工验收清单.md)。

## 回滚

在安装器所在目录打开 PowerShell，运行 `.\ai-prompt-ime-0.2.3-setup.exe --rollback-latest`；使用 ZIP 内安装器时，运行 `.\安装绘画提示词.exe --rollback-latest`。看到恢复成功后重新部署小狼毫。自定义用户目录需要再带同一个 `--user-dir` 参数。新安装器兼容 0.2.0 Python 安装器的备份格式。回滚只撤销最近一次方案挂载/更新，不卸载小狼毫；若文件安装后被手工改过或删除，会停止并报告冲突，避免覆盖后续改动。旧备份和手动回滚步骤见[安装与回滚](docs/安装与回滚.md)。

## 词库与交付内容

当前完整词库是唯一默认：**151,471个内部词条键／276,472条中文拼音映射**。内部键包含来源标签与私有短语键，不等于去重后的英文输出数量。同一英文可以保留不同中文入口，但同一候选列表中相同英文只显示一次。

| 文件 | 用途 |
|---|---|
| [ai-prompt-ime-0.2.3-setup.exe](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/ai-prompt-ime-0.2.3-setup.exe) | 独立安装器，内置完整方案和词库，单个文件即可离线安装 |
| [ai-prompt-ime-0.2.3.zip](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/ai-prompt-ime-0.2.3.zip) | 同一完整方案、相同安装器及文档，不需要与EXE重复安装 |
| [ai-prompt-ime-0.2.3-dictionary.zip](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/ai-prompt-ime-0.2.3-dictionary.zip) | 固定原始来源、补充快照和转换脚本，供数据追溯，不需要安装 |
| [SHA256SUMS.txt](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/SHA256SUMS.txt) | 上述文件的SHA-256；每个ZIP另含内部校验清单 |

数据包括[ffdkj Danbooru中英对照表](https://github.com/ffdkj/ffdkj-Danbooru_Tag-Chinese-English-Translation-Table)（固定commit `d232b4ee431f13c6f34c7f31c35b937b26bb56c2`），以及n714、Physton、e621归档和MTT的固定文本快照。来源、许可与未覆盖部分见[补充词库来源](docs/补充词库来源.md)。ffdkj原81,359个可检索标签的检索/英文输出保留；完全重复的生成行合并，原始快照不改写。

项目维护的颜色层625条英文表达／2,356条映射，皮毛配色层625条表达，常用质量/材质等维护表132种英文表达／217条中文拼音映射，分别生成后合并。原始ffdkj共336,155条记录，其中254,796个没有可用映射；e621也存在未连接中文的英文标签。**来源已归档不代表全量可中文输入。** 自动拼音及上游翻译未逐条人工审读。

仓库不含完整`dictionary/`、原始`tag.sqlite`、引擎、临时构建或发布二进制。重建原始ffdkj词库需自行取得固定commit数据，按转换脚本放入`dictionary/source/d232b4ee431f13c6f34c7f31c35b937b26bb56c2/`；追溯包也保留同一快照和项目覆盖。步骤与依赖见[开发与发布](docs/开发与发布.md)，精确计数与去重边界见[词库交付说明](docs/词库交付说明.md)。

## 许可

原 ffdkj、n714、Physton 和 MTT 数据按其仓库 MIT 声明保留；e621 标签归档按仓库 Unlicense 声明保留。完整文本见 [licenses](licenses)，来源内的额外署名及限制说明见[补充词库来源](docs/补充词库来源.md)。小狼毫与librime由使用者自行安装，本仓库和方案ZIP不捆绑其二进制。

本项目自有 YAML、Lua、Python 和 Go 代码采用 **MIT License**，完整文本见根目录 [LICENSE](LICENSE)。第三方数据与依赖保留各自版权及许可声明，见[第三方许可](docs/第三方许可.md)。

## 开发与维护署名

开发由 **GPT（Codex）和 DeepSeek** 完成；**sekluyu** 负责项目目标、发布决策与本机实机验收。

## 已知边界

- 部分不同标签使用相同中文别名，当前保留；维护者决定后续优先讨论候选排序，不再作为独立Issue修复。
- 空格/下划线近似写法继续保留，不属于本版已删除的完全重复项；后续只考虑调整展示优先级。

- 当前只交付并验收 Windows 小狼毫方案，未验收macOS或手机端。
- 逐词选 tag 或固定的质量、材质、皮毛、配色短语，支持别名；不提供任意整句中文语义转换或LLM兜底。
- 以SDXL/Pony常见标签使用场景为起点，不保证任意模型能识别每个词；同音词需要人工选候选。
- 默认词库和扩展词库均未按成人内容做筛除，源数据含成人相关标签。
- 仓库不含 librime 引擎。运行 `tests/engine_test.py` 需要自备 Windows x64 librime 及配套头文件，并按[开发与发布](docs/开发与发布.md)配置路径与依赖；未准备引擎时会因无法加载 `rime.dll` 报错。这不影响已安装小狼毫的用户安装方案。

构建、可选测试和发布顺序见[开发与发布](docs/开发与发布.md)；版本发布审核项目见[发布检查清单](docs/发布检查清单.md)。
