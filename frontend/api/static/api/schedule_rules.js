// Constants for modal buttons
const delete_button = document.getElementById('del-rule');
const add_button = document.getElementById('add-rule');

// Initialize toast, allows user to write new/deleted rules to disk
const save_rules_toast = new bootstrap.Toast(document.getElementById("save_rules_toast"));

// Replace 24h timestamps from template with 12h
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.schedule-rule.time').forEach(rule => {
        rule.innerHTML = format12h(rule.dataset.original);
    });
});


// Handler for schedule rules button on each card, opens collapse
function open_rules(button) {
    // Scroll opened card into view
    const id = button.id.split("-")[0];
    document.getElementById(`${id}-card`).scrollIntoView({behavior: 'smooth'});
};


// Takes element and text, creates bootstrap tooltip on element (dismissed on focus/hover)
// If text is blank the element's title attribute is used
function show_tooltip(element, text=null) {
    // Show tooltip on field with invalid param
    const tooltipConfig = text ? { title: text } : { title: element.getAttribute('title') };
    const tooltip = new bootstrap.Tooltip(element, tooltipConfig);
    tooltip.show();

    // Dismiss on hover or focus
    function dismiss_tooltip() {
        tooltip.dispose();
        element.removeEventListener('focus', dismiss_tooltip);
        element.removeEventListener('mouseover', dismiss_tooltip);
    };
    element.addEventListener('focus', dismiss_tooltip, { once: true });
    element.addEventListener('mouseover', dismiss_tooltip, { once: true });
};


// Replace modal buttons with loading animation, prevent user submitting multiple times
function loading_animation(start=true) {
    if (start) {
        document.getElementById('rule-loading').classList.remove('d-none');
        document.getElementById('rule-buttons').classList.add('d-none');
    } else {
        document.getElementById('rule-loading').classList.add('d-none');
        document.getElementById('rule-buttons').classList.remove('d-none');
    };
};


// Handler for toggle under timestamp field in rule modal
function toggle_time_mode(event) {
    if (event.target.checked) {
        document.getElementById('timestamp-input').classList.add('d-none');
        document.getElementById('keyword-input').classList.remove('d-none');
    } else {
        document.getElementById('timestamp-input').classList.remove('d-none');
        document.getElementById('keyword-input').classList.add('d-none');
    };
};


// Handler for toggle under rule field in rule modal
function toggle_fade_mode(event) {
    if (event.target.checked) {
        document.getElementById('duration-input').classList.remove('d-none');
    } else {
        document.getElementById('duration-input').classList.add('d-none');
    };
};


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
};


// Takes object containing rule parameters, loads rule_modal template, shows modal
async function open_schedule_rule_modal(payload) {
    console.log(payload);

    // Fetch template, show modal
    var result = await fetch('/edit_rule', {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: { 'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') }
    });

    // Load response into modal body
    document.getElementById('rule-modal-body').innerHTML = await result.text();
    ruleModal.show();

    // Focus time field
    await sleep(468);
    document.getElementById(`timestamp`).focus();

    // Press enter to submit
    document.getElementById('schedule-rule-modal').querySelectorAll('input').forEach(input => {
        input.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                add_rule();
            };
        });
    });
};


// Called by edit button next to schedule rule
// Opens modal with delete button + data attributes for selected rule
function edit_existing_rule(el) {
    // Get target device/sensor, rule number
    let [target, num] = el.id.split("-");
    num = num.replace(/[a-zA-Z]/g, '');

    // Get timestamp, rule, instance type
    const timestamp = document.getElementById(`${target}-rule${num}-time`).dataset.original;
    const rule = document.getElementById(`${target}-rule${num}`).dataset.original;
    const type = target_node_status[`${target.replace(/[0-9]/g, '')}s`][target]['type'];

    // Add dataset attributes, used by add_rule function
    add_button.dataset.target = target;
    add_button.dataset.type = type;

    // Add dataset attributes, used by delete_rule function
    delete_button.dataset.target = target;
    delete_button.dataset.number = num;
    delete_button.classList.remove('d-none')

    const payload = {'timestamp': timestamp, 'rule': rule, 'type': type};
    open_schedule_rule_modal(payload);
};


// Called by + button under schedule rules
// Opens modal with delete button hidden, blank attributes (new rule)
function add_new_rule(el) {
    // Get target device/sensor
    const target = el.id.split("-")[0];

    // Get instance type
    if (target.startsWith('sensor')) {
        var type = target_node_status['sensors'][target]['type'];
    } else {
        var type = target_node_status['devices'][target]['type'];
    };

    // Add dataset attributes to add button
    add_button.dataset.target = target;
    add_button.dataset.type = type;

    // Hide delete button (adding new rule)
    delete_button.classList.add('d-none')

    const payload = {'timestamp': '', 'rule': '', 'type': type};
    open_schedule_rule_modal(payload);
};


