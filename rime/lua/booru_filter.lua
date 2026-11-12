local M = {}
function M.init(env)
  env.labels = {}
  local file = assert(io.open(rime_api.get_user_data_dir() .. '/booru.tsv', 'r'))
  for line in file:lines() do
    local tag, zh = line:match('^([^\t]+)\t([^\t]+)')
    if tag and tag ~= 'tag' and not env.labels[tag] then env.labels[tag] = zh end
  end
  file:close()
end
function M.func(input, env)
  for cand in input:iter() do
    local label = env.labels[cand.text]
    if label then
      -- Escape literal parentheses/backslashes used by SD prompt parsers.
      local text = cand.text:gsub('([\\()])', '\\%1')
      if env.engine.context:get_option('booru_separator') then text = text .. ', ' end
      local out = Candidate(cand.type, cand.start, cand._end, text, label)
      out.quality = cand.quality
      out.preedit = cand.preedit
      yield(out)
    else
      yield(cand)
    end
  end
end
return M
