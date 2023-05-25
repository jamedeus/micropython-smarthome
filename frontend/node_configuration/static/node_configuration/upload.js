// Checkmark animation shown when upload complete
const upload_complete = `<svg class="checkmark mx-auto" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                             <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                             <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                         </svg>`

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

// Show the modal with id modal, optionally change title/body/footer
function show_modal(modal, title=false, body=false, footer=false) {
    if (title) {
        document.getElementById(modal._element.id + "-title").innerHTML = title;
    };

    if (body) {
        document.getElementById(modal._element.id + "-body").innerHTML = body;
    };

    if (footer) {
        document.getElementById(modal._element.id + "-footer").innerHTML = footer;
    };

    modal.show();
};

// Used by both pages to upload config files to nodes
async function upload() {
    // Show loading screen
    show_modal(uploadModal);

    if (edit_existing) {
        // Re-upload existing config
        var response = await send_post_request("upload/True", {config: target_filename, ip: target_ip});
    } else {
        // Upload config
        var response = await send_post_request("upload", {config: target_filename, ip: target_ip});
    };

    // If upload successful, show success animation and reload page
    if (response.ok) {
        // Change title, show success animation
        show_modal(uploadModal, "Upload Complete", upload_complete);

        // Wait for animation to complete before reloading
        await sleep(1200);
        window.location.replace("/config_overview");

    // Unable to upload because node has not run setup
    } else if (response.status == 409) {
        const error = await response.text();
        run_setup_prompt(error);

    // Unable to upload because node is unreachable
    } else if (response.status == 404) {
        target_unreachable_prompt();

    // Other error, show in alert
    } else {
        alert(await response.text());

        // Hide modal allowing user to access page again
        uploadModal.hide();
    };
};

// Shown when unable to upload because target node has not run setup yet
async function run_setup_prompt(error) {
    const footer = `<button type="button" id="yes-button" class="btn btn-secondary" data-bs-dismiss="modal">Yes</button>
                    <button type="button" id="no-button" class="btn btn-secondary" data-bs-dismiss="modal">No</button>`

    // Replace loading modal with error modal, ask if user wants to run setup routine
    uploadModal.hide();
    show_modal(errorModal, "Error", `${error}`, footer);

    document.getElementById('yes-button').addEventListener('click', async function() {
        // Show loading again, upload setup file
        errorModal.hide();
        show_modal(uploadModal);
        var result = await send_post_request("setup", {ip: target_ip});

        if (result.ok) {
            // After uploading config, tell user to reboot node then click OK
            uploadModal.hide();
            const footer = `<button type="button" id="ok-button" class="btn btn-success" data-bs-dismiss="modal">OK</button>`
            show_modal(errorModal, "Success", "Please reboot node, then press OK to resume upload", footer);

            // When user clicks OK, resubmit form (setup has finished running, should now be able to upload)
            document.getElementById('ok-button').addEventListener('click', function() {
                errorModal.hide();
                upload();
            }, { once: true });
        } else {
            alert(await result.text());

            // Re-enable submit button so user can try again
            try{ document.getElementById("submit-button").disabled = false; }catch(err){};
        };
    }, { once: true });

    document.getElementById('no-button').addEventListener('click', function() {
        errorModal.hide();
        uploadModal.hide();
        try{ document.getElementById("submit-button").disabled = false; }catch(err){};
    }, { once: true });
};

// Shown when unable to upload because target node unreachable
async function target_unreachable_prompt() {
    uploadModal.hide();

    // Show error modal with instructions
    const footer = `<button type="button" id="ok-button" class="btn btn-success" data-bs-dismiss="modal">OK</button>`
    show_modal(errorModal, "Connection Error", `<p class="text-center">Unable to connect to ${target_ip}<br/>Possible causes:</p><ul><li>Node is not connected to wifi</li><li>Node IP has changed</li><li>Node has not run webrepl_setup</li></ul>`, footer);

    // When user clicks OK, re-enable submit button so user can try again
    document.getElementById('ok-button').addEventListener('click', function() {
        errorModal.hide();
        uploadModal.hide();
        try{ document.getElementById("submit-button").disabled = false; }catch(err){};
    }, { once: true });
};
