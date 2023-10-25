// Takes true (edit existing config and reupload) or false (create new config)
async function submit_form(edit) {
    // Add IR Blaster config if present
    // TODO add a listener that does this automatically
    if (irblaster_configured.checked) {
        config['ir_blaster'] = {
            'pin': document.getElementById('device0-pin').value,
            'target': []
        };
        document.querySelectorAll('.ir_target').forEach(function(target) {
            if (target.checked) {
                config['ir_blaster']['target'].push(target.id.split('-')[1]);
            };
        });
    } else {
        delete config['ir_blaster'];
    };

    console.log(config)

    // Generate config file from form data
    if (edit) {
        var response = await send_post_request("generate_config_file/True", config);
    } else {
        var response = await send_post_request("generate_config_file", config);
    };

    // If successfully created new config, redirect to overview
    if (!edit && response.ok) {
        // Redirect back to overview where user can upload the newly-created config
        window.location.replace("/config_overview");

    // If successfully edited existing config, re-upload to target node
    } else if (edit && response.ok) {
        upload();

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

// Show warning when config with same name already exists
function handle_duplicate_prompt() {
    const name = document.getElementById("friendlyName").value;
    show_modal(duplicateModal, false, `<p>You are about to overwrite <b>${name}</b>, an existing config.</p><p>This cannot be undone - are you sure?</p>`);

    // If overwrite confirmed delete existing config and resubmit form
    document.getElementById('confirm-overwrite').addEventListener('click', async function() {
        var response = await send_post_request("delete_config", `${name}.json`);
        submit_form(false);
    }, { once: true });

    // Re-enable submit button if overwrite canceled
    document.getElementById('cancel-overwrite').addEventListener('click', function() {
        document.getElementById("submit-button").disabled = false;
    }, { once: true });
};
