"""Verify left/right leg and foot assignments, surfaces, and final commits."""
import argparse,csv,hashlib,io,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from general_phrases import pose_rows,PREFIX
from term_repairs import expansion_rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--engine',action='store_true');p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 allrows=list(csv.DictReader((ROOT/'rime/booru.tsv').open(encoding='utf-8'),delimiter='\t'))
 k=lambda r:(r['code'],r['tag'].removeprefix(PREFIX))
 current={k(r):r for r in allrows}
 old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','v0.2.9:rime/booru.tsv'],cwd=ROOT).decode()),delimiter='\t'))
 prior={k(r):r for r in old}
 phrases=[r for r in pose_rows() if any(t in r['zh'] for t in ['〔腿部放置〕','〔脚部放置〕','〔交叉腿脚〕','〔左右腿脚组合〕'])]
 assert set(current)-set(prior)=={k(r) for r in pose_rows()+expansion_rows()}-set(prior)
 assert all(current[key]==r for key,r in prior.items() if key!=('yugang','bathtub')),'Existing row changed'
 for r in phrases:
  assert current[k(r)]=={**r,'weight':str(r['weight'])}
  zh=r['zh'].split('〔',1)[0];en=r['tag'].removeprefix(PREFIX)
  for cn,eng in [('左腿','left leg'),('右腿','right leg'),('左脚','left foot'),('右脚','right foot'),('双腿','both legs'),('双脚','both feet')]:
   if zh.startswith(cn):assert en.startswith(eng),(zh,en)
  if zh.startswith('左腿') and '右膝' in zh:assert 'across right knee' in en
  if zh.startswith('右腿') and '左膝' in zh:assert 'across left knee' in en
 selected=0
 if a.engine:
  sys.path.insert(0,str(ROOT/'tests'));from engine_test import Engine
  a.output_dir.mkdir(parents=True,exist_ok=True)
  os.environ['BOORU_TEST_USER']=str(a.output_dir/'runtime');os.environ['BOORU_TEST_LOG']=str(a.output_dir)
  e=Engine()
  try:
   for r in phrases:
    e.reset()
    for ch in r['code']:e.key(ch)
    text=r['tag'].removeprefix(PREFIX)+', '
    candidates,last=e.candidates()
    assert candidates and candidates[0]['text']==text,(r,candidates)
    assert candidates[0]['comment'].startswith(r['zh'].split('〔',1)[0]),(r,candidates)
    e.key(' ');assert e.commit()==text
    selected+=1
  finally:e.close()
 result=dict(status='PASS',baseline='v0.2.9',rows=len(allrows),new_phrase_mappings=len(phrases),english_phrases=len({r['tag'] for r in phrases}),engine_selections=selected,unrelated_existing_rows_unchanged=True,dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest())
 a.output_dir.mkdir(parents=True,exist_ok=True);(a.output_dir/'leg-foot-phrases.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
