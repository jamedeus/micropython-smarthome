// Receives command parameters in value
async function send_command(value) {
    // Add target and selected command to request body
    value["target"] = target_node

    let csrftoken = getCookie('csrftoken');

    var result = await fetch('/send_command', {
        method: 'POST',
        body: JSON.stringify(value),
        headers: { 'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            "X-CSRFToken": csrftoken }
    });

    return result
};



// Handler for current_rule reset menu option
async function reset(el) {
    const target = el.id.split("-")[0];
    console.log(`Reseting ${target}`);
    // Device or sensor
    const category = target.replace(/[0-9]/g, '') + "s";

    var result = await send_command({'command': 'reset_rule', 'instance': target});
    result = await result.json();

    if (JSON.stringify(result).startsWith('{"ERROR')) {
        console.log(`Failed to reset ${target} rule`);
    } else {
        // Update current rule
        const scheduled = target_node_status[category][target]["scheduled_rule"];

        try {
            // Update slider position
            const slider = document.getElementById(target + "-rule");
            slider.value = scheduled;
            $('input[type="range"]').rangeslider('update', true);

            // Select handle element closest to slider, update current rule displayed
            var $handle = $('.rangeslider__handle', document.getElementById(target + '-rule').nextSibling);
            $handle[0].textContent = get_display_value(slider);
        } catch(err) {};

        // Disable reset option
        document.getElementById(target + "-reset").classList.add("disabled");
    };
};



// Handler for "Reset all rules" option in global menu
function reset_all_rules() {
    Array.from(document.getElementsByClassName("reset-rule")).forEach(option => {
        if (!option.classList.contains("disabled")) {
            option.click();
        };
    });
};



// Handler for device enable/disable toggle
async function enable_disable_handler(el) {
    const target = el.id.split("-")[0];
    // Device or sensor
    const category = target.replace(/[0-9]/g, '') + "s";

    if (target_node_status[category][target]["enabled"]) {
        console.log(`Disabling ${target}`);
        el.innerHTML = "Enable";
        var result = await send_command({'command': 'disable', 'instance': target, 'delay_input': ''});
    } else {
        el.innerHTML = "Disable";
        console.log(`Enabling ${target}`);
        var result = await send_command({'command': 'enable', 'instance': target, 'delay_input': ''});
    };

    result = await result.json();
    if (JSON.stringify(result).startsWith('{"ERROR')) {
        // Command failed
        if (target_node_status[category][target]["enabled"]) {
            alert(`Failed to disable ${target}`);
            // Expand card, change menu option text
            // TODO figure out why collapse('show') doesn't work. Temporary workaround (no animation) below
//                     $('#' + target + '-body').collapse('show')
            var card = document.getElementById(target + "-body").classList.add('show');
            el.innerHTML = "Disable";
        } else {
            alert(`Failed to enable ${target}`);
            // Collapse card, change menu option text
            $('#' + target + '-body').collapse('hide');
            el.innerHTML = "Enable";
        };
    };
};

// Handler for device power on/off toggle
async function power(el) {
    const target = el.id.split("-")[0];

    if (el.classList.contains("toggle-on")) {
        // Fade button back to on appearance
        el.classList.remove("toggle-on");
        el.classList.add("toggle-off");

        var result = await send_command({'command': 'turn_off', 'instance': target});
        result = await result.json();

        // If send failed, fade button back to off appearance
        if (JSON.stringify(result).startsWith('{"ERROR')) {
            console.log(`Failed to turn off ${target}`);
            el.classList.remove("toggle-off");
            el.classList.add("toggle-on");
        };

    } else {
        // Fade button back to off appearance
        el.classList.remove("toggle-off");
        el.classList.add("toggle-on");

        var result = await send_command({'command': 'turn_on', 'instance': target});
        result = await result.json();

        // If send failed, fade button back to on appearance
        if (JSON.stringify(result).startsWith('{"ERROR')) {
            console.log(`Failed to turn on ${target}`);
            el.classList.remove("toggle-on");
            el.classList.add("toggle-off");
        };

    };
};

// Handler for trigger sensor button
async function trigger(el) {
    const target = el.id.split("-")[0];
    el.classList.remove("trigger-off");
    el.classList.add("trigger-on");

    // Prevent getting stuck in wrong state if condition_met changes back before next status update
    target_node_status["sensors"][target]["condition_met"] = true;

    var result = await send_command({'command': 'trigger_sensor', 'instance': target});
    result = await result.json();

    if (JSON.stringify(result).startsWith('{"ERROR')) {
        console.log(`Failed to trigger ${target}`);
        el.classList.remove("trigger-on");
        el.classList.add("trigger-off");
    } else {
        // Update page contents immediately after triggering (sensor probably turned targets on)
        updateStatusObject();
    };
};
