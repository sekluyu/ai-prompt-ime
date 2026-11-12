"""Install only this scheme; back up managed files and preserve unrelated settings."""
import argparse
import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=['booru.schema.yaml','booru.dict.yaml','booru.tsv','lua/booru_filter.lua']
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def updated_config(text):
    if re.search(r'(?m)^\s*-\s*\{\s*schema:\s*[\'"]?booru[\'"]?\s*\}\s*(?:#.*)?$',text): return text
    newline='\r\n' if '\r\n' in text else '\n'
    # Preserve the user's schema list and all comments; accept the ordinary block layout.
    matches=list(re.finditer(r'^  schema_list:[ \t]*(?:#[^\r\n]*)?(?:\r?\n|$)',text,re.M))
    if len(matches)==1:
        end=matches[0].end()
        return text[:end]+('' if text[:end].endswith('\n') else newline)+'    - {schema: booru}'+newline+text[end:]
    if not text.strip(): return 'patch:'+newline+'  schema_list/+:'+newline+'    - {schema: booru}'+newline
    if len(re.findall(r'^patch:[ \t]*(?:\r?\n|$)',text,re.M))==1 and not re.search(r'schema_list',text):
        return re.sub(r'(^patch:[ \t]*(?:\r?\n|$))',lambda m:m.group(1)+('' if m.group(1).endswith('\n') else newline)+'  schema_list/+:'+newline+'    - {schema: booru}'+newline,text,count=1,flags=re.M)
    raise ValueError('Unrecognized default.custom.yaml layout; no files changed. Add booru to schema_list manually, then retry.')

def install(user):
    sources=[ROOT/'rime'/name for name in FILES]
    for source in sources:
        if not source.is_file(): raise FileNotFoundError(source)
    config=user/'default.custom.yaml'
    old=config.read_bytes() if config.exists() else None
    new=updated_config(old.decode('utf-8-sig') if old else '').encode('utf-8')
    # Complete preflight before any user-directory mutation.
    user.mkdir(parents=True,exist_ok=True)
    backup=user/'booru-backups'/str(time.time_ns()); backup.mkdir(parents=True)
    names=FILES+['default.custom.yaml']
    marker=user/'booru-last-backup.txt'
    previous=marker.read_text(encoding='utf-8').strip() if marker.exists() else None
    manifest={'user_dir':str(user.resolve()),'files':[],'created_at':time.strftime('%Y-%m-%d %H:%M:%S'),'previous_manifest':previous}
    for name in names:
        dest=user/name
        item={'name':name,'existed':dest.exists()}
        if dest.exists():
            saved=backup/name; saved.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(dest,saved)
        manifest['files'].append(item)
    manifest_path=backup/'manifest.json'
    # Save recovery information before writing managed files.
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in FILES:
        dest=user/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/'rime'/name,dest)
    config.write_bytes(new)
    for item in manifest['files']: item['installed_sha256']=digest(user/item['name'])
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    marker.write_text(str(manifest_path),encoding='utf-8')
    version=re.search(r'(?m)^\s+version:\s*[\'"]?([^\s\'"]+)',(ROOT/'rime/booru.schema.yaml').read_text(encoding='utf-8'))
    print('【安装成功】绘画提示词文件已复制到小狼毫用户文件夹。')
    package=ROOT/'PACKAGE_INFO.json'
    variant=json.loads(package.read_text(encoding='utf-8')).get('variant','default') if package.is_file() else 'default'
    print('本次安装：v'+(version.group(1) if version else '未标记')+' · '+('扩展词库' if variant=='searchable' else '默认词库')+'。\n')
    print('【请完成最后一步，让新版本生效】')
    print('1. 右键点击任务栏右下角的小狼毫图标，选择“重新部署”。')
    print('2. 等待部署完成后，按 F4，选择“绘画提示词”即可使用。')
    print('\n这是依托小狼毫运行的提示词输入方案，使用前需要已安装小狼毫。')
    print('安装前状态已备份到：'+str(manifest_path))
    return manifest_path

def rollback(manifest_path):
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')); user=Path(manifest['user_dir'])
    for item in manifest['files']:
        name=item['name']
        if name not in FILES+['default.custom.yaml']: raise ValueError('Unexpected file in manifest')
        dest=user/name
        if not dest.exists() or digest(dest)!=item.get('installed_sha256'):
            raise ValueError('File changed after install; preserve current work and merge manually: '+str(dest))
        if item['existed'] and not (manifest_path.parent/name).is_file(): raise FileNotFoundError(name)
    for item in manifest['files']:
        dest=user/item['name']
        if item['existed']: shutil.copy2(manifest_path.parent/item['name'],dest)
        elif dest.exists(): dest.unlink()
    marker=user/'booru-last-backup.txt'
    if marker.exists() and marker.read_text(encoding='utf-8').strip()==str(manifest_path):
        if manifest.get('previous_manifest'): marker.write_text(manifest['previous_manifest'],encoding='utf-8')
        else: marker.unlink()
    print('Restored managed files. Redeploy Weasel to refresh its compiled cache.')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--user-dir',type=Path,default=Path(os.environ.get('APPDATA','.'))/'Rime'); p.add_argument('--rollback',type=Path); p.add_argument('--rollback-latest',action='store_true')
    args=p.parse_args()
    if args.rollback_latest: rollback(Path((args.user_dir/'booru-last-backup.txt').read_text(encoding='utf-8').strip()))
    elif args.rollback: rollback(args.rollback)
    else: install(args.user_dir)
