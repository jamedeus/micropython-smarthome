// Takes id (int), returns nickname input template
function create_nickname_input(id) {
    return `<div class="mb-2">
                <label for="${id}-nickname"<b>Nickname:</b></label>
                <input type="text" class="form-control nickname" id="${id}-nickname" placeholder="" oninput="prevent_duplicate_nickname(event);update_config(this);" data-section="${id}" data-param="nickname" required>
            </div>`
}


// Takes id (int), returns dropdown template with options for all sensor pins
function create_pin_dropdown_sensor(id) {
    return `<div class="mb-2">
                <label for="${id}-pin"><b>Pin:</b></label>
                <select id="${id}-pin" class="form-select pin-select" autocomplete="off" onchange="pinSelected(this)" oninput="update_config(this);" data-section="${id}" data-param="pin" required>
                    <option selected disabled>Select pin</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                    <option value="13">13</option>
                    <option value="14">14</option>
                    <option value="15">15</option>
                    <option value="16">16</option>
                    <option value="17">17</option>
                    <option value="18">18</option>
                    <option value="19">19</option>
                    <option value="21">21</option>
                    <option value="22">22</option>
                    <option value="23">23</option>
                    <option value="25">25</option>
                    <option value="26">26</option>
                    <option value="27">27</option>
                    <option value="32">32</option>
                    <option value="33">33</option>
                    <option value="34">34</option>
                    <option value="35">35</option>
                    <option value="36">36</option>
                    <option value="39">39</option>
                </select>
            </div>`
};


// Takes id (int), returns dropdown template with options for all device pins
function create_pin_dropdown_device(id) {
    return `<div class="mb-2">
                <label for="${id}-pin"><b>Pin:</b></label>
                <select id="${id}-pin" class="form-select pin-select" autocomplete="off" onchange="pinSelected(this)" oninput="update_config(this);" data-section="${id}" data-param="pin" required>
                    <option selected disabled>Select pin</option>
                    <option value="4">4</option>
                    <option value="13">13</option>
                    <option value="16">16</option>
                    <option value="17">17</option>
                    <option value="18">18</option>
                    <option value="19">19</option>
                    <option value="21">21</option>
                    <option value="22">22</option>
                    <option value="23">23</option>
                    <option value="25">25</option>
                    <option value="26">26</option>
                    <option value="27">27</option>
                    <option value="32">32</option>
                    <option value="33">33</option>
                </select>
            </div>`
};


// Takes id (int), returns dropdown template with standard rule options
function create_standard_rule_input(id) {
    return `<div class="mb-2">
                <label for="${id}-default_rule"><b>Default Rule:</b></label>
                <select id="${id}-default_rule" class="form-select" autocomplete="off" oninput="update_config(this);" data-section="${id}" data-param="default_rule" required>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
            </div>`
};


// Takes id (int), returns dropdown template with on and off options
function create_on_off_rule_input(id) {
    return `<div class="mb-2">
                <label for="${id}-default_rule"><b>Default Rule:</b></label>
                <select id="${id}-default_rule" class="form-select" autocomplete="off" oninput="update_config(this);" data-section="${id}" data-param="default_rule" required>
                    <option>Select default rule</option>
                    <option value="on">On</option>
                    <option value="off">Off</option>
                </select>
            </div>`
};


// Returns slider template with values configured by args
// min/max: the value limits for the slider, should match device/sensor limits
// display_min/display_max: the values displayed, actual values are scaled to this range
// display_type: int or float, determines whether decimal is shown
// step: int or float, controls step size for slider
// button_step: int or float, controls step size for +/- buttons
function create_slider_rule_input(id, min, max, display_min, display_max, display_type, step, button_step) {
    return `<div class="mb-2">
                <label for="${id}-default_rule" class="mt-1"><b>Default Rule:</b></label>
                <div class="d-flex flex-row align-items-center my-2">
                    <button id="${id}-default_rule-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="${button_step}"><i class="bi-dash-lg"></i></button>
                    <input id="${id}-default_rule" type="range" class="mx-auto" min="${min}" max="${max}" data-displaymin="${display_min}" data-displaymax="${display_max}" data-displaytype="${display_type}" step="${step}" value="" oninput="update_config(this);" autocomplete="off" data-section="${id}" data-param="default_rule">
                    <button id="${id}-default_rule-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="${button_step}"><i class="bi-plus-lg"></i></button>
                </div>
            </div>`
}


