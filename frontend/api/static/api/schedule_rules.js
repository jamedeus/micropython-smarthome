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



// Handler for add button in schedule rules dropdown, used to create new rules and edit existing
async function add_rule(el) {
    // Disable + add loading animation to submit button
//     document.getElementById('add-rule').innerHTML =
    document.getElementById('add-rule').disabled = true;

    // Get target device/sensor + type
    const target = el.dataset.target;
    const type = el.dataset.type;

    // Get rule number
    const num = el.id.split("add")[1];

    // Get timestamp depending on check mode
    if (document.getElementById('toggle-time-mode').checked) {
        var timestamp = document.getElementById('keyword').value;
        var original_timestamp = document.getElementById('keyword').dataset.original;
        var timestamp_el = document.getElementById('keyword');
    } else {
        var timestamp = document.getElementById('timestamp').value;
        var original_timestamp = document.getElementById('timestamp').dataset.original;
        var timestamp_el = document.getElementById('timestamp');
    };

    console.log(timestamp_el.id)

    // Get rule
    let rule = document.getElementById('rule-input').value;

    // If fade rule: convert to correct syntax
    if (['dimmer', 'bulb', 'pwm'].includes(type)) {
        if (document.getElementById('toggle-rule-mode').checked) {
            const duration = document.getElementById('duration').value;
            rule = `fade/${rule}/${duration}`;
        };
    };

    // Do not add incomplete rule
    if (timestamp.length == 0 || rule.length == 0) {
//         el.disabled = false;
        return;
    };

    // Prevent other functions modifying status object until finished adding rule
    // Otherwise if user clicked add after monitoring function got new status, but before it overwrote old, changes made below may be overwritten
    status_lock = true;

    // If user modified an existing rule without changing timestamp, add overwrite arg
    if (original_timestamp == timestamp) {
        var result = await send_command({'command': 'add_rule', 'instance': target, 'time': timestamp, 'rule': rule, 'overwrite': 'overwrite'});
        result = await result.json();
    } else {
        var result = await send_command({'command': 'add_rule', 'instance': target, 'time': timestamp, 'rule': rule});
        result = await result.json();
    };

    console.log(result);

    if (JSON.stringify(result).startsWith('{"ERROR":"Rule already exists')) {
        // Show tooltip on field with invalid param
        const tooltip = new bootstrap.Tooltip(timestamp_el);
        tooltip.show();

        // Dismiss on hover or focus
        function dismiss_tooltip() {
            tooltip.dispose();
            timestamp_el.removeEventListener('focus', dismiss_tooltip);
            timestamp_el.removeEventListener('mouseover', dismiss_tooltip);
        };
        timestamp_el.addEventListener('focus', dismiss_tooltip, { once: true });
        timestamp_el.addEventListener('mouseover', dismiss_tooltip, { once: true });

    } else if (JSON.stringify(result) == '{"ERROR":"Invalid rule"}') {
        const rule_field = document.getElementById('rule-input');

        // Show tooltip on field with invalid param
        const tooltip = new bootstrap.Tooltip(rule_field);
        tooltip.show();

        // Dismiss on hover or focus
        function dismiss_tooltip() {
            tooltip.dispose();
            rule_field.removeEventListener('focus', dismiss_tooltip);
            rule_field.removeEventListener('mouseover', dismiss_tooltip);
        };
        rule_field.addEventListener('focus', dismiss_tooltip, { once: true });
        rule_field.addEventListener('mouseover', dismiss_tooltip, { once: true });

    } else if (JSON.stringify(result).startsWith('{"ERROR')) {
        // All other errors (unable to connect etc.)
        alert(JSON.stringify(result));

    } else {
        // Add to current status object (prevent duplicate being created when new status object containing this rule is received)
        target_node_status[target.replace(/[0-9]/g, '') + "s"][target]["schedule"][timestamp] = rule;

        // If user modified existing rule's timestamp, delete rule with old timestamp
        if (timestamp_el.dataset.original && timestamp != timestamp_el.dataset.original) {
//             delete_rule(document.getElementById(target + "-remove" + num), false);
            delete_rule(document.getElementById('del-rule'), false);
        };

        // Show rules table if first rule added
        if (document.getElementById(target + "-rules").rows.length == 1) {
            document.getElementById(target + "-rules").classList.remove('d-none');
        };

        // Get new row number
        const table = document.getElementById(target + "-rules");
        const row = parseInt(table.rows[table.rows.length-1].id.split("-")[2]) + 1

        // Add row number + target id + time field to empty row template
        var template = `<tr id="${target}-row-${row}">
                            <td><input type="time" class="form-control" id="${target}-rule${row}-time" placeholder="HH:MM" name="${target}-rule${row}-time" value="${timestamp}" data-original="${timestamp}"></td>
                            <td><input type="text" class="form-control" id="${target}-rule${row}" placeholder="" name="${target}-rule${row}" value="${rule}"></td>
                            <td class="min"><button type="button" class="btn btn-sm btn-primary mt-1" id="${target}-edit${row}"  onclick="edit_rule_with_modal(this);"><i class="bi-pencil"></i></button></td>
                        </tr>`

        // Add new row
        document.getElementById(target + "-rules").insertAdjacentHTML('beforeend', template);

        // Replace original values with new values (used to detect change after adding)
        timestamp_el.dataset.original = timestamp;

        // Allow overwriting
        status_lock = false;

        // Hide modal
        ruleModal.hide();

        // Show toast message, allows user to write change to disk
        save_rules_toast.show();
    };

    // Re-enable add button, change text back
    document.getElementById('add-rule').disabled = false;
    document.getElementById('add-rule').innerHTML = "Submit";
};



