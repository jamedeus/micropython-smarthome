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
    // Slider library requires jquery listener
    if (field.type == 'range') {
        $('#' + field.id).on('change', async function(e) {
            schedule_rule_field_handler(e);
        });

    // All others inputs use vanilla listener
    } else {
        field.addEventListener("input", schedule_rule_field_handler);
    };
};



// Handler for schedule rules button on each card
function open_rules(button) {
    // Scroll opened card into view
    const id = button.id.split("-")[0];
    document.getElementById(`${id}-card`).scrollIntoView({behavior: 'smooth'});

    // Update all range sliders (prevents overflowing card width due to incorrect rendering while hidden)
    $('input[type="range"]').rangeslider('update', true);
}


// Initialize toast, allows user to write new/deleted rules to disk
const save_rules_toast = new bootstrap.Toast(document.getElementById("save_rules_toast"));



// Runs when user changes schedule rule fields
// Existing rules: Delete button changes to add button
// Modified rules: If changed back to original value, add button reverts back to delete
function schedule_rule_field_handler(e) {
    const id = e.target.id.split("-")[0];
    const row = e.target.id.split("-")[1].replace("rule", "");
    const time_field = document.getElementById(`${id}-rule${row}-time`);
    const rule_field = document.getElementById(`${id}-rule${row}`);

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

    // Track if a slider was added (needs to be initialized)
    var slider = false;

    // Add row number + target id + time field to empty row template
    var template = `<tr id="${target}-row-${row}">
                        <td><input type="time" class="form-control" id="${target}-rule${row}-time" placeholder="HH:MM" name="${target}-rule${row}-time" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Rule at this time already exists"></td>`

    // Add rule field depending on target type
    if (target.startsWith("device")) {
        var type = target_node_status['devices'][target]['type'];

        if (type == "dimmer" || type == "bulb") {
            // Text field
            template += `<td><input type="text" class="form-control" id="${target}-rule${row}" placeholder="" name="${target}-rule${row}" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule"></td>`

        } else if (type == "relay" || type == "dumb-relay" || type == "desktop" || type == "mosfet") {
            // Dropdown
            template += `<td><select id="${target}-rule${row}" name="${target}-rule${row}" class="form-select schedule-rule" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule" autocomplete="off">
                             <option>Select rule</option>
                             <option value="enabled">Enabled</option>
                             <option value="disabled">Disabled</option>
                         </select></td>`

        } else if (type == "pwm") {
            // Slider
            slider = true;
            template += `<td style="width: 100%">
                             <div class="d-flex flex-row align-items-center mt-2 pt-1">
                                 <input id="${target}-rule${row}" name="${target}-rule${row}" type="range" class="schedule-rule mx-auto" min="0" max="1023" data-displaymin="0" data-displaymax="100" data-displaytype="int" step="1" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule" autocomplete="off">
                             </div>
                         </td>`

        } else if (type == "api-target") {
            // Button with hidden field, opens modal
            template += `<td><button id="${target}-rule${row}-button" class="form-control" onclick="open_rule_modal(this);" type="button">Set rule</button>
                        <input type="text" class="form-control rule ${target}" id="${target}-rule${row}" value="" style="display:none;"></td>`

        };
    } else if (target.startsWith("sensor")) {
        var type = target_node_status['sensors'][target]['type'];

        if (type == "pir") {
            // Slider
            slider = true;
            template += `<td style="width: 100%">
                             <div class="d-flex flex-row align-items-center mt-2 pt-1">
                                 <input id="${target}-rule${row}" name="${target}-rule${row}" type="range" class="schedule-rule mx-auto" min="0" max="60" data-displaymin="0" data-displaymax="60" data-displaytype="float" step="0.5" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule" autocomplete="off">
                             </div>
                         </td>`

        } else if (type == "switch" || type == "desktop") {
            // Dropdown
            template += `<td><select id="${target}-rule${row}" name="${target}-rule${row}" class="form-select schedule-rule" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule" autocomplete="off">
                             <option>Select rule</option>
                             <option value="enabled">Enabled</option>
                             <option value="disabled">Disabled</option>
                         </select></td>`

        } else if (type == "dummy") {
            // Dropdown with additional options
            template += `<td><select id="${target}-rule${row}" name="${target}-rule${row}" class="form-select schedule-rule" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule" autocomplete="off">
                             <option>Select rule</option>
                             <option value="enabled">Enabled</option>
                             <option value="disabled">Disabled</option>
                             <option value="on">On</option>
                             <option value="off">Off</option>
                         </select></td>`

        } else if (type == "si7021") {
            // Slider
            slider = true;
            template += `<td><input id="${target}-rule${row}" name="${target}-rule${row}" type="range" class="schedule-rule mx-auto" min="65" max="80" data-displaymin="65" data-displaymax="80" data-displaytype="float" step="0.5" data-bs-toggle="tooltip" data-bs-trigger="manual" title="Invalid rule" autocomplete="off"></td>`

        };
    };

    // Finish empty row with add rule button
    template +=     `<td class="min"><button type="button" class="remove btn btn-sm btn-success mt-1" id="${target}-add${row}" onclick="add_rule(this)"><i class="bi-plus-lg"></i></button></td>
                 </tr>`

    // Add new empty rows
    document.getElementById(target + "-rules").insertAdjacentHTML('beforeend', template);

    // Add tooltips (used for help messages when invalid rule entered)
    schedule_rule_tooltips[`${target}-rule${row}-time`] = new bootstrap.Tooltip(document.getElementById(`${target}-rule${row}-time`));
    schedule_rule_tooltips[`${target}-rule${row}`] = new bootstrap.Tooltip(document.getElementById(`${target}-rule${row}`));

    // Add listener to dismiss tooltips on hover/select
    document.getElementById(`${target}-rule${row}-time`).addEventListener("mouseover", hide_tooltip);
    document.getElementById(`${target}-rule${row}-time`).addEventListener("focus", hide_tooltip);
    document.getElementById(`${target}-rule${row}`).addEventListener("mouseover", hide_tooltip);
    document.getElementById(`${target}-rule${row}`).addEventListener("focus", hide_tooltip);

    // Focus time field
    document.getElementById(`${target}-rule${row}-time`).focus();

    // Hide add rule button (will be un-hidden when user finishes adding this rule)
    document.getElementById(target + "-add-rule").style.display = "none"

    // If a slider was added, initialze and attach listener
    if (slider) {
        // Initialize
        $('#' + `${target}-rule${row}`).rangeslider({
            polyfill: false,
            onInit: function() {
            // Select handle element closest to slider, update displayed rule
            $handle = $('.rangeslider__handle', this.$range);
            $handle[0].textContent = get_display_value(document.getElementById(`${target}-rule${row}`));

            this.$range[0].classList.add("mx-auto")
            }
        });

        // Update current rule displayed while slider moves
        $('#' + `${target}-rule${row}`).on('input', function(e) {

            // Select handle element closest to slider, update displayed rule
            var $handle = $('.rangeslider__handle', e.target.nextSibling);
            $handle[0].textContent = get_display_value(document.getElementById(e.target.id));
        });
    };
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
    const timestamp = document.getElementById(`${target}-rule${num}-time`);

    // Get rule input
    const rule = document.getElementById(`${target}-rule${num}`);

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

        // Slider input requires jquery listener to cover all scenarios
        if (rule.type == 'range') {
            $('#' + rule.id).on('change', async function(e) {
                schedule_rule_field_handler(e);
            });
        // All others inputs use vanilla listener
        } else {
            rule.addEventListener("input", schedule_rule_field_handler);
        };

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
    const timestamp = document.getElementById(`${target}-rule${rule}-time`).dataset.original;

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
                                <td><input type="time" class="form-control" id="${target}-rule1-time" placeholder="HH:MM" name="${target}-rule1-time"></td>
                                <td><input type="text" class="form-control" id="${target}-rule1" placeholder="" name="${target}-rule1"></td>
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