// Takes id (int), returns input with IPv4 regex
function create_ip_input(id) {
    return `<div class="mb-2">
                <label for="${id}-ip"><b>IP:</b></label>
                <input type="text" class="form-control ip-input validate" id="${id}-ip" placeholder="" pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$" oninput="update_config(this);" data-section="${id}" data-param="ip" required>
            </div>`
}


// Takes id, min, max (all int), returns advanced settings collapse
// div template with inputs to configure min_rule, max_rule
// BUG update_config listener adds raw value before constrained to range
// ie if max=100 and user enters 1000 then 1000 is added to config, 100 shown on screen
function create_advanced_settings_dimmable_light(id, min, max) {
    return `<div class="mt-3 text-center">
                <a class="text-decoration-none text-dim" data-bs-toggle="collapse" href="#${id}-advanced_settings" role="button" aria-expanded="false" aria-controls="${id}-advanced_settings">Advanced</a>
            </div>

            <div id="${id}-advanced_settings" class="collapse">
                <div class="mb-2">
                    <label for="${id}-min_rule"><b>Min brightness:</b></label>
                    <input type="min" class="form-control rule-limits" id="${id}-min_rule" placeholder="${min}" value="${min}" data-min="${min}" data-max="${max}" oninput="update_config(this);" data-section="${id}" data-param="min_rule" required>
                </div>

                <div class="mb-2">
                    <label for="${id}-max_rule"><b>Max brightness:</b></label>
                    <input type="text" class="form-control rule-limits" id="${id}-max_rule" placeholder="${max}" value="${max}" data-min="${min}" data-max="${max}" oninput="update_config(this);" data-section="${id}" data-param="max_rule" required>
                </div>
            </div>`
}


// Takes device or sensor ID, type, metadata entry, and category (device or sensor)
// Returns config card template with appropriate input elements
function get_template(id, type, type_metadata, category) {
    // Add nickname section to template, other sections added below as needed
    var template = create_nickname_input(id);

    // Add non-rule input fields
    Object.keys(type_metadata.config_template).forEach(function(param) {
        if (param == "pin" && category == "sensor") {
            template += create_pin_dropdown_sensor(id);
        } else if (param == "pin" && category == "device") {
            template += create_pin_dropdown_device(id);
        } else if (param == "ip" && type != "api-target") {
            template += create_ip_input(id);
        }
    });

    // Add rule input field
    if (type_metadata.rule_prompt == 'int_or_fade') {
        // Get actual minimum/maximum rules
        const min = type_metadata.rule_limits[0];
        const max = type_metadata.rule_limits[1];
        // Calculate button step size (should always move display value by 1)
        const button_step = parseInt(max / 100);
        // Add slider template with display-max 100, actual value matches actual max
        template += create_slider_rule_input(id, min, max, min, '100', 'int', '1', button_step);
        template += create_advanced_settings_dimmable_light(id, min, max);

    } else if (type_metadata.rule_prompt == 'float_range') {
        // Get actual minimum/maximum rules
        const min = type_metadata.rule_limits[0];
        const max = type_metadata.rule_limits[1];
        // Add slider template with display min and max from metadata
        template += create_slider_rule_input(id, min, max, min, max, 'float', '0.5', '0.5');

    } else if (type_metadata.rule_prompt == 'standard') {
        template += create_standard_rule_input(id);

    } else if (type_metadata.rule_prompt == 'on_off') {
        template += create_on_off_rule_input(id);
    };

    // Add type-specific components
    if (type == "si7021") {
        template += `<div class="mb-2">
                         <label class="form-label" for="${id}-mode"><b>Mode:</b></label>
                         <select id="${id}-mode" class="form-select mb-3" oninput="update_config(this);" data-section="${id}" data-param="mode" required>
                             <option value="cool" id="cool">Cool</option>
                             <option value="heat" id="heat">Heat</option>
                         </select>
                     </div>

                     <div class="mb-2">
                         <label for="${id}-tolerance"><b>Tolerance:</b></label>
                         <input type="text" class="form-control thermostat" id="${id}-tolerance" placeholder="" oninput="update_config(this);" data-section="${id}" data-param="tolerance" required>
                     </div>`

    } else if (type == "api-target") {
        template += `<div class="mb-2">
                         <label for="${id}-ip"><b>Target Node:</b></label>
                         <select id="${id}-ip" class="form-select mb-3" onchange="api_target_selected(this)" oninput="update_config(this);" data-section="${id}" data-param="ip">
                             <option value="" selected="selected" selected></option>`

        for (var x in ApiTargetOptions) {
            if (x == "addresses") { continue };
            template +=    `<option value="${ApiTargetOptions["addresses"][x]}">${x}</option>`
        };

        template += `</select>
                     </div>

                     <div class="mb-2 text-center">
                         <button id="${id}-default_rule-button" class="btn btn-secondary mt-3" onclick="open_rule_modal(this);" data-target="${id}-default_rule" disabled>Set rule</button>
                     </div>

                     <div class="mb-2 text-center">
                         <label for="${id}-default_rule" style="display:none;"><b>Default Rule:</b></label>
                         <input type="default_rule" class="form-control" id="${id}-default_rule" placeholder="" style="display:none;" onchange="document.getElementById('${id}-default_rule-button').dataset.original = this.value; update_config(this);" data-section="${id}" data-param="defaut_rule" required>
                         </div>`
    };

    return template;
};


