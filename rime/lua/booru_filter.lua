local M = {}

local colors = {'red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple',
  'pink', 'black', 'white', 'gray', 'brown', 'gold', 'silver', 'cream', 'tan'}
local species = {'fox', 'wolf', 'dog', 'cat', 'tiger', 'lion', 'leopard',
  'cheetah', 'snow leopard', 'rabbit', 'deer', 'bear', 'panda', 'red panda',
  'raccoon', 'otter', 'hyena', 'horse', 'goat', 'sheep', 'dragon', 'wyvern',
  'gryphon', 'unicorn'}
local random_kinds = {['random fur color']='single', ['random single-color fur']='single',
  ['random two-tone fur']='double', ['random species']='species'}

local function random_text(tag, env)
  local kind = random_kinds[tag]
  if not kind then return tag end
  local context = env.engine.context
  local query = context.input or ''
  if env.random_query ~= query then
    env.random_query, env.random_values = query, {}
  end
  if not env.random_values[kind] then
    local text
    if kind == 'species' then
      text = species[math.random(#species)]
    else
      local first = math.random(#colors)
      if kind == 'single' then
        text = colors[first] .. ' fur'
      else
        local second = math.random(#colors - 1)
        if second >= first then second = second + 1 end
        text = colors[first] .. ' and ' .. colors[second] .. ' fur'
      end
    end
    env.random_values[kind] = text
  end
  return env.random_values[kind]
end

local function english(tag)
  return (tag:gsub('^__prompt__:', ''))
end

local function plain(label)
  return (label:gsub('〔.-〕', ''))
end

-- Keep the full index in one string. Large Lua tables caused per-key stalls
-- in the supported librime build, even with a pass-through filter.
function M.init(env)
  local file = assert(io.open(rime_api.get_user_data_dir() .. '/booru.annotations.tsv', 'rb'))
  env.annotations = file:read('*a')
  file:close()
  math.randomseed(os.time())
  env.random_values = {}
  local context = env.engine.context
  local function clear() env.random_query, env.random_values = nil, {} end
  env.random_commit = context.commit_notifier:connect(clear)
  env.random_update = context.update_notifier:connect(function(ctx)
    if ctx.input == '' then clear() end
  end)
  assert(env.annotations:sub(1, #'# booru-annotations-v1\t') == '# booru-annotations-v1\t', 'Invalid annotation index; rebuild the scheme')
end

function M.fini(env)
  env.random_commit:disconnect()
  env.random_update:disconnect()
end

local function lookup(blob, target)
  local low, high = 1, #blob
  while low <= high do
    local first = math.floor((low + high) / 2)
    while first > 1 and blob:byte(first - 1) ~= 10 do first = first - 1 end
    local last = blob:find('\n', first, true) or (#blob + 1)
    local tab = blob:find('\t', first, true)
    if not tab or tab >= last then return nil end
    local key = blob:sub(first, tab - 1)
    if key == target then
      return blob:sub(tab + 1, last - 3), blob:sub(last - 1, last - 1) == '1'
    elseif key < target then
      low = last + 1
    else
      high = first - 1
    end
  end
end

function M.comment(cand, env)
  local fallback = lookup(env.annotations, 'L:' .. english(cand.text))
  local context = env.engine.context
  local raw = context.input or cand.preedit or ''
  local query = raw:sub(cand.start + 1, cand._end):gsub("'+$", '')
  local prefix = 'M:' .. #cand.text .. ':' .. cand.text .. ':'
  local matched, primary = lookup(env.annotations, prefix .. query)
  if not matched and cand.comment then
    -- Native table completion comments expose the remaining code. Direct lookup
    -- avoids walking all aliases or materializing the lazy candidate stream.
    local rest = cand.comment:match('^~([a-z]+)$')
    if rest then
      matched, primary = lookup(env.annotations, prefix .. query .. rest)
    end
  end
  if not matched then return fallback end
  if fallback and not primary and plain(matched) ~= plain(fallback) then
    return plain(matched) .. ' · ' .. plain(fallback) .. (matched:match('(〔.*)$') or '')
  end
  return matched
end

function M.func(input, env)
  -- Ranking lives in the native dictionary. Keep its lazy, exact-before-prefix
  -- order and remove repeated final text across the whole candidate stream.
  local seen = {}
  for cand in input:iter() do
    local label = M.comment(cand, env)
    if label then
      local text = random_text(english(cand.text), env):gsub('([\\()])', '\\%1')
      if label:find('〔待续写〕', 1, true) then
        text = text .. ' '
      elseif env.engine.context:get_option('booru_separator') then
        text = text .. ','
        if env.engine.context:get_option('booru_space') then text = text .. ' ' end
      end
      if not seen[text] then
        seen[text] = true
        local out = Candidate(cand.type, cand.start, cand._end, text, label)
        out.quality, out.preedit = cand.quality, cand.preedit
        yield(out)
      end
    elseif not seen[cand.text] then
      seen[cand.text] = true
      yield(cand)
    end
  end
end
return M
