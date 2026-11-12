import importlib.util
import tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('install',Path(__file__).resolve().parents[1]/'tools/install.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def main():
    original=b'# preserve comment\r\npatch:\r\n  schema_list:\r\n    - {schema: luna_pinyin}\r\n  menu/page_size: 9\r\n'
    with tempfile.TemporaryDirectory() as tmp:
        user=Path(tmp); config=user/'default.custom.yaml'; config.write_bytes(original)
        untouched=user/'weasel.custom.yaml'; untouched.write_bytes(b'unchanged')
        existing=user/'booru.tsv'; existing.write_bytes(b'previous version')
        manifest=m.install(user)
        assert b'luna_pinyin' in config.read_bytes() and b'menu/page_size: 9' in config.read_bytes()
        assert config.read_bytes().count(b'schema: booru')==1
        assert b'schema_list:\r\n    - {schema: booru}\r\n' in config.read_bytes()
        assert b'\r\r\n' not in config.read_bytes()
        assert m.updated_config(config.read_text())==config.read_text()
        m.rollback(manifest)
        assert config.read_bytes()==original
        assert existing.read_bytes()==b'previous version'
        assert untouched.read_bytes()==b'unchanged'
        assert not (user/'booru.schema.yaml').exists()
        assert not (user/'booru-last-backup.txt').exists()
    assert 'schema_list/+' in m.updated_config('')
    assert 'schema_list/+' in m.updated_config('patch:\n  menu/page_size: 9\n')
    try: m.updated_config('patch: {schema_list: [{schema: luna_pinyin}]}')
    except ValueError: pass
    else: raise AssertionError('Unsupported syntax should stop without writes')
    print('PASS: install, preserve unrelated settings, idempotent config, rollback, unfamiliar layout refusal')

if __name__=='__main__': main()