// Takes device or sensor ID, type, metadata entry, and completed template
// Inserts template into card, instantiates elements, adds listeners
function render_template(id, type, type_metadata, template) {
    // Insert template into div, scroll down until visible
    const card = document.querySelector(`.${id} .configParams`);
    card.innerHTML = template;
    card.scrollIntoView({behavior: "smooth"});

    // Instantiate slider if added
    if (type_metadata.rule_prompt == 'float_range' || type_metadata.rule_prompt == 'int_or_fade') {
        add_new_slider(`${id}-default_rule`);
    };

    // Disable already-used pins in the new pin dropdown
    if (Object.keys(type_metadata.config_template).includes('pin')) {
        preventDuplicatePins();
    };

    // Add listeners to format IP field while typing, validate when focus leaves
    if (Object.keys(type_metadata.config_template).includes('ip')) {
        ip = document.getElementById(`${id}-ip`);
        ip.addEventListener('input', formatIp);
        ip.addEventListener('blur', validateField);
    };

    // Add listener to constrain tolerance field
    if (type == "si7021") {
        document.getElementById(`${id}-tolerance`).addEventListener('input', thermostatToleranceLimit);
    };

    // Add listener for rule max/min fields in advanced settings collapse
    if (type_metadata.rule_prompt == 'int_or_fade') {
        document.getElementById(`${id}-max_rule`).addEventListener('input', ruleLimits);
        document.getElementById(`${id}-min_rule`).addEventListener('input', ruleLimits);
    };

    // Return reference to card
    return card
}


// Called when user selects sensor type from dropdown
function load_sensor_section(select) {
    // Get ID of sensor
    const id = select.id.split("-")[0];

    // Get user-selected type + metadata
    const type = document.getElementById(select.id).value
    const type_metadata = metadata['sensors'][type];

    // Disable "Select sensor type" option after selection made
    if (type != "clear") {
        select.children[0].disabled = true;
    };

    // Render template for currently-selected sensor type
    var template = get_template(id, type, type_metadata, 'sensor');
    const card = render_template(id, type, type_metadata, template);

    // Disable Thermostat dropdown options if selected (can't have multiple)
    preventDuplicateThermostat();

    // Add correct template to config object
    config[id] = metadata['sensors'][type]['config_template'];

    // Trigger listeners that update config object on all inputs
    card.querySelectorAll("input").forEach(input => trigger_input_event(input));
    card.querySelectorAll("select").forEach(input => trigger_input_event(input));
};



