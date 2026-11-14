"""Verify the pending vocabulary batch and the reported shouzaib completion."""
import argparse,csv,hashlib,io,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','v0.2.11:rime/booru.tsv'],cwd=ROOT).decode()),delimiter='\t'))
 rows=list(csv.DictReader((ROOT/'rime/booru.tsv').open(encoding='utf-8'),delimiter='\t'))
 key=lambda r:(r['code'],r['tag'].removeprefix('__prompt__:'))
 before={key(r):r for r in old};now={key(r):r for r in rows}
 assert all(now[k]==r for k,r in before.items())
 added=sorted(set(now)-set(before));assert len(added)==15
 sys.path.insert(0,str(ROOT/'tests'));from engine_test import Engine
 os.environ['BOORU_TEST_USER']=str(a.output_dir/'runtime');os.environ['BOORU_TEST_LOG']=str(a.output_dir)
 e=Engine();results=[]
 def select(code,expected):
  e.reset()
  for c in code:e.key(c)
  menu,_=e.candidates();assert menu,(code,menu)
  if expected.startswith('random '):
   assert 'random' not in menu[0]['text'] and menu[0]['text'].endswith(', '),(code,menu)
   expected=menu[0]['text']
   again,_=e.candidates();assert again[0]['text']==expected
  else:assert menu[0]['text']==expected,(code,menu)
  e.key(' ');assert e.commit()==expected
  results.append({'code':code,'commit':expected,'comment':menu[0]['comment']})
 try:
  for code,en in added:select(code,en+', ')
  for i in range(20):
   select('suijiwuzhong','random species, ')
   select('suijishuangsepimao','random two-tone fur, ')
  for code in ['suijiwuzhong','suijishuangsepimao']:
   assert len({r['commit'] for r in results if r['code']==code})>5
  select('shouzaib','hands_behind_back, ')
  select('shuangshoubeihoukunbang','arms_bound_behind_back, ')
 finally:e.close()
 report={'status':'PASS','baseline':'v0.2.11','new_mappings':len(added),'prior_entries_unchanged':True,'real_engine_checks':len(results),'results':results,'dictionary_sha256':hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest()}
 (a.output_dir/'pending-vocabulary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True))
if __name__=='__main__':main()
