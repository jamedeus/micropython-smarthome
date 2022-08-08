// Initialize all range sliders, add listeners
for (slider of $('input[type="range"]')) {
    // Initialize
    $('#' + slider.id).rangeslider({
        polyfill: false,
        onInit: function() {
        // Select handle element closest to slider, update displayed rule
        $handle = $('.rangeslider__handle', this.$range);
        $handle[0].textContent = this.value;

        this.$range[0].classList.add("mx-auto")
        }
    });

    // Update current rule displayed while slider moves
    $('#' + slider.id).on('input', function(e) {
        // Select handle element closest to slider, update displayed rule
        var $handle = $('.rangeslider__handle', e.target.nextSibling);
        $handle[0].textContent = this.value;
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

        console.log(`${id}: new rule = ${new_rule}, type = ${typeof(new_rule)}`)

        // Fire API command
        var result = await send_command({'command': 'set_rule', 'instance': id, 'rule': new_rule});
        result = await result.json();
    });
};



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
    $handle[0].textContent = document.getElementById(target + '-rule').value;

    // Show reset button if new rule differs from scheduled, otherwise hide reset button
    if (new_rule != scheduled) {
        document.getElementById(target + "-reset").classList.remove("disabled");
    } else {
        document.getElementById(target + "-reset").classList.add("disabled");
    };

    // Fire API command
    var result = await send_command({'command': 'set_rule', 'instance': target, 'rule': new_rule.toString()});
    result = await result.json();
};
