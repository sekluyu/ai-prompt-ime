"""Build a Windows x64 installer with its dictionary embedded; no runtime download."""
import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build(source, output, go='go', variant='default', test=False):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, CGO_ENABLED='0', GOOS='windows', GOARCH='amd64',
               GOWORK='off', GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off')
    with tempfile.TemporaryDirectory(prefix='ai-prompt-ime-native-') as temp:
        stage = Path(temp)
        for path in (ROOT/'tools/windows-installer').iterdir():
            if path.is_file():
                shutil.copy2(path, stage/path.name)
        shutil.copytree(source, stage/'payload')
        (stage/'notices').mkdir()
        shutil.copy2(ROOT/'LICENSE', stage/'notices/LICENSE')
        for name in ['ffdkj-LICENSE.txt', 'go-LICENSE.txt', 'go-PATENTS.txt']:
            shutil.copy2(ROOT/'licenses'/name, stage/'notices'/name)
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
