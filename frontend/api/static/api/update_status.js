// Maps subscribed parameters to callback functions
class Observer {
    constructor() {
        // Store param:callback pairs
        this.subscribers = {};
    };

    // Add callback if not already subscribed to param
    subscribe(param, callback) {
        if (!this.subscribers[param]) {
            this.subscribers[param] = callback;
            return callback;
        } else {
            console.log(`Already subscribed to ${param}`);
            return false;
        };
    };

    // Run callback with data from new status
    update(param, new_status) {
        if (this.subscribers[param]) {
            this.subscribers[param](new_status);
        } else {
            console.log(`Not subscribed to ${param}`);
        };
    };
};

// Called every 5 seconds, gets new status and updates page to reflect
// Also detects offline nodes and shows unable to connect modal
async function get_new_status() {
    // Get new status object
    var new_status = await fetch(`/get_status/${target_node_status.metadata.id}`);
    new_status = await new_status.json();

    // Unable to connect (first failure)
    if (selected_node_unreachable == false && String(new_status).startsWith("Error:")) {
        errorModal.show();
        console.log("Unable to connect to target, will retry every 5 seconds.");
        selected_node_unreachable = true;
        return;

    // Able to connect after failure
    } else if (selected_node_unreachable == true && !String(new_status).startsWith("Error:")) {
        errorModal.hide();
        // Refresh page (node config may have changed, need to get new device/sensor cards)
        location.reload();

    // Still unable to connect (not first failure)
    } else if (selected_node_unreachable == true) {
        return;
    };

    // Find differences between old and new status, update page to reflect
    update_status(target_node_status, new_status);

    // Overwrite old status (unless adding schedule rule in progress)
    if (!status_lock) {
        target_node_status = new_status;
    };
};
setInterval(get_new_status, 5000);

// Iterate new and old status objects, find changes, call observer callbacks
function update_status(oldStatus, newStatus) {
    for (let section in newStatus) {
        for (let instance in newStatus[section]) {
            for (let param in newStatus[section][instance]) {
                if (JSON.stringify(newStatus[section][instance][param]) != JSON.stringify(oldStatus[section][instance][param])) {
                    monitor_status.update(param, { section, instance, param, value: newStatus[section][instance] });
                };
            };
        };
    };
};



// Instantiate observer, add callback for each param shown in frontend
const monitor_status = new Observer();

// Collapse/expand card to reflect disable/enable
const update_enabled_state = monitor_status.subscribe("enabled", (new_status) => {
    // Get card collapse instance
    const card = document.getElementById(`${new_status['instance']}-body`);
    const cardCollapse = bootstrap.Collapse.getOrCreateInstance(card, { toggle: false });

    if (new_status['value']['enabled']) {
        // Expand card, change menu option text
        cardCollapse.show();
        document.getElementById(`${new_status['instance']}-enable`).innerHTML = "Disable";
        console.log(`${new_status['instance']} enabled`);

    } else {
        // Collapse card, change menu option text
        cardCollapse.hide();
        document.getElementById(`${new_status['instance']}-enable`).innerHTML = "Enable";
        console.log(`${new_status['instance']} disabled`);
    };
});

// Run animation on power button
const update_power_state = monitor_status.subscribe("turned_on", (new_status) => {
    // Get power button
    const button = document.getElementById(`${new_status['instance']}-power-state`);

    // Device turned ON since last status update
    if (new_status['value']['turned_on']) {
        button.classList.remove("toggle-off");
        button.classList.add("toggle-on");
        console.log(`${new_status['instance']} turned on`);

        // Device turned OFF since last status update
    } else {
        button.classList.remove("toggle-on");
        button.classList.add("toggle-off");
        console.log(`${new_status['instance']} turned off`);
    };
});

// Run animation on trigger button
const update_condition_met = monitor_status.subscribe("condition_met", (new_status) => {
    // Get trigger button
    const button = document.getElementById(`${new_status['instance']}-trigger`);

    // Sensor was triggered since last status update
    if (new_status['value']['condition_met']) {
        button.classList.remove("trigger-off")
        button.classList.add("trigger-on")
        console.log(`${new_status['instance']} triggered`);

        // Sensor no longer triggered
    } else {
        button.checked = false;
        button.classList.remove("trigger-on")
        button.classList.add("trigger-off")
        console.log(`${new_status['instance']} no longer triggered`);
    };
});

