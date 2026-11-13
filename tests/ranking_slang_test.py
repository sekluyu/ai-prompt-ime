"""Validate data/ranking and explicit project phrases against Git; no Rime session."""
import csv,hashlib,io,json,re,subprocess,sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ranking import chinese_group,compiled_weights
from general_phrases import slang_rows,pose_rows,PREFIX

def main():
    baseline=subprocess.check_output(['git','show','v0.2.3:rime/booru.tsv'],cwd=ROOT)
    old=list(csv.DictReader(io.StringIO(baseline.decode('utf-8-sig')),delimiter='\t'))
    with (ROOT/'rime/booru.tsv').open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream,delimiter='\t'))
    lookup=lambda row:(row['code'],row['tag'].removeprefix(PREFIX))
    previous={lookup(row):row for row in old};current={lookup(row):row for row in rows}
    assert len(rows)==len(current),'Duplicate final output for one pinyin'
    assert set(previous)<=set(current),'An existing lookup/output was removed'
    allowed={lookup(row) for row in slang_rows()+pose_rows()}
    assert set(current)-set(previous)==allowed-set(previous),'Unexpected extra lookup'
    for key,row in current.items():
        assert row['role'] in {'primary','alias'} and re.fullmatch('[a-z]+',row['code'])
        if key in previous:
            assert int(row['weight'])>=int(previous[key]['weight'])
            if key not in allowed:assert row['weight']==previous[key]['weight'],'Unrelated original heat changed'
    native={}
    for line in (ROOT/'rime/booru.dict.yaml').read_text(encoding='utf-8').split('...\n',1)[1].splitlines():
        tag,code,value=line.split('\t');native[(tag,code)]=int(value)
    assert len(native)==len(rows) and native==compiled_weights(rows)
    assert len(set(native.values()))==len(rows) and min(native.values())>0
    by_code=defaultdict(list)
    for row in rows:by_code[row['code']].append(row)
    for code,items in by_code.items():
        primaries=[native[(r['tag'],code)] for r in items if r['role']=='primary']
        aliases=[native[(r['tag'],code)] for r in items if r['role']=='alias']
        if primaries and aliases:assert min(primaries)>max(aliases),code
        for role in ['primary','alias']:
            ordered=sorted((r for r in items if r['role']==role),key=lambda r:-native[(r['tag'],code)])
            seen=set();last=None
            for row in ordered:
                group=chinese_group(row['zh'])
                if group!=last:assert group not in seen,(code,role,group);seen.add(group);last=group
    def ordered(code):return sorted(by_code[code],key=lambda row:-native[(row['tag'],code)])
    assert [lookup(row)[1] for row in ordered('huli')[:2]]==['fox','nursing']
    assert lookup(ordered('baifa')[0])[1]=='white_hair'
    assert lookup(ordered('bi')[0])[1]=='pussy'
    assert lookup(ordered('piyan')[0])[1]=='anus'
    assert lookup(ordered('jiba')[0])[1]=='penis'
    assert lookup(ordered('diao')[0])[1]=='penis'
    assert lookup(ordered('pigu')[0])[1]=='butt'
    assert current[('bi','vulva')]['role']=='alias'
    assert ('baifa','white hair') in current and ('baifa','white_hair') in current
    assert ('huli','fossa') in current,'Withdrawn issue data was unexpectedly removed'
    sample_codes=['huli','baifa','baisepimao','jiezuo','zhilianggenggao','bi','piyan','jiba','diao','pigu']
    preview={code:[{'english':lookup(row)[1],'zh':row['zh'],'role':row['role'],'original_weight':int(row['weight'])} for row in ordered(code)] for code in sample_codes}
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    report={'status':'PASS','baseline_ref':'v0.2.3','baseline_rows':len(old),'rows':len(rows),'added_lookup_pairs':sorted([list(key) for key in set(current)-set(previous)]),'all_prior_lookup_pairs_preserved':True,'old_heat_preserved_except_explicit_slang_rows':True,'primary_before_alias_for_all_codes':True,'chinese_groups_contiguous_within_tier':True,'native_dictionary_sha256':sha(ROOT/'rime/booru.dict.yaml'),'dictionary_sha256':sha(ROOT/'rime/booru.tsv'),'lua_sha256':sha(ROOT/'rime/lua/booru_filter.lua'),'preview':preview,'scope':'compiled dictionary ordering and data coverage only; native exact-before-prefix behavior uses librime; no Rime session or key events'}
    target=ROOT/'validation/gpt/ranking-slang.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='preview'},ensure_ascii=False))
    print(json.dumps({'huli_preview':preview['huli'],'slang_heads':{code:preview[code][0] for code in ['bi','piyan','jiba','diao','pigu']}},ensure_ascii=False))

if __name__=='__main__':main()
