// Initialize all range sliders, add listeners
for (slider of $('input[type="range"]')) {
    // Initialize
    $('#' + slider.id).rangeslider({
        polyfill: false,
        onInit: function() {
        // Select handle element closest to slider, update displayed rule
        $handle = $('.rangeslider__handle', this.$range);
        $handle[0].textContent = get_display_value(slider);

        this.$range[0].classList.add("mx-auto")
        }
    });

    // Update current rule displayed while slider moves
    $('#' + slider.id).on('input', function(e) {

        // Select handle element closest to slider, update displayed rule
        var $handle = $('.rangeslider__handle', e.target.nextSibling);
        $handle[0].textContent = get_display_value(document.getElementById(e.target.id));
    });

    // Runs once when user releases click on slider
    $('#' + slider.id).on('change', async function(e) {
        const id = e.target.id.split("-")[0];
        // Device or sensor
        const category = id.replace(/[0-9]/g, '') + "s";

        const new_rule = this.value;
        const scheduled = target_node_status[category][id]["scheduled_rule"];

        // Enable reset option if new rule differs from scheduled, otherwise disable
        if (new_rule != scheduled) {
            document.getElementById(id + "-reset").classList.remove("disabled");
        } else {
            document.getElementById(id + "-reset").classList.add("disabled");
        };

        // Fire API command
        var result = await send_command({'command': 'set_rule', 'instance': id, 'rule': new_rule});
        result = await result.json();
    });
};



// Read slider's data attributes, convert element's value to desired range as either float or int
function get_display_value(slider) {
    // Get slider value range
    const vmin = slider.min;
    const vmax = slider.max;

    // Get display range (may differ)
    const dmin = slider.dataset.displaymin;
    const dmax = slider.dataset.displaymax;

    if (slider.dataset.displaytype == "float") {
        return parseFloat(map_range(parseFloat(slider.value), parseFloat(vmin), parseFloat(vmax), parseFloat(dmin), parseFloat(dmax))).toFixed(1);

    } else {
        return parseInt(map_range(parseInt(slider.value), parseInt(vmin), parseInt(vmax), parseInt(dmin), parseInt(dmax)));
    };
};



// Maps value x in range to equivalent value in different range
function map_range(x, in_min, in_max, out_min, out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}



// Enable reset option if current rule differs from scheduled
for (slider of document.getElementsByClassName("current-rule-slider")) {
    const id = slider.id.split("-")[0];
    // Device or sensor
    const category = id.replace(/[0-9]/g, '') + "s";

    // Used in listeners below
    const rule = slider.value;
    const scheduled = target_node_status[category][id]["scheduled_rule"];

    // If current rule != scheduled rule, enable reset option
    if (rule != scheduled) {
        document.getElementById(id + "-reset").classList.remove("disabled");
    } else {
        document.getElementById(id + "-reset").classList.add("disabled");
    };
};



// Handler for rule slider plus and minus buttons
async function rule_slider_increment(button) {
    const target = button.id.split("-")[0];
    // Device or sensor
    const category = target.replace(/[0-9]/g, '') + "s";

    const current = parseFloat(document.getElementById(`${target}-rule`).value);
    const scheduled = target_node_status[category][target]["scheduled_rule"];

    if (button.id.split("-")[2] == "up") {
        var new_rule = current + parseFloat(button.dataset.stepsize);
    } else {
        var new_rule = current - parseFloat(button.dataset.stepsize);
    };

    // Update slider position
    document.getElementById(`${target}-rule`).value = new_rule;
    $('input[type="range"]').rangeslider('update', true);
    // Select handle element closest to slider, update current rule displayed
    var $handle = $('.rangeslider__handle', document.getElementById(target + '-rule').nextSibling);
    $handle[0].textContent = get_display_value(document.getElementById(`${target}-rule`));

    // Enable reset menu option if new rule differs from scheduled, otherwise hide reset button
    if (new_rule != scheduled) {
        document.getElementById(target + "-reset").classList.remove("disabled");
    } else {
        document.getElementById(target + "-reset").classList.add("disabled");
    };

    // Fire API command
    var result = await send_command({'command': 'set_rule', 'instance': target, 'rule': new_rule.toString()});
    result = await result.json();
};