// Update temperature in thermostat card
const update_temperature = monitor_status.subscribe("temp", (new_status) => {
    console.log(`Temperature: ${new_status['value']['temp']}`)
    const new_temp = new_status['value']['temp'].toFixed(2);

    // Update temp shown on climate data card
    document.getElementById("temperature").innerHTML = new_temp;

    // Add reading to temp history chart
    temp_history_chart.data.labels.push(moment());
    temp_history_chart.data.datasets.forEach((dataset) => {
        dataset.data.push(new_temp);
    });
    temp_history_chart.update();
});

// Update humidity in thermostat card
const update_humidity = monitor_status.subscribe("humid", (new_status) => {
    console.log(`Humidity: ${new_status['value']['humid']}`)
    document.getElementById("humidity").innerHTML = new_status['value']['humid'].toFixed(2);
});

// Called by both current_rule and scheduled_rule
// Update rule slider, enable/disable reset option if different from/same as scheduled
function update_rules(new_status) {
    try {
        // TODO shouldn't move slider while user is moving it (currently jumps back to current rule every time this runs)
        const slider = document.getElementById(`${new_status['instance']}-rule`);

        slider.value = new_status["value"]["current_rule"];
        $('input[type="range"]').rangeslider('update', true);

        // Select handle element closest to slider, update current rule displayed
        var $handle = $('.rangeslider__handle', document.getElementById(`${new_status['instance']}-rule`).nextSibling);
        $handle[0].textContent = get_display_value(slider);

        if (new_status['value']["current_rule"] != new_status['value']["scheduled_rule"]) {
            // Enable reset option
            document.getElementById(`${new_status['instance']}-reset`).classList.remove("disabled");
        } else {
            // Disable reset option
            document.getElementById(`${new_status['instance']}-reset`).classList.add("disabled");
        };
    } catch(err) {};
};

const update_current_rule = monitor_status.subscribe("current_rule", (new_status) => {
    console.log(`${new_status['instance']} new rule: ${new_status["value"]["current_rule"]}`)
    update_rules(new_status);
});

const update_scheduled_rule = monitor_status.subscribe("scheduled_rule", (new_status) => {
    console.log(`${new_status['instance']} new scheduled rule: ${new_status["value"]["scheduled_rule"]}`)
    update_rules(new_status);
});

// Find new, deleted, or modified rules and update table to reflect
const update_schedule_rules = monitor_status.subscribe("schedule", (new_status) => {
    console.log(`Updating ${new_status['instance']} schedule rules`)
    const old_rules = target_node_status[new_status.section][new_status.instance]["schedule"];
    const new_rules = new_status['value']["schedule"]
    const instance = new_status['instance']

    var table = document.getElementById(`${instance}-rules`);
    var rows = Array.from(table.rows);

    // Find deleted rules
    for (let time in old_rules) {
        if (!new_rules[time]) {
            // Deleted rule found - iterate table rows, find rule, remove
            for (row of rows) {
                if (row.cells[0].children[0]?.dataset.original == time) {
                    row.remove();
                    break;
                };
            };
        };
    };

    // Find new or modified rules
    for (let time in new_rules) {
        if (!old_rules[time]) {
            // New rule found (didn't exist in old). Get new row number
            const row = parseInt(rows[rows.length-1].id.split("-")[2]) + 1

            // Add row number + instance id + rule vlaues to template
            var template = `<tr id="${instance}-row-${row}">
            <td><input type="time" class="form-control" id="schedule-${instance}-rule${row}-time" placeholder="HH:MM" name="schedule-${instance}-rule${row}-time" value=${time} data-original=${time}></td>
            <td><input type="text" class="form-control" id="schedule-${instance}-rule${row}-value" placeholder="" name="schedule-${instance}-rule${row}-value" value=${new_rules[time]} data-original=${new_rules[time]}></td>
            <td class="min"><button type="button" class="remove btn btn-sm btn-danger mt-1" id="${instance}-remove${row}" onclick="delete_rule(this)"><i class="bi-trash"></i></button></td>
            </tr>`

            // Add new row
            table.insertAdjacentHTML('beforeend', template);

            // Add listeners, changes delete button to add button if user modifies fields (newly added rows don't have listener until add button clicked)
            document.getElementById(`schedule-${instance}-rule${row}-time`).addEventListener("input", schedule_rule_field_handler);
            document.getElementById(`schedule-${instance}-rule${row}-value`).addEventListener("input", schedule_rule_field_handler);

        } else if (new_rules[time] != old_rules[time]) {
            // Timestamp unchanged, rule changed
            console.log("overwriting rule")
            for (row of rows) {
                if (row.cells[0].children[0]?.value == time) {
                    row.cells[1].children[0].value = new_rules[time];
                    row.cells[1].children[0].dataset.original = new_rules[time];
                };
            };
        };
    };
});
