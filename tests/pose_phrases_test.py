"""Check posture coverage and hand assignment without real Rime key events."""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from general_phrases import PREFIX,pose_rows

def main():
    expected=pose_rows()
    with (ROOT/'rime/booru.tsv').open(encoding='utf-8') as stream:
        rows=list(csv.DictReader(stream,delimiter='\t'))
    lookup=lambda r:(r['code'],r['tag'].removeprefix(PREFIX))
    current={lookup(r):r for r in rows}
    old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','v0.2.5:rime/booru.tsv'],cwd=ROOT).decode('utf-8')),delimiter='\t'))
    previous={lookup(r):r for r in old}
    expected_keys={lookup(r) for r in expected}
    assert len(current)==len(rows),'Duplicate pinyin/output pair'
    assert set(previous)<=set(current),'Existing output removed'
    assert set(current)-set(previous)==expected_keys-set(previous)
    for key,prior in previous.items():
        if key not in expected_keys:
            assert current[key]==prior,'Unrelated row modified: '+str(key)
    for row in expected:
        actual=current[lookup(row)]
        assert actual['role']=='primary' and actual['zh']==row['zh']
        assert int(actual['weight'])==10000
    cases={
        'shangbanshenzhili':'upright torso',
        'zuozhi':'sitting upright',
        'beibutingzhi':'straight back',
        'zuoshoufuyao':'left hand resting on hip',
        'youshoumotou':'right hand touching head',
        'zuoshoufuyaoyoushoumotou':'left hand resting on hip, right hand touching head',
        'zuoshoumotouyoushoufuyao':'left hand touching head, right hand resting on hip',
        'yizhishoutuoxiaba':'one hand supporting chin',
        'lingyizhishoufangdatuishang':'the other hand resting on thigh',
        'yishoumoerduolingyishoumoweiba':'one hand touching ear, the other hand touching tail',
        'zuoshoutuosai':'left hand cupping cheek',
        'zuoshoumolian':'left hand touching face',
    }
    native={}
    for line in (ROOT/'rime/booru.dict.yaml').read_text(encoding='utf-8').split('...\n',1)[1].splitlines():
        tag,code,weight=line.split('\t');native[(tag,code)]=int(weight)
    for code,text in cases.items():
        assert (code,text) in current,(code,text)
        candidates=[r for r in rows if r['code']==code]
        head=max(candidates,key=lambda r:native[(r['tag'],code)])
        assert head['tag'].removeprefix(PREFIX)==text,(code,head)
    for side in ['left hand','right hand','one hand','the other hand']:
        assert any(r['tag']==PREFIX+side+' touching head' for r in expected)
        assert any(r['tag']==PREFIX+side+' supporting chin' for r in expected)
    # Selecting two independent entries gives the same clause content as a preset.
    assert cases['zuoshoufuyao']+', '+cases['youshoumotou']==cases['zuoshoufuyaoyoushoumotou']
    result={'status':'PASS','baseline':'v0.2.5','baseline_rows':len(old),'rows':len(rows),'curated_pose_mappings':len(expected),'new_lookup_pairs':len(set(current)-set(previous)),'all_prior_pairs_preserved':True,'unrelated_rows_unchanged':True,'assignment_samples':cases,'dictionary_sha256':hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest(),'native_dictionary_sha256':hashlib.sha256((ROOT/'rime/booru.dict.yaml').read_bytes()).hexdigest(),'scope':'Data and compiled exact-code priority only; no real input or image-quality acceptance.'}
    target=ROOT/'validation/gpt/pose-phrases.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
