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


// Handler for rule slider plus and minus buttons
async function rule_slider_increment(button) {
    const target = button.id.split("-")[0];
    const slider = document.getElementById(`${target}-rule`);
    const current = parseFloat(slider.value);

    // Get increment amount
    if (button.id.split("-")[2] == "up") {
        var increment = parseFloat(button.dataset.stepsize);
    } else {
        var increment = -parseFloat(button.dataset.stepsize);
    };

    // Get new rule
    const new_rule = current + increment;

    // Update slider position
    slider.value = new_rule;
    $('input[type="range"]').rangeslider('update', true);
    // Select handle element closest to slider, update current rule displayed
    var $handle = $('.rangeslider__handle', slider.nextSibling);
    $handle[0].textContent = get_display_value(slider);

    // Enable reset menu option if new rule differs from scheduled, otherwise hide reset button
    update_reset_option(target, new_rule);

    // Fire API command
    var result = await send_command({'command': 'increment_rule', 'instance': target, 'amount': increment.toString()});
    result = await result.json();
};
