"""Validate imported coverage and exercise representative entries with librime."""
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import general_phrases as phrases

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',action='store_true');a=p.parse_args()
    report=json.loads((ROOT/'data/library_sources.json').read_text(encoding='utf-8'))
    packed=(ROOT/'data/imported_terms.tsv.gz').read_bytes()
    assert hashlib.sha256(packed).hexdigest()==report['generated_sha256']
    raw=gzip.decompress(packed)
    assert hashlib.sha256(raw).hexdigest()==report['uncompressed_sha256']
    assert {s['key'] for s in report['sources']}=={'n714','e621','mtt','physton'}
    with gzip.open(ROOT/'data/imported_terms.tsv.gz','rt',encoding='utf-8') as f: imported=list(csv.DictReader(f,delimiter='\t'))
    assert len(imported)==report['counts']['output:mappings']
    assert len({(r['tag'],r['code']) for r in imported})==len(imported)
    for row in imported:
        assert re.fullmatch('[a-z]+',row['code']) and row['tag'] and row['zh']
        assert not any(c in row['tag']+row['zh'] for c in '\t\r\n\0')
        assert 0<=int(row['weight'])<=9999
    source=Path(os.environ.get('BOORU_TEST_SOURCE',str(ROOT/'rime')))
    rows=list(csv.DictReader((source/'booru.tsv').open(encoding='utf-8'),delimiter='\t'))
    runtime={(r['tag'],r['code']):r for r in rows}
    assert len(runtime)==len(rows)
    by_output={(r['code'],r['tag'].removeprefix(phrases.PREFIX)):r for r in rows}
    assert len(by_output)==len(rows),'Duplicate final English output for the same pinyin'
    if os.environ.get('BOORU_TEST_VARIANT','default')=='default':
        import io
        baseline=subprocess.check_output(['git','show','v0.2.2:rime/booru.tsv'],cwd=ROOT).decode('utf-8')
        old=list(csv.DictReader(io.StringIO(baseline),delimiter='\t'))
        for row in old:
            if not row['tag'].startswith(phrases.PREFIX):
                actual=by_output[(row['code'],row['tag'])]
                assert int(actual['weight'])>=int(row['weight'])
    for name in ['n714-LICENSE.txt','e621-archive-UNLICENSE.txt','mtt-search-LICENSE.txt','physton-LICENSE.txt']:assert (ROOT/'licenses'/name).is_file()
    if not a.engine:
        print(json.dumps({'status':'PASS','static_import_mappings':len(imported),'runtime_mappings':len(rows)},ensure_ascii=False));return
    spec=importlib.util.spec_from_file_location('native_engine',ROOT/'tests/engine_test.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=module.Engine()
    labels={};weights={}
    for r in rows:
        if r['tag'] not in labels or int(r['weight'])>weights[r['tag']]:labels[r['tag']]=r['zh'];weights[r['tag']]=int(r['weight'])
    results=[]
    def select(code,text,label=None,first=False):
        engine.reset()
        for ch in code:engine.key(ch)
        expected=re.sub(r'([\\()])',r'\\\1',text)+', '
        for page in range(1000):
            candidates,last=engine.candidates()
            found=next((i for i,c in enumerate(candidates) if c['text']==expected and (label is None or c['comment']==label)),None)
            if found is not None:break
            if last:raise AssertionError((code,text,'candidate missing'))
            engine.key('=')
        else:raise AssertionError((code,text,'too many ambiguous candidates'))
        if first:assert page==0 and found==0,(code,candidates[:3])
        engine.key(str(found+1))
        assert engine.commit()==expected,(code,text)
        results.append({'code':code,'text':text})
    try:
        required={'zhilianggenggao':'high quality','gaozhiliang':'high quality','tigaozhiliang':'high quality','jiezuo':'masterpiece','dashiji':'masterpiece','zuijiazhiliang':'best quality','zuijiahuazhi':'best quality','zhenshipifu':'realistic skin','zhenshipimao':'realistic fur','zhenshimaopi':'realistic fur','zhenshimaofa':'realistic fur','maofaxijie':'detailed fur','furui':'furry','shouren':'anthro','roudian':'pawpads','jinchengse':'golden orange','naiyouse':'cream','jinchengnaiyousepimao':'golden orange and cream fur','jinchengyunaiyousepimao':'golden orange and cream fur','jinchengsehe-naiyousepimao'.replace('-',''):'golden orange and cream fur','jinchengseyu-naiyousede-pimao'.replace('-',''):'golden orange and cream fur','huangbaipeise':'yellow and white color scheme','texie':'close-up'}
        for code,text in required.items():select(code,text,first=True)
        quote_cases=[row for row in rows if '"' in row['tag'] or '"' in row['zh']]
        for row in quote_cases[:24]:select(row['code'],row['tag'].removeprefix(phrases.PREFIX),labels[row['tag']])
        for row in phrases.prompt_rows():
            actual=by_output[(row['code'],row['tag'].removeprefix(phrases.PREFIX))]
            select(row['code'],row['tag'].removeprefix(phrases.PREFIX),labels[actual['tag']])
        fur=phrases.fur_color_rows()
        for row in fur[::max(1,len(fur)//96)]:
            actual=by_output[(row['code'],row['tag'].removeprefix(phrases.PREFIX))]
            select(row['code'],row['tag'].removeprefix(phrases.PREFIX),labels[actual['tag']])
        variant='searchable' if os.environ.get('BOORU_TEST_VARIANT')=='full' else 'default'
        libs=phrases.library_rows(variant)
        sample_counts={}
        for name in ['n714','physton','mtt','e621+mtt']:
            unique={}
            for row in libs:
                if name not in row['source'].split(';') or (row['code'],row['tag'].removeprefix(phrases.PREFIX)) not in by_output:continue
                if row['tag'] not in unique or len(row['code'])>len(unique[row['tag']]['code']):unique[row['tag']]=row
            choices=sorted(unique.values(),key=lambda r:r['tag'])
            chosen=[choices[i*len(choices)//min(24,len(choices))] for i in range(min(24,len(choices)))]
            assert chosen,name
            for row in chosen:
                actual=by_output[(row['code'],row['tag'].removeprefix(phrases.PREFIX))]
                select(row['code'],row['tag'].removeprefix(phrases.PREFIX),labels[actual['tag']])
            sample_counts[name]=len(chosen)
        # Pure mode and space-only shortcut also apply to the new multiword fur phrase.
        engine.reset();engine.call('process_key',module.I,[module.ID,module.I,module.I],engine.sid,0xffc6,12)
        for ch in 'jinchengnaiyousepimao':engine.key(ch)
        engine.key(' ');assert engine.commit()=='golden orange and cream fur,'
        engine.call('set_option',None,[module.ID,module.S,module.I],engine.sid,b'booru_separator',0)
        for ch in 'jiezuo':engine.key(ch)
        engine.key(' ');assert engine.commit()=='masterpiece'
        evidence={'status':'PASS','variant':variant,'required_cases':len(required),'curated_spellings':len(phrases.prompt_rows()),'fur_color_samples':len(fur[::max(1,len(fur)//96)]),'library_samples':sample_counts,'quoted_field_samples':min(24,len(quote_cases)),'native_selections':len(results),'checks':['priority Chinese terms first candidate','curated aliases including zhi/zhua/zhao ambiguity','source-stratified native candidate selection','tone+fur output is not color scheme','comma retained with spacing disabled','plain mode'],'limitation':'Input/output checks, not generated-image quality or desktop TSF acceptance'}
        target=ROOT/'validation/gpt'/('prompt-test-'+os.environ.get('BOORU_TEST_VARIANT','default')+'.json')
        target.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(evidence,ensure_ascii=False))
    finally:engine.close()

if __name__=='__main__':main()
