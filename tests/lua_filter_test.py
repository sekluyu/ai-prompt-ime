"""Exercise the Lua filter with mock candidates; no Rime session or key events."""
import ctypes as C
import hashlib
import json
import os
import subprocess
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
local function fixture_index(e)
  local records={}
  for tag,zh in pairs(e.labels or {}) do
    tag=tag:gsub('^__prompt__:', '')
    records['L:'..tag]=zh..'\t0'
  end
  for key,zh in pairs(e.matches or {}) do
    local tag,code=key:match('^(.-)\t(.*)$')
    records['M:'..#tag..':'..tag..':'..code]=zh..'\t'..((e.primary_matches or {})[key] and '1' or '0')
  end
  local keys={}
  for key in pairs(records) do keys[#keys+1]=key end
  table.sort(keys)
  local lines={'# booru-annotations-v1\ttest'}
  for _,key in ipairs(keys) do lines[#lines+1]=key..'\t'..records[key] end
  e.annotations=table.concat(lines,'\n')..'\n'
end
local function run(words)
  fixture_index(env)
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

-- A complete two-hand phrase remains one candidate and one final delimiter.
local paired='left hand resting on hip, right hand touching head'
env.labels[paired]='左手扶腰右手摸头〔通用姿态·双手〕'
values.booru_separator=true
values.booru_space=true
assert(run({'__prompt__:'..paired})[1].text==paired..', ')
values.booru_space=false
assert(run({'__prompt__:'..paired})[1].text==paired..',')
values.booru_separator=false
assert(run({'__prompt__:'..paired})[1].text==paired)

-- Exact aliases and native completion suffixes choose the matching Chinese,
-- not whichever label happened to be the highest-frequency label for a tag.
env.labels['fennec_fox']='耳廓狐'
env.labels['high quality']='高质量〔质量词〕'
env.matches={['__prompt__:fennec_fox\thuli']='狐狸〔e621〕',
             ['__prompt__:high quality\tzhilianggenggao']='质量更高〔质量词〕'}
env.primary_matches={['__prompt__:high quality\tzhilianggenggao']=true}
fixture_index(env)
env.engine.context.input='huli'
assert(filter.comment({text='__prompt__:fennec_fox',start=0,_end=4},env)=='狐狸 · 耳廓狐〔e621〕')
env.engine.context.input='hul'
assert(filter.comment({text='__prompt__:fennec_fox',start=0,_end=3,comment='~i'},env)=='狐狸 · 耳廓狐〔e621〕')
env.engine.context.input='zhilianggenggao'
assert(filter.comment({text='__prompt__:high quality',start=0,_end=#'zhilianggenggao'},env)=='质量更高〔质量词〕')
env.engine.context.input='xxhuli'
assert(filter.comment({text='__prompt__:fennec_fox',start=2,_end=6},env)=='狐狸 · 耳廓狐〔e621〕')

-- Candidate fields containing literal quotes survive the compiled index.
env.matches['__prompt__:"honest"_john\tchengshiyuehan']='诚实约翰'
fixture_index(env)
env.engine.context.input='chengshiyuehan'
assert(filter.comment({text='__prompt__:"honest"_john',start=0,_end=#'chengshiyuehan'},env)=='诚实约翰')
local old_api=rime_api

-- Load the actual compiled annotations, still with a fake
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
indexed.engine.context.input='zuoshoufuyaoyoushoumotou'
assert(filter.comment({text='__prompt__:left hand resting on hip, right hand touching head',start=0,_end=#indexed.engine.context.input},indexed)=='左手扶腰右手摸头〔通用姿态·双手〕')
indexed.engine.context.input='lingyizhishoufangdatuishang'
assert(filter.comment({text='__prompt__:the other hand resting on thigh',start=0,_end=#indexed.engine.context.input},indexed)=='另一只手放大腿上〔通用姿态·单手〕')
rime_api=old_api

-- Compare every exact mapping against the shipped v0.2.6 implementation.
-- The large legacy tables exist only in this standalone regression process.
rime_api={get_user_data_dir=function()return SOURCE_DIR end}
local legacy=assert(load(BASELINE_CODE))()
local previous={engine=indexed.engine}
legacy.init(previous)
local function unquote(value)
  if value:sub(1,1)=='"' and value:sub(-1)=='"' then
    return (value:sub(2,-2):gsub('""','"'))
  end
  return value
end
local file=assert(io.open(SOURCE_DIR..'/booru.tsv','r'))
local count=0
for line in file:lines() do
  local tag,zh,code=line:match('^([^\t]+)\t([^\t]+)\t([^\t]+)\t%d+')
  if tag then
    tag=unquote(tag)
    indexed.engine.context.input=code
    local cand={text=tag,start=0,_end=#code}
    assert(filter.comment(cand,indexed)==legacy.comment(cand,previous),'Exact annotation mismatch: '..code)
    count=count+1
    if count%251==0 and #code>1 then
      indexed.engine.context.input=code:sub(1,-2)
      cand._end=#code-1
      cand.comment='~'..code:sub(-1)
      assert(filter.comment(cand,indexed)==legacy.comment(cand,previous),'Completion mismatch: '..code)
      cand.comment=nil
      indexed.engine.context.input='!'
      cand._end=1
      assert(filter.comment(cand,indexed)==legacy.comment(cand,previous),'Fallback mismatch: '..code)
    end
  end
end
file:close()
EXACT_MAPPINGS_CHECKED=count
rime_api=old_api
'''
    path=(ROOT/'rime/lua/booru_filter.lua').as_posix()
    baseline=subprocess.check_output(['git','show','v0.2.6:rime/lua/booru_filter.lua'],cwd=ROOT).decode('utf-8')
    script=('BASELINE_CODE=[====['+baseline+']====]\nFILTER_PATH=[=['+path+']=]\nSOURCE_DIR=[=['+(ROOT/'rime').as_posix()+']=]\n'+code).encode('utf-8')
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
        dll.lua_getglobal(state,b'EXACT_MAPPINGS_CHECKED');exact_checked=int(dll.lua_tonumberx(state,-1,None))
    finally:dll.lua_close(state)
    report={'status':'PASS','lua_sha256':hashlib.sha256((ROOT/'rime/lua/booru_filter.lua').read_bytes()).hexdigest(),'checks':['exact-output duplicates','alias and later-stream duplicates','query reset','first-candidate metadata','underscore/space distinctions preserved','spacing and plain modes','literal escaping','matched exact Chinese and completion suffix','segment offsets','v2 role parsing and quoted fields','slang comments with ordinary fallback definitions'],'scope':'Lua mock candidates only; no Rime session, key events or real desktop typing'}
    report.update(annotations_sha256=hashlib.sha256((ROOT/'rime/booru.annotations.tsv').read_bytes()).hexdigest(),dictionary_sha256=hashlib.sha256((ROOT/'rime/booru.tsv').read_bytes()).hexdigest(),index_load_cpu_seconds=round(load_seconds,3),index_lua_mib=round(lua_mib,2),memory_scope='Lua standalone index only; not Weasel process memory or typing latency')
    report.update(exact_mappings_compared=exact_checked,reference='v0.2.6 Lua',sampled_completion_and_fallback=True)
    target=ROOT/'validation/gpt/lua-filter-unit.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
