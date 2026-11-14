"""Check reviewed corrections, unchanged entries and actual template commits."""
import argparse,csv,ctypes as C,hashlib,io,json,os,re,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from term_repairs import repair_rows,expansion_rows,repair_target_keys
from general_phrases import pose_rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',action='store_true');p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','v0.2.8:rime/booru.tsv'],cwd=ROOT).decode()),delimiter='\t'))
    rows=list(csv.DictReader((ROOT/'rime/booru.tsv').open(encoding='utf-8'),delimiter='\t'))
    key=lambda r:(r['code'],r['tag'].removeprefix('__prompt__:'))
    current={key(r):r for r in rows}
    assert len(current)==len(rows)
    repaired=repair_rows(old)
    expected={key(r) for r in repaired}|{key(r) for r in expansion_rows()+pose_rows()}
    assert set(current)==expected,'An unreviewed lookup was removed or added'
    changed=repair_target_keys()|{key(r) for r in expansion_rows()+pose_rows()}
    for prior in repaired:
        if key(prior) not in changed:
            assert current[key(prior)]==prior,('Unrelated entry changed',prior,current[key(prior)])
    for code,en in [('cuowudefuji','bad abs'),('duogenweiba','multiple_tails'),('lianggenweiba','two_tails'),('sangenweiba','3_tails'),('changweiba','long_tail'),('dimawei','low_ponytail'),('cemawei','side_ponytail')]:
        assert (code,en) in current,(code,en)
    for pair in [('fuji','absolute_territory'),('qingxilunkuo','detailed_bulge'),('shuangmayi','two_tails'),('shuangmayi','2_tails'),('dimayi','low_ponytail'),('zhangweiba','long_tail')]:
        assert pair not in current,pair
    results=[]
    if a.engine:
        sys.path.insert(0,str(ROOT/'tests'))
        from engine_test import Engine
        a.output_dir.mkdir(parents=True,exist_ok=True)
        os.environ['BOORU_TEST_USER']=str(a.output_dir/'runtime')
        os.environ['BOORU_TEST_LOG']=str(a.output_dir)
        engine=Engine()
        def choose(code,en,first=False):
            engine.reset()
            for ch in code:engine.key(ch)
            suffix=' ' if '〔待续写〕' in current[(code,en)]['zh'] else ', '
            text=re.sub(r'([\\()])',r'\\\1',en)+suffix
            for page in range(1000):
                candidates,last=engine.candidates()
                index=next((i for i,r in enumerate(candidates) if r['text']==text),None)
                if index is not None:break
                assert not last,('Missing candidate',code,en,candidates)
                engine.key('=')
            else:raise AssertionError(('Too many pages',code,en))
            if first:assert page==0 and index==0,(code,candidates)
            engine.key(str(index+1));assert engine.commit()==text
            results.append(dict(code=code,output=text))
        try:
            # Every new or corrected pair, including aliases that land on later pages.
            before={key(r) for r in old}
            for code,en in sorted(set(current)-before):choose(code,en)
            templates=[r for r in expansion_rows() if '〔常用组合〕' in r['zh']]
            for code in ['zhengmian','fumian']:
                selected=max((r for r in templates if r['code']==code),key=lambda r:int(r['weight']))
                choose(code,selected['tag'].removeprefix('__prompt__:'),first=True)
            for r in templates:
                if r['code'] in ['zhengmian','fumian']:continue
                text=r['tag'].removeprefix('__prompt__:')
                for separator,space in [(True,True),(True,False),(False,False)]:
                    engine.reset()
                    for option,value in [('booru_separator',separator),('booru_space',space)]:
                        engine.call('set_option',None,[C.c_size_t,C.c_char_p,C.c_int],engine.sid,option.encode(),int(value))
                    for ch in r['code']:engine.key(ch)
                    engine.key(' ')
                    expected=text+(','+(' ' if space else '') if separator else '')
                    assert engine.commit()==expected,(r['code'],separator,space)
            engine.call('set_option',None,[C.c_size_t,C.c_char_p,C.c_int],engine.sid,b'booru_separator',1)
            engine.call('set_option',None,[C.c_size_t,C.c_char_p,C.c_int],engine.sid,b'booru_space',1)
        finally:engine.close()
    report=dict(status='PASS',baseline='v0.2.8',baseline_rows=len(old),rows=len(rows),added_pairs=len(set(current)-{key(r) for r in old}),removed_or_replaced_pairs=len({key(r) for r in old}-set(current)),all_changes_covered_by_reviewed_data=True,engine_pairs_checked=len(results),dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest(),results=results)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'term-repairs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=True))

if __name__=='__main__':main()
