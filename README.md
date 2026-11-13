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

**当前版本：[v0.2.6](https://github.com/sekluyu/ai-prompt-ime/releases/tag/v0.2.6)。** 本版补充躯干姿态及左右手／一只手和另一只手的动作短语，净增323条映射，完整库为唯一默认，共276,799条。v0.2.5的276,476条检索/英文组合全部保留。数据、Lua模拟、Go及隔离安装/回滚检查通过；维护者已确认本机输入检查通过。

本次提供**独立EXE、内含相同EXE的方案ZIP与源码**，普通安装无需Python、.NET或Go。完整词库为唯一默认。词库来源及许可见[补充词库来源](docs/补充词库来源.md)，排序规则见[候选排序与俗称](docs/候选排序与俗称-0.2.4.md)。

> 本版本已由维护者完成本机输入检查，并通过火绒扫描，未发现风险。

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

前置条件：Windows 10/11 x64、已安装并能正常输入中文的[小狼毫](https://github.com/rime/weasel/releases)。这是小狼毫（Rime）的扩展输入方案，不安装或替换小狼毫，不需要API key或在线服务。

1. 从[v0.2.4 Release](https://github.com/sekluyu/ai-prompt-ime/releases/tag/v0.2.6)下载[独立安装器](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.6/ai-prompt-ime-0.2.6-setup.exe)，对照同页SHA256SUMS.txt核对。也可完整解压方案ZIP，使用根目录的`安装绘画提示词.exe`；两者内容相同，无需重复安装。
2. 双击EXE。方案和词库内置，无需Python、.NET、Go、联网或管理员权限。安装器先备份同名方案文件及`default.custom.yaml`，再写入更新。
3. 看到“【安装成功】”后，右键小狼毫托盘图标，选择“重新部署”。文件复制完成不代表新版本已部署。
4. 部署结束后按F4，选择“绘画提示词”；输入`shuangmawei`选词应得到`twintails, `。实际输入与网页表现由使用者验收。

安装器默认使用`%APPDATA%\Rime`，自定义用户目录、回滚及手动安装步骤见[安装与回滚](docs/安装与回滚.md)。若安全软件告警，停止运行被检测EXE并保留日志，不将关闭防护作为安装步骤。

本轮没有修改使用者的真实Rime目录。源码中的`tools/install.py`仍是可选Python入口，普通用户使用EXE不需要Python。

## 使用

1. 切到小狼毫，按 **F4** 打开方案菜单，选“绘画提示词”。F4若被系统/应用占用，可用 **Ctrl＋反引号**；自定义过热键时以自己的配置为准。
2. 输入连续小写无声调拼音，ü输入v；候选框显示英文 tag 和中文释义。空格选首项，数字键选对应项，`=` 下一页、`-` 上一页，Esc取消。
3. 逐词输入并选中。例如女孩、单人、白发可组成 `1girl, solo, white_hair, `。**Ctrl＋Alt＋F9**只切换是否在逗号后添加空格，逗号保留：开启时如 `yellow, white, `，关闭时如 `yellow,white,`；末尾多余分隔符可手动删掉。
4. 日常聊天时通过方案菜单切回原中文方案。本方案不根据窗口或网址自动启停。

0.2.3支持25种颜色及别名，新增金橙、奶油、象牙、米色、米白、黄褐、深浅棕、深浅灰和金黄。整体配色输出 `color scheme`，皮毛配色输出 `fur`。质量词、材质词、兽人词、光照词和负面词分别标注类别；负面词需要自行填入绘图软件的负面提示词框，输入法不识别当前输入框。

质量词是常见表达，不保证添加后一定提高画质；先提供中文检索，不按主模型版本屏蔽词条。
详细行为见[使用说明](docs/使用说明.md)，实机操作见[人工验收清单](docs/人工验收清单.md)。

## 回滚

在安装器所在目录打开PowerShell，运行`.\ai-prompt-ime-0.2.6-setup.exe --rollback-latest`；ZIP内EXE相应改用`.\安装绘画提示词.exe --rollback-latest`。看到回滚成功后重新部署小狼毫。自定义用户目录时带同一个`--user-dir`。回滚只管理本方案文件，不卸载小狼毫；文件安装后被手工修改或删除时会拒绝覆盖。手动安装的更新须用复制前留存的文件手动恢复，不能借用旧EXE的回滚清单。详见[安装与回滚](docs/安装与回滚.md)。

## 词库与交付内容

当前完整词库是唯一默认：**151,682个内部词条键／276,799条中文拼音映射**。内部键包含来源标签与私有短语键，不等于去重后的英文输出数量。同一英文可以保留不同中文入口，但同一候选列表中相同英文只显示一次。

| 文件 | 用途 |
|---|---|
| [ai-prompt-ime-0.2.6-setup.exe](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.6/ai-prompt-ime-0.2.6-setup.exe) | 独立离线安装器，内置完整词库，无需Python |
| [ai-prompt-ime-0.2.6.zip](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.6/ai-prompt-ime-0.2.6.zip) | 同一安装器、完整方案、词库、Lua和文档，也可手动复制 |
| [SHA256SUMS.txt](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.6/SHA256SUMS.txt) | 独立EXE与方案ZIP的SHA-256；ZIP内另含文件校验清单，校验一致不等于安全认证 |
| Release的Source code | 对应v0.2.4标签的源码，含构建脚本与俗称维护表 |

本次不重新打包词库追溯附件；固定来源追溯仍见[v0.2.3追溯包](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/ai-prompt-ime-0.2.3-dictionary.zip)，本次新代码和俗称表以v0.2.4源码为准。不要用旧版EXE覆盖本版方案。

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

## v0.2.4：排序与俗称

本版保留v0.2.3全部276,472条检索/英文组合，新增4条入口，总计276,476条。完整拼音与前缀补全仍由Rime区分；同等匹配长度下，明确主词优先，再按中文说明分组，同组原热度排序。其余资料保持扩展层，不因相同中文或近似英文而删除。

例如完整huli的构建预览先为fox（狐狸）、nursing（护理），再到具体狐种/角色和其他扩展。注释按本次命中的中文入口显示，有可靠主释义时可附“狐狸 · 耳廓狐”。构建预览不是实机输入结果。

俗称入口包括bi（逼／屄→pussy，vulva作为其他候选）、piyan（屁眼→anus）、jiba/diao（鸡巴/屌→penis），以及现有pigu（屁股）的butt优先、ass随后。候选标明俗称及部位，规范中文入口继续保留。

本轮已通过数据、Lua模拟候选、Go单元测试及最终EXE的隔离安装/回滚检查；安全软件兼容仍未解决。真实小狼毫/网页排序由维护者验收。不修改狐狸等既有别名，不合并空格/下划线写法，不重建已删除的Issue。

## v0.2.6：姿势与双手动作

上半身直立、坐直、背部挺直可直接检索；左右手动作可分别选词，例如`zuoshoufuyao`再输入`youshoumotou`，也可用完整`zuoshoufuyaoyoushoumotou`一次选中常用组合。支持一只手／另一只手及一手／另一手的较短入口。摸脸、托腮、托下巴分别维护，候选标注通用姿态。详见[姿势与双手动作](docs/姿势与双手动作.md)及[项目手册](docs/项目手册.md)。
