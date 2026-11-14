"""Check editable leg/foot prefixes and a real prefix + noun sequence."""
import argparse,csv,ctypes as C,hashlib,io,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from term_repairs import expansion_rows
from general_phrases import pose_rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 current=list(csv.DictReader((ROOT/'rime/booru.tsv').open(encoding='utf-8'),delimiter='\t'))
 old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','v0.2.10:rime/booru.tsv'],cwd=ROOT).decode()),delimiter='\t'))
 k=lambda r:(r['code'],r['tag'].removeprefix('__prompt__:'))
 now={k(r):r for r in current};prior={k(r):r for r in old}
 prefixes=[r for r in expansion_rows() if '〔待续写〕' in r['zh']]
 assert set(now)-set(prior)=={k(r) for r in expansion_rows()+pose_rows()}-set(prior)
 assert all(now[key]==r for key,r in prior.items() if key!=('yugang','bathtub'))
 sys.path.insert(0,str(ROOT/'tests'));from engine_test import Engine
 os.environ['BOORU_TEST_USER']=str(a.output_dir/'runtime');os.environ['BOORU_TEST_LOG']=str(a.output_dir)
 e=Engine();checked=0
 def option(name,value):e.call('set_option',None,[C.c_size_t,C.c_char_p,C.c_int],e.sid,name.encode(),int(value))
 def choose(code,expected):
  for ch in code:e.key(ch)
  menu,_=e.candidates();assert menu[0]['text']==expected,(code,menu)
  e.key(' ');result=e.commit();assert result==expected;return result
 try:
  for separator,space in [(True,True),(True,False),(False,False)]:
   option('booru_separator',separator);option('booru_space',space)
   for r in prefixes:
    e.reset();choose(r['code'],r['tag'].removeprefix('__prompt__:')+' ');checked+=1
  option('booru_separator',True);option('booru_space',True)
  e.reset();sequence=choose('zuotuifangzai','left leg resting on ')
  sequence+=choose('zhuozi','table, ')
  assert sequence=='left leg resting on table, '
  e.reset();assert choose('youjiaofangdishang','right foot resting on the floor, ')
 finally:e.close()
 report=dict(status='PASS',version='0.2.11-local',prefixes=len({r['tag'] for r in prefixes}),mappings=len(prefixes),option_checks=checked,sequence=sequence,previous_entries_unchanged_except_reviewed_bathtub_priority=True,dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest())
 (a.output_dir/'continuation-phrases.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
