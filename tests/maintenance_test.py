"""Check complete builds and release packaging in disposable directories only."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import package_release


def run(script,*args,ok=True):
    result=subprocess.run([sys.executable,str(ROOT/script),*map(str,args)],
                          cwd=ROOT,stdin=subprocess.DEVNULL,capture_output=True,
                          encoding='utf-8',timeout=120)
    if (result.returncode==0)!=ok:
        raise AssertionError(result.stdout+result.stderr)
    return result


class MaintenanceTests(unittest.TestCase):
    installer=None
    go=None

    def test_complete_default_build_and_demo_boundary(self):
        originals={name:(ROOT/'rime'/name).read_bytes()
                   for name in ['booru.tsv','booru.dict.yaml']}
        report=ROOT/'validation/gpt/build.json'
        prior_report=report.read_bytes() if report.exists() else None
        with tempfile.TemporaryDirectory(prefix='ime-build-test-') as tmp:
            output=Path(tmp)/'complete'
            for _ in range(2):
                run('tools/build.py','--output-dir',output)
                for name,data in originals.items():
                    self.assertEqual((output/name).read_bytes(),data,name)
            for args in [('--demo',),('--demo','--output-dir',ROOT/'rime'),
                         ('--demo','--output-dir',ROOT/'rime/demo'),
                         ('--demo','--source',ROOT/'rime/booru.tsv')]:
                run('tools/build.py',*args,ok=False)
            run('tools/build.py','--source',Path(tmp)/'missing.tsv',
                '--output-dir',Path(tmp)/'missing',ok=False)
            self.assertFalse((Path(tmp)/'missing').exists())
            demo=Path(tmp)/'demo'
            run('tools/build.py','--demo','--output-dir',demo)
            self.assertLess((demo/'booru.tsv').stat().st_size,len(originals['booru.tsv']))
        for name,data in originals.items():
            self.assertEqual((ROOT/'rime'/name).read_bytes(),data,name)
        self.assertEqual(report.read_bytes() if report.exists() else None,prior_report)

    def test_version_mismatch_is_rejected(self):
        package_release.check_versions()
        with patch.object(package_release,'VERSION','mismatched-version'):
            with self.assertRaisesRegex(ValueError,'version mismatch'):
                package_release.check_versions()

    def check_package(self,folder,expected_exe=None):
        version=package_release.VERSION
        self.assertEqual({p.name for p in folder.iterdir()},
                         {f'ai-prompt-ime-{version}.zip',
                          f'ai-prompt-ime-{version}-setup.exe','SHA256SUMS.txt'})
        exe=(folder/f'ai-prompt-ime-{version}-setup.exe').read_bytes()
        if expected_exe is not None:
            self.assertEqual(exe,expected_exe)
        for line in (folder/'SHA256SUMS.txt').read_text().splitlines():
            digest,name=line.split('  ',1)
            self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),digest)
        with zipfile.ZipFile(folder/f'ai-prompt-ime-{version}.zip') as archive:
            self.assertIsNone(archive.testzip())
            prefix=f'ai-prompt-ime-{version}/'
            self.assertEqual(archive.read(prefix+package_release.LAUNCHER),exe)
            manifest=archive.read(prefix+'SHA256SUMS.txt').decode('utf-8')
            for line in manifest.splitlines():
                digest,name=line.split('  ',1)
                self.assertEqual(hashlib.sha256(archive.read(prefix+name)).hexdigest(),digest)
            readme=archive.read(prefix+'README.md').decode('utf-8')
            self.assertNotIn('尚未发布GitHub',readme)
            self.assertIn('打包操作不代表已验收或发布',readme)
            self.assertFalse(any('/dictionary/' in name for name in archive.namelist()))
            for name in package_release.SCHEME_FILES:
                self.assertEqual(archive.read(prefix+'rime/'+name),(ROOT/'rime'/name).read_bytes())

    def test_reuse_installer_without_raw_dictionary(self):
        if self.installer is None:
            self.skipTest('Pass --installer <accepted EXE> for packaging integration')
        with tempfile.TemporaryDirectory(prefix='ime-reuse-test-') as tmp:
            base=Path(tmp)
            run('tools/package_release.py','--installer',self.installer,
                '--artifacts-root',base/'no-raw-dictionary','--output-dir',base/'package')
            self.check_package(base/'package',self.installer.read_bytes())
            # Optional trace packaging still works with explicitly supplied data.
            raw=base/'artifacts/dictionary'
            raw.mkdir(parents=True)
            (raw/'fixture.txt').write_text('trace fixture',encoding='utf-8')
            run('tools/package_release.py','--installer',self.installer,
                '--include-dictionary','--artifacts-root',raw.parent,
                '--output-dir',base/'with-trace')
            trace=base/'with-trace'/f'ai-prompt-ime-{package_release.VERSION}-dictionary.zip'
            with zipfile.ZipFile(trace) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(archive.read(f'ai-prompt-ime-{package_release.VERSION}-dictionary/dictionary/fixture.txt'),b'trace fixture')
            run('tools/package_release.py','--include-dictionary',
                '--artifacts-root',base/'missing','--output-dir',base/'failed',ok=False)
            self.assertFalse((base/'failed').exists())
            source=base/'changed-source'
            source.mkdir()
            # A same-version EXE must still reject different scheme content.
            (source/'booru.schema.yaml').write_text('different scheme',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'payload does not match'):
                package_release.check_installer(self.installer,source)

    def test_compile_installer_without_raw_dictionary(self):
        if self.go is None:
            self.skipTest('Pass --go <go.exe> for compiler packaging integration')
        with tempfile.TemporaryDirectory(prefix='ime-compile-test-') as tmp:
            base=Path(tmp)
            run('tools/package_release.py','--go',self.go,
                '--artifacts-root',base/'no-raw-dictionary','--output-dir',base/'package')
            self.check_package(base/'package')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer',type=Path)
    parser.add_argument('--go',type=Path)
    args,rest=parser.parse_known_args()
    MaintenanceTests.installer=args.installer.resolve() if args.installer else None
    MaintenanceTests.go=args.go.resolve() if args.go else None
    unittest.main(argv=[sys.argv[0],*rest])
