"""Create reviewable archives. Does not access the real Rime user directory."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.0'
LAUNCHER='安装绘画提示词.exe'
def build_launcher(folder):
    framework=Path(os.environ.get('SystemRoot','C:/Windows'))/'Microsoft.NET'
    csc=next((p for p in [framework/'Framework64/v4.0.30319/csc.exe',framework/'Framework/v4.0.30319/csc.exe'] if p.is_file()),None)
    if csc is None: raise FileNotFoundError('Packaging the Windows launcher requires the .NET Framework C# compiler (csc.exe).')
    subprocess.run([str(csc),'/nologo','/target:exe','/platform:anycpu','/out:'+str(folder/LAUNCHER),str(ROOT/'tools/install_launcher.cs')],check=True)
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
    args=parser.parse_args()
    artifacts=args.artifacts_root.resolve()
    dist=args.output_dir.resolve();dist.mkdir(parents=True,exist_ok=True)
    reports={name:json.loads((artifacts/f'validation/gpt/formal-{name}-engine.json').read_text(encoding='utf-8')) for name in ['default','full']}
    assert all(r['status']=='PASS' for r in reports.values())
    archives=[]
    for variant in ['default','searchable','dictionary']:
        name=f'ai-prompt-ime-{VERSION}'+('' if variant=='default' else '-'+variant)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/name;folder.mkdir()
            (folder/'licenses').mkdir()
            shutil.copy2(ROOT/'licenses/ffdkj-LICENSE.txt',folder/'licenses/ffdkj-LICENSE.txt')
            shutil.copy2(ROOT/'licenses/pypinyin-LICENSE.txt',folder/'licenses/pypinyin-LICENSE.txt')
            shutil.copy2(ROOT/'LICENSE',folder/'LICENSE')
            shutil.copytree(ROOT/'docs',folder/'docs')
            (folder/'tools').mkdir()
            if variant=='dictionary':
                shutil.copytree(artifacts/'dictionary',folder/'dictionary')
                for tool in ['convert_dictionary.py','build.py']:shutil.copy2(ROOT/'tools'/tool,folder/'tools'/tool)
                # Build can target this directory after converting without the project checkout.
                (folder/'rime').mkdir();(folder/'validation/gpt').mkdir(parents=True)
                (folder/'README.md').write_text('词库追溯数据包 0.2.0；用于数据溯源，不需要安装。见 docs/词库交付说明.md。内含固定原始快照、规范化记录及待复核异常。\n\n项目自有代码采用 MIT，见 LICENSE；开发：GPT（Codex）和 DeepSeek；项目目标、发布决策与本机验收：sekluyu。第三方词库许可见 licenses/ffdkj-LICENSE.txt。\n',encoding='utf-8')
            else:
                src=ROOT/'rime' if variant=='default' else artifacts/'validation/gpt/full-build/rime'
                shutil.copytree(src,folder/'rime')
                shutil.copy2(ROOT/'tools/install.py',folder/'tools/install.py')
                shutil.copy2(ROOT/'tools/install_launcher.cs',folder/'tools/install_launcher.cs')
                build_launcher(folder)
                (folder/'validation').mkdir()
                report='default' if variant=='default' else 'full'
                shutil.copy2(artifacts/f'validation/gpt/formal-{report}-engine.json',folder/'validation/engine-test.json')
                for n in ['source.json','conversion-report.json']:shutil.copy2(artifacts/'dictionary'/n,folder/'validation'/n)
                prefix='' if variant=='default' else '> 本附件为扩展安装包：81359 个 tag、81420 条映射，替换默认词库使用，不叠加安装。解压后直接运行本包的 `python tools/install.py`。\n\n'
                (folder/'README.md').write_text(prefix+(ROOT/'README.md').read_text(encoding='utf-8'),encoding='utf-8')
            sums(folder)
            target=dist/(name+'.zip');zip_dir(folder,target);archives.append(target)
    (dist/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in archives),encoding='utf-8')
    print(json.dumps([dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in archives],indent=2))
if __name__=='__main__':main()
