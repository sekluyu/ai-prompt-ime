local M = {}

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
  assert(env.annotations:sub(1, #'# booru-annotations-v1\t') == '# booru-annotations-v1\t', 'Invalid annotation index; rebuild the scheme')
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
      local text = english(cand.text):gsub('([\\()])', '\\%1')
      if env.engine.context:get_option('booru_separator') then
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
