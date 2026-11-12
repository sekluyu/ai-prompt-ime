"""Create reviewable archives. Does not access the real Rime user directory."""
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
import csv
from pathlib import Path
from build_windows_installer import build as build_installer

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.3'
LAUNCHER='安装绘画提示词.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sums(folder):
    files=sorted(p for p in folder.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
    (folder/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(folder).as_posix()+'\n' for p in files),encoding='utf-8')
def zip_dir(folder,target):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(folder.parent))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-root',type=Path,default=ROOT,help='Read dictionary and validation inputs from this directory')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist',help='Write release ZIPs and their checksum file here')
    parser.add_argument('--go',default='go',help='Go compiler for the native Windows installer')
    parser.add_argument('--validation-root',type=Path,default=ROOT/'validation/gpt',help='Current data/Lua reports and historical complete-corpus engine baseline')
    parser.add_argument('--prompt-snapshot',type=Path,help='Pinned text-only n714/Physton/e621/MTT source snapshots for the trace archive')
    args=parser.parse_args()
    artifacts=args.artifacts_root.resolve()
    validation=args.validation_root.resolve()
    dist=args.output_dir.resolve();dist.mkdir(parents=True,exist_ok=True)
    proof=json.loads((validation/'deduplication.json').read_text(encoding='utf-8'))
    assert proof['status']=='PASS' and proof['dictionary_sha256']==sha(ROOT/'rime/booru.tsv')
    assert proof['lua_sha256']==sha(ROOT/'rime/lua/booru_filter.lua')
    lua=json.loads((validation/'lua-filter-unit.json').read_text(encoding='utf-8'))
    assert lua['status']=='PASS' and lua['lua_sha256']==proof['lua_sha256']
    baseline=json.loads((validation/'formal-full-engine.json').read_text(encoding='utf-8'))
    assert baseline['status']=='PASS' and baseline['dictionary_sha256']==proof['before_dictionary_sha256']
    archives=[]
    for variant in ['default','dictionary']:
        name=f'ai-prompt-ime-{VERSION}'+('' if variant=='default' else '-'+variant)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/name;folder.mkdir()
            shutil.copytree(ROOT/'licenses',folder/'licenses')
            shutil.copy2(ROOT/'LICENSE',folder/'LICENSE')
            shutil.copy2(ROOT/'CHANGELOG.md',folder/'CHANGELOG.md')
            shutil.copytree(ROOT/'docs',folder/'docs')
            (folder/'tools').mkdir()
            if variant=='dictionary':
                shutil.copytree(artifacts/'dictionary',folder/'dictionary')
                for tool in ['convert_dictionary.py','build.py','import_prompt_libraries.py']:shutil.copy2(ROOT/'tools'/tool,folder/'tools'/tool)
                shutil.copy2(ROOT/'tools/general_phrases.py',folder/'tools/general_phrases.py')
                shutil.copytree(ROOT/'data',folder/'data')
                if args.prompt_snapshot:
                    shutil.copytree(args.prompt_snapshot,folder/'supplemental-snapshots')
                # Build can target this directory after converting without the project checkout.
                (folder/'rime').mkdir();(folder/'validation/gpt').mkdir(parents=True)
                (folder/'README.md').write_text('词库追溯数据包 '+VERSION+'；用于数据溯源，不需要安装。见 docs/词库交付说明.md 与 docs/补充词库来源.md。内含固定原始SQLite、来源TSV、项目覆盖、补充数据及转换脚本；不包含已清理的可再生大型中间JSON/SQLite。\n\n项目自有代码采用 MIT，见 LICENSE；开发：GPT（Codex）和 DeepSeek；项目目标、发布决策与本机验收：sekluyu。各上游许可见 licenses 目录。开发重建需要 Python 3、pypinyin 0.55.0，导入补充词库另需 PyYAML 6.0.3；普通用户使用独立 EXE 安装不需要 Python。\n',encoding='utf-8')
            else:
                src=ROOT/'rime'
                shutil.copytree(src,folder/'rime')
                shutil.copy2(ROOT/'tools/install.py',folder/'tools/install.py')
                (folder/'PACKAGE_INFO.json').write_text(json.dumps({'version':VERSION,'variant':variant}),encoding='utf-8')
                build_installer(src,folder/LAUNCHER,args.go,variant)
                (folder/'validation').mkdir()
                # Historical engine evidence is explicitly a baseline; the new
                # candidate has data-coverage and isolated Lua checks, not a new
                # real-input acceptance performed on the user's behalf.
                shutil.copy2(validation/'formal-full-engine.json',folder/'validation/baseline-engine-test.json')
                shutil.copy2(validation/'color-test-full.json',folder/'validation/baseline-color-test.json')
                shutil.copy2(validation/'prompt-test-full.json',folder/'validation/baseline-prompt-test.json')
                for evidence_name in ['deduplication.json','lua-filter-unit.json']:
                    shutil.copy2(validation/evidence_name,folder/'validation'/evidence_name)
                for n in ['source.json','conversion-report.json']:shutil.copy2(artifacts/'dictionary'/n,folder/'validation'/n)
                with (src/'booru.tsv').open(encoding='utf-8') as stream:
                    mappings=sum(1 for _ in csv.DictReader(stream,delimiter='\t'))
                prefix='> 本附件为 '+VERSION+' 安装包，完整词库为唯一默认，共 '+str(mappings)+' 条拼音映射。双击本包的 `安装绘画提示词.exe`，无需 Python。完整词库为唯一版本；已知别名问题见docs/已知问题.md，验证范围见docs/词库交付说明.md。\n\n'
                (folder/'README.md').write_text(prefix+(ROOT/'README.md').read_text(encoding='utf-8'),encoding='utf-8')
            sums(folder)
            target=dist/(name+'.zip');zip_dir(folder,target);archives.append(target)
            if variant!='dictionary':
                setup=dist/(f'ai-prompt-ime-{VERSION}'+('' if variant=='default' else '-searchable')+'-setup.exe')
                setup.write_bytes((folder/LAUNCHER).read_bytes());archives.append(setup)
    (dist/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in archives),encoding='utf-8')
    print(json.dumps([dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in archives],indent=2))
if __name__=='__main__':main()
