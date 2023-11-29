import { useContext } from 'react';
import { ConfigContext } from './ConfigContext';

// Parse bool set by django template, determines whether config is re-uploaded on submit
const edit_existing = JSON.parse(document.getElementById("edit_existing").textContent);

// Get original friendly name if editing (prevents rejecting existing name as duplicate)
if (edit_existing) {
    var orig_name = JSON.parse(document.getElementById("config").textContent).metadata.id.toLowerCase();
}

// Parse ApiTarget options object set by django template
// Contains valid API commands for each instance (device/sensor) of all existing nodes
const api_target_options = JSON.parse(document.getElementById("api_target_options").textContent);

// Takes name of cookie, returns cookie
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


// Takes endpoint and POST body, makes backend request, returns response
async function send_post_request(url, body) {
    let csrftoken = getCookie('csrftoken');

    var response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            "X-CSRFToken": csrftoken
        }
    });

    return response;
}


// TODO completely untested
// Called by submit button on page 3, posts config object to backend
async function submit(submit_button) {
    // Get full config (state object)
    const { config } = useContext(ConfigContext);
    console.log(config)

    // Edit and reupload if editing existing config, otherwise create config
    let response;
    if (edit_existing) {
        response = await send_post_request("generate_config_file/True", config);
    } else {
        response = await send_post_request("generate_config_file", config);
    }

    // If successfully created new config, redirect to overview
    if (!edit_existing && response.ok) {
        // Redirect back to overview where user can upload the newly-created config
        window.location.replace("/config_overview");

        // If successfully edited existing config, re-upload to target node
    } else if (edit_existing && response.ok) {
        // TODO implement
        upload();

        // If config with same name already exists, show modal allowing user to overwrite
    } else if (!edit_existing && response.status == 409) {
        // TODO implement modal, remove submit button arg (hndle in react)
        handle_duplicate_prompt(config.metadata.id, submit_button);

        // If other error, display in alert
    } else {
        alert(await response.text());
        return false;
    }
}


export { send_post_request, submit, edit_existing, orig_name, api_target_options };
