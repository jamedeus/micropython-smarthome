// Takes id (int), returns nickname input template
function create_nickname_input(id) {
    return `<div class="mb-2">
                <label class="w-100">
                    <b>Nickname:</b>
                    <input type="text" class="form-control nickname" placeholder="" oninput="prevent_duplicate_nickname(event);update_config(this);" data-section="${id}" data-param="nickname" required>
                </label>
            </div>`
}


// Takes id (int), returns dropdown template with options for all sensor pins
function create_pin_dropdown_sensor(id) {
    return `<div class="mb-2">
                <label class="w-100">
                    <b>Pin:</b>
                    <select class="form-select pin-select" autocomplete="off" onchange="pinSelected(this)" oninput="update_config(this);" data-section="${id}" data-param="pin" required>
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
                </label>
            </div>`
};


// Takes id (int), returns dropdown template with options for all device pins
function create_pin_dropdown_device(id) {
    return `<div class="mb-2">
                <label class="w-100">
                    <b>Pin:</b>
                    <select class="form-select pin-select" autocomplete="off" onchange="pinSelected(this)" oninput="update_config(this);" data-section="${id}" data-param="pin" required>
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
                </label>
            </div>`
};


// Takes id (int), returns dropdown template with standard rule options
function create_standard_rule_input(id) {
    return `<div class="mb-2">
                <label class="w-100">
                    <b>Default Rule:</b>
                    <select class="form-select" oninput="update_config(this);" data-section="${id}" data-param="default_rule" autocomplete="off" required>
                        <option value="enabled">Enabled</option>
                        <option value="disabled">Disabled</option>
                    </select>
                </label>
            </div>`
};


// Takes id (int), returns dropdown template with on and off options
function create_on_off_rule_input(id) {
    return `<div class="mb-2">
                <label class="w-100">
                    <b>Default Rule:</b>
                    <select class="form-select" oninput="update_config(this);" data-section="${id}" data-param="default_rule" autocomplete="off" required>
                        <option>Select default rule</option>
                        <option value="on">On</option>
                        <option value="off">Off</option>
                    </select>
                </label>
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
                <label class="mt-1 w-100">
                    <b>Default Rule:</b>
                    <div class="d-flex flex-row align-items-center my-2">
                        <button class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-section="${id}" data-direction="down" data-stepsize="${button_step}"><i class="bi-dash-lg"></i></button>
                        <input type="range" class="mx-auto" min="${min}" max="${max}" data-displaymin="${display_min}" data-displaymax="${display_max}" data-displaytype="${display_type}" step="${step}" value="" onchange="update_config(this);" autocomplete="off" data-section="${id}" data-param="default_rule">
                        <button class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-section="${id}" data-direction="up" data-stepsize="${button_step}"><i class="bi-plus-lg"></i></button>
                    </div>
                </label>
            </div>`
}


// Takes id (int), returns input with IPv4 regex
function create_ip_input(id) {
    return `<div class="mb-2">
                <label class="w-100">
                    <b>IP:</b>
                    <input type="text" class="form-control ip-input validate" placeholder="" pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$" oninput="update_config(this);" data-section="${id}" data-param="ip" required>
                </label>
            </div>`
}