// Handler for delete button in schedule rules dropdown
// Removes row from table after deleting rule unless called with remove=false
async function delete_rule(selected, remove=true) {
    // Prevent user submitting multiple times
    selected.disabled = true;

    // Get target device/sensor
    const target = selected.dataset.target;

    // Get rule number
    const rule = selected.dataset.number;

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
    } else if (remove) {
        // Delete row if success
        document.getElementById(`${target}-row-${rule}`).remove();

        // Check if deleted rule was last rule
        if (document.getElementById(target + "-rules").rows.length == 1) {
            document.getElementById(target + "-rules").classList.add('d-none');
        };

        // Show toast message, allows user to write change to disk
        save_rules_toast.show();
    };

    // Re-enable delete button
    selected.disabled = false;
};



// Handler for toggle under timestamp field in modal
function toggle_time_mode(event) {
    if (event.target.checked) {
        document.getElementById('timestamp-input').classList.add('d-none');
        document.getElementById('keyword-input').classList.remove('d-none');
    } else {
        document.getElementById('timestamp-input').classList.remove('d-none');
        document.getElementById('keyword-input').classList.add('d-none');
    };
};



// Handler for toggle under rule field in modal
function toggle_fade_mode(event) {
    if (event.target.checked) {
        document.getElementById('duration-input').classList.remove('d-none');
    } else {
        document.getElementById('duration-input').classList.add('d-none');
    };
};



async function open_schedule_rule_modal(payload) {
    console.log(payload);

    // Fetch template, show modal
    var result = await fetch('/edit_rule', {
        method: 'POST',
        body: JSON.stringify(payload),
                             headers: { 'Accept': 'application/json, text/plain, */*',
                                 'Content-Type': 'application/json',
                             "X-CSRFToken": getCookie('csrftoken') }
    });

    document.getElementById('rule-modal-body').innerHTML = await result.text();
    ruleModal.show();
    // Focus time field
    document.getElementById(`timestamp`).focus();
};



function edit_rule_with_modal(el) {
    // Get target device/sensor, rule number
    const target = el.id.split("-")[0];
    const num = el.id.split("edit")[1];

    // Get timestamp + rule values
    const timestamp = document.getElementById(`${target}-rule${num}-time`).value;
    const rule = document.getElementById(`${target}-rule${num}`).value;

    // Get instance type
    if (target.startsWith('sensor')) {
        var type = target_node_status['sensors'][target]['type'];
    } else {
        var type = target_node_status['devices'][target]['type'];
    };

    // Add dataset attributes to add button
    document.getElementById('add-rule').dataset.target = target;
    document.getElementById('add-rule').dataset.type = type;

    // Add dataset attributes to delete button, show
    document.getElementById('del-rule').dataset.target = target;
    document.getElementById('del-rule').dataset.number = num;
    document.getElementById('del-rule').classList.remove('d-none')

    const payload = {'timestamp': timestamp, 'rule': rule, 'type': type};
    open_schedule_rule_modal(payload);
};



function add_rule_with_modal(el) {
    // Get target device/sensor
    const target = el.id.split("-")[0];

    // Get instance type
    if (target.startsWith('sensor')) {
        var type = target_node_status['sensors'][target]['type'];
    } else {
        var type = target_node_status['devices'][target]['type'];
    };

    // Add dataset attributes to add button
    document.getElementById('add-rule').dataset.target = target;
    document.getElementById('add-rule').dataset.type = type;

    // Hide delete button (adding new rule)
    document.getElementById('del-rule').classList.add('d-none')

    const payload = {'timestamp': '', 'rule': '', 'type': type};
    open_schedule_rule_modal(payload);
};
