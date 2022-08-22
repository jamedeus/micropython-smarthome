// Get array of schedule rule input tooltips (used to show help messages when invalid rule entered, not shown on hover)
var schedule_rule_tooltips = {};
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
for (i in tooltipTriggerList) {
    // Add with element ID as key, tooltip as value
    schedule_rule_tooltips[tooltipTriggerList[i].id] = new bootstrap.Tooltip(tooltipTriggerList[i]);
};



// Tooltip stays visible until user hovers or selects field
function hide_tooltip(e) {
    schedule_rule_tooltips[e.target.id].hide();
};



// Add listeners to hide tooltip on hover/select
for (id in schedule_rule_tooltips) {
    document.getElementById(id).addEventListener("mouseover", hide_tooltip);
    document.getElementById(id).addEventListener("focus", hide_tooltip);
};



// Add listeners to existing schedule rule fields, if modified change delete button to upload button
for (field of document.getElementsByClassName("schedule-rule")) {
    field.addEventListener("input", schedule_rule_field_handler);
};



// Initialize toast, allows user to write new/deleted rules to disk
const save_rules_toast = new bootstrap.Toast(document.getElementById("save_rules_toast"));



// Runs when user changes schedule rule fields
// Existing rules: Delete button changes to add button
// Modified rules: If changed back to original value, add button reverts back to delete
function schedule_rule_field_handler(e) {
    const id = e.target.id.split("-")[1];
    const row = e.target.id.split("-")[2].replace("rule", "");
    const time_field = document.getElementById(`schedule-${id}-rule${row}-time`);
    const rule_field = document.getElementById(`schedule-${id}-rule${row}-value`);

    // Function runs on each keystroke, only need to change button once on first change
    // Subsequent changes will throw error when getting button element (ID changed first time)
    try {
        // If user changed an existing rule, replace Delete button with Add button
        if (time_field.value != time_field.dataset.original || rule_field.value != rule_field.dataset.original) {

            var button = document.getElementById(id + "-remove" + row);

            // Change to Add button
            button.classList.remove("btn-danger");
            button.classList.add("btn-success");
            button.innerHTML = "<i class='bi-plus-lg'>";
            button.id = button.id.replace("remove", "add");
            button.setAttribute( "onClick", "add_rule(this);" );

        // If user modified a rule and then reverted changes, replace Add button with Delete button
        } else {

            var button = document.getElementById(id + "-add" + row);

            // Change back to Delete button
            button.classList.remove("btn-success");
            button.classList.add("btn-danger");
            button.innerHTML = "<i class='bi-trash'></i>";
            button.id = button.id.replace("add", "remove");
            button.setAttribute( "onClick", "delete_rule(this);" );

        };
    } catch(err) {};
};



