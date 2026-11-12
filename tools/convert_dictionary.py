"""Pinned ffdkj snapshot -> complete normalized archive and searchable TSVs."""
import csv
import hashlib
import json
import math
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/pydeps'))
from pypinyin import lazy_pinyin, Style, load_phrases_dict, __version__
COMMIT='d232b4ee431f13c6f34c7f31c35b937b26bb56c2'
FIELDS=['tag','zh','code','weight']
def write_json(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def write_tsv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    start=time.perf_counter(); out=ROOT/'dictionary'; src=out/'source'/COMMIT
    c=sqlite3.connect((src/'tag.sqlite').as_uri()+'?mode=ro',uri=True)
    assert c.execute('pragma quick_check').fetchone()[0]=='ok'
    columns=[x[1] for x in c.execute('pragma table_info(tags)')]
    assert columns==['name','category','cn_name','post_count'],columns
    allrows=c.execute('select name,category,cn_name,post_count from tags order by name').fetchall()
    known={r[0] for r in allrows}
    # Bootstrap aliases are explicit project overrides, never represented as upstream text.
    override_path=out/'overrides.tsv'
    if not override_path.exists(): override_path=ROOT/'fixtures/pre-formal-20261112/rime/booru.tsv'
    overrides=list(csv.DictReader(override_path.open(encoding='utf-8'),delimiter='\t'))
    overrides=[dict(r,weight=10000) for r in overrides if r['tag'] in known]
    write_tsv(out/'overrides.tsv',overrides)
    if not (out/'overrides-reasons.json').exists():
        write_json(out/'overrides-reasons.json',{'origin':'GPT curated bootstrap, promoted to explicit local aliases','reason':'Preserve core input spellings and resolve known words; tags verified against pinned source','count':len(overrides),'not_upstream_translation':True})
    bytag={}
    for r in overrides: bytag.setdefault(r['tag'],[]).append(r)
    load_phrases_dict({'长发':[['chang'],['fa']],'行走':[['xing'],['zou']],'头发':[['tou'],['fa']],'白发':[['bai'],['fa']],'绿色':[['lv'],['se']]})
    dbpath=out/'normalized.sqlite'
    if dbpath.exists(): dbpath.unlink()
    db=sqlite3.connect(dbpath)
    db.executescript('CREATE TABLE tags(tag TEXT PRIMARY KEY,category INTEGER,post_count INTEGER,source_zh TEXT); CREATE TABLE aliases(tag TEXT REFERENCES tags(tag),zh TEXT,code TEXT,weight INTEGER,origin TEXT,pinyin_status TEXT,UNIQUE(tag,zh,code));')
    counts=Counter(); categories=Counter(); mapping={}; covered=set(); common_pool={}
    with (out/'exceptions.jsonl').open('w',encoding='utf-8') as errors,(out/'metadata.jsonl').open('w',encoding='utf-8') as meta:
        def exception(tag,field,raw,reason,action,detail):
            errors.write(json.dumps(dict(source_ref=COMMIT,source_row=tag,tag=tag,field=field,raw_value=raw,reason=reason,action=action,detail=detail),ensure_ascii=False)+'\n'); counts['exceptions']+=1;counts['reason_'+reason]+=1
        for tag,category,zh,post_count in allrows:
            categories[str(category)]+=1
            db.execute('insert into tags values(?,?,?,?)',(tag,category,post_count,zh))
            aliases=[]; status='pending'
            count=post_count
            if not isinstance(count,int) or count<0:
                exception(tag,'post_count',count,'invalid_count','fallback_count','Ranking uses 0; original retained');count=0
            weight=min(9999,1+math.floor(1000*math.log10(1+count)))
            if category not in {0,1,3,4,5}:
                exception(tag,'category',category,'unknown_category','quarantine','Original retained; not searchable')
            else:
                text=(zh or '').strip()
                if not text:
                    exception(tag,'zh',zh,'empty_zh','quarantine','No source translation')
                elif re.search(r'[\t\r\n\x00]',tag+text):
                    exception(tag,'zh',zh,'invalid_field','quarantine','TSV control character')
                elif not re.fullmatch(r'[\u3400-\u4dbf\u4e00-\u9fff]+',text):
                    exception(tag,'zh',zh,'unsupported_text','needs_review','Mixed scripts/punctuation require explicit alias; source retained, not silently stripped')
                else:
                    syllables=lazy_pinyin(text,style=Style.NORMAL,strict=False,v_to_u=False,errors=lambda x:['?'])
                    code=''.join(syllables).lower().replace('ü','v').replace('u:','v')
                    if not re.fullmatch('[a-z]+',code):
                        exception(tag,'code',code,'ambiguous_pinyin','needs_review','Unresolved pronunciation')
                    else:
                        aliases.append(dict(zh=text,code=code,origin='source',weight=weight,pinyin_status='auto'));status='auto'
                for r in bytag.get(tag,[]):
                    aliases.append(dict(zh=r['zh'],code=r['code'],origin='manual',weight=10000,pinyin_status='reviewed'))
                for a in aliases:
                    db.execute("insert into aliases values(?,?,?,?,?,?) ON CONFLICT(tag,zh,code) DO UPDATE SET weight=max(aliases.weight,excluded.weight), origin=CASE WHEN excluded.origin='manual' THEN 'manual' ELSE aliases.origin END, pinyin_status=CASE WHEN excluded.origin='manual' THEN 'reviewed' ELSE aliases.pinyin_status END",(tag,a['zh'],a['code'],a['weight'],a['origin'],a['pinyin_status']))
                    key=(tag,a['code']); row=dict(tag=tag,zh=a['zh'],code=a['code'],weight=a['weight'])
                    old=mapping.get(key)
                    if old:
                        counts['duplicate_merged']+=1
                        exception(tag,'code',a['code'],'duplicate_merged','merged','Alternative Chinese label retained in metadata')
                    if not old or row['weight']>old['weight'] or (row['weight']==old['weight'] and row['zh']<old['zh']): mapping[key]=row
                if aliases: covered.add(tag)
                if category==0 and aliases: common_pool[tag]=count
            if aliases and status=='pending': status='reviewed'
            meta.write(json.dumps(dict(tag=tag,category=category,post_count=post_count,source_zh=zh,aliases=aliases,pinyin_status=status,source_ref=COMMIT),ensure_ascii=False)+'\n')
        db.commit()
    db.close();c.close()
    rows=sorted(mapping.values(),key=lambda r:(r['code'],-r['weight'],r['tag']))
    write_tsv(out/'entries.tsv',rows)
    selected=set(sorted(common_pool,key=lambda t:(-common_pool[t],t))[:20000])|set(bytag)
    common=[r for r in rows if r['tag'] in selected]
    write_tsv(out/'entries.common.tsv',common)
    manifest=dict(interface_version='v1',repository='https://github.com/ffdkj/ffdkj-Danbooru_Tag-Chinese-English-Translation-Table',commit=COMMIT,downloaded_utc=datetime.fromtimestamp((src/'tag.sqlite').stat().st_mtime,timezone.utc).isoformat(),table='tags',columns=columns,source_records=len(allrows),pypinyin=__version__,python=sys.version.split()[0],hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in src.iterdir() if p.is_file()},phrase_overrides=['长发','行走','头发','白发','绿色'])
    write_json(out/'source.json',manifest)
    report=dict(status='PASS',source_records=len(allrows),normalized_tags=len(allrows),searchable_tags=len(covered),searchable_mappings=len(rows),unmapped_tags=len(known-covered),default_tags=len({r['tag'] for r in common}),default_mappings=len(common),default_policy='Top 20000 searchable general-category tags by upstream post_count plus verified bootstrap core aliases',categories=dict(categories),counts=dict(counts),elapsed_seconds=round(time.perf_counter()-start,3),limitation='All source records archived and processed. Search TSV excludes unresolved/mixed-script translations. Auto phrase readings have not been exhaustively manually reviewed; model effect acceptance belongs to boss.')
    write_json(out/'conversion-report.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
