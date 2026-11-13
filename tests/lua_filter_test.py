"""Exercise the Lua filter with mock candidates; no Rime session or key events."""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    native=Path(os.environ.get('BOORU_RIME_DIST',str(ROOT/'tools/librime/dist')))
    dll=C.CDLL(str(native/'lib/rime.dll'))
    dll.luaL_newstate.restype=C.c_void_p
    dll.luaL_openlibs.argtypes=[C.c_void_p]
    dll.luaL_loadstring.argtypes=[C.c_void_p,C.c_char_p];dll.luaL_loadstring.restype=C.c_int
    dll.lua_pcallk.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ssize_t,C.c_void_p];dll.lua_pcallk.restype=C.c_int
    dll.lua_tolstring.argtypes=[C.c_void_p,C.c_int,C.c_void_p];dll.lua_tolstring.restype=C.c_char_p
    dll.lua_close.argtypes=[C.c_void_p]
    code=r'''
local filter = assert(loadfile(FILTER_PATH))()
Candidate = function(kind, start, finish, text, comment)
  return {type=kind, start=start, _end=finish, text=text, comment=comment}
end
local values={booru_separator=true, booru_space=true}
local env={labels={pawpads='肉垫〔兽人词〕', ['__prompt__:pawpads']='肉垫〔兽人词〕', ['white_fur']='白色皮毛', ['__prompt__:white fur']='白色皮毛〔皮毛配色〕', ['x_(y)']='字面括号'}}
env.engine={context={get_option=function(self,name) return values[name] end}}
local function run(words)
  local input={iter=function(self)
    local i=0
    return function()
      i=i+1
      if not words[i] then return nil end
      return {text=words[i], type='table', start=0, _end=3, quality=10-i, preedit='test'}
    end
  end}
  local result={}
  yield=function(c) result[#result+1]=c end
  filter.func(input,env)
  return result
end
local r=run({'pawpads','__prompt__:pawpads','pawpads','__prompt__:white fur','white_fur','?','?'})
assert(#r==4)
assert(r[1].text=='pawpads, ' and r[1].comment=='肉垫〔兽人词〕')
assert(r[1].quality==9 and r[1].preedit=='test')
assert(r[2].text=='white fur, ' and r[3].text=='white_fur, ')
assert(r[4].text=='?')
-- A later-page duplicate is still part of the same lazy candidate stream.
local words={'pawpads'}
for i=1,10 do words[#words+1]='other'..i end
words[#words+1]='__prompt__:pawpads'
assert(#run(words)==11)
-- No seen state leaks into the next query, and spacing/plain mode are retained.
assert(#run({'pawpads','__prompt__:pawpads'})==1)
values.booru_space=false
assert(run({'pawpads','__prompt__:pawpads'})[1].text=='pawpads,')
values.booru_separator=false
assert(run({'pawpads','__prompt__:pawpads'})[1].text=='pawpads')
assert(run({'x_(y)'})[1].text=='x_\\(y\\)')

-- Exact aliases and native completion suffixes choose the matching Chinese,
-- not whichever label happened to be the highest-frequency label for a tag.
env.labels['fennec_fox']='耳廓狐'
env.labels['high quality']='高质量〔质量词〕'
env.matches={['__prompt__:fennec_fox\thuli']='狐狸〔e621〕',
             ['__prompt__:high quality\tzhilianggenggao']='质量更高〔质量词〕'}
env.primary_matches={['__prompt__:high quality\tzhilianggenggao']=true}
env.engine.context.input='huli'
assert(filter.comment({text='__prompt__:fennec_fox',start=0,_end=4},env)=='狐狸 · 耳廓狐〔e621〕')
env.engine.context.input='hul'
assert(filter.comment({text='__prompt__:fennec_fox',start=0,_end=3,comment='~i'},env)=='狐狸 · 耳廓狐〔e621〕')
env.engine.context.input='zhilianggenggao'
assert(filter.comment({text='__prompt__:high quality',start=0,_end=#'zhilianggenggao'},env)=='质量更高〔质量词〕')
env.engine.context.input='xxhuli'
assert(filter.comment({text='__prompt__:fennec_fox',start=2,_end=6},env)=='狐狸 · 耳廓狐〔e621〕')

-- Parse the v2 fifth column and keep ordinary definitions as fallback even
-- when an explicit slang lookup has a larger original heat.
local old_io,old_api=io,rime_api
local lines={
  'tag\tzh\tcode\tweight\trole',
  'fennec_fox\t耳廓狐\terkuohu\t2500\tprimary',
  '__prompt__:fennec_fox\t狐狸〔e621〕\thuli\t4500\talias',
  'penis\t阴茎\tyinjing\t3000\tprimary',
  '__prompt__:penis\t鸡巴〔俗称·阴茎〕\tjiba\t10000\tprimary',
  '"__prompt__:""honest""_john"\t诚实约翰\tchengshiyuehan\t2000\talias',
}
io={open=function()
  return {lines=function() local i=0;return function() i=i+1;return lines[i] end end,close=function()end}
end}
rime_api={get_user_data_dir=function()return 'mock' end}
local parsed={engine=env.engine}
filter.init(parsed)
assert(parsed.labels.fennec_fox=='耳廓狐' and parsed.labels.penis=='阴茎')
assert(parsed.matches['__prompt__:"honest"_john\tchengshiyuehan']=='诚实约翰')
parsed.engine.context.input='jiba'
assert(filter.comment({text='__prompt__:penis',start=0,_end=4},parsed)=='鸡巴〔俗称·阴茎〕')
io,rime_api=old_io,old_api

-- Load the actual generated TSV through the same parser, still with a fake
-- context: this checks the real index without starting Rime or sending keys.
rime_api={get_user_data_dir=function()return SOURCE_DIR end}
local indexed={engine={context={input='huli'}}}
local started=os.clock()
filter.init(indexed)
INDEX_LOAD_SECONDS=os.clock()-started
collectgarbage('collect')
INDEX_LUA_MIB=collectgarbage('count')/1024
assert(filter.comment({text='__prompt__:fennec_fox',start=0,_end=4},indexed)=='狐狸 · 耳廓狐〔e621〕')
indexed.engine.context.input='bi'
assert(filter.comment({text='__prompt__:pussy',start=0,_end=2},indexed)=='逼／屄〔俗称·外阴〕')
assert(filter.comment({text='__prompt__:vulva',start=0,_end=2},indexed)=='逼／屄 · 外阴〔俗称·外阴〕')
indexed.engine.context.input='piyan'
assert(filter.comment({text='__prompt__:anus',start=0,_end=5},indexed)=='屁眼〔俗称·肛门〕')
indexed.engine.context.input='zhilianggenggao'
assert(filter.comment({text='__prompt__:high quality',start=0,_end=#'zhilianggenggao'},indexed)=='质量更高〔质量词〕')
rime_api=old_api
'''
    path=(ROOT/'rime/lua/booru_filter.lua').as_posix()
    script=('FILTER_PATH=[=['+path+']=]\nSOURCE_DIR=[=['+(ROOT/'rime').as_posix()+']=]\n'+code).encode('utf-8')
    state=dll.luaL_newstate()
    try:
        dll.luaL_openlibs(state)
        status=dll.luaL_loadstring(state,script)
        if status==0:status=dll.lua_pcallk(state,0,0,0,0,None)
        assert status==0,(dll.lua_tolstring(state,-1,None) or b'Lua error').decode('utf-8')
        dll.lua_getglobal.argtypes=[C.c_void_p,C.c_char_p]
        dll.lua_tonumberx.argtypes=[C.c_void_p,C.c_int,C.c_void_p];dll.lua_tonumberx.restype=C.c_double
        dll.lua_getglobal(state,b'INDEX_LOAD_SECONDS');load_seconds=dll.lua_tonumberx(state,-1,None)
        dll.lua_getglobal(state,b'INDEX_LUA_MIB');lua_mib=dll.lua_tonumberx(state,-1,None)
    finally:dll.lua_close(state)
    report={'status':'PASS','lua_sha256':hashlib.sha256((ROOT/'rime/lua/booru_filter.lua').read_bytes()).hexdigest(),'checks':['exact-output duplicates','alias and later-stream duplicates','query reset','first-candidate metadata','underscore/space distinctions preserved','spacing and plain modes','literal escaping','matched exact Chinese and completion suffix','segment offsets','v2 role parsing and quoted fields','slang comments with ordinary fallback definitions'],'scope':'Lua mock candidates only; no Rime session, key events or real desktop typing'}
    report.update(dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest(),index_load_cpu_seconds=round(load_seconds,3),index_lua_mib=round(lua_mib,2),memory_scope='Lua standalone index only; not Weasel process memory or typing latency')
    target=ROOT/'validation/gpt/lua-filter-unit.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
