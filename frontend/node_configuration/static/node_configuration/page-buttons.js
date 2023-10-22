document.getElementById('page1-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Confirm all nickname fields are populated (prevent blank titles on pages 2-3)
    var nicknames = document.getElementsByClassName('nickname');
    var valid = true;

    // If nickname field is blank, add red highlight + listener to remove highlight on input
    for (i=0; i<nicknames.length; i++) {
        if (nicknames[i].value == "") {
            nicknames[i].classList.add("is-invalid");
            nicknames[i].scrollIntoView({behavior: "smooth"});
            nicknames[i].addEventListener("input", (e) => {
                e.target.classList.remove("is-invalid");
            }, { once: true });
            valid = false;
        };
    };

    // Don't proceed to page2 if blank fields exist
    if (!valid) { return };

    // Get array of all sensor target selection divs on page2
    sensors = document.getElementsByClassName("sensor-targets");

    // Find device instances that require updates
    for (device in instances['devices']) {
        // Get device nickname and type
        const nickname = instances['devices'][device]['output']['nickname'];
        const type = instances['devices'][device]['output']['_type'];

        // If device is new, add target select options on page2, add schedule rules card on page3
        if (instances['devices'][device].new) {
            handle_new_device(device, nickname, type);

        // If device nickname changed, but type did not change (targets + rules don't need to be cleared)
        } else if (instances['devices'][device].name_changed && ! instances['devices'][device].modified) {
            rename_device(device, nickname, type);

        // If device type changed, change type displayed on page2 and page3
        } else if (instances['devices'][device].modified) {
            change_device_type(device, nickname, type);
        };
    };

    // Find sensor instances that require updates
    for (sensor in instances['sensors']) {
        // Get sensor nickname and type
        const nickname = instances['sensors'][sensor]['output']['nickname'];
        const type = instances['sensors'][sensor]['output']['_type'];

        // If sensor is new, add target select card to page2
        if (instances['sensors'][sensor].new) {
            handle_new_sensor(sensor, nickname, type);

        // If sensor nickname changed, but type did not change (targets + rules don't need to be cleared)
        } else if (instances['sensors'][sensor].name_changed && ! instances['sensors'][sensor].modified) {
            rename_sensor(sensor, nickname, type);

        // If sensor type changed, change type displayed on page2 and page3
        } else if (instances['sensors'][sensor].modified) {
            change_sensor_type(sensor, nickname, type);
        };
    };

    // Show page2
    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page1").classList.remove("d-flex");
    document.getElementById("page1").style.display = "none";
});


// Takes new device ID, nickname, and type
// Adds target select option to all cards on page 2
// Adds schedule rules card to page 3
function handle_new_device(device, nickname, type) {
    // Add checkbox for device to all sensor target select cards (page2)
    for (sensor of sensors) {
        const sen_id = sensor.id.split("-")[0];

        template = `<input type='checkbox' class='form-check-input ${sen_id} ${device} target' id='target-${sen_id}-${device}' value='target-${sen_id}-${device}'>
                    <label for='target-${sen_id}-${device}' class='form-check-label ${sen_id} ${device} target-label'>${nickname}</label>
                    <br class='${device}'>`;

        sensor.insertAdjacentHTML('beforeend', template);
    };

    // Add schedule rule section for the new device to page3
    template = create_schedule_rule_section(device, nickname, type);
    document.getElementById("page3-cards").insertAdjacentHTML('beforeend', template);

    // Prevent duplicates if user goes back to page 1
    instances['devices'][device].new = false;
};


// Takes device ID and nickname
// Changes nickname on target select options, schedule rules card
function rename_device(device, nickname, type) {
    // Change name on schedule rules card
    document.getElementById(`${device}-rules-label`).innerHTML = `<b>${nickname} (${type})</b>`;

    // Change text on all target options
    target_labels = document.getElementsByClassName(`${device} target-label`);
    for (i=0; i<target_labels.length; i++) {
        target_labels[i].innerHTML = `${nickname}`;
    };

    instances['devices'][device].name_changed = false;
};


// Takes device ID, nickname, and type
// Changes type displayed on target select options, schedule rules card
function change_device_type(device, nickname, type) {
    target_checks = document.getElementsByClassName(`${device} target`);
    target_labels = document.getElementsByClassName(`${device} target-label`);

    // Uncheck all target option boxes and change label text
    for (i=0; i<target_checks.length; i++) {
        target_checks[i].checked = false;
        target_labels[i].innerHTML = `${nickname}`;
    };

    // Change name and tooltip on schedule rules card
    document.getElementById(`${device}-rules-label`).title = `${device} - ${type}`;
    document.getElementById(`${device}-rules-label`).innerHTML = `<b>${nickname} (${type})</b>`;

    // Clear existing schedule rules (likely invalid after type change)
    template = `<tr>
                    <th style='text-align: center;'>Time</th>
                    <th style='text-align: center;'>Rule</th>
                </tr>`;
    document.getElementById(`${device}-rules`).innerHTML = template
    document.getElementById(`${device}-rules`).classList.add('d-none');

    // Prevent running again (unless device type changes again)
    instances['devices'][device].modified = false;
}


