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
    // TODO remove hardcoded options, load from metadata
    if (config.ir_blaster) {
        const tv_options = document.getElementById('checkbox-tv').checked;
        const ac_options = document.getElementById('checkbox-ac').checked;

        // Skip if neither is checked
        if (tv_options || ac_options) {
            const instance_string = 'ir_blaster-Ir Blaster'
            ApiTargetOptions['self-target'][instance_string] = {}

            if (tv_options) {
                ApiTargetOptions['self-target'][instance_string]['tv'] = ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source']
            };
            if (ac_options) {
                ApiTargetOptions['self-target'][instance_string]['ac'] = ['start', 'stop', 'off']
            };
        };
    };
};
