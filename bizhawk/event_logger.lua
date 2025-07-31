-- IWRAM/EWRAM Monitor Script for BizHawk
local REGIONS = {
    { name = "iwram", START = 0x03000000, SIZE = 0x8000 },
    { name = "ewram", START = 0x02000000, SIZE = 0x40000 }
}
local IWRAM_CHUNK_SIZE = math.floor(0x8000 / 5)  -- 0x8000 / 5 = 0x1000 = 4096
local EWRAM_CHUNK_SIZE = math.floor(0x40000 / 5) -- 0x40000 / 5 = 0x8000 = 32768


local prev_frame = {}
local access_freq = {}
local recent_changes = {}     -- Track recent changes for sliding window frequency
local FREQ_WINDOW_SIZE = 100  -- Frequency window size in frames
local FPS = 60
local key_history = {}

-- Frame set and chunk tracking
local frame_set_id = 0
local current_chunk_id = 0  -- 0-4: chunk number processed each frame (both IWRAM and EWRAM)

-- Buffered logging with enhanced safety
local log_buffer = {}
local LOG_BUFFER_SIZE = 200         -- Increased from 100 to reduce flush frequency
local FORCE_FLUSH_INTERVAL = 300    -- Force flush every 300 frames (5 seconds at 60fps)

local function flush_log_buffer()
    if #log_buffer == 0 then return end
    local log_filename = "C:\\Users\\Danimal\\Downloads\\BizHawk-2.10-win-x64\\event_logs\\event_log.csv"
    local f = io.open(log_filename, "a")
    if f then
        for _, line in ipairs(log_buffer) do
            f:write(line)
        end
        f:close()
    else
        print("Error: Could not open log file for writing")
    end
    log_buffer = {}
end

-- Enhanced exit handler with error protection
local function safe_exit_handler()
    print("Script terminating - flushing remaining logs...")
    local success, error_msg = pcall(flush_log_buffer)
    if not success then
        print("Error during log flush: " .. tostring(error_msg))
    end
    print("Log flush complete")
end

-- Register multiple exit handlers for different termination scenarios
event.onexit(safe_exit_handler)

-- Also flush on script unload (additional safety)
if event.onloadstate then
    event.onloadstate(function()
        print("State loaded - flushing logs for safety...")
        pcall(flush_log_buffer)
    end)
end


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
    local timestamp = os.time() * 1000 + math.floor((emu.framecount() % FPS) * (1000 / FPS))
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
    local log_line = string.format("%d,%s,%d,%08X,%08X,%08X,%d,%08X,%s,%s,%d,%d\n",
        timestamp,
        region,
        frame,
        addr,
        prev_val,
        curr_val,
        freq,
        pc,
        last_keys_str,
        current_keys,
        frame_set_id,
        current_chunk_id
    )
    table.insert(log_buffer, log_line)
    if #log_buffer >= LOG_BUFFER_SIZE then
        flush_log_buffer()
    end
end


local scan_offsets = { iwram = 0, ewram = 0 }
local current_step = 0
local last_forced_flush = 0  -- Track last forced flush frame