// Takes id (int), returns input with URI regex (IP or domain)
function create_uri_input(id) {
    return `<div class="mb-2">
                <label class="w-100">
                    <b>URI:</b>
                    <input type="text" class="form-control validate" placeholder="IP address or URL" pattern="(?:(?:http|https):\/\/)?(?:\S+(?::\S*)?@)?(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::\d{1,5})?|(?:(?:http|https):\/\/)?[a-zA-Z0-9.]+(?:-[a-zA-Z0-9]+)*(?:\.[a-zA-Z]{2,6})+(?:\/\S*)?" oninput="update_config(this);" data-section="${id}" data-param="uri" required>
                </label>
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
                    <label class="w-100">
                        <b>Min brightness:</b>
                        <input type="min" class="form-control rule-limits" placeholder="${min}" value="${min}" data-min="${min}" data-max="${max}" oninput="update_config(this);" data-section="${id}" data-param="min_rule" required>
                    </label>
                </div>

                <div class="mb-2">
                    <label class="w-100">
                        <b>Max brightness:</b>
                        <input type="text" class="form-control rule-limits" placeholder="${max}" value="${max}" data-min="${min}" data-max="${max}" oninput="update_config(this);" data-section="${id}" data-param="max_rule" required>
                    </label>
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
        } else if (param == "uri") {
            template += create_uri_input(id);
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
    if (type == "si7021" || type == "dht22") {
        template += `<div class="mb-3">
                         <label class="w-100">
                             <b>Mode:</b>
                             <select class="form-select" oninput="update_config(this);" data-section="${id}" data-param="mode" required>
                                 <option value="cool">Cool</option>
                                 <option value="heat">Heat</option>
                             </select>
                         </label>
                     </div>

                    <div class="mb-3">
                        <label class="w-100">
                            <b>Units:</b>
                            <select class="form-select" oninput="update_thermostat_slider(this);update_config(this);" data-section="${id}" data-param="units" required>
                                <option value="fahrenheit">Fahrenheit</option>
                                <option value="celsius">Celsius</option>
                                <option value="kelvin">Kelvin</option>
                            </select>
                        </label>
                    </div>

                     <div class="mb-2">
                         <label class="w-100">
                             <b>Tolerance:</b>
                             <input type="text" class="form-control thermostat" placeholder="" oninput="update_config(this);" data-section="${id}" data-param="tolerance" required>
                         </label>
                     </div>`

    } else if (type == "api-target") {
        template += `<div class="mb-3">
                         <label class="w-100">
                            <b>Target Node:</b>
                            <select class="form-select" onchange="api_target_selected(this);update_config(this);" data-section="${id}" data-param="ip">
                                <option value="" selected="selected" selected></option>`

        for (var x in ApiTargetOptions) {
            if (x == "addresses") { continue };
            template += `       <option value="${ApiTargetOptions["addresses"][x]}">${x}</option>`
        };

        template += `       </select>
                        </label>
                    </div>

                    <div class="mb-2 text-center">
                        <button id="${id}-default_rule-button" class="btn btn-secondary mt-3" onclick="open_rule_modal(this);" data-target="${id}-default_rule" disabled>Set rule</button>
                    </div>

                    <div style="display:none;">
                        <input type="text" id="${id}-default_rule" onchange="update_config(this);" data-section="${id}" data-param="default_rule" required>
                    </div>`
    };

    return template;
};


// Takes config section and param, returns input element that sets param
function get_input_element(section, param) {
    return document.querySelector(`[data-section="${section}"][data-param="${param}"]`);
}


// Takes device or sensor ID, type, metadata entry, and completed template
// Inserts template into card, instantiates elements, adds listeners
function render_template(id, type, type_metadata, template) {
    // Insert template into div, scroll down until visible
    const card = document.getElementById(`${id}-params`);
    card.innerHTML = template;
    card.scrollIntoView({behavior: "smooth"});

    // Instantiate slider if added
    if (type_metadata.rule_prompt == 'float_range' || type_metadata.rule_prompt == 'int_or_fade') {
        add_new_slider(get_input_element(id, 'default_rule'));
    };

    // Disable already-used pins in the new pin dropdown
    if (Object.keys(type_metadata.config_template).includes('pin')) {
        preventDuplicatePins();
    };

    // Add listeners to format IP field while typing, validate when focus leaves
    if (Object.keys(type_metadata.config_template).includes('ip')) {
        const ip = get_input_element(id, 'ip');
        ip.addEventListener('input', formatIp);
        ip.addEventListener('blur', validateField);
    };

    // Add listener to constrain tolerance field
    if (type == "si7021") {
        get_input_element(id, 'tolerance').addEventListener('input', thermostatToleranceLimit);
    };

    // Add listener for rule max/min fields in advanced settings collapse
    if (type_metadata.rule_prompt == 'int_or_fade') {
        get_input_element(id, 'max_rule').addEventListener('input', ruleLimits);
        get_input_element(id, 'min_rule').addEventListener('input', ruleLimits);
    };

    // Return reference to card
    return card
}


// Called when user selects sensor type from dropdown
function load_sensor_section(select) {
    // Get ID of sensor
    const id = select.dataset.section;

    // Get user-selected type + metadata
    const type = select.value
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
    const id = select.dataset.section;

    // Get user-selected type + metadata
    const type = select.value
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
    var template = `<div id="addDeviceDiv${index}" class="fade-in mb-4" data-section="device${index}">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 id="device${index}-title" class="card-title mx-auto my-auto">device${index}</h4>
                                    <button class="btn my-auto pe-2 delete" data-section="device${index}" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label class="w-100">
                                    <b>Type:</b>
                                    <select onchange="load_device_section(this)" class="form-select mt-2" data-section="device${index}" data-param="_type" required>
                                    <option value="clear">Select device type</option>
                                    ${options}
                                    </select>
                                </label>
                                <div id="device${index}-params" class="card-body" data-section="device${index}"></div>
                            </div>
                        </div>
                    </div>`;

    // Render div, scroll down until visible
    document.getElementById("addDeviceButton").insertAdjacentHTML('beforebegin', template);
    document.getElementById(`addDeviceDiv${index}`).scrollIntoView({behavior: "smooth"});

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
    var template = `<div id="addSensorDiv${index}" class="fade-in mb-4" data-section="sensor${index}">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 id="sensor${index}-title" class="card-title mx-auto my-auto">sensor${index}</h4>
                                    <button class="btn my-auto pe-2 delete" data-section="sensor${index}" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label class="w-100">
                                    <b>Type:</b>
                                    <select onchange="load_sensor_section(this)" class="form-select mt-2" data-section="sensor${index}" data-param="_type" required>
                                    <option value="clear">Select sensor type</option>
                                    ${options}
                                    </select>
                                </label>
                                <div id="sensor${index}-params" class="card-body" data-section="sensor${index}"></div>
                            </div>
                        </div>
                    </div>`;

    // Render div, scroll down until visible
    document.getElementById("addSensorButton").insertAdjacentHTML('beforebegin', template);
    document.getElementById(`addSensorDiv${index}`).scrollIntoView({behavior: "smooth"});

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
    const category = target.replace(/[0-9]/g, '');

    // If target is device get object containing all sensor configs (used to update target IDs)
    if (category === 'device') {
        var sensors = filterObject(config, 'sensor');
    };

    return new Promise(resolve => {
        // Iterate all cards after the deleted card
        for (i=parseInt(num)+1; i<cards.length; i++) {
            // Decrement config section attribute of all input elements
            document.querySelectorAll(`[data-section="${target.replace(num, i)}"]`).forEach(el => {
                el.dataset.section = `${target.replace(num, i-1)}`;
                // Decrement ID if present
                if (el.hasAttribute("id")) {
                    el.id = el.id.replace(i, i-1);
                };
            });

            // Decrement card title text and ID
            document.getElementById(`${category}${i}-title`).innerHTML = `${category}${i-1}`
            document.getElementById(`${category}${i}-title`).id = `${category}${i-1}-title`

            // Adjust IDs in config object
            config[`${category}${i-1}`] = JSON.parse(JSON.stringify(config[`${category}${i}`]));
            delete config[`${category}${i}`];

            if (category === 'device') {
                // Adjust IDs of all sensor targets
                for (sensor in sensors) {
                    if (config[sensor]['targets'].includes(`device${i}`)) {
                        config[sensor]['targets'] = config[sensor]['targets'].filter(item => item !== `device${i}`);
                        config[sensor]['targets'].push(`device${i-1}`);
                    };
                };
            };
        };
        resolve();
    });
};


// Takes device ID, removes from targets section of all sensors
function remove_device_from_targets(device) {
    // Get object containing all sensor sections
    const sensors = filterObject(config, 'sensor');
    // Remove device from all sensor targets
    for (sensor in sensors) {
        config[sensor]['targets'] = config[sensor]['targets'].filter(item => item !== device);
    };
}


// Called by delete button in top right corner of device/sensor cards
async function remove_instance(el) {
    // Instance ID string (device1, sensor2, etc)
    var target = el.dataset.section;

    // Get pixel value of 1rem (used in animation)
    const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize)

    // Remove from config, get elements for delete animation
    if (target.startsWith("device")) {
        delete config[target];
        var num = target.replace("device", "");
        var cards = Array.from(document.getElementById("devices").children);
        var button = document.getElementById('addDeviceButton');
        // Get height of card to be deleted + 1.5rem (gap between cards)
        var card_div = document.getElementById(`addDeviceDiv${num}`);
        var animation_height = card_div.clientHeight / remPx + 1.5;
        // Remove from sensor targets
        remove_device_from_targets(target);
    } else {
        delete config[target];
        var num = target.replace("sensor", "");
        var cards = Array.from(document.getElementById("sensors").children);
        var button = document.getElementById('addSensorButton');
        // Get height of card to be deleted + 1.5rem (gap between cards)
        var card_div = document.getElementById(`addSensorDiv${num}`);
        var animation_height = card_div.clientHeight / remPx + 1.5;
    };

    // Remove last element in column (button under cards)
    cards.pop();

    // Set CSS var used in slide-up animation
    document.documentElement.style.setProperty('--animation-height', `${animation_height}rem`);

    // Disable all delete buttons until finished, prevent user deleting multiple at same time
    document.querySelectorAll('.delete').forEach(button => button.disabled = true);

    // Update all other card's IDs and classes while running animation
    await Promise.all([delete_animation(cards, num, button), update_ids(cards, num, target)])

    // Delete card
    card_div.remove();

    // Re-enable delete buttons
    document.querySelectorAll('.delete').forEach(button => button.disabled = false);

    // Rebuild self-target options with new instance IDs
    get_self_target_options();
};
