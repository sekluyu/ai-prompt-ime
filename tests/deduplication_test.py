"""Compare generated entries with a saved baseline without starting an input method."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream,delimiter='\t'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    before=read(args.before);after=read(ROOT/'rime/booru.tsv')
    group=lambda row:(row['code'],row['tag'].removeprefix('__prompt__:'))
    original=defaultdict(list)
    for row in before:original[group(row)].append(row)
    current={group(row):row for row in after}
    assert len(current)==len(after),'An exact output/pinyin pair is still duplicated'
    assert set(current)==set(original),'A lookup/output pair was lost or unexpectedly added'
    for key,rows in original.items():assert int(current[key]['weight'])==max(int(r['weight']) for r in rows),key
    exact=[{'code':key[0],'output':key[1],'before':rows,'after':current[key]} for key,rows in original.items() if len(rows)>1]
    near=defaultdict(list)
    for row in after:
        text=group(row)[1];near[(row['code'],text.replace('_',' '))].append(row)
    near=[{'code':key[0],'normalized_for_review_only':key[1],'candidates':rows} for key,rows in sorted(near.items()) if len({group(r)[1] for r in rows})>1]
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'完全重复合并清单.json').write_text(json.dumps(exact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.output_dir/'近似写法待审核.json').write_text(json.dumps(near,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 空格／下划线近似写法（仅审核，尚未合并）','','仅将下划线替换为空格作比对，不把它作为删除规则。以下每组的不同英文输出均保留。','','| 拼音 | 英文候选 | 中文注释 |','|---|---|---|']
    for item in near:
        words=sorted({group(row)[1] for row in item['candidates']})
        labels=sorted({row['zh'] for row in item['candidates']})
        escape=lambda s:s.replace('|','\\|').replace('\n',' ')
        lines.append('| '+escape(item['code'])+' | '+' / '.join(escape(word) for word in words)+' | '+' / '.join(escape(label) for label in labels)+' |')
    (args.output_dir/'近似写法待审核.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    report={'status':'PASS','before_rows':len(before),'after_rows':len(after),'removed_rows':len(before)-len(after),'merged_exact_groups':len(exact),'remaining_exact_groups':0,'lookup_output_pairs_preserved':True,'maximum_weights_preserved':True,'near_groups_preserved_for_review':len(near),'before_dictionary_sha256':sha(args.before),'dictionary_sha256':sha(ROOT/'rime/booru.tsv'),'lua_sha256':sha(ROOT/'rime/lua/booru_filter.lua'),'validation_scope':'data coverage and exact-output uniqueness; Lua unit check separately; no Rime session, key events or real desktop typing'}
    (ROOT/'validation/gpt/deduplication.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.output_dir/'去重数据核对.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
