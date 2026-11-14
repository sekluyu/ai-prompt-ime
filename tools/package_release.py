"""Create reviewable archives. Does not access the real Rime user directory."""
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
import csv
import os
import re
import subprocess
from pathlib import Path
from build_windows_installer import build as build_installer

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.8'
LAUNCHER='安装绘画提示词.exe'
SCHEME_FILES=['booru.schema.yaml','booru.dict.yaml','booru.tsv','booru.annotations.tsv','lua/booru_filter.lua']

def check_versions():
    for path, pattern in [
        (ROOT/'rime/booru.schema.yaml', r'(?m)^  version: "([^"]+)"$'),
        (ROOT/'rime/booru.dict.yaml', r'(?m)^version: "([^"]+)"$'),
        (ROOT/'tools/build.py', r"'version: \"([^\"]+)\"'"),
        (ROOT/'tools/windows-installer/main.go', r'var version = "([^"]+)"'),
    ]:
        match=re.search(pattern,path.read_text(encoding='utf-8'))
        if not match or match[1]!=VERSION:
            raise ValueError('Release version mismatch: '+path.relative_to(ROOT).as_posix())

def check_installer(exe, source):
    """Check a reused or newly built EXE only in a disposable user directory."""
    with tempfile.TemporaryDirectory(prefix='ime-package-check-') as tmp:
        base=Path(tmp)
        env=dict(os.environ,APPDATA=str(base/'AppData'))
        def run(*args):
            return subprocess.run([str(exe),*map(str,args)],cwd=base,env=env,
                                  stdin=subprocess.DEVNULL,capture_output=True,
                                  encoding='utf-8',check=True,timeout=30).stdout
        if run('--version').strip()!=f'AI Prompt IME {VERSION} / default / windows-amd64':
            raise ValueError('Installer version or corpus variant does not match this release')
        notices=[ROOT/'LICENSE',*sorted((ROOT/'licenses').iterdir())]
        expected=''.join('\n--- '+p.name+' ---\n'+p.read_text(encoding='utf-8')+'\n'
                         for p in notices if p.is_file())
        if run('--license')!=expected:
            raise ValueError('Installer notices do not match current licenses')
        user=base/'Rime'
        run('--user-dir',user)
        for name in SCHEME_FILES:
            if (user/name).read_bytes()!=(source/name).read_bytes():
                raise ValueError('Installer payload does not match source: '+name)
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
    parser.add_argument('--artifacts-root',type=Path,default=ROOT,help='Raw dictionary root; used only with --include-dictionary')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist',help='Write release ZIPs and their checksum file here')
    parser.add_argument('--go',default='go',help='Go compiler for the native Windows installer')
    parser.add_argument('--installer',type=Path,help='Reuse an accepted EXE instead of compiling; verify version, payload and notices in isolation')
    parser.add_argument('--include-dictionary',action='store_true',help='Also build the optional source trace ZIP; requires --artifacts-root')
    parser.add_argument('--validation-root',type=Path,default=ROOT/'validation/gpt',help='Current data/Lua reports and historical complete-corpus engine baseline')
    parser.add_argument('--prompt-snapshot',type=Path,help='Pinned text-only n714/Physton/e621/MTT source snapshots for the trace archive')
    args=parser.parse_args()
    check_versions()
    installer=args.installer.resolve() if args.installer else None
    artifacts=args.artifacts_root.resolve()
    if args.include_dictionary and not (artifacts/'dictionary').is_dir():
        parser.error('--include-dictionary requires an artifacts root containing dictionary/')
    validation=args.validation_root.resolve()
    dist=args.output_dir.resolve();dist.mkdir(parents=True,exist_ok=True)
    proof=json.loads((validation/'ranking-slang.json').read_text(encoding='utf-8'))
    assert proof['status']=='PASS' and proof['dictionary_sha256']==sha(ROOT/'rime/booru.tsv')
    assert proof['native_dictionary_sha256']==sha(ROOT/'rime/booru.dict.yaml')
    lua=json.loads((validation/'lua-filter-unit.json').read_text(encoding='utf-8'))
    assert lua['status']=='PASS' and lua['lua_sha256']==sha(ROOT/'rime/lua/booru_filter.lua')
    assert lua['dictionary_sha256']==proof['dictionary_sha256']
    assert lua['annotations_sha256']==sha(ROOT/'rime/booru.annotations.tsv')
    latency=json.loads((validation/'latency.json').read_text(encoding='utf-8'))
    assert latency['status']=='PASS' and latency['outputs_identical']
    assert latency['candidate_lua_sha256']==lua['lua_sha256']
    assert latency['dictionary_sha256']==proof['dictionary_sha256']
    assert latency['annotations_sha256']==lua['annotations_sha256']
    pose=json.loads((validation/'pose-phrases.json').read_text(encoding='utf-8'))
    assert pose['status']=='PASS' and pose['dictionary_sha256']==proof['dictionary_sha256']
    assert pose['native_dictionary_sha256']==proof['native_dictionary_sha256']
    archives=[]
    for variant in (['default','dictionary'] if args.include_dictionary else ['default']):
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
                for tool in ['convert_dictionary.py','build.py','import_prompt_libraries.py','ranking.py','annotations.py']:shutil.copy2(ROOT/'tools'/tool,folder/'tools'/tool)
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
                if installer:
                    shutil.copy2(installer,folder/LAUNCHER)
                else:
                    build_installer(src,folder/LAUNCHER,args.go,variant)
                if not (folder/LAUNCHER).is_file():
                    raise FileNotFoundError('Compiled installer disappeared; inspect the build environment before packaging')
                check_installer(folder/LAUNCHER,src)
                (folder/'validation').mkdir()
                # Historical engine evidence is explicitly a baseline; the new
                # candidate has data-coverage and isolated Lua checks, not a new
                # real-input acceptance performed on the user's behalf.
                shutil.copy2(validation/'formal-full-engine.json',folder/'validation/baseline-engine-test.json')
                shutil.copy2(validation/'color-test-full.json',folder/'validation/baseline-color-test.json')
                shutil.copy2(validation/'prompt-test-full.json',folder/'validation/baseline-prompt-test.json')
                for evidence_name in ['ranking-slang.json','lua-filter-unit.json','pose-phrases.json','latency.json']:
                    shutil.copy2(validation/evidence_name,folder/'validation'/evidence_name)
                with (src/'booru.tsv').open(encoding='utf-8') as stream:
                    mappings=sum(1 for _ in csv.DictReader(stream,delimiter='\t'))
                prefix='> 本附件为 '+VERSION+' 方案安装包，完整词库为唯一默认，共 '+str(mappings)+' 条拼音映射。双击本包的 `安装绘画提示词.exe`，无需 Python。打包操作不代表已验收或发布；公开版本与验收状态以对应GitHub Release为准。\n\n'
                (folder/'README.md').write_text(prefix+(ROOT/'README.md').read_text(encoding='utf-8'),encoding='utf-8')
            if variant!='dictionary' and not (folder/LAUNCHER).is_file():
                raise FileNotFoundError('Installer is unavailable; refusing to produce an incomplete scheme archive')
            sums(folder)
            target=dist/(name+'.zip');zip_dir(folder,target);archives.append(target)
            if variant!='dictionary':
                setup=dist/(f'ai-prompt-ime-{VERSION}'+('' if variant=='default' else '-searchable')+'-setup.exe')
                setup.write_bytes((folder/LAUNCHER).read_bytes());archives.append(setup)
    (dist/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in archives),encoding='utf-8')
    print(json.dumps([dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in archives],indent=2))
if __name__=='__main__':main()
