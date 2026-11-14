"""Check new body poses, preserved prior local data, and real Space commits."""
import argparse,csv,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from general_phrases import pose_rows
from term_repairs import expansion_rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 read=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'))
 key=lambda r:(r['code'],r['tag'].removeprefix('__prompt__:'))
 before={key(r):r for r in read(a.before)};now={key(r):r for r in read(ROOT/'rime/booru.tsv')}
 added=[r for r in pose_rows() if key(r) not in before]
 assert set(now)-set(before)=={key(r) for r in pose_rows()+expansion_rows()}-set(before)
 assert all(now[k]==r for k,r in before.items()),'Prior local entry changed'
 cases={'tuifangping':'sitting with legs extended forward','zuotuifangping':'sitting with left leg extended forward','youtuifangping':'sitting with right leg extended forward','shuangtuifangping':'sitting with both legs extended forward','zuotuishuipingtaiqi':'left leg held horizontally','zuotuishenzhiyoutuiwanqu':'sitting with left leg extended and right knee bent','youtuishenzhizuotuiwanqu':'sitting with right leg extended and left knee bent'}
 for code,en in cases.items():assert (code,en) in now,(code,en)
 assert 'horizontal' not in cases['tuifangping']
 sys.path.insert(0,str(ROOT/'tests'));from engine_test import Engine
 a.output_dir.mkdir(parents=True,exist_ok=True);os.environ['BOORU_TEST_USER']=str(a.output_dir/'runtime');os.environ['BOORU_TEST_LOG']=str(a.output_dir)
 e=Engine();selected=0
 try:
  for r in added:
   e.reset()
   for ch in r['code']:e.key(ch)
   expected=r['tag'].removeprefix('__prompt__:')+', '
   menu,_=e.candidates();assert menu[0]['text']==expected,(r,menu)
   assert menu[0]['comment'].startswith(r['zh'].split('〔',1)[0]),(r,menu)
   e.key(' ');assert e.commit()==expected
   selected+=1
 finally:e.close()
 result=dict(status='PASS',new_mappings=len(added),new_english_expressions=len({r['tag'] for r in added}),engine_selections=selected,prior_local_entries_unchanged=True,flat_legs_meaning='sitting with legs extended forward',cases=cases,dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest())
 (a.output_dir/'body-postures.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
