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
};

async function send_post_request(url, body) {
    let csrftoken = getCookie('csrftoken');

    var response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: { 'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            "X-CSRFToken": csrftoken }
    });

    return response
};

// Takes true (edit existing config and reupload) or false (create new config)
async function submit_form(edit) {
    const value = Object.fromEntries(new FormData(document.getElementById("form")).entries());

    // Update all instance properties before sending to backend
    for (sensor in instances['sensors']) {
        instances['sensors'][sensor].update();
    };

    for (device in instances['devices']) {
        instances['devices'][device].update();
    };

    // Add to request body
    value['sensors'] = instances['sensors']
    value['devices'] = instances['devices']

    console.log(value)

    // Generate config file from form data
    if (edit) {
        var response = await send_post_request(base_url + "generateConfigFile/True", value);
    } else {
        var response = await send_post_request("generateConfigFile", value);
    };

    // If successfully created new config, redirect to overview
    if (!edit && response.ok) {
        // Redirect back to overview where user can upload the newly-created config
        window.location.replace("/node_configuration");

    // If successfully edited existing config, re-upload to target node
    } else if (edit && response.ok) {
        reupload();

    // If config with same name already exists, show modal allowing user to overwrite
    } else if (!edit && response.status == 409) {
        handle_duplicate_prompt();

    // If other error, display in alert
    } else {
        alert(await response.text());

        // Re-enable submit button so user can try again
        document.getElementById("submit-button").disabled = false;

        return false;
    };
};

async function reupload() {
    // Show loading screen
    show_modal("upload-modal");

    // Reupload config file
    var result = await send_post_request(base_url + "upload/True", {config: target_filename, ip: target_ip});

    // If reupload successful, redirect back to overview (otherwise display error in alert)
    if (result.ok) {
        // Change title, show success animation
        const title = "Upload Complete"
        const body = `<svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                            <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                            <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                        </svg>`
        show_modal("upload-modal", title, body);

        // Wait for animation to complete before redirect
        await sleep(1200);
        window.location.replace("/node_configuration");

    // Unable to upload because node has not run setup
    } else if (result.status == 409) {
        const error = await result.text();
        run_setup_prompt(error);

    // Unable to upload because node is unreachable
    } else if (result.status == 404) {
        target_unreachable_prompt();

    // Other error, show in alert
    } else {
        alert(await result.text());

        // Re-enable submit button so user can try again
        document.getElementById("submit-button").disabled = false;
    };
};

// Shown when config with the same name already exists
function handle_duplicate_prompt() {
    // Get duplicate name, add to modal body
    const name = document.getElementById("friendlyName").value;
    document.getElementById("duplicate-modal-body").innerHTML = `<p>Config named <b>${name}</b> already exists. Would you like to overwrite it? This cannot be undone.</p>`
    $('#duplicate-modal').modal('show');

    // Add listener to overwrite button, sends delete command for the existing config then re-submits form
    $('#confirm-overwrite').click(async function() {
        // Disable listener once triggered, prevent overwrite button stacking multiple actions
        $('#confirm-overwrite').off('click');

        var response = await send_post_request("delete_config", name + ".json");

        // Re-submit form
        submit_form(false);
    });

    // Add listener to cancel button
    $('#cancel-overwrite').click(function() {
        // Prevent stacking listeners on overwrite button each time cancel pressed
        $('#confirm-overwrite').off('click');
        document.getElementById("submit-button").disabled = false;
    });
};

// Shown when unable to upload because target node has not run setup yet
async function run_setup_prompt(error) {
    const footer = `<button type="button" id="yes-button" class="btn btn-secondary" data-bs-dismiss="modal">Yes</button>
                    <button type="button" id="no-button" class="btn btn-secondary" data-bs-dismiss="modal">No</button>`

    // Replace loading modal with error modal, ask if user wants to run setup routine
    $('#upload-modal').modal('hide');
    show_modal("error-modal", "Error", `${error}`, footer);

    $('#yes-button').click(async function() {
        // Remove listeners (prevent stacking)
        $('#yes-button').off('click');

        // Show loading again, upload setup file
        $("#error-modal").modal("hide");
        show_modal("upload-modal");
        var result = await send_post_request(base_url + "setup", {ip: target_ip});

        if (result.ok) {
            // After uploading config, tell user to reboot node then click OK
            $("#upload-modal").modal("hide");
            const footer = `<button type="button" id="ok-button" class="btn btn-success" data-bs-dismiss="modal">OK</button>`
            show_modal("error-modal", "Success", "Please reboot node, then press OK to resume upload", footer);

            // When user clicks OK, resubmit form (setup has finished running, should now be able to upload)
            $('#ok-button').click(function() {
                $("#error-modal").modal("hide");
                $('#ok-button').off('click');
                submit_form(true);
            });
        } else {
            alert(await result.text());

            // Re-enable submit button so user can try again
            document.getElementById("submit-button").disabled = false;
        };
    });

    $('#no-button').click(function() {
        // Remove listeners (prevent stacking)
        $('#yes-button').off('click');
        $('#error-modal').modal('hide');
        document.getElementById("submit-button").disabled = false;
    });
};

// Shown when unable to upload because target node unreachable
async function target_unreachable_prompt() {
    $('#upload-modal').modal('hide');

    // Show error modal with instructions
    const footer = `<button type="button" id="ok-button" class="btn btn-success" data-bs-dismiss="modal">OK</button>`
    show_modal("error-modal", "Connection Error", `<p class="text-center">Unable to connect to ${target_ip}<br/>Possible causes:</p><ul><li>Node is not connected to wifi</li><li>Node IP has changed</li><li>Node has not run webrepl_setup</li></ul>`, footer);

    // When user clicks OK, re-enable submit button so user can try again
    $('#ok-button').click(function() {
        $("#error-modal").modal("hide");
        $("#upload-modal").modal("hide");
        $('#ok-button').off('click');
        document.getElementById("submit-button").disabled = false;
    });
};
