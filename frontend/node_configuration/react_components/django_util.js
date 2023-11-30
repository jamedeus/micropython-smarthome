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

export { send_post_request, edit_existing, orig_name, api_target_options };
