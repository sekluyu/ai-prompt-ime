"""Real librime integration test in a disposable project-local user directory."""
import ctypes as C
import csv
import json
import re
import shutil
import time
import os
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
I=C.c_int; P=C.c_void_p; S=C.c_char_p; ID=C.c_size_t
class Traits(C.Structure):
    _fields_=[('data_size',I)]+[(n,S) for n in ['shared_data_dir','user_data_dir','distribution_name','distribution_code_name','distribution_version','app_name']]+[('modules',C.POINTER(S)),('min_log_level',I)]+[(n,S) for n in ['log_dir','prebuilt_data_dir','staging_dir']]
class Composition(C.Structure):
    _fields_=[(n,I) for n in ['length','cursor_pos','sel_start','sel_end']]+[('preedit',S)]
class Candidate(C.Structure):
    _fields_=[('text',S),('comment',S),('reserved',P)]
class Menu(C.Structure):
    _fields_=[(n,I) for n in ['page_size','page_no','is_last_page','highlighted_candidate_index','num_candidates']]+[('candidates',C.POINTER(Candidate)),('select_keys',S)]
class Context(C.Structure):
    _fields_=[('data_size',I),('composition',Composition),('menu',Menu),('commit_text_preview',S),('select_labels',C.POINTER(S))]
class Commit(C.Structure):
    _fields_=[('data_size',I),('text',S)]

def init(t):
    obj=t(); obj.data_size=C.sizeof(t)-C.sizeof(I); return obj

class Engine:
    def __init__(self):
        native=Path(os.environ.get('BOORU_RIME_DIST',str(ROOT/'tools/librime/dist')))
        self.dll=C.CDLL(str(native/'lib/rime.dll'))
        self.dll.rime_get_api.restype=P
        addr=self.dll.rime_get_api()
        header=(native/'include/rime_api.h').read_text()
        body=header.split('typedef struct RIME_FLAVORED(rime_api_t) {')[1].split('} RIME_FLAVORED(RimeApi)')[0]
        names=re.findall(r'\(\*(\w+)\)',body)
        class Api(C.Structure):
            _fields_=[('data_size',I)]+[(n,P) for n in names]
        self.api=C.cast(addr,C.POINTER(Api)).contents
        self.keep=[]
        user=Path(os.environ.get('BOORU_TEST_USER',str(ROOT/'validation/gpt/runtime')))
        user.mkdir(parents=True,exist_ok=True)
        for p in Path(os.environ.get('BOORU_TEST_SOURCE',str(ROOT/'rime'))).iterdir():
            if p.is_file(): shutil.copy2(p,user/p.name)
            elif p.name=='lua': shutil.copytree(p,user/p.name,dirs_exist_ok=True)
        (user/'default.yaml').write_text('config_version: "1"\nschema_list:\n  - schema: booru\nswitcher:\n  hotkeys: [Control+grave]\n',encoding='utf-8')
        self.traits=init(Traits)
        self.traits.shared_data_dir=str(user).encode()
        self.traits.user_data_dir=str(user).encode()
        self.traits.app_name=b'rime.booru-test'
        self.traits.log_dir=os.environ.get('BOORU_TEST_LOG',str(ROOT/'validation/gpt')).encode()
        self.traits.min_log_level=1
        self.call('setup',None,[C.POINTER(Traits)],C.byref(self.traits))
        self.call('initialize',None,[C.POINTER(Traits)],C.byref(self.traits))
        self.call('deployer_initialize',None,[C.POINTER(Traits)],C.byref(self.traits))
        assert self.call('deploy_schema',I,[S],str(user/'booru.schema.yaml').encode()),'schema compilation failed'
        self.sid=self.call('create_session',ID,[])
        assert self.sid
        assert self.call('select_schema',I,[ID,S],self.sid,b'booru')
    def call(self,name,ret,args,*values):
        ptr=getattr(self.api,name)
        if not ptr: raise RuntimeError('Unavailable Rime API: '+name)
        return C.CFUNCTYPE(ret,*args)(ptr)(*values)
    def key(self,ch):
        return self.call('process_key',I,[ID,I,I],self.sid,ord(ch) if isinstance(ch,str) else ch,0)
    def candidates(self):
        ctx=init(Context)
        assert self.call('get_context',I,[ID,C.POINTER(Context)],self.sid,C.byref(ctx))
        out=[dict(text=ctx.menu.candidates[i].text.decode(),comment=(ctx.menu.candidates[i].comment or b'').decode()) for i in range(ctx.menu.num_candidates)]
        last=bool(ctx.menu.is_last_page)
        self.call('free_context',I,[C.POINTER(Context)],C.byref(ctx))
        return out,last
    def commit(self):
        c=init(Commit)
        if not self.call('get_commit',I,[ID,C.POINTER(Commit)],self.sid,C.byref(c)): return None
        text=c.text.decode(); self.call('free_commit',I,[C.POINTER(Commit)],C.byref(c)); return text
    def reset(self):
        self.call('clear_composition',None,[ID],self.sid)
        self.commit()
    def close(self):
        self.call('destroy_session',I,[ID],self.sid)
        self.call('finalize',None,[])