async function add_rule_row(el) {
    // Get target device/sensor
    const target = el.id.split("-")[0];

    // Get new row number
    const table = document.getElementById(target + "-rules");
    const row = parseInt(table.rows[table.rows.length-1].id.split("-")[2]) + 1

    // Add row number + target id to empty row template (different template if api-target)
    if (target.startsWith("device") && target_node_status['devices'][target]['type'] == 'api-target') {
        var template = `<tr id="${target}-row-${row}">
                            <td><input type="time" class="form-control" id="schedule-${target}-rule${row}-time" placeholder="HH:MM" name="schedule-${target}-rule${row}-time" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Rule at this time already exists"></td>
                            <td><button id="schedule-${target}-rule${row}-button" class="form-control" onclick="open_rule_modal(this);" type="button">Set rule</button>
                            <input type="text" class="form-control rule ${target}" id="schedule-${target}-rule${row}-value" value="" style="display:none;"></td>
                            <td class="min"><button type="button" class="remove btn btn-sm btn-success mt-1" id="${target}-add${row}" onclick="add_rule_api(this)"><i class="bi-plus-lg"></i></button></td>
                        </tr>`
    } else {
        var template = `<tr id="${target}-row-${row}">
                            <td><input type="time" class="form-control" id="schedule-${target}-rule${row}-time" placeholder="HH:MM" name="schedule-${target}-rule${row}-time" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Rule at this time already exists"></td>
                            <td><input type="text" class="form-control" id="schedule-${target}-rule${row}-value" placeholder="" name="schedule-${target}-rule${row}-value" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule"></td>
                            <td class="min"><button type="button" class="remove btn btn-sm btn-success mt-1" id="${target}-add${row}" onclick="add_rule(this)"><i class="bi-plus-lg"></i></button></td>
                        </tr>`
    };

    // Add new empty rows
    document.getElementById(target + "-rules").insertAdjacentHTML('beforeend', template);

    // Add tooltips (used for help messages when invalid rule entered)
    schedule_rule_tooltips[`schedule-${target}-rule${row}-time`] = new bootstrap.Tooltip(document.getElementById(`schedule-${target}-rule${row}-time`));
    schedule_rule_tooltips[`schedule-${target}-rule${row}-value`] = new bootstrap.Tooltip(document.getElementById(`schedule-${target}-rule${row}-value`));

    // Add listener to dismiss tooltips on hover/select
    document.getElementById(`schedule-${target}-rule${row}-time`).addEventListener("mouseover", hide_tooltip);
    document.getElementById(`schedule-${target}-rule${row}-time`).addEventListener("focus", hide_tooltip);
    document.getElementById(`schedule-${target}-rule${row}-value`).addEventListener("mouseover", hide_tooltip);
    document.getElementById(`schedule-${target}-rule${row}-value`).addEventListener("focus", hide_tooltip);

    // Focus time field
    document.getElementById(`schedule-${target}-rule${row}-time`).focus();

    // Hide add rule button (will be un-hidden when user finishes adding this rule)
    document.getElementById(target + "-add-rule").style.display = "none"
};



function disable_row(row, disable) {
    if (disable) {
        for (field of row.children) {
            field.children[0].disabled = true;
        };
    } else {
        for (field of row.children) {
            field.children[0].disabled = false;
        };
    };
};



