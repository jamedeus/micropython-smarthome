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



// Handler for back button (top-left)
function back(node) {
    // Show loading animation
    document.getElementById('container').classList.remove('fade-in');
    document.getElementById('container').classList.add('fade-out');

    // Redirect to overview
    if (typeof recording == 'undefined') {
        window.location.href = '/api';
    } else {
        window.location.href = `/api/recording/${recording}`;
    };
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



// Handler for device enable/disable toggle
async function enable_disable_handler(el) {
    const target = el.id.split("-")[0];
    const card = document.getElementById(`${target}-body`);
    const cardCollapse = bootstrap.Collapse.getOrCreateInstance(card, { toggle: false });

    if (window.getComputedStyle(card).display == 'none') {
        var result = await send_command({'command': 'enable', 'instance': target, 'delay_input': ''});
        console.log(`Enabling ${target}`);
        cardCollapse.show();
        el.innerHTML = "Disable";
    } else {
        var result = await send_command({'command': 'disable', 'instance': target, 'delay_input': ''});
        console.log(`Disabling ${target}`);
        cardCollapse.hide();
        el.innerHTML = "Enable";
    };

    result = await result.json();
    if (JSON.stringify(result).startsWith('"Error')) {
        // Command failed, flip state back
        if (window.getComputedStyle(card).display == 'none') {
            el.innerHTML = "Enable";
            alert(`Failed to enable ${target}`);
        } else {
            el.innerHTML = "Disable";
            alert(`Failed to disable ${target}`);
        };
        cardCollapse.toggle();
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
        // Catch error for record mode
        try{updateStatusObject()}catch(err){};
    };
};



// Highlight all targets of sensor when menu option clicked, dismiss highlights on next click
function show_targets(el) {
    // Get sensor ID, array of all targets
    const sensor = el.id.split("-")[0];
    const targets = target_node_status["sensors"][sensor]["targets"];

    // Prevent click bubbling to listener below, close dropdown manually
    event.stopPropagation();
    bootstrap.Dropdown.getInstance(document.getElementById(`${sensor}-menu-button`)).toggle();

    // Iterate targets, add glow effect
    targets.forEach(function(target) {
        document.getElementById(target + "-card").classList.remove("highlight-off");
        document.getElementById(target + "-card").classList.add("highlight-on");
    });

    // Listener removes glow effect on next click
    document.addEventListener("click", function() {
        targets.forEach(function(target) {
            document.getElementById(target + "-card").classList.remove("highlight-on");
            document.getElementById(target + "-card").classList.add("highlight-off");
        });
    }, {once : true});
};



// Handler for debug menu option
async function debug(el) {
    const target = el.id.split("-")[0];
    console.log(`Getting ${target} attributes`);

    var result = await send_command({'command': 'get_attributes', 'instance': target});
    result = await result.json();

    if (JSON.stringify(result).startsWith('{"ERROR')) {
        console.log(`Failed to get ${target} attributes`);
    } else {
        // Dump json reply to modal body, show modal
        document.getElementById('debug-json').innerHTML = JSON.stringify(result, null, 4);
        debugModal.show();
    };
};
