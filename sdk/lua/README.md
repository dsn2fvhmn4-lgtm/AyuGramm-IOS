# AyuGram plugins in Lua

Lua 5.4 with the base, coroutine, string, table, math and utf8 libraries (no `io`, `os`, `load`
or files). A plugin is one `.lua` file with a `-- @key value` header, or a `.plugin` bundle.

```lua
-- @id hello.lua
-- @name Hello from Lua
-- @version 1.0
-- @permissions messages

ayu.hooks.before(ayu.points.outgoing_text, function(text, ctx)
  if text == ".shrug" then return "¯\\_(ツ)_/¯" end
  return nil -- nil keeps the text unchanged
end)

ayu.on("load", function() ayu.log("loaded") end)

-- Every API from the documentation is available through ayu.call / ayu.api:
ayu.api("ui.overlay.addText")({ id = "hi", text = "Lua!", anchor = "topRight" })
ayu.request("net.fetch", { url = "https://example.com" }, function(answer) ayu.log(answer.status) end)
```

## `.plugin` bundles

A zip with `plugin.json` (`{"main": "main.lua"}`) and more files in the same language.
`require("util")` loads `util.lua` from the bundle (JavaScript: `require("./util")`).
Python bundles join the helper files before the main file.