// Handler for add button in schedule rules dropdown, used to create new rules and edit existing
async function add_rule(el) {
    // Get target device/sensor
    const target = el.id.split("-")[0];

    // Get rule number
    const num = el.id.split("add")[1];

    // Disable row fields + button (prevent user submitting multiple times)
    row = document.getElementById(target + "-row-" + num);
    disable_row(row, true);

    // Get timestamp input
    const timestamp = document.getElementById(`schedule-${target}-rule${num}-time`);

    // Get rule input
    const rule = document.getElementById(`schedule-${target}-rule${num}-value`);

    // Do not add incomplete rule
    if (timestamp.value.length == 0 || rule.value.length == 0) {
        el.disabled = false;
        return;
    };

    // Prevent other functions modifying status object until finished adding rule
    // Otherwise if user clicked add after monitoring function got new status, but before it overwrote old, changes made below may be overwritten
    status_lock = true;

    // If user modified an existing rule without changing timestamp, add overwrite arg
    if (timestamp.dataset.original == timestamp.value) {
        var result = await send_command({'command': 'add_rule', 'instance': target, 'time': timestamp.value, 'rule': rule.value, 'overwrite': 'overwrite'});
        result = await result.json();
    } else {
        var result = await send_command({'command': 'add_rule', 'instance': target, 'time': timestamp.value, 'rule': rule.value});
        result = await result.json();
    };

    if (JSON.stringify(result).startsWith('{"ERROR":"Rule already exists')) {
        // Re-enable row inputs and button
        disable_row(row, false);

        // Focus field with invalid param
        timestamp.focus();

        // Show tooltip
        schedule_rule_tooltips[timestamp.id].show();

    } else if (JSON.stringify(result) == '{"ERROR":"Invalid rule"}') {
        // Re-enable row inputs and button
        disable_row(row, false);

        // Focus field with invalid param
        rule.focus();

        // Show tooltip
        schedule_rule_tooltips[rule.id].show();

    } else if (JSON.stringify(result).startsWith('{"ERROR')) {
        // All other errors (unable to connect etc.)
        alert(JSON.stringify(result));

        // Re-enable row inputs and button
        disable_row(row, false);

    } else {
        // Add to current status object (prevent duplicate being created when new status object containing this rule is received)
        target_node_status[target.replace(/[0-9]/g, '') + "s"][target]["schedule"][timestamp.value] = rule.value;

        // If successfully added, change add button to delete button, re-enable
        el.classList.remove("btn-success");
        el.classList.add("btn-danger");
        el.innerHTML = "<i class='bi-trash'></i>";
        el.id = el.id.replace("add", "remove");
        el.setAttribute( "onClick", "delete_rule(this);" );

        // If user modified existing rule's timestamp, delete rule with old timestamp
        if (timestamp.dataset.original && timestamp.value != timestamp.dataset.original) {
            delete_rule(document.getElementById(target + "-remove" + num), false);
        };

        // Replace original values with new values (used to detect change after adding)
        timestamp.dataset.original = timestamp.value;
        rule.dataset.original = rule.value;

        // Allow overwriting
        status_lock = false;

        // Add listeners, changes delete button to add button if user modifies fields (newly added rows don't have listener until add button clicked)
        timestamp.addEventListener("input", schedule_rule_field_handler);
        rule.addEventListener("input", schedule_rule_field_handler);

        // Unhide add rule button so user can continue adding rules if needed
        document.getElementById(target + "-add-rule").style.display = "initial"

        // Re-enable row inputs and button
        disable_row(row, false);

        // Show toast message, allows user to write change to disk
        save_rules_toast.show();
    };
};



// Handler for delete button in schedule rules dropdown
// Removes row from table after deleting rule unless called with remove=false
async function delete_rule(selected, remove=true) {
    // Prevent user submitting multiple times
    selected.disabled = true;

    // Get target device/sensor
    const target = selected.id.split("-")[0];

    // Get rule number
    const rule = selected.id.split("-")[1].replace(/[a-z]/g, '')

    // Get timestamp
    // Uses dataset.original instead of .value to allow editing existing rules (old needs to be deleted before adding new, see add_rule() below)
    // While delete button is visible to user, dataset.original and .value are always identical (changes to add button when different)
    const timestamp = document.getElementById(`schedule-${target}-rule${rule}-time`).dataset.original;

    // Send command
    var result = await send_command({'command': 'remove_rule', 'instance': target, 'rule': timestamp});
    result = await result.json();

    if (JSON.stringify(result).startsWith('{"ERROR')) {
        // Re-enable button if failed to delete
        alert(JSON.stringify(result));
        selected.disabled = false;
    } else if (remove) {
        // Delete row if success
        document.getElementById(selected.id).parentElement.parentElement.remove();

        // Check if deleted rule was last rule
        if (document.getElementById(target + "-rules").rows.length == 1) {
            // If no rules remain, add blank row
            var template = `<tr id="${target}-row-1">
                                <td><input type="time" class="form-control" id="schedule-${target}-rule1-time" placeholder="HH:MM" name="schedule-${target}-rule1-time"></td>
                                <td><input type="text" class="form-control" id="schedule-${target}-rule1-value" placeholder="" name="schedule-${target}-rule1-value"></td>
                                <td class="min"><button type="button" class="remove btn btn-sm btn-success mt-1" id="${target}-add1" onclick="add_rule(this)"><i class="bi-plus-lg"></i></button></td>
                            </tr>`

            document.getElementById(target + "-rules").insertAdjacentHTML('beforeend', template);

            // Hide add row button
            document.getElementById(target + "-add-rule").style.display = "none";
        };

        // Show toast message, allows user to write change to disk
        save_rules_toast.show();
    };
};
