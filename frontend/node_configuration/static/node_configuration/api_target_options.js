// Called when user changes target node in edit page dropdown
function api_target_selected(el) {
    if (el.value) {
        document.getElementById(`${el.dataset.section}-default_rule-button`).disabled = false;
        // Clear old rule so menu doesn't populate when opened
        document.getElementById(`${el.dataset.section}-default_rule`).value = "";
        update_config(document.getElementById(`${el.dataset.section}-default_rule`));
    } else {
        document.getElementById(`${el.dataset.section}-default_rule-button`).disabled = true;
    };
};


// Called when user opens modal on edit page with "self-target" selected
// Gets all valid commands for current devices and sensors, adds to object
function get_self_target_options() {
    // Clear existing options
    ApiTargetOptions['self-target'] = {}

    // Get objects containing only devices and sensors
    const devices = filterObject(config, 'device');
    const sensors = filterObject(config, 'sensor');

    // Add all device options
    for (device in devices) {
        const instance_string = `${device}-${devices[device]['nickname']} (${devices[device]['_type']})`;

        // Remove on/off commands for ApiTarget (prevent turning self on/off in infinite loop)
        if (devices[device]['_type'] == 'api-target') {
            ApiTargetOptions['self-target'][instance_string] = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule'];
        } else {
            ApiTargetOptions['self-target'][instance_string] = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'];
        };
    };

    // Add all sensor options
    for (sensor in sensors) {
        const instance_string = `${sensor}-${sensors[sensor]['nickname']} (${sensors[sensor]['_type']})`;

        // Remove trigger command for sensors that don't support it
        if (sensors[sensor]['_type'] == "si7021" || sensors[sensor]['_type'] == "switch") {
            ApiTargetOptions['self-target'][instance_string] = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule'];
        } else {
            ApiTargetOptions['self-target'][instance_string] = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor'];
        };
    };

    // Add IR Blaster options (if configured)
    if (config.ir_blaster) {
        // Get NodeList of all IR target checkboxes
        const targets = document.querySelectorAll(".ir-target");

        // Skip if all boxes are unchecked
        if (Array.from(targets).some(checkbox => checkbox.checked)) {
            const instance_string = 'ir_blaster-Ir Blaster'
            ApiTargetOptions['self-target'][instance_string] = {}

            // Add options from ir_keys mapping dict for each checked box
            targets.forEach(function(checkbox) {
                if (checkbox.checked) {
                    ApiTargetOptions['self-target'][instance_string][checkbox.dataset.target] = ir_keys[checkbox.dataset.target]
                }
            });
        };
    };
};
