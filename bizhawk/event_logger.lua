-- IWRAM/EWRAM Monitor Script for BizHawk
local REGIONS = {
    { name = "iwram", START = 0x03000000, SIZE = 0x8000 },
    { name = "ewram", START = 0x02000000, SIZE = 0x40000 }
}
local CHUNK_SIZE = 0x400  -- Scan 1KB per event

local prev_frame = {}
local access_freq = {}
local FPS = 60
local frame_count = 0
local key_history = {}

os.execute("mkdir \"event_logs\"")
os.execute("mkdir \"snapshots\"")

function get_current_keys()
    local keys = input.get()
    local pressed_keys = {}
    for k, v in pairs(keys) do
        if v then table.insert(pressed_keys, k) end
    end
    table.sort(pressed_keys)
    return table.concat(pressed_keys, "+")
end

function push_key_history(current_keys)
    if current_keys ~= "" then
        table.insert(key_history, current_keys)
        if #key_history > 20 then
            table.remove(key_history, 1)
        end
    end
end

function get_last_n_keys(n)
    local start_idx = math.max(1, #key_history - n + 1)
    local last_keys = {}
    for i = start_idx, #key_history do
        table.insert(last_keys, key_history[i])
    end
    return table.concat(last_keys, " | ")
end

local json = require("json")  -- BizHawk Lua usually has a JSON library; if not, use a compatible one

function log_change(region, addr, prev_val, curr_val, frame, freq, pc, last_keys_str)
    -- Prepare data table
    local timestamp = os.time() * 1000 + math.floor((frame_count % FPS) * (1000 / FPS))
    local data = {
        unix_milli = timestamp,
        memory_region = region,
        frame = frame,
        address = string.format("%08X", addr),
        prev_val_hex = string.format("%08X", prev_val),
        new_val_hex = string.format("%08X", curr_val),
        total_changes = freq,
        pc_address = string.format("%08X", pc),
        key_history = {}
    }
    -- Parse last_keys_str into array (split on '|', trim spaces, reverse order)
    for key in string.gmatch(last_keys_str, "([^|]+)") do
        key = key:gsub("^%s+", ""):gsub("%s+$", "")
        table.insert(data.key_history, 1, key) -- insert at front for reverse order
    end

    -- Write JSON file named after the frame
    local filename = string.format("event_logs/%d.json", frame)
    local f = io.open(filename, "w")
    if f then
        f:write(json.encode(data))
        f:close()
    end
end

local scan_offset = 0
local region_index = 1

function track_changes(frame)
    local region = REGIONS[region_index]
    local MEM_START = region.START
    local MEM_SIZE = region.SIZE
    local region_name = region.name

    local chunk_start = scan_offset
    local chunk_end = math.min(chunk_start + CHUNK_SIZE - 1, MEM_SIZE - 1)
    local pc = emu.getregister("R15") or 0

    -- Capture and update key history
    local current_keys = get_current_keys()
    push_key_history(current_keys)
    local last_keys_str = get_last_n_keys(5)

    for offset = chunk_start, chunk_end, 4 do
        local addr = MEM_START + offset
        local curr_val = memory.read_u32_le(addr)
        local prev_val = prev_frame[addr]
        if prev_val and curr_val ~= prev_val then
            access_freq[addr] = (access_freq[addr] or 0) + 1
            log_change(region_name, addr, prev_val, curr_val, frame, access_freq[addr], pc, last_keys_str)
        end
        prev_frame[addr] = curr_val
    end

    -- Take a snapshot every 10th frame, named by frame
    if frame % 10 == 0 then
        client.screenshot(string.format("snapshots/snap_%d.png", frame))
    end

    scan_offset = chunk_end + 1
    if scan_offset >= MEM_SIZE then
        scan_offset = 0
        region_index = region_index + 1
        if region_index > #REGIONS then
            region_index = 1
        end
    end
end

local frame_skip = 1

event.onframeend(function()
    frame_count = frame_count + 1
    if frame_count % frame_skip == 0 then
        track_changes(frame_count)
    end
end)

for k, v in pairs(emu.getregisters()) do print(k, v) end
print("🔍 IWRAM/EWRAM Tracker Initialized")