// Takes target ID, new rule timestamp, new rule
// Adds new row to schedule rules table with params
function add_new_row(target, timestamp, rule) {
    // Get schedule rules table for target instance
    const table = document.getElementById(target + "-rules");

    // If adding first rule: unhide table
    if (table.rows.length == 1) {
        table.classList.remove('d-none');
    };

    // Get index for new row by parsing ID from last row and incrementing
    // Cannot use length, results in duplicate IDs if rows above were deleted before adding
    const row = parseInt(table.rows[table.rows.length-1].id.split("-")[2]) + 1

    // Populate template with received parameters
    var template = `<tr id="${target}-row-${row}">
    <td><span class="form-control schedule-rule time" id="${target}-rule${row}-time" data-original="${timestamp}" onclick="edit_existing_rule(this);">${format12h(timestamp)}</span></td>
    <td><span class="form-control schedule-rule" id="${target}-rule${row}" data-original="${rule}" onclick="edit_existing_rule(this);">${rule}</span></td>
    <td class="min"><button type="button" class="btn btn-sm btn-primary mt-1" id="${target}-edit${row}" onclick="edit_existing_rule(this);"><i class="bi-pencil"></i></button></td>
    </tr>`

    // Add row to bottom of table
    table.insertAdjacentHTML('beforeend', template);
};


// Takes 24h timestamp, returns 12h with am/pm suffix
function format12h(timestamp) {
    let [hour, minute] = timestamp.split(':');
    const suffix = parseInt(hour) >= 12 ? 'pm' : 'am';
    // Convert to 12h format, if midnight replace 0 with 12
    hour = parseInt(hour) % 12;
    hour = hour === 0 ? 12 : hour;
    return `${hour}:${minute} ${suffix}`;
};


// Handler for add button in schedule rules dropdown, used to create new rules and edit existing
async function add_rule() {
    // Start loading animation
    loading_animation();

    // Get target device/sensor + type
    const target = add_button.dataset.target;
    const type = add_button.dataset.type;

    // Get timestamp or time keyword depending on toggle position
    // TODO will break if toggle was changed, set dataset attrs on both?
    if (document.getElementById('toggle-time-mode').checked) {
        var timestamp_el = document.getElementById('keyword');
    } else {
        var timestamp_el = document.getElementById('timestamp');
    };

    const timestamp = timestamp_el.value;
    const original_timestamp = timestamp_el.dataset.original;

    // Get rule (all inputs have same ID, only 1 included in template)
    const rule_field = document.getElementById('rule-input');
    let rule = rule_field.value;

    // If fade rule: convert to correct syntax
    if (['dimmer', 'bulb', 'pwm'].includes(type)) {
        if (document.getElementById('toggle-rule-mode').checked) {
            // TODO handle empty duration field
            const duration = document.getElementById('duration').value;
            rule = `fade/${rule}/${duration}`;
        };
    };

    // Do not add incomplete rule
    if (timestamp.length == 0) {
        show_tooltip(timestamp_el, "Required field");
        add_button.disabled = false;
        return;
    } else if (rule.length == 0) {
        show_tooltip(rule_field, "Required field");
        add_button.disabled = false;
        return;
    };

    // Prevent other functions modifying status object until finished adding rule
    // Otherwise changes below can be overwritten if this runs between receiving new status and overwriting old
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
        show_tooltip(timestamp_el);

    } else if (JSON.stringify(result) == '{"ERROR":"Invalid rule"}') {
        // Show tooltip on field with invalid param
        show_tooltip(rule_field);

    } else if (JSON.stringify(result).startsWith('{"ERROR')) {
        // All other errors (unable to connect etc.)
        alert(JSON.stringify(result));

    } else {
        // Add to current status object (prevent duplicate being created when new status object containing this rule is received)
        target_node_status[target.replace(/[0-9]/g, '') + "s"][target]["schedule"][timestamp] = rule;

        // New rule added
        if (original_timestamp == '') {
            // Add to schedule rules table
            add_new_row(target, timestamp, rule);

        // Modified existing rules timestamp
        } else if (original_timestamp != timestamp) {
            // Delete rule with old timestamp
            await delete_rule();

            // Add new rule to schedule rules table
            add_new_row(target, timestamp, rule);

        // Modified existing rule without changing timestamp
        } else if (original_timestamp === timestamp) {
            // Modify rule in rule field
            const num = delete_button.dataset.number;
            document.getElementById(`${target}-rule${num}`).dataset.original = rule;
        };

        // Resume status updates
        status_lock = false;

        // Show toast message, allows user to write change to disk
        save_rules_toast.show();
    };

    // Stop loading animation, hide modal
    ruleModal.hide();
    await sleep(468);
    loading_animation(false);
};


// Handler for delete button in schedule rules dropdown, removes row after deleting rule
async function delete_rule() {
    // Start loading animation
    loading_animation();

    // Get target device/sensor and rule index
    const target = delete_button.dataset.target;
    const rule = delete_button.dataset.number;

    // Get timestamp from schedule rules table
    const timestamp = document.getElementById(`${target}-rule${rule}-time`).dataset.original;

    // Delete rule
    var result = await send_command({'command': 'remove_rule', 'instance': target, 'rule': timestamp});
    result = await result.json();

    if (JSON.stringify(result).startsWith('{"ERROR')) {
        alert(JSON.stringify(result));
    } else {
        // Delete row from schedule rules table
        document.getElementById(`${target}-row-${rule}`).remove();

        // Hide schedule rules table if last rule deleted
        if (document.getElementById(target + "-rules").rows.length == 1) {
            document.getElementById(target + "-rules").classList.add('d-none');
        };

        // Show toast message, allows user to write change to disk
        save_rules_toast.show();
    };

    // Stop loading animation, hide modal
    ruleModal.hide();
    await sleep(468);
    loading_animation(false);
};
