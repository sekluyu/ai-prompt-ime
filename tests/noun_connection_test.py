"""Check the reported foot + bathtub + side composition and noun priority."""
import argparse,csv,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 read=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter='\t'))
 key=lambda r:(r['code'],r['tag'].removeprefix('__prompt__:'))
 old={key(r):r for r in read(a.before)};now={key(r):r for r in read(ROOT/'rime/booru.tsv')}
 assert set(old)<=set(now)
 assert all(now[k]==r for k,r in old.items() if k!=('yugang','bathtub'))
 assert now[('yugang','bathtub')]['role']=='primary' and now[('yugang','bathtub')]['weight']=='11000'
 sys.path.insert(0,str(ROOT/'tests'));from engine_test import Engine
 a.output_dir.mkdir(parents=True,exist_ok=True);os.environ['BOORU_TEST_USER']=str(a.output_dir/'runtime');os.environ['BOORU_TEST_LOG']=str(a.output_dir)
 e=Engine();sequences=[]
 def choose(code,text):
  for c in code:e.key(c)
  menu,_=e.candidates();assert menu[0]['text']==text,(code,menu)
  e.key(' ');committed=e.commit();assert committed==text;return committed
 try:
  for code,prefix in [('jiaofangzaizuoce','one foot positioned to the left of '),('zuojiaofangzaizuoce','left foot positioned to the left of '),('youjiaofangzaizuoce','right foot positioned to the left of '),('jiaofangzaiyoubian','one foot positioned to the right of '),('tuifangzaipangbian','one leg resting beside ')]:
   e.reset();text=choose(code,prefix)+choose('yugang','bathtub, ');sequences.append(text)
 finally:e.close()
 result=dict(status='PASS',tested_sequences=sequences,unrelated_entries_unchanged=True,new_mappings=len(set(now)-set(old)),dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest())
 (a.output_dir/'noun-connection.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
