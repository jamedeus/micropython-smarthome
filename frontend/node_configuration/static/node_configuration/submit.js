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
        show_modal("upload-modal", "Upload Complete", upload_complete);

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

        // Hide modal allowing user to access page again
        $('#upload-modal').modal('hide');

        // Re-enable submit button so user can try again
        // TODO would this be global if moved outside conditional??
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
