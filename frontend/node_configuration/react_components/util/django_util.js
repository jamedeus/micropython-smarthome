// Takes name of context element created with json_script django tag
// Parses JSON contents if it exists and returns, otherwise returns null
function load_django_context(name) {
    const element = document.getElementById(name);
    if (element) {
        return JSON.parse(element.textContent);
    } else {
        return null;
    }
}

// Parse bool that determines whether editing config (re-upload on submit) or creating new
const edit_existing = load_django_context("edit_existing");

// Parse IP of target node if editing existing config
const target_node_ip = load_django_context("target_node_ip");

// Parse original friendly name of config being edited (prevent duplicate detection from rejecting)
const config = load_django_context("config");
let orig_name;
if (orig_name) {
    orig_name = config.metadata.id.toLowerCase();
}

// Parse ApiTarget options object set by django template
// Contains valid API commands for each instance (device/sensor) of all existing nodes
const api_target_options = load_django_context("api_target_options");

// Parse schedule keywords object from element created by django template
// Contains object with keywords as key, timestamps as value (HH:MM)
const schedule_keywords = load_django_context("schedule_keywords");

// Parse client_ip string from element created by django template
// Displayed in desktop integration instructions
const client_ip = load_django_context("client_ip");

// Parse link to desktop_integration_modal installer zip
const desktop_integration_link = load_django_context("desktop_integration_link");

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

export {
    send_post_request,
    edit_existing,
    orig_name,
    target_node_ip,
    api_target_options,
    schedule_keywords,
    client_ip,
    desktop_integration_link
};
