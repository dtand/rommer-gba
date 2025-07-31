-- IWRAM/EWRAM Monitor Script for BizHawk
local REGIONS = {
    { name = "iwram", START = 0x03000000, SIZE = 0x8000 },
    { name = "ewram", START = 0x02000000, SIZE = 0x40000 }
}
local IWRAM_CHUNK_SIZE = math.floor(0x8000 / 16)  -- 0x8000 / 16 = 0x400 = 1024
local EWRAM_CHUNK_SIZE = math.floor(0x40000 / 16) -- 0x40000 / 16 = 0x4000 = 16384


local prev_frame = {}
local access_freq = {}
local FPS = 60
local frame_count = 0
local key_history = {}

-- Buffered logging
local log_buffer = {}
local LOG_BUFFER_SIZE = 100

local function flush_log_buffer()
    if #log_buffer == 0 then return end
    local log_filename = "C:\\Users\\Danimal\\Downloads\\BizHawk-2.10-win-x64\\event_logs\\event_log.csv"
    local f = io.open(log_filename, "a")
    if f then
        for _, line in ipairs(log_buffer) do
            f:write(line)
        end
        f:close()
    end
    log_buffer = {}
end

-- Flush buffer on script exit
event.onexit(function()
    flush_log_buffer()
end)


-- Log rotation at script start
local log_filename = "C:\\Users\\Danimal\\Downloads\\BizHawk-2.10-win-x64\\event_logs\\event_log.csv"
local attr = io.open(log_filename, "r")
if attr then
    attr:close()
    local ts = os.time()
    local rotated = string.format("C:\\Users\\Danimal\\Downloads\\BizHawk-2.10-win-x64\\event_logs\\event_log_%d.csv", ts)
    os.rename(log_filename, rotated)
end

-- Clear the snapshots directory at script start
local snapshot_dir = "C:\\Users\\Danimal\\Downloads\\BizHawk-2.10-win-x64\\snapshots"
os.execute('mkdir "' .. snapshot_dir .. '" >nul 2>&1')
for file in io.popen('dir /b "' .. snapshot_dir .. '"'):lines() do
    os.remove(snapshot_dir .. "\\" .. file)
end

function get_current_keys()
    local keys = input.get()
    local gba_keys = {
        X = true, Z = true, W = true, E = true,
        Enter = true, Space = true,
        Up = true, Down = true, Left = true, Right = true
    }
    local pressed_keys = {}
    for k, v in pairs(keys) do
        if v and gba_keys[k] then
            table.insert(pressed_keys, k)
        end
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

function log_change(region, addr, prev_val, curr_val, frame, freq, pc, last_keys_str, current_keys)
    local timestamp = os.time() * 1000 + math.floor((frame_count % FPS) * (1000 / FPS))
    if not last_keys_str or last_keys_str == "" then
        last_keys_str = "None"
    end
    if not current_keys or current_keys == "" then
        current_keys = "None"
    end
    -- Escape double quotes in last_keys_str and wrap in quotes if it contains a comma
    if string.find(last_keys_str, '[,\"]') then
        last_keys_str = '"' .. last_keys_str:gsub('"', '""') .. '"'
    end
    local log_line = string.format("%d,%s,%d,%08X,%08X,%08X,%d,%08X,%s,%s\n",
        timestamp,
        region,
        frame,
        addr,
        prev_val,
        curr_val,
        freq,
        pc,
        last_keys_str,
        current_keys
    )
    table.insert(log_buffer, log_line)
    if #log_buffer >= LOG_BUFFER_SIZE then
        flush_log_buffer()
    end
end


local scan_offsets = { iwram = 0, ewram = 0 }
local current_step = 0


function track_changes(frame)
    local pc = emu.getregister("R15") or 0
    -- Capture and update key history
    local current_keys = get_current_keys()
    push_key_history(current_keys)
    local last_keys_str = get_last_n_keys(5)

    -- Only take a snapshot when reading the first chunk
    local snapshot_dir = "C:\\Users\\Danimal\\Downloads\\BizHawk-2.10-win-x64\\snapshots"
    local snap_path = string.format("%s\\%d.png", snapshot_dir, frame)
    client.screenshot(snap_path)

    -- IWRAM analysis
    do
        local region = REGIONS[1]
        local MEM_START = region.START
        local MEM_SIZE = region.SIZE
        local region_name = region.name
        local chunk_start = scan_offsets.iwram
        local chunk_end = math.min(chunk_start + IWRAM_CHUNK_SIZE - 1, MEM_SIZE - 1)
        for offset = chunk_start, chunk_end, 4 do
            local addr = MEM_START + offset
            local curr_val = memory.read_u32_le(addr)
            local prev_val = prev_frame[addr]
            if prev_val and curr_val ~= prev_val then
                access_freq[addr] = (access_freq[addr] or 0) + 1
                log_change(region_name, addr, prev_val, curr_val, frame, access_freq[addr], pc, last_keys_str, current_keys)
            end
            prev_frame[addr] = curr_val
        end
        scan_offsets.iwram = chunk_end + 1
        if scan_offsets.iwram >= MEM_SIZE then
            scan_offsets.iwram = 0
        end
    end

    -- EWRAM analysis (added at line 144)
    do
        local region = REGIONS[2]
        local MEM_START = region.START
        local MEM_SIZE = region.SIZE
        local region_name = region.name
        local chunk_start = scan_offsets.ewram
        local chunk_end = math.min(chunk_start + EWRAM_CHUNK_SIZE - 1, MEM_SIZE - 1)
        for offset = chunk_start, chunk_end, 4 do
            local addr = MEM_START + offset
            local curr_val = memory.read_u32_le(addr)
            local prev_val = prev_frame[addr]
            if prev_val and curr_val ~= prev_val then
                access_freq[addr] = (access_freq[addr] or 0) + 1
                log_change(region_name, addr, prev_val, curr_val, frame, access_freq[addr], pc, last_keys_str, current_keys)
            end
            prev_frame[addr] = curr_val
        end
        scan_offsets.ewram = chunk_end + 1
        if scan_offsets.ewram >= MEM_SIZE then
            scan_offsets.ewram = 0
        end
    end
    current_step = current_step + 1
end



while emu.framecount() == 0 do
    emu.yield()
end

local frame_skip = 1

event.onframeend(function()
    frame_count = frame_count + 1
    if frame_count % frame_skip == 0 then
        track_changes(emu.framecount())
    end
end)

print("🔍 IWRAM/EWRAM Tracker Initialized")
