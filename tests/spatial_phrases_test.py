"""Verify relative positions, frame positions and unchanged prior local entries."""
import argparse,csv,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from term_repairs import expansion_rows
from general_phrases import pose_rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 read=lambda f:list(csv.DictReader(f.open(encoding='utf-8-sig'),delimiter='\t'))
 key=lambda r:(r['code'],r['tag'].removeprefix('__prompt__:'))
 old={key(r):r for r in read(a.before)};now={key(r):r for r in read(ROOT/'rime/booru.tsv')}
 added=[r for r in expansion_rows() if key(r) not in old]
 assert set(now)-set(old)=={key(r) for r in expansion_rows()+pose_rows()}-set(old)
 assert all(now[k]==r for k,r in old.items() if k!=('yugang','bathtub')),'Prior local entry changed'
 for r in added:
  text=r['tag'].removeprefix('__prompt__:');zh=r['zh']
  for cn,en in [('左腿','left leg'),('右腿','right leg'),('左脚','left foot'),('右脚','right foot')]:
   if zh.startswith(cn):assert text.startswith(en),(zh,text)
  if '某物右侧' in zh or '某物右边' in zh:assert 'to the right of' in text
  if '某物左侧' in zh or '某物左边' in zh:assert 'to the left of' in text
  if '画面左侧' in zh or '画面左边' in zh:assert 'left side of the frame' in text
  if '画面右侧' in zh or '画面右边' in zh:assert 'right side of the frame' in text
 sys.path.insert(0,str(ROOT/'tests'));from engine_test import Engine
 a.output_dir.mkdir(parents=True,exist_ok=True);os.environ['BOORU_TEST_USER']=str(a.output_dir/'runtime');os.environ['BOORU_TEST_LOG']=str(a.output_dir)
 engine=Engine();checked=0
 try:
  for r in added:
   engine.reset()
   for ch in r['code']:engine.key(ch)
   suffix=' ' if '〔待续写〕' in r['zh'] else ', '
   expected=r['tag'].removeprefix('__prompt__:')+suffix
   menu,_=engine.candidates();assert menu[0]['text']==expected,(r,menu)
   engine.key(' ');assert engine.commit()==expected
   checked+=1
 finally:engine.close()
 report=dict(status='PASS',added_mappings=len(added),english_expressions_in_added_mappings=len({r['tag'] for r in added}),new_english_outputs=len({r['tag'].removeprefix('__prompt__:') for r in added}-{k[1] for k in old}),engine_selections=checked,previous_local_entries_unchanged_except_reviewed_bathtub_priority=True,dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest())
 (a.output_dir/'spatial-phrases.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
