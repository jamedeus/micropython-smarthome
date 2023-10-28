// Takes object and key prefix, returns all keys that begin with prefix
function filterObject(obj, prefix) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (key.startsWith(prefix)) {
            acc[key] = value;
        }
        return acc;
    }, {});
};


// Returns True if any nickname fields are empty, otherwise False
function blank_nicknames_exist() {
    // Confirm all nickname fields are populated (prevent blank titles on pages 2-3)
    var nicknames = document.getElementsByClassName('nickname');
    var missing = false;

    // If nickname field is blank, add red highlight + listener to remove highlight on input
    for (i=0; i<nicknames.length; i++) {
        if (nicknames[i].value == "") {
            nicknames[i].classList.add("is-invalid");
            nicknames[i].scrollIntoView({behavior: "smooth"});
            nicknames[i].addEventListener("input", (e) => {
                e.target.classList.remove("is-invalid");
            }, { once: true });
            missing = true;
        };
    };

    return missing;
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
            template += `<label>
                             ${devices[device]['nickname']}
                             <input type='checkbox' class='form-check-input' data-sensor='${sensor}' data-target='${device}' oninput="update_config_targets(this);" checked>
                         </label><br>`;
        } else {
            template += `<label>
                             ${devices[device]['nickname']}
                             <input type='checkbox' class='form-check-input' data-sensor='${sensor}' data-target='${device}' oninput="update_config_targets(this);">
                         </label><br>`;
        };
    };

    // Close div, return template
    template += "</div></div></div></br>";
    return template
};


// Takes device/sensor ID, nickname, and type
// Returns template for schedule rules section on page 3
function create_schedule_rule_section(id, nickname, type) {
    return `<div class='card mb-4'>
                <div class='card-body text-center'>
                    <label id='${id}-rules-label' class='card-title schedule-rule-card' title='${id} - ${type}'>
                        <b>${nickname} (${type})</b>
                    </label>
                    <table id='${id}-rules' class='table table-borderless d-none'>
                        <tr>
                            <th style='text-align: center;'>Time</th>
                            <th style='text-align: center;'>Rule</th>
                        </tr>
                    </table>
                    <div>
                        <button type="button" class="btn btn-secondary add" id="${id}-add-rule" data-type="${type}" onclick="add_new_rule(this)">Add Rule</i></button>
                    </div>
                </div>
            </div>`;
};


// Page 1 back button handler, exits config editor
function show_overview() {
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
};


// Page 2 back button handler, shows page 1
function show_page_1() {
    // Show page 1
    document.getElementById("page1").classList.remove("d-none");
    document.getElementById("page1").classList.add("d-flex");
    // Hide pages 2 and 3
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").classList.add("d-none");
    document.getElementById("page3").classList.remove("d-flex");
    document.getElementById("page3").classList.add("d-none");

    // Update sliders (fix incorrect width caused by display: none)
    $('input[type="range"]').rangeslider('update', true);
}


// Page 1 next button handler, renders target select cards and shows page 2
function show_page_2() {
    // Don't proceed to page2 if blank nickname fields exist
    if (blank_nicknames_exist()) { return };

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

    // Show page 2
    document.getElementById("page2").classList.remove("d-none");
    document.getElementById("page2").classList.add("d-flex");
    // Hide pages 1 and 3
    document.getElementById("page1").classList.remove("d-flex");
    document.getElementById("page1").classList.add("d-none");
    document.getElementById("page3").classList.remove("d-flex");
    document.getElementById("page3").classList.add("d-none");
};


// Page 2 next button handler, renders schedule rules cards and shows page 3
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

    // Show page 3
    document.getElementById("page3").classList.remove("d-none");
    document.getElementById("page3").classList.add("d-flex");
    // Hide pages 1 and 2
    document.getElementById("page1").classList.remove("d-flex");
    document.getElementById("page1").classList.add("d-none");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").classList.add("d-none");

    // Update sliders (fix incorrect width caused by display: none)
    $('input[type="range"]').rangeslider('update', true);
};
