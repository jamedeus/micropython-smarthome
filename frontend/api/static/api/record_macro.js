// Overwrite send_command, redirect to add_macro_action view
async function send_command(value) {
    // Add target and selected command to request body
    value["target"] = target_node

    // Add friendly name of target instance (catch error for IR)
    try {
        category = value.instance.replace(/[^a-z]+/g, '');
        value["friendly_name"] = target_node_status[category + 's'][value.instance]['nickname'];
    }catch(err){};

    var payload = {'name': recording, 'action': value}

    let csrftoken = getCookie('csrftoken');

    var result = await fetch('/add_macro_action', {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: { 'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            "X-CSRFToken": csrftoken }
    });

    return result
};
