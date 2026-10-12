-- Scripted BizHawk harness: reads a job file and executes commands frame-exactly.
-- Job file path: env BH_JOB, else job.txt next to this script.
-- Commands (one per line, # = comment):
--   wait <frames>                 advance N frames with no input
--   press <Button[+Button]> [n]   hold buttons for n frames (default 2), then release 1 frame
--   touch <x> <y> [n]             touch bottom screen at x,y for n frames (default 2)
--   shot <name>                   save framebuffer PNG: <outdir>\<name>_f<frame>.png
--   outdir <path>                 set screenshot output folder
--   savestate <path> / loadstate <path>
--   exit                          close emulator

local job = os.getenv("BH_JOB")
if not job or job == "" then
  local src = debug.getinfo(1, "S").source:sub(2)
  job = src:match("^(.*)[/\\]") .. "\\job.txt"
end
local outdir = os.getenv("BH_OUT") or "."
local logf = io.open(outdir .. "\\capture_log.txt", "w")
local function log(s) if logf then logf:write(s .. "\n"); logf:flush() end; console.log(s) end

local function advance(n, buttons, touch)
  for _ = 1, n do
    if buttons then joypad.set(buttons) end
    if touch then
      joypad.setanalog({ ["Touch X"] = touch[1], ["Touch Y"] = touch[2] })
      joypad.set({ ["Touch"] = true })
    end
    emu.frameadvance()
  end
end

-- Run as fast as possible: no frame throttle, no sound.
emu.limitframerate(false)
client.SetSoundOn(false)

local lines = {}
for l in io.lines(job) do lines[#lines + 1] = l end

for _, raw in ipairs(lines) do
  local l = raw:gsub("#.*", ""):match("^%s*(.-)%s*$")
  if l ~= "" then
    local cmd, rest = l:match("^(%S+)%s*(.*)$")
    if cmd == "wait" then
      advance(tonumber(rest))
    elseif cmd == "press" then
      local btns, n = rest:match("^(%S+)%s*(%d*)$")
      local t = {}
      for b in btns:gmatch("[^+]+") do t[b] = true end
      advance(tonumber(n) or 2, t)
      advance(1)
    elseif cmd == "touch" then
      local x, y, n = rest:match("^(%d+)%s+(%d+)%s*(%d*)$")
      advance(tonumber(n) or 2, nil, { tonumber(x), tonumber(y) })
      advance(1)
    elseif cmd == "outdir" then
      outdir = rest
    elseif cmd == "shot" then
      local f = string.format("%s\\%s_f%06d.png", outdir, rest, emu.framecount())
      client.screenshot(f)
      log("shot " .. f)
    elseif cmd == "savestate" then
      savestate.save(rest)
    elseif cmd == "loadstate" then
      savestate.load(rest)
    elseif cmd == "keys" then
      for k, v in pairs(joypad.get()) do log("key " .. tostring(k) .. "=" .. tostring(v)) end
    elseif cmd == "domains" then
      for _, dn in ipairs(memory.getmemorydomainlist()) do log("domain " .. dn .. " size " .. memory.getmemorydomainsize(dn)) end
    elseif cmd == "dump" then
      local dn, a, n, f = rest:match("^(.-)%s+(%S+)%s+(%S+)%s+(%S+)$")
      local bytes = memory.read_bytes_as_array(tonumber(a), tonumber(n), dn)
      local fh = io.open(outdir .. "\\" .. f, "wb")
      for i = 1, #bytes do fh:write(string.char(bytes[i])) end
      fh:close()
      log("dump " .. dn .. " " .. a .. " " .. n .. " -> " .. f)
    elseif cmd == "watch" then
      local a = tonumber(rest)
      event.onmemorywrite(function(addr, val)
        local ok, pc = pcall(emu.getregister, "ARM9 r15")
        log(string.format("write %08X val %s pc %s lr %s f%d", addr, tostring(val), tostring(pc),
          tostring(select(2, pcall(emu.getregister, "ARM9 r14"))), emu.framecount()))
      end, a, "watch")
      log("watching " .. rest)
    elseif cmd == "regs" then
      for k, v in pairs(emu.getregisters()) do if tostring(k):find("ARM9") then log(k .. "=" .. string.format("%X", v)) end end
    elseif cmd == "exit" then
      log("exit at frame " .. emu.framecount())
      if logf then logf:close() end
      client.exit()
    else
      log("unknown command: " .. l)
    end
  end
end
log("job complete at frame " .. emu.framecount())
if logf then logf:close() end
