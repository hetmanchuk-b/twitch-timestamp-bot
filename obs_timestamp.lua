--[[
    Twitch Timestamp Bot — OBS Studio Hotkey Script
    -------------------------------------------------------
    Allows the streamer to press a hotkey in OBS to instantly
    record a stream timestamp without typing in Twitch chat.

    Setup in OBS Studio:
    1. Go to Tools -> Scripts
    2. Click "+" and select this obs_timestamp.lua file
    3. Enter your Bot Server URL and optional API Key
    4. Go to Settings -> Hotkeys and assign a hotkey to
       "Twitch Bot: Save Stream Timestamp"
--]]

obs = obslua

-- Configurable settings
server_url = "http://localhost:8080"
api_key = ""
author_name = "streamer"
default_note = "OBS Hotkey"

hotkey_id = obs.OBS_INVALID_HOTKEY_ID

function script_description()
    return [[<h2>🎬 Twitch Timestamp Bot — OBS Hotkey</h2>
<p>Press a hotkey to save a live stream highlight timestamp without writing in chat.</p>
<hr/>]]
end

function script_properties()
    local props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, "server_url", "Bot Server URL (e.g. https://your-bot.onrender.com):", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "api_key", "API Key (optional, from .env):", obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_text(props, "author_name", "Author Name (default: streamer):", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "default_note", "Default Note / Label:", obs.OBS_TEXT_DEFAULT)
    return props
end

function script_defaults(settings)
    obs.obs_data_set_default_string(settings, "server_url", "http://localhost:8080")
    obs.obs_data_set_default_string(settings, "api_key", "")
    obs.obs_data_set_default_string(settings, "author_name", "streamer")
    obs.obs_data_set_default_string(settings, "default_note", "OBS Hotkey")
end

function script_update(settings)
    server_url = obs.obs_data_get_string(settings, "server_url")
    api_key = obs.obs_data_get_string(settings, "api_key")
    author_name = obs.obs_data_get_string(settings, "author_name")
    default_note = obs.obs_data_get_string(settings, "default_note")

    -- Strip trailing slashes
    if server_url:sub(-1) == "/" then
        server_url = server_url:sub(1, -2)
    end
end

-- URL encoding helper
function url_encode(str)
    if str then
        str = string.gsub(str, "\n", "\r\n")
        str = string.gsub(str, "([^%w %-%_%.%~])",
            function (c) return string.format("%%%02X", string.byte(c)) end)
        str = string.gsub(str, " ", "+")
    end
    return str
end

-- Callback triggered when hotkey is pressed
function trigger_timestamp()
    if not server_url or server_url == "" then
        obs.script_log(obs.LOG_WARNING, "[Twitch Bot] Server URL is not configured.")
        return
    end

    local endpoint = server_url .. "/api/time"
    local query_params = "?author=" .. url_encode(author_name)
    
    if default_note and default_note ~= "" then
        query_params = query_params .. "&note=" .. url_encode(default_note)
    end
    if api_key and api_key ~= "" then
        query_params = query_params .. "&key=" .. url_encode(api_key)
    end

    local full_url = endpoint .. query_params
    obs.script_log(obs.LOG_INFO, "[Twitch Bot] Hotkey triggered! Sending request to: " .. endpoint)

    -- Execute background curl command (works on Windows 10/11, macOS, and Linux)
    local cmd = ""
    if package.config:sub(1,1) == "\\" then
        -- Windows: use start /B to run detached without popping a terminal window
        cmd = 'start /B curl.exe -s --max-time 5 "' .. full_url .. '" > nul 2>&1'
    else
        -- macOS / Linux
        cmd = 'curl -s --max-time 5 "' .. full_url .. '" > /dev/null 2>&1 &'
    end

    os.execute(cmd)
end

function on_hotkey_pressed(pressed)
    if pressed then
        trigger_timestamp()
    end
end

function script_load(settings)
    hotkey_id = obs.obs_hotkey_register_frontend(
        "twitch_timestamp_save_hotkey",
        "Twitch Bot: Save Stream Timestamp",
        on_hotkey_pressed
    )
    local hotkey_save_array = obs.obs_data_get_array(settings, "twitch_timestamp_save_hotkey")
    obs.obs_data_array_release(hotkey_save_array)
end

function script_save(settings)
    local hotkey_save_array = obs.obs_hotkey_save(hotkey_id)
    obs.obs_data_set_array(settings, "twitch_timestamp_save_hotkey", hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)
end
