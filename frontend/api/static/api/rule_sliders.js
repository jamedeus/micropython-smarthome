// Initialize all range sliders, add listeners
for (slider of $('input[type="range"]')) {
    add_new_slider(slider);

    // Attach listener to current_rule sliders, but not schedule rule sliders
    if (!slider.classList.contains('schedule-rule')) {
        // Runs once when user releases click on slider
        $(slider).on('change', async function(e) {
            const id = e.target.id.split("-")[0];
            const new_rule = this.value;

            // Enable reset option if new rule differs from scheduled, otherwise disable
            update_reset_option(id, new_rule);

            // Fire API command
            var result = await send_command({'command': 'set_rule', 'instance': id, 'rule': new_rule});
            result = await result.json();
        });
    };

    // Enable reset option if current rule differs from scheduled
    update_reset_option(slider.id.split("-")[0], slider.value);
};


// Enable reset option if current rule differs from scheduled
function update_reset_option(id, current_rule) {
    if (current_rule != get_status_attribute(id, "scheduled_rule")) {
        document.getElementById(`${id}-reset`).classList.remove("disabled");
    } else {
        document.getElementById(`${id}-reset`).classList.add("disabled");
    };
};


// Sends increment_rule API call when slider plus/minus buttons clicked
// Called by rule_slider_increment (see node_configuration rule_sliders.js)
async function rule_slider_increment_button_clicked(button, slider) {
    // Only send API call for current rule (not schedule rules)
    if (slider.classList.contains('current-rule-slider')) {
        // Get ID of device/sensor, current rule
        const target = button.dataset.section;
        const current = parseFloat(slider.value);

        // Get increment amount, new rule
        if (button.dataset.direction == "up") {
            var increment = parseFloat(button.dataset.stepsize);
        } else {
            var increment = -parseFloat(button.dataset.stepsize);
        };
        const new_rule = current + increment;

        // Enable reset menu option if new rule differs from scheduled, otherwise disable
        update_reset_option(target, new_rule);

        // Fire API command
        var result = await send_command({'command': 'increment_rule', 'instance': target, 'amount': increment.toString()});
        result = await result.json();
    };
};
