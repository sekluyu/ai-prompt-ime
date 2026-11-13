local M = {}

local function unquote(value)
  if value:sub(1, 1) == '"' and value:sub(-1) == '"' then
    return (value:sub(2, -2):gsub('""', '"'))
  end
  return value
end

local function english(tag)
  return (tag:gsub('^__prompt__:', ''))
end

local function plain(label)
  return (label:gsub('〔.-〕', ''))
end

function M.init(env)
  env.labels, env.label_weights, env.label_levels = {}, {}, {}
  env.matches, env.primary_matches = {}, {}
  local file = assert(io.open(rime_api.get_user_data_dir() .. '/booru.tsv', 'r'))
  for line in file:lines() do
    local tag, zh, code, weight, role = line:match('^([^\t]+)\t([^\t]+)\t([^\t]+)\t(%d+)\t?([^\t]*)')
    if tag and tag ~= 'tag' then
      tag, zh = unquote(tag), unquote(zh)
      weight = tonumber(weight)
      if role == '' then role = tag:match('^__prompt__:') and 'alias' or 'primary' end
      local key, text = tag .. '\t' .. code, english(tag)
      env.matches[key] = zh
      if role == 'primary' then env.primary_matches[key] = true end
      -- Prefer a direct, non-slang definition for explanatory fallback labels.
      local level = (role == 'primary' and 2 or 0) + (zh:find('〔俗称', 1, true) and 0 or 1)
      if not env.labels[text] or level > env.label_levels[text] or
          (level == env.label_levels[text] and weight > env.label_weights[text]) then
        env.labels[text], env.label_weights[text], env.label_levels[text] = zh, weight, level
      end
    end
  end
  file:close()
end

function M.comment(cand, env)
  local fallback = env.labels[english(cand.text)] or env.labels[cand.text]
  local context = env.engine.context
  local raw = context.input or cand.preedit or ''
  local query = raw:sub(cand.start + 1, cand._end):gsub("'+$", '')
  local key = cand.text .. '\t' .. query
  local matched = env.matches and env.matches[key]
  if not matched and cand.comment then
    -- Native table completion comments expose the remaining code. Direct lookup
    -- avoids walking all aliases or materializing the lazy candidate stream.
    local rest = cand.comment:match('^~([a-z]+)$')
    if rest then
      key = cand.text .. '\t' .. query .. rest
      matched = env.matches and env.matches[key]
    end
  end
  if not matched then return fallback end
  if fallback and not (env.primary_matches and env.primary_matches[key]) and plain(matched) ~= plain(fallback) then
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
