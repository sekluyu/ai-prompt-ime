"""Check all generated color spellings and the spacing hotkey using real librime."""
import importlib.util
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from general_phrases import color_rows, PREFIX
spec=importlib.util.spec_from_file_location('engine_test',ROOT/'tests/engine_test.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def main():
    engine=m.Engine()
    rows=color_rows()
    meanings=defaultdict(set)
    for row in rows:meanings[row['code']].add(row['tag'])
    try:
        for row in rows:
            engine.reset()
            for ch in row['code']: engine.key(ch)
            expected=row['tag'].removeprefix(PREFIX)+', '
            for page in range(100):
                candidates,last=engine.candidates()
                found=next((i for i,c in enumerate(candidates) if c['text']==expected and c['comment']==row['zh']),None)
                if found is not None:break
                if last:raise AssertionError((row,candidates))
                engine.key('=')
            else:raise AssertionError(('too many candidates',row))
            if len(meanings[row['code']])==1:assert page==0 and found==0,(row,candidates[:3])
            engine.key(str(found+1))
            assert engine.commit()==expected,row
        # Exercise the actual configured Control+Alt+F9 binding, not just set_option.
        engine.reset()
        engine.call('process_key',m.I,[m.ID,m.I,m.I],engine.sid,0xffc6,12)
        assert not engine.call('get_option',m.I,[m.ID,m.S],engine.sid,b'booru_space')
        for ch in 'huangbaipeise': engine.key(ch)
        engine.key(' ')
        assert engine.commit()=='yellow and white color scheme,'
        engine.call('process_key',m.I,[m.ID,m.I,m.I],engine.sid,0xffc6,12)
        assert engine.call('get_option',m.I,[m.ID,m.S],engine.sid,b'booru_space')
        for ch in 'huangse': engine.key(ch)
        engine.key(' ')
        assert engine.commit()=='yellow, '
        engine.call('set_option',None,[m.ID,m.S,m.I],engine.sid,b'booru_separator',0)
        for ch in 'baise': engine.key(ch)
        engine.key(' ')
        assert engine.commit()=='white'
        report=dict(status='PASS',color_mappings=len(rows),general_phrases=len({r['tag'] for r in rows}),ambiguous_color_codes=sum(len(tags)>1 for tags in meanings.values()),checks=['all generated spellings: marked comment + actual selection; unique color codes first candidate, ambiguous codes selectable','real Control+Alt+F9 switches only trailing space','comma retained when space disabled','plain mode retained'],source_variant=os.environ.get('BOORU_TEST_VARIANT','default'))
        target=ROOT/'validation/gpt'/('color-test-'+report['source_variant']+'.json')
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False))
    finally:
        engine.close()

if __name__=='__main__':main()