function track_changes(frame)
    local pc = emu.getregister("R15") or 0
    -- Capture and update key history
    local current_keys = get_current_keys()
    push_key_history(current_keys)
    local last_keys_str = get_last_n_keys(5)

    -- Check if we're about to complete both memory region scans (final chunk)
    local iwram_will_reset = (scan_offsets.iwram + IWRAM_CHUNK_SIZE) >= REGIONS[1].SIZE
    local ewram_will_reset = (scan_offsets.ewram + EWRAM_CHUNK_SIZE) >= REGIONS[2].SIZE
    local is_final_chunk = iwram_will_reset and ewram_will_reset

    -- Calculate current chunk ID based on offsets
    -- Both IWRAM and EWRAM process the same chunk number each frame (0-4)
    local iwram_chunk = math.floor(scan_offsets.iwram / IWRAM_CHUNK_SIZE)
    local ewram_chunk = math.floor(scan_offsets.ewram / EWRAM_CHUNK_SIZE)
    -- Since both regions process in sync, they should have the same chunk number
    current_chunk_id = iwram_chunk  -- 0-4

    -- Combined IWRAM and EWRAM analysis
    do
        local iwram_region = REGIONS[1]
        local ewram_region = REGIONS[2]
        
        local iwram_chunk_start = scan_offsets.iwram
        local iwram_chunk_end = math.min(iwram_chunk_start + IWRAM_CHUNK_SIZE - 1, iwram_region.SIZE - 1)
        
        local ewram_chunk_start = scan_offsets.ewram
        local ewram_chunk_end = math.min(ewram_chunk_start + EWRAM_CHUNK_SIZE - 1, ewram_region.SIZE - 1)
        
        -- Process IWRAM chunk
        for offset = iwram_chunk_start, iwram_chunk_end, 4 do
            local addr = iwram_region.START + offset
            local curr_val = memory.read_u32_le(addr)
            local prev_val = prev_frame[addr]
            if prev_val and curr_val ~= prev_val then
                -- Update sliding window frequency
                if not recent_changes[addr] then
                    recent_changes[addr] = {}
                end
                table.insert(recent_changes[addr], frame)
                
                -- Clean old entries outside the window
                local window_start = frame - FREQ_WINDOW_SIZE
                local filtered_changes = {}
                for _, change_frame in ipairs(recent_changes[addr]) do
                    if change_frame >= window_start then
                        table.insert(filtered_changes, change_frame)
                    end
                end
                recent_changes[addr] = filtered_changes
                
                -- Calculate frequency as changes within the window
                local recent_freq = #recent_changes[addr]
                
                -- Keep global counter for backward compatibility
                access_freq[addr] = (access_freq[addr] or 0) + 1
                
                log_change(iwram_region.name, addr, prev_val, curr_val, frame, recent_freq, pc, last_keys_str, current_keys)
            end
            prev_frame[addr] = curr_val
        end
        
        -- Process EWRAM chunk
        for offset = ewram_chunk_start, ewram_chunk_end, 4 do
            local addr = ewram_region.START + offset
            local curr_val = memory.read_u32_le(addr)
            local prev_val = prev_frame[addr]
            if prev_val and curr_val ~= prev_val then
                -- Update sliding window frequency
                if not recent_changes[addr] then
                    recent_changes[addr] = {}
                end
                table.insert(recent_changes[addr], frame)
                
                -- Clean old entries outside the window
                local window_start = frame - FREQ_WINDOW_SIZE
                local filtered_changes = {}
                for _, change_frame in ipairs(recent_changes[addr]) do
                    if change_frame >= window_start then
                        table.insert(filtered_changes, change_frame)
                    end
                end
                recent_changes[addr] = filtered_changes
                
                -- Calculate frequency as changes within the window
                local recent_freq = #recent_changes[addr]
                
                -- Keep global counter for backward compatibility
                access_freq[addr] = (access_freq[addr] or 0) + 1
                
                log_change(ewram_region.name, addr, prev_val, curr_val, frame, recent_freq, pc, last_keys_str, current_keys)
            end
            prev_frame[addr] = curr_val
        end
        
        -- Update offsets for both regions
        scan_offsets.iwram = iwram_chunk_end + 1
        if scan_offsets.iwram >= iwram_region.SIZE then
            scan_offsets.iwram = 0
        end
        
        scan_offsets.ewram = ewram_chunk_end + 1
        if scan_offsets.ewram >= ewram_region.SIZE then
            scan_offsets.ewram = 0
            -- Only take a snapshot when final chunks are completed
            local snapshot_dir = "C:\\Users\\Danimal\\Downloads\\BizHawk-2.10-win-x64\\snapshots"
            local snap_path = string.format("%s\\%d.png", snapshot_dir, frame_set_id)
            client.screenshot(snap_path)
        end
    end
    
    -- Increment frame_set_id when both regions have completed their cycles
    if is_final_chunk then
        frame_set_id = frame_set_id + 1
    end
    
    current_step = current_step + 1
end

while emu.framecount() == 0 do
    emu.yield()
end

event.onframeend(function()
    -- Wrap in pcall for error protection
    local success, error_msg = pcall(track_changes, emu.framecount())
    if not success then
        print("Error in track_changes: " .. tostring(error_msg))
        -- Force flush on error to preserve data
        pcall(flush_log_buffer)
    end
end)

print("🔍 IWRAM/EWRAM Tracker Initialized")