def main():
    start=time.perf_counter(); e=Engine(); initialized=time.perf_counter(); results=[]
    try:
        rows=list(csv.DictReader((Path(os.environ.get('BOORU_TEST_SOURCE',str(ROOT/'rime')))/'booru.tsv').open(encoding='utf-8'),delimiter='\t'))
        labels={}; label_weights={}
        for r in rows:
            if r['tag'] not in labels or int(r['weight'])>label_weights[r['tag']]:
                labels[r['tag']]=r['zh'];label_weights[r['tag']]=int(r['weight'])
        total_rows=len(rows)
        limit=int(os.environ.get('BOORU_TEST_LIMIT',len(rows)))
        if len(rows)>limit:
            rows=[rows[i*len(rows)//limit] for i in range(limit)]
        for row in rows:
            e.reset()
            for ch in row['code']: e.key(ch)
            for page in range(100):
                candidates,last=e.candidates()
                text=row['tag'].removeprefix('__prompt__:')
                expected=re.sub(r'([\\()])',r'\\\1',text)+', '
                found=next((i for i,c in enumerate(candidates) if c['text']==expected and c['comment'].startswith(row['zh'].split('〔',1)[0])),None)
                if found is not None: break
                if last: raise AssertionError(f'Missing candidate {row}')
                e.key('=')
            else: raise AssertionError('paging did not terminate')
            assert candidates[found]['comment'].startswith(row['zh'].split('〔',1)[0]),row
            e.key(str(found+1))
            actual=e.commit()
            assert actual==expected,(row,actual)
            results.append(dict(code=row['code'],commit=actual,comment=candidates[found]['comment']))
        # Option isolation: raw-tag output, cancellation, ASCII mode, unknown input.
        e.reset(); e.call('set_option',None,[ID,S,I],e.sid,b'booru_separator',0)
        for ch in 'shuangmawei': e.key(ch)
        e.key(' '); assert e.commit()=='twintails'
        e.call('set_option',None,[ID,S,I],e.sid,b'booru_separator',1)
        for ch in 'guoxiwa': e.key(ch)
        e.key(0xff1b); assert e.commit() is None
        e.reset()
        for ch in 'zzzzzz': e.key(ch)
        assert not e.candidates()[0]
        e.reset(); e.call('set_option',None,[ID,S,I],e.sid,b'ascii_mode',1)
        assert not e.key('a'), 'ASCII keystroke should pass to application'
        e.call('set_option',None,[ID,S,I],e.sid,b'ascii_mode',0)
        # Repeat the core sequence exactly as a user would select it with Space.
        sequence=''
        for code in ['nvhai','danren','baifa','shuangmawei','guoxiwa']:
            for ch in code: e.key(ch)
            e.key(' '); sequence+=e.commit() or ''
        assert sequence=='1girl, solo, white_hair, twintails, thighhighs, ',sequence
        version=e.call('get_version',S,[]).decode()
        source=Path(os.environ.get('BOORU_TEST_SOURCE',str(ROOT/'rime')))
        report=dict(status='PASS',engine='official librime '+version+' Windows x64, Lua enabled',dictionary_rows=total_rows,dictionary_sha256=hashlib.sha256((source/'booru.tsv').read_bytes()).hexdigest(),tested_rows=len(results),initialization_compile_seconds=round(initialized-start,3),elapsed_seconds=round(time.perf_counter()-start,3),core_sequence=sequence,checks=['bounded deterministic candidate sample + Chinese comments + selection commits','raw-tag option','Escape cancellation','unknown code','ASCII passthrough','multi-tag Space sequence'],results=results,limitation='One automated engine check, not exhaustive human acceptance; not proof of Windows TSF input or image quality')
        import sys
        sys.path.insert(0,str(ROOT/'tools/pydeps'))
        import psutil
        memory=psutil.Process().memory_info()
        report['process_rss_bytes']=memory.rss
        report['process_peak_working_set_bytes']=memory.peak_wset
        (ROOT/f'validation/gpt/engine-test-{version}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/'validation/gpt/engine-test.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False))
    finally: e.close()

if __name__=='__main__': main()