// Called when user selects device type from dropdown
function load_device_section(select) {
    // Get ID of device
    const id = select.id.split("-")[0];

    // Get user-selected type + metadata
    const type = document.getElementById(select.id).value;
    const type_metadata = metadata['devices'][type];

    // Disable "Select device type" option after selection made
    if (type != "clear") {
        select.children[0].disabled = true;
    };

    // Render template for currently-selected device type
    var template = get_template(id, type, type_metadata, 'device');
    const card = render_template(id, type, type_metadata, template);

    // Add correct template to config object
    config[id] = metadata['devices'][type]['config_template'];

    // Trigger listeners that update config object on all inputs
    card.querySelectorAll("input").forEach(input => trigger_input_event(input));
    card.querySelectorAll("select").forEach(input => trigger_input_event(input));
};


// Called when user clicks + button under devices
async function load_next_device() {
    // Get index of new device (number of existing + 1)
    const index = Object.keys(filterObject(config, 'device')).length + 1;

    // Add section to config object
    config[`device${index}`] = {};

    // Generate device type options from metadata
    let options = "";
    for (device in metadata.devices) {
        options += `<option value="${metadata['devices'][device]['config_name']}">${metadata['devices'][device]['class_name']}</option>`;
    };

    // Create card template with all options, correct index
    var template = `<div id="addDeviceDiv${index}" class="device${index} fade-in mb-4">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 class="card-title device${index} mx-auto my-auto">device${index}</h4>
                                    <button class="btn my-auto pe-2 delete device${index}" id="device${index}-remove" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label for="device${index}-type" class="form-label"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_device_section(this)" id="device${index}-type" class="form-select" data-section="device${index}" data-param="_type" required>
                                    <option value="clear">Select device type</option>
                                    ${options}
                                    </select>
                                </div>
                                <div class="card-body device${index} configParams"></div>
                            </div>
                        </div>
                    </div>`;

    // Render div, scroll down until visible
    document.getElementById("addDeviceButton").insertAdjacentHTML('beforebegin', template);
    document.getElementById("addDeviceDiv" + (index)).scrollIntoView({behavior: "smooth"});

    // Wait for fade animation to complete, remove class (prevent conflict with fade-out if card is deleted)
    await sleep(400);
    document.getElementById(`addDeviceDiv${index}`).classList.remove('fade-in');
};



// Called when user clicks + button under sensors
async function load_next_sensor() {
    // Get index of new sensor (number of existing + 1)
    const index = Object.keys(filterObject(config, 'sensor')).length + 1;

    // Add section to config object
    config[`sensor${index}`] = {};

    // Generate sensor type options from metadata
    let options = "";
    for (sensor in metadata.sensors) {
        options += `<option value="${metadata['sensors'][sensor]['config_name']}">${metadata['sensors'][sensor]['class_name']}</option>`;
    };

    // Create card template with all options, correct index
    var template = `<div id="addSensorDiv${index}" class="sensor${index} fade-in mb-4">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 class="card-title sensor${index} mx-auto my-auto">sensor${index}</h4>
                                    <button class="btn my-auto pe-2 delete sensor${index}" id="sensor${index}-remove" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label for="sensor${index}-type" class="form-label"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_sensor_section(this)" id="sensor${index}-type" class="form-select" data-section="sensor${index}" data-param="_type" required>
                                    <option value="clear">Select sensor type</option>
                                    ${options}
                                    </select>
                                </div>

                                <div class="card-body sensor${index} configParams"></div>
                            </div>
                        </div>
                    </div>`;

    // Render div, scroll down until visible
    document.getElementById("addSensorButton").insertAdjacentHTML('beforebegin', template);
    document.getElementById("addSensorDiv" + (index)).scrollIntoView({behavior: "smooth"});

    // Disable Thermostat dropdown options if selected (can't have multiple)
    preventDuplicateThermostat();

    // Wait for fade animation to complete, remove class (prevent conflict with fade-out if card is deleted)
    await sleep(400);
    document.getElementById(`addSensorDiv${index}`).classList.remove('fade-in');
};



