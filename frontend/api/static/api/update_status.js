// Request new status object, compare to old, update page contents to reflect changes (if any)
async function updateStatusObject() {
    // Get status object
    var new_status = await fetch("/get_status/" + target_node);
    new_status = await new_status.json();

    // If unable to connect
    if (selected_node_unreachable == false && new_status == "Error: Unable to connect.") {
        $("#error-modal").modal("show");
        console.log("Unable to connect to target, will retry every 5 seconds.");
        selected_node_unreachable = true;
        return;

    } else if (selected_node_unreachable == true && new_status != "Error: Unable to connect.") {
        $("#error-modal").modal("hide");
        console.log("Re-connected to target.");
        selected_node_unreachable = false;
    } else if (selected_node_unreachable == true) {
        // Prevent iterating error message in loop below
        return;
    };

    // Find changes
    for (let section in new_status) {
        for (let instance in new_status[section]) {
            for (let param in new_status[section][instance]) {
                if (JSON.stringify(new_status[section][instance][param]) != JSON.stringify(target_node_status[section][instance][param])) {

                    if (param == "turned_on") {
                        // Get element
                        const button = document.getElementById(instance + "-power-state");

                        // Device turned ON since last status update
                        if (new_status[section][instance][param]) {
                            button.classList.remove("toggle-off");
                            button.classList.add("toggle-on");

                        // Device turned OFF since last status update
                        } else {
                            button.classList.remove("toggle-on");
                            button.classList.add("toggle-off");
                        };

                    } else if (param == "condition_met") {
                        // Get button
                        const button = document.getElementById(instance + "-trigger");

                        // Sensor was triggered since last status update
                        if (new_status[section][instance][param]) {
                            button.classList.remove("trigger-off")
                            button.classList.add("trigger-on")

                        // Sensor no longer triggered
                        } else {
                            button.checked = false;
                            button.classList.remove("trigger-on")
                            button.classList.add("trigger-off")
                        };

                    } else if (param == "current_rule" || param == "scheduled_rule") {
                        try {
                            // TODO shouldn't move slider while user is moving it (currently jumps back to current rule every time this runs)
                            const slider = document.getElementById(instance + "-rule");

                            slider.value = new_status[section][instance]["current_rule"];
                            $('input[type="range"]').rangeslider('update', true);

                            // Select handle element closest to slider, update current rule displayed
                            var $handle = $('.rangeslider__handle', document.getElementById(instance + '-rule').nextSibling);
                            $handle[0].textContent = document.getElementById(instance + '-rule').value;

                            if (new_status[section][instance]["current_rule"] != new_status[section][instance]["scheduled_rule"]) {
                                // Enable reset option
                                document.getElementById(instance + "-reset").classList.remove("disabled");
                            } else {
                                // Disable reset option
                                document.getElementById(instance + "-reset").classList.add("disabled");
                            };
                        } catch(err) {};

                    } else if (param == "enabled") {
                        if (new_status[section][instance]["enabled"]) {
                            // Expand card, change menu option text
                            $('#' + instance + '-body').collapse('show')
                            document.getElementById(instance + "-enable").innerHTML = "Disable";

                        } else {
                            // Collapse card, change menu option text
                            $('#' + instance + '-body').collapse('hide')
                            document.getElementById(instance + "-enable").innerHTML = "Enable";

                        };

                    } else if (param == "temp") {
                        document.getElementById("temperature").innerHTML = new_status[section][instance]["temp"].toFixed(2)

                    } else if (param == "humid") {
                        document.getElementById("humidity").innerHTML = new_status[section][instance]["humid"].toFixed(2)

                    } else if (param == "schedule") {
                        updateScheduleRules(instance, target_node_status[section][instance]["schedule"], new_status[section][instance]["schedule"]);

//                             } else if (param == "") {

                    // TODO Continue adding endpoints here as they are implemented

                    };
                };
            };
        };
    };

    // Do not overwrite old config with error (if connection lost, will have nothing to compare against when re-connected)
    if (!selected_node_unreachable && !status_lock) {
        target_node_status = new_status;
    };
}



// Called by updateStatusObject, passes instance name, schedule rules from last status object, schedule rules from current status object
// Finds new, deleted, or modified rules and updates table to reflect
function updateScheduleRules(instance, old_rules, new_rules) {
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
};



// Query status every 5 seconds
function monitorSelectedNodeStatus(start) {
    if (start) {
        statusTimer = setInterval(updateStatusObject, 5000);
    } else {
        clearInterval(statusTimer);
    };
};



// Start monitoring
monitorSelectedNodeStatus(true);
