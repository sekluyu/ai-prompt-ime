local M = {}
function M.init(env)
  env.labels = {}
  env.label_weights = {}
  -- csv.DictWriter quotes fields containing a literal double quote.
  local function unquote(value)
    if value:sub(1, 1) == '"' and value:sub(-1) == '"' then
      return (value:sub(2, -2):gsub('""', '"'))
    end
    return value
  end
  local file = assert(io.open(rime_api.get_user_data_dir() .. '/booru.tsv', 'r'))
  for line in file:lines() do
    local tag, zh, code, weight = line:match('^([^\t]+)\t([^\t]+)\t([^\t]+)\t(%d+)')
    if tag and tag ~= 'tag' then
      tag, zh = unquote(tag), unquote(zh)
      weight = tonumber(weight)
      if not env.labels[tag] or weight > env.label_weights[tag] then
        env.labels[tag] = zh
        env.label_weights[tag] = weight
      end
    end
  end
  file:close()
end
function M.func(input, env)
  -- One set per candidate stream, including later pages and alias completions.
  local seen = {}
  for cand in input:iter() do
    local label = env.labels[cand.text]
    if label then
      -- Escape literal parentheses/backslashes used by SD prompt parsers.
      local text = cand.text:gsub('^__prompt__:', ''):gsub('([\\()])', '\\%1')
      if env.engine.context:get_option('booru_separator') then
        text = text .. ','
        if env.engine.context:get_option('booru_space') then text = text .. ' ' end
      end
      if not seen[text] then
        seen[text] = true
        local out = Candidate(cand.type, cand.start, cand._end, text, label)
        out.quality = cand.quality
        out.preedit = cand.preedit
        yield(out)
      end
    else
      if not seen[cand.text] then
        seen[cand.text] = true
        yield(cand)
      end
    end
  end
end
return M
