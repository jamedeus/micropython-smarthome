// Called by submit button on page 3, posts config object to backend
async function submit(submit_button) {
    // Disable submit button, prevent submitting multiple times
    submit_button.disabled = true;

    console.log(config)

    // Edit and reupload if editing existing config, otherwise create config
    if (edit_existing) {
        var response = await send_post_request("generate_config_file/True", config);
    } else {
        var response = await send_post_request("generate_config_file", config);
    };

    // If successfully created new config, redirect to overview
    if (!edit_existing && response.ok) {
        // Redirect back to overview where user can upload the newly-created config
        window.location.replace("/config_overview");

    // If successfully edited existing config, re-upload to target node
    } else if (edit_existing && response.ok) {
        upload();

    // If config with same name already exists, show modal allowing user to overwrite
    } else if (!edit_existing && response.status == 409) {
        handle_duplicate_prompt(config.metadata.id, submit_button);

    // If other error, display in alert
    } else {
        alert(await response.text());

        // Re-enable submit button so user can try again
        submit_button.disabled = false;

        return false;
    };
};


// Takes duplicate name and reference to submit_button, shows modal
function handle_duplicate_prompt(name, submit_button) {
    show_modal(duplicateModal, false, `<p>You are about to overwrite <b>${name}</b>, an existing config.</p><p>This cannot be undone - are you sure?</p>`);

    // If overwrite confirmed delete existing config and resubmit form
    document.getElementById('confirm-overwrite').addEventListener('click', async function() {
        var response = await send_post_request("delete_config", `${name}.json`);
        submit_form(false);
    }, { once: true });

    // Re-enable submit button if overwrite canceled
    document.getElementById('cancel-overwrite').addEventListener('click', function() {
        submit_button.disabled = false;
    }, { once: true });
};
