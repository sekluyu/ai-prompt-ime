"""Exercise a standalone EXE only in disposable directories, with PATH empty."""
import argparse
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['booru.schema.yaml', 'booru.dict.yaml', 'booru.tsv', 'lua/booru_filter.lua']
spec = importlib.util.spec_from_file_location('legacy_installer', ROOT/'tools/install.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'rime')
    args = parser.parse_args()
    # Native PE64, with no CLR header (.NET runtime entry).
    pe = args.exe.read_bytes()
    offset = struct.unpack_from('<I', pe, 0x3c)[0]
    assert pe[offset:offset+4] == b'PE\0\0'
    assert struct.unpack_from('<H', pe, offset+4)[0] == 0x8664
    optional = offset+24
    assert struct.unpack_from('<H', pe, optional)[0] == 0x20b
    assert struct.unpack_from('<II', pe, optional+112+14*8) == (0, 0), 'EXE requires the CLR'
    with tempfile.TemporaryDirectory(prefix='ime-native-') as tmp:
        base = Path(tmp)/'中文路径 with spaces'
        base.mkdir()
        exe = base/'独立安装.exe'
        shutil.copy2(args.exe, exe)
        empty_path = base/'empty-path'
        empty_path.mkdir()
        appdata = base/'模拟 AppData'
        env = dict(os.environ, PATH=str(empty_path), APPDATA=str(appdata))
        def run(*options, ok=True):
            p = subprocess.run([str(exe), *map(str, options)], cwd=base, env=env,
                               stdin=subprocess.DEVNULL, capture_output=True,
                               encoding='utf-8', timeout=30)
            assert (p.returncode == 0) == ok, p.stdout+p.stderr
            return p
        for option in ['--help', '--version', '--license']:
            output = run(option)
            assert output.stdout or output.stderr
        license_text = run('--license').stdout
        for text in ['MIT License', 'ffdkj', 'Google', 'DeepSeek', 'Physton', 'n714-LICENSE', 'e621-archive-UNLICENSE', 'mtt-search-LICENSE']:
            assert text in license_text
        assert not appdata.exists(), 'Read-only options touched the user directory'

        installed=run()  # Default APPDATA directory, with the EXE alone and no Python on PATH.
        assert '【安装成功】绘画提示词文件已复制到小狼毫用户文件夹。' in installed.stdout
        assert '【请完成最后一步，让新版本生效】' in installed.stdout and '重新部署' in installed.stdout
        assert installed.stdout.index('请完成最后一步') < installed.stdout.index('安装前状态已备份到')
        assert '未安装或替换小狼毫' not in installed.stdout
        variant=run('--version').stdout.split('/')[1].strip()
        assert ('扩展词库' if variant=='searchable' else '默认词库') in installed.stdout
        user = appdata/'Rime'
        for name in FILES:
            assert (user/name).read_bytes() == (args.source/name).read_bytes(), name
        run('--rollback-latest')
        assert not (user/'default.custom.yaml').exists()
        assert not (user/'booru-last-backup.txt').exists()
        assert (user/'booru-backups').is_dir()

        user = base/'自定义 Rime 用户目录'
        user.mkdir()
        original = b'\xef\xbb\xbf# preserve\r\npatch:\r\n  schema_list:\r\n    - {schema: luna_pinyin}\r\n  menu/page_size: 9\r\n'
        config = user/'default.custom.yaml'
        config.write_bytes(original)
        (user/'booru.tsv').write_bytes(b'old dictionary')
        (user/'weasel.custom.yaml').write_bytes(b'untouched')
        run('--user-dir', str(user)+'\\')
        first = (user/'booru-last-backup.txt').read_text(encoding='utf-8')
        run('--user-dir', user)
        assert config.read_bytes().count(b'schema: booru') == 1
        run('--user-dir', user, '--rollback-latest')
        assert (user/'booru-last-backup.txt').read_text(encoding='utf-8') == first
        run('--user-dir', user, '--rollback-latest')
        assert config.read_bytes() == original
        assert (user/'booru.tsv').read_bytes() == b'old dictionary'
        assert (user/'weasel.custom.yaml').read_bytes() == b'untouched'

        # Python 0.2.0 backups and native backups remain mutually readable.
        old_manifest = legacy.install(user)
        run('--rollback', old_manifest)
        assert config.read_bytes() == original
        run('--user-dir', user)
        native_manifest = Path((user/'booru-last-backup.txt').read_text(encoding='utf-8'))
        legacy.rollback(native_manifest)
        assert config.read_bytes() == original

        unfamiliar = base/'unfamiliar'
        unfamiliar.mkdir()
        (unfamiliar/'default.custom.yaml').write_bytes(b'patch: {schema_list: [{schema: luna_pinyin}]}')
        before = {p.name:p.read_bytes() for p in unfamiliar.iterdir()}
        run('--user-dir', unfamiliar, ok=False)
        assert {p.name:p.read_bytes() for p in unfamiliar.iterdir()} == before
        run('--user-dir', unfamiliar, '--unknown-option', ok=False)
        run('--user-dir', unfamiliar, '--rollback-latest', '--rollback', first, ok=False)
        assert {p.name:p.read_bytes() for p in unfamiliar.iterdir()} == before

        conflict = base/'conflict'
        run('--user-dir', conflict)
        (conflict/'booru.tsv').write_bytes(b'manual change')
        snapshot = {p.relative_to(conflict).as_posix():p.read_bytes() for p in conflict.rglob('*') if p.is_file()}
        run('--user-dir', conflict, '--rollback-latest', ok=False)
        assert {p.relative_to(conflict).as_posix():p.read_bytes() for p in conflict.rglob('*') if p.is_file()} == snapshot

        # Check manifest path whitelisting before any managed file is restored.
        run('--user-dir', conflict)
        manifest_path = Path((conflict/'booru-last-backup.txt').read_text(encoding='utf-8'))
        m = json.loads(manifest_path.read_text(encoding='utf-8'))
        m['files'][-1]['name'] = '../unrelated.txt'
        manifest_path.write_text(json.dumps(m), encoding='utf-8')
        snapshot = {p.relative_to(conflict).as_posix():p.read_bytes() for p in conflict.rglob('*') if p.is_file()}
        run('--rollback', manifest_path, ok=False)
        assert {p.relative_to(conflict).as_posix():p.read_bytes() for p in conflict.rglob('*') if p.is_file()} == snapshot

    print('PASS: native PE64/no CLR; standalone install and rollback with empty PATH; exact embedded data; BOM/CRLF; backup chain; Python backup compatibility both directions; config/conflict/argument/manifest refusal without writes')

if __name__ == '__main__':
    main()