// Takes new sensor ID, nickname, and type
// Adds target select card to page 2
function handle_new_sensor(sensor, nickname, type) {
    // Target select card opening div
    var template =  `<div class='card ${sensor}'>
                         <div class='card-body'>
                             <label id='${sensor}-targets-label' for='${sensor}-targets' class='card-title sensor-targets-label ${sensor}'><b>${nickname} (${type})</b> targets:</label>
                             <div id='${sensor}-targets' class='form-check sensor-targets ${sensor}'>`

    // Iterate devices, add checkbox for each to new sensor card
    for (device in instances['devices']) {
        template += `<input type='checkbox' class='form-check-input ${device} ${sensor} target' id='target-${sensor}-${device}' value='target-${sensor}-${device}'>
                     <label for='target-${sensor}-${device}' class='form-check-label ${device} ${sensor} target-label'>${instances['devices'][device]['output']['nickname']}</label><br>`;
    };

    // Close div, add to DOM
    template += "</div></div></div></br>"
    document.getElementById("page2-cards").insertAdjacentHTML('beforeend', template);

    // Add schedule rule section for the new sensor to page3
    template = create_schedule_rule_section(sensor, nickname, type);
    document.getElementById("page3-cards").insertAdjacentHTML('beforeend', template);

    // Prevent duplicates if user goes back to page 1
    instances['sensors'][sensor].new = false;
};


// Takes sensor ID and nickname
// Changes nickname on target select card, schedule rules card
function rename_sensor(sensor, nickname, type) {
    // Change name on schedule rules card
    document.getElementById(`${sensor}-rules-label`).innerHTML = `<b>${nickname} (${type})</b>`;

    // Change name on targets card
    document.getElementById(`${sensor}-targets-label`).innerHTML = `<b>${nickname} (${type})</b> targets:`;

    instances['sensors'][sensor].name_changed = false;
};


// Takes sensor ID, nickname, and type
// Changes type displayed on target select options, schedule rules card
function change_sensor_type(sensor, nickname, type) {
    // Uncheck all target boxes
    for (el of document.getElementById(`${sensor}-targets`).children) {
        // Children contains inputs, their labels, and line breaks - only process inputs
        if (el.classList.contains("form-check-input")) {
            el.checked = false;
        };
    };

    // Change nickname and type on target card
    document.getElementById(`${sensor}-targets-label`).innerHTML = `<b>${nickname} (${type})</b> targets:`;

    // Change name and tooltip on schedule rules card
    document.getElementById(`${sensor}-rules-label`).title = `${sensor} - ${type}`;
    document.getElementById(`${sensor}-rules-label`).innerHTML = `<b>${nickname} (${type})</b>`;

    // Clear existing schedule rules (likely invalid after type change)
    template = `<tr>
                    <th style='text-align: center;'>Time</th>
                    <th style='text-align: center;'>Rule</th>
                </tr>`;
    document.getElementById(`${sensor}-rules`).innerHTML = template
    document.getElementById(`${sensor}-rules`).classList.add('d-none');

    // Prevent running again (unless user changes type again)
    instances['sensors'][sensor].modified = false;
};


// Takes device/sensor ID, nickname, and type
// Returns template for schedule rules section on page 3
function create_schedule_rule_section(id, nickname, type) {
    return `<div class='card mb-4 ${id}'>
                <div class='card-body text-center'>
                    <label id='${id}-rules-label' class='card-title schedule-rule-card ${id}' title='${id} - ${type}'>
                        <b>${nickname} (${type})</b>
                    </label>
                    <table id='${id}-rules' class='table table-borderless ${id} d-none'>
                        <tr>
                            <th style='text-align: center;'>Time</th>
                            <th style='text-align: center;'>Rule</th>
                        </tr>
                    </table>
                    <div>
                        <button type="button" class="btn btn-secondary add ${id}" id="${id}-add-rule" data-type="${type}" onclick="add_new_rule(this)">Add Rule</i></button>
                    </div>
                </div>
            </div>`;
};


document.getElementById('page2-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page3
    document.getElementById("page3").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";

    // Update sliders (fix incorrect width caused by display: none)
    $('input[type="range"]').rangeslider('update', true);
});


document.getElementById('page1-back-button').addEventListener("click", function(e) {
    // If user changed any inputs, show warning before redirecting to overview
    if (changes_made) {
        const body = "<p class='text-center'>Your changes will be lost if you go back - are you sure?</p>";
        const footer = `<button type="button" id="yes-button" class="btn btn-danger" data-bs-dismiss="modal" onclick="window.location.replace('/config_overview');">Go Back</button>
                        <button type="button" id="no-button" class="btn btn-secondary" data-bs-dismiss="modal">Keep Editing</button>`;
        show_modal(errorModal, "Warning", body, footer);

    // Skip warning if no changes
    } else {
        window.location.replace("/config_overview");
    };
});


document.getElementById('page2-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page1
    document.getElementById("page1").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";

    // Update sliders (fix incorrect width caused by display: none)
    $('input[type="range"]').rangeslider('update', true);
});


document.getElementById('page3-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page2
    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page3").classList.remove("d-flex");
    document.getElementById("page3").style.display = "none";
});
