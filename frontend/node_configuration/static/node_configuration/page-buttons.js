// Takes object and key prefix, returns all keys that begin with prefix
function filterObject(obj, prefix) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (key.startsWith(prefix)) {
            acc[key] = value;
        }
        return acc;
    }, {});
};


// Takes sensor ID, sensor config section, object of all device sections
// Returns sensor targets card with existing target devices pre-selected
function get_target_card_template(sensor, config, devices) {
    const nickname = config['nickname'];
    const type = config['_type'];

    // Populate div opening
    var template = `<div class='card ${sensor}'>
                        <div class='card-body'>
                            <label id='${sensor}-targets-label' for='${sensor}-targets' class='card-title'><b>${nickname} (${type})</b> targets:</label>
                            <div id='${sensor}-targets' class='form-check'>`

    // Iterate devices, add option for each
    for (device in devices) {
        if (config['targets'].includes(device)) {
            template += `<input type='checkbox' class='form-check-input' id='target-${sensor}-${device}' oninput="update_config_targets(this);" checked>
                         <label for='target-${sensor}-${device}' class='form-check-label'>${devices[device]['nickname']}</label><br>`;
        } else {
            template += `<input type='checkbox' class='form-check-input' id='target-${sensor}-${device}' oninput="update_config_targets(this);">
                         <label for='target-${sensor}-${device}' class='form-check-label'>${devices[device]['nickname']}</label><br>`;
        };
    };

    // Close div, return template
    template += "</div></div></div></br>";
    return template
};


function show_page_2() {
    // Get objects containing only devices and sensors
    const devices = filterObject(config, 'device');
    const sensors = filterObject(config, 'sensor');

    // Clear page2 div
    const target_section = document.getElementById('page2-cards');
    target_section.innerHTML = "<h3>Select targets for each sensor</h3>";

    // Iterate sensors, add target card for each with checkbox for each device
    for (sensor in sensors) {
        const template = get_target_card_template(sensor, config[sensor], devices);
        target_section.insertAdjacentHTML('beforeend', template);
    };

    // Show page2
    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page1").classList.remove("d-flex");
    document.getElementById("page1").style.display = "none";
};


function show_page_3() {
    // Get objects containing only devices and sensors
    const devices = filterObject(config, 'device');
    const sensors = filterObject(config, 'sensor');

    // Clear page3 div
    const target_section = document.getElementById('page3-cards');
    target_section.innerHTML = "";

    // Iterate sensors, add schedule rules card for each with existing rules
    for (sensor in sensors) {
        // Add empty schedule rule section
        const template = create_schedule_rule_section(sensor, config[sensor]['nickname'], config[sensor]['_type']);
        target_section.insertAdjacentHTML('beforeend', template);

        // Add each existing rule to section
        for (rule in config[sensor]['schedule']) {
            add_new_row(sensor, rule, config[sensor]['schedule'][rule], config[sensor]['_type']);
        };
    };

    // Iterate sensors, add schedule rules card for each with existing rules
    for (device in devices) {
        // Add empty schedule rule section
        const template = create_schedule_rule_section(device, config[device]['nickname'], config[device]['_type']);
        target_section.insertAdjacentHTML('beforeend', template);

        // Add each existing rule to section
        for (rule in config[device]['schedule']) {
            add_new_row(device, rule, config[device]['schedule'][rule], config[device]['_type']);
        };
    };

    // Show page3
    document.getElementById("page3").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";
};


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

    // Generate target select cards, show page
    show_page_2();
});


// Takes new device ID, nickname, and type
// Adds target select option to all cards on page 2
// Adds schedule rules card to page 3
function handle_new_device(device, nickname, type) {
    // Prevent duplicates if user goes back to page 1
    instances['devices'][device].new = false;
};


// Takes device ID and nickname
// Changes nickname on target select options, schedule rules card
function rename_device(device, nickname, type) {
    instances['devices'][device].name_changed = false;
};


// Takes device ID, nickname, and type
// Changes type displayed on target select options, schedule rules card
function change_device_type(device, nickname, type) {
    // Prevent running again (unless device type changes again)
    instances['devices'][device].modified = false;
}


// Takes new sensor ID, nickname, and type
// Adds target select card to page 2
function handle_new_sensor(sensor, nickname, type) {
    // Prevent duplicates if user goes back to page 1
    instances['sensors'][sensor].new = false;
};


// Takes sensor ID and nickname
// Changes nickname on target select card, schedule rules card
function rename_sensor(sensor, nickname, type) {
    instances['sensors'][sensor].name_changed = false;
};


// Takes sensor ID, nickname, and type
// Changes type displayed on target select options, schedule rules card
function change_sensor_type(sensor, nickname, type) {
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

    // Generate schedule rule cards, show page 3
    show_page_3();

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
