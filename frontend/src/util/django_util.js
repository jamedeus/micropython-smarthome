// Takes name of context element created with json_script django tag
// Parses JSON contents if it exists and returns, otherwise returns null
function parse_dom_context(name) {
    const element = document.getElementById(name);
    if (element) {
        return JSON.parse(element.textContent);
    } else {
        return null;
    }
}

// Parse bool that determines whether editing config (re-upload on submit) or creating new
const edit_existing = parse_dom_context("edit_existing");

// Parse IP of target node if editing existing config
const target_node_ip = parse_dom_context("target_node_ip");

// Parse original friendly name of config being edited (prevent duplicate detection from rejecting)
const config = parse_dom_context("config");
let orig_name;
if (orig_name) {
    orig_name = config.metadata.id.toLowerCase();
}

// Parse ApiTarget options object set by django template
// Contains valid API commands for each instance (device/sensor) of all existing nodes
const api_target_options = parse_dom_context("api_target_options");

// Takes name of cookie, returns cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
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
    const csrftoken = getCookie('csrftoken');

    const response = await fetch(url, {
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
    parse_dom_context,
    getCookie,
    send_post_request,
    edit_existing,
    orig_name,
    target_node_ip,
    api_target_options
};
