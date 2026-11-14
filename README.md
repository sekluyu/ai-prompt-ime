# AI 绘画提示词输入方案

基于 Windows 小狼毫（Rime）的离线提示词方案：输入中文拼音，选择英文标签或维护短语，直接填入绘图软件。先自行安装小狼毫；本项目不安装或替换输入法引擎。

**当前版本：[v0.2.8](https://github.com/sekluyu/ai-prompt-ime/releases/tag/v0.2.8)**。完整词库为唯一默认，共 **276,799 条中文拼音映射 / 151,682 个内部词条键**。无需API key、Python、Go或.NET。

## v0.2.8 更新

- 正式纳入v0.2.7本地候选的按键延迟修复：全量Lua注释表改为构建期生成的排序文本索引，运行时二分查找。
- 全部词条、原热度、排序、中文说明、候选去重及分隔符规则保留；新增的注释索引与方案一并安装和回滚。
- v0.2.7未单独公开发布，v0.2.8是后续正式版本。延迟与验证范围见[性能修复说明](docs/按键延迟修复-0.2.7.md)。
- 本版本已通过数据、Lua全库对照、隔离引擎性能及安装回滚检查，并获维护者授权发布。本次EXE未记录独立的安全软件扫描结果，不继承v0.2.6的扫描结论。

## 下载与安装

| 附件 | 用途 |
|---|---|
| [独立安装器](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.8/ai-prompt-ime-0.2.8-setup.exe) | 单个EXE内置完整方案，无需额外运行环境 |
| [方案ZIP](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.8/ai-prompt-ime-0.2.8.zip) | 相同安装器、方案、许可与说明，可手动安装 |
| [SHA256SUMS.txt](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.8/SHA256SUMS.txt) | 校验独立EXE和ZIP |

1. 下载并核对SHA-256，运行安装器。它先备份同名方案和配置，再复制文件。
2. 成功后右键小狼毫托盘，选择“重新部署”；复制完成不等于新版本已部署。
3. 按F4或Ctrl＋反引号选择“绘画提示词”，输入`shuangmawei`应得到`twintails, `。

默认使用`%APPDATA%\Rime`；自定义用户目录、手动安装及回滚见[安装与回滚](docs/安装与回滚.md)。回滚使用本版EXE的`--rollback-latest`并重新部署。新版安装器可处理旧备份链，旧版EXE不能回滚新备份格式。

## 使用示例

| 中文 | 拼音 | 英文输出（省略分隔符） |
|---|---|---|
| 双马尾 | shuangmawei | twintails |
| 过膝袜 | guoxiwa | thighhighs |
| 白发／白头发／白毛 | baifa / baitoufa / baimao | white_hair |
| 高质量 | gaozhiliang | high quality |
| 黄白配色 | huangbaipeise | yellow and white color scheme |
| 金橙与奶油色皮毛 | jinchengyunaiyousepimao | golden orange and cream fur |
| 左手扶腰 | zuoshoufuyao | left hand resting on hip |
| 左手扶腰右手摸头 | zuoshoufuyaoyoushoumotou | left hand resting on hip, right hand touching head |

空格选首项，数字键选择候选，`=`下一页、`-`上一页，Esc取消。默认追加英文逗号和空格；**Ctrl＋Alt＋F9只切换逗号后的空格，逗号保留**。日常聊天通过方案菜单切回原中文方案。

完整匹配/补全长度优先，同等匹配下主词优先、按中文说明分组。相近含义、泛称别名及空格/下划线不同写法保留，不因近似语义删词。单次候选流按最终英文去重。

## 可选：截图识图与工具箱

独立项目 **[AI Prompt Vision](https://github.com/sekluyu/ai-prompt-vision)** 提供图片/截图识别、SwinV2与EVA02双模型、选区、标签编辑，以及可修改的全局截图快捷键。

- [下载识图扩展与工具箱 v0.1.0](https://github.com/sekluyu/ai-prompt-vision/releases/tag/v0.1.0)。
- 打开工具箱，点“安装/更新识图”即可下载并校验独立扩展；也支持本地ZIP。
- 识图模型按需下载、不捆绑在本方案。工具箱按需打开；开启截图快捷键后由识图扩展自己驻留托盘。
- 默认建议截图快捷键Ctrl＋Alt＋F8，可修改，不占用本方案Ctrl＋Alt＋F9。

识图代码、模型与快捷键不进入Rime，不参与逐键处理。仅使用本输入法的用户无需安装识图扩展。

## 来源、许可和边界

自有代码 **MIT**，署名sekluyu，开发：GPT（Codex）与DeepSeek；第三方许可见[licenses](licenses)及[来源说明](docs/补充词库来源.md)。固定来源包括ffdkj、n714、Physton、e621标签归档及MTT；词表存在未逐条人工审读的翻译和自动拼音。

完整词库未按成人内容筛除。标签和通用短语不保证所有绘图模型均能理解；本方案不是任意中文整句翻译器，也不自动识别正负提示词框。原始固定数据追溯仍可引用[v0.2.3追溯包](https://github.com/sekluyu/ai-prompt-ime/releases/download/v0.2.3/ai-prompt-ime-0.2.3-dictionary.zip)，不重复打包不变的数据库。

只交付和验证Windows小狼毫方案；源码不捆绑小狼毫/librime引擎、原始数据库或发布二进制。

[项目手册](docs/项目手册.md) · [开发与发布](docs/开发与发布.md) · [姿势与双手动作](docs/姿势与双手动作.md) · [更新记录](CHANGELOG.md)
