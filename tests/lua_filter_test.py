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
'''
    path=(ROOT/'rime/lua/booru_filter.lua').as_posix()
    script=('FILTER_PATH=[=['+path+']=]\n'+code).encode('utf-8')
    state=dll.luaL_newstate()
    try:
        dll.luaL_openlibs(state)
        status=dll.luaL_loadstring(state,script)
        if status==0:status=dll.lua_pcallk(state,0,0,0,0,None)
        assert status==0,(dll.lua_tolstring(state,-1,None) or b'Lua error').decode('utf-8')
    finally:dll.lua_close(state)
    report={'status':'PASS','lua_sha256':hashlib.sha256((ROOT/'rime/lua/booru_filter.lua').read_bytes()).hexdigest(),'checks':['exact-output duplicates','alias and later-stream duplicates','query reset','first-candidate metadata','underscore/space distinctions preserved','spacing and plain modes','literal escaping'],'scope':'Lua mock candidates only; no Rime session, key events or real desktop typing'}
    target=ROOT/'validation/gpt/lua-filter-unit.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
