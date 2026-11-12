"""Create reviewable archives. Does not access the real Rime user directory."""
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from build_windows_installer import build as build_installer

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.2'
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
    parser.add_argument('--validation-root',type=Path,default=ROOT/'validation/gpt',help='Current matching engine reports and full-build/rime')
    args=parser.parse_args()
    artifacts=args.artifacts_root.resolve()
    validation=args.validation_root.resolve()
    dist=args.output_dir.resolve();dist.mkdir(parents=True,exist_ok=True)
    reports={name:json.loads((validation/f'formal-{name}-engine.json').read_text(encoding='utf-8')) for name in ['default','full']}
    assert all(r['status']=='PASS' for r in reports.values())
    for name,src in [('default',ROOT/'rime'),('full',validation/'full-build/rime')]:
        assert reports[name]['dictionary_sha256']==sha(src/'booru.tsv'),'Engine report must match the current dictionary'
        assert json.loads((validation/f'color-test-{name}.json').read_text(encoding='utf-8'))['status']=='PASS'
    archives=[]
    for variant in ['default','searchable','dictionary']:
        name=f'ai-prompt-ime-{VERSION}'+('' if variant=='default' else '-'+variant)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/name;folder.mkdir()
            (folder/'licenses').mkdir()
            shutil.copy2(ROOT/'licenses/ffdkj-LICENSE.txt',folder/'licenses/ffdkj-LICENSE.txt')
            shutil.copy2(ROOT/'licenses/pypinyin-LICENSE.txt',folder/'licenses/pypinyin-LICENSE.txt')
            for license_name in ['go-LICENSE.txt','go-PATENTS.txt']:
                shutil.copy2(ROOT/'licenses'/license_name,folder/'licenses'/license_name)
            shutil.copy2(ROOT/'LICENSE',folder/'LICENSE')
            shutil.copy2(ROOT/'CHANGELOG.md',folder/'CHANGELOG.md')
            shutil.copytree(ROOT/'docs',folder/'docs')
            (folder/'tools').mkdir()
            if variant=='dictionary':
                shutil.copytree(artifacts/'dictionary',folder/'dictionary')
                for tool in ['convert_dictionary.py','build.py']:shutil.copy2(ROOT/'tools'/tool,folder/'tools'/tool)
                shutil.copy2(ROOT/'tools/general_phrases.py',folder/'tools/general_phrases.py')
                shutil.copytree(ROOT/'data',folder/'data')
                # Build can target this directory after converting without the project checkout.
                (folder/'rime').mkdir();(folder/'validation/gpt').mkdir(parents=True)
                (folder/'README.md').write_text('词库追溯数据包 '+VERSION+'；用于数据溯源，不需要安装。见 docs/词库交付说明.md。内含固定原始快照、规范化记录及待复核异常。\n\n项目自有代码采用 MIT，见 LICENSE；开发：GPT（Codex）和 DeepSeek；项目目标、发布决策与本机验收：sekluyu。第三方词库许可见 licenses/ffdkj-LICENSE.txt。转换与构建词库仍需要 Python 3，普通用户使用独立 EXE 安装不需要 Python。\n',encoding='utf-8')
            else:
                src=ROOT/'rime' if variant=='default' else validation/'full-build/rime'
                shutil.copytree(src,folder/'rime')
                shutil.copy2(ROOT/'tools/install.py',folder/'tools/install.py')
                build_installer(src,folder/LAUNCHER,args.go,variant)
                (folder/'validation').mkdir()
                report='default' if variant=='default' else 'full'
                shutil.copy2(validation/f'formal-{report}-engine.json',folder/'validation/engine-test.json')
                shutil.copy2(validation/f'color-test-{report}.json',folder/'validation/color-test.json')
                for n in ['source.json','conversion-report.json']:shutil.copy2(artifacts/'dictionary'/n,folder/'validation'/n)
                prefix='' if variant=='default' else '> 本附件为扩展安装包：81359 个来源 tag，另加 196 条通用颜色/配色表达，共 82191 条拼音映射；替换默认词库使用，不叠加安装。双击本包的 `安装绘画提示词.exe`，无需 Python。\n\n'
                (folder/'README.md').write_text(prefix+(ROOT/'README.md').read_text(encoding='utf-8'),encoding='utf-8')
            sums(folder)
            target=dist/(name+'.zip');zip_dir(folder,target);archives.append(target)
            if variant!='dictionary':
                setup=dist/(f'ai-prompt-ime-{VERSION}'+('' if variant=='default' else '-searchable')+'-setup.exe')
                shutil.copy2(folder/LAUNCHER,setup);archives.append(setup)
    (dist/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in archives),encoding='utf-8')
    print(json.dumps([dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in archives],indent=2))
if __name__=='__main__':main()
