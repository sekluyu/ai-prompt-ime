"""Build a Windows x64 installer with its dictionary embedded; no runtime download."""
import argparse
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def write_resources(source, target):
    """Use a standard, deterministic ZIP; no encryption or external unpacker."""
    resources = [('payload/'+p.relative_to(source).as_posix(), p)
                 for p in sorted(source.rglob('*')) if p.is_file()]
    resources.append(('notices/LICENSE', ROOT/'LICENSE'))
    resources.extend(('notices/'+p.name, p) for p in sorted((ROOT/'licenses').iterdir()) if p.is_file())
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in resources:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

def build(source, output, go='go', variant='default', test=False):
    source = Path(source).resolve()
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, CGO_ENABLED='0', GOOS='windows', GOARCH='amd64',
               GOWORK='off', GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off')
    with tempfile.TemporaryDirectory(prefix='ai-prompt-ime-native-') as temp:
        stage = Path(temp)
        for path in (ROOT/'tools/windows-installer').iterdir():
            if path.is_file():
                shutil.copy2(path, stage/path.name)
        write_resources(source, stage/'resources.zip')
        if test:
            subprocess.run([str(go), 'test', '-count=1', '-v', '.'], cwd=stage, env=env, check=True)
        subprocess.run([str(go), 'build', '-trimpath', '-buildvcs=false',
                        '-ldflags=-s -w -X main.variant='+variant, '-o', str(output), '.'],
                       cwd=stage, env=env, check=True)
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'rime')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--go', default='go')
    parser.add_argument('--variant', choices=['default', 'searchable'], default='default')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    print(build(args.source, args.output, args.go, args.variant, args.test))