// Delete instance card animation
// Takes array of card divs, index of card to delete, add instance button
// Fades out card to delete, slides up all cards below + add button
async function delete_animation(cards, num, button) {
    return new Promise(async resolve => {
        // Fade out card to be deleted
        cards[num].classList.add('fade-out');

        // Slide up all cards below, wait for animation to complete
        for (i=parseInt(num)+1; i<cards.length; i++) {
            cards[i].children[0].classList.add('slide-up');
        };
        button.classList.add('slide-up');
        await sleep(800);

        // Prevent cards jumping higher when hidden card is actually deleted
        for (i=parseInt(num)+1; i<cards.length; i++) {
            cards[i].children[0].classList.remove('slide-up');
        };
        button.classList.remove('slide-up');
        resolve();
    });
};



// Runs when card deleted, decrement references to instance ID of all subsequent cards to prevent gap in indices
// Example: If device2 is deleted, device3 becomes device2, device4 becomes device3, etc
function update_ids(cards, num, target) {
    return new Promise(resolve => {
        // Iterate all cards after the deleted card
        for (i=parseInt(num)+1; i<cards.length; i++) {
            // Get all elements associated with current card
            let elements = document.querySelectorAll(`.${target.replace(num, i)}`);

            // Decrement all instance ID references (device1, sensor2, etc) by 1
            for (el=0; el<elements.length; el++) {
                if (elements[el].hasAttribute("id")) {
                    elements[el].id = elements[el].id.replace(i, i-1);
                };

                if (elements[el].hasAttribute("for")) {
                    elements[el].setAttribute("for", elements[el].getAttribute("for").replace(i, i-1));
                };

                if (elements[el].classList.contains("card-title") || elements[el].classList.contains("form-check-label")) {
                    if (target.startsWith('device')) {
                        elements[el].innerHTML = elements[el].innerHTML.replace(`device${i}`, `device${i-1}`);
                    } else {
                        elements[el].innerHTML = elements[el].innerHTML.replace(`sensor${i}`, `sensor${i-1}`);
                    };
                };

                // Decrement class
                elements[el].classList.remove(target.replace(num, i))
                elements[el].classList.add(target.replace(num, i-1))
            };

            // Adjust IDs in config object
            if (target.startsWith('device')) {
                config[`device${i-1}`] = config[`device${i}`];
                delete config[`device${i}`];
            } else {
                config[`sensor${i-1}`] = config[`sensor${i}`];
                delete config[`sensor${i}`];
            };
        };
        resolve();
    });
};


// Called by delete button in top right corner of device/sensor cards
async function remove_instance(el) {
    // Instance ID string (device1, sensor2, etc)
    var target = el.id.split("-")[0];

    // Get pixel value of 1rem (used in animation)
    const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize)

    // Remove from config, get elements for delete animation
    if (target.startsWith("device")) {
        delete config[target];
        var num = target.replace("device", "");
        var cards = Array.from(document.getElementById("devices").children);
        var button = document.getElementById('addDeviceButton');
        // Get height of card to be deleted + 1.5rem (gap between cards)
        var animation_height = document.getElementById(`addDeviceDiv${num}`).clientHeight / remPx + 1.5;
    } else {
        delete config[target];
        var num = target.replace("sensor", "");
        var cards = Array.from(document.getElementById("sensors").children);
        var button = document.getElementById('addSensorButton');
        // Get height of card to be deleted + 1.5rem (gap between cards)
        var animation_height = document.getElementById(`addSensorDiv${num}`).clientHeight / remPx + 1.5;
    };

    // Remove last element in column (button under cards)
    cards.pop();

    // Set CSS var used in slide-up animation
    document.documentElement.style.setProperty('--animation-height', `${animation_height}rem`);

    // Disable all delete buttons until finished, prevent user deleting multiple at same time
    document.querySelectorAll('.delete').forEach(button => button.disabled = true);

    // Get all elements with deleted card's class (used to delete later, must get before other card classes change)
    let elements = document.querySelectorAll(`.${target}`);

    // Update all other card's IDs and classes while running animation
    await Promise.all([delete_animation(cards, num, button), update_ids(cards, num, target)])

    // Delete card + all options on page2-3
    for (i=0; i<elements.length; i++) {
        elements[i].remove();
    };

    // Re-enable delete buttons
    document.querySelectorAll('.delete').forEach(button => button.disabled = false);

    // Rebuild self-target options with new instance IDs
    get_self_target_options();
};
