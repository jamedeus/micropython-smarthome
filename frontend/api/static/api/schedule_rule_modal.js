// Constants for modal buttons
const delete_button = document.getElementById('del-rule');
const add_button = document.getElementById('add-rule');

// Used to identify HH:MM timestamp
const timestamp_regex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;


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
    const type = el.dataset.type;

    // Add dataset attributes, used by add_rule function
    add_button.dataset.target = target;
    add_button.dataset.type = type;

    // Add dataset attributes, used by delete_rule function
    delete_button.dataset.target = target;
    delete_button.dataset.number = num;
    delete_button.classList.remove('d-none')

    const payload = {
        'timestamp': timestamp,
        'rule': rule,
        'type': type,
        'target': target
    };
    open_schedule_rule_modal(payload);
};


// Called by + button under schedule rules
// Opens modal with delete button hidden, blank attributes (new rule)
function add_new_rule(el) {
    // Get target device/sensor
    const target = el.id.split("-")[0];
    const type = el.dataset.type;

    // Add dataset attributes to add button
    add_button.dataset.target = target;
    add_button.dataset.type = type;

    // Hide delete button (adding new rule)
    delete_button.classList.add('d-none')

    const payload = {
        'timestamp': '',
        'rule': '',
        'type': type,
        'target': target
    };
    open_schedule_rule_modal(payload);
};


// Takes target ID, new rule timestamp, new rule
// Adds new row to schedule rules table with params
function add_new_row(target, timestamp, rule, type) {
    // Get schedule rules table for target instance
    const table = document.getElementById(target + "-rules");

    // If adding first rule: unhide table, set row to 1
    if (table.rows.length == 1) {
        table.classList.remove('d-none');
        var row = 1;

    } else {
        // Get index for new row by parsing ID from last row and incrementing
        // Cannot use length, results in duplicate IDs if rows above were deleted before adding
        var row = parseInt(table.rows[table.rows.length-1].id.split("-")[2]) + 1;
    };

    // Populate template with received parameters
    // NOTE: Inconsistent quotes on data-original are important, attribute may contain
    // string representation of dict containing double quotes, breaks if double quoted
    var template = `<tr id="${target}-row-${row}">
    <td><span class="form-control schedule-rule time ${target}" id="${target}-rule${row}-time" data-original="${timestamp}" data-type="${type}" onclick="edit_existing_rule(this);">${format12h(timestamp)}</span></td>
    <td><span class="form-control schedule-rule rule ${target}" id="${target}-rule${row}" data-original='${rule}' data-type="${type}" onclick="edit_existing_rule(this);">${rule}</span></td>
    <td class="min"><button type="button" class="btn btn-sm btn-primary mt-1" id="${target}-edit${row}" data-type="${type}" onclick="edit_existing_rule(this);"><i class="bi-pencil"></i></button></td>
    </tr>`

    // Add row to bottom of table
    table.insertAdjacentHTML('beforeend', template);

    // Change text for api-target
    if (type === "api-target") {
        document.getElementById(`${target}-rule${row}`).innerHTML = "click to view";
    };
};


// Takes 24h timestamp, returns 12h with am/pm suffix
function format12h(timestamp) {
    // Return keywords unchanged
    if ( ! timestamp_regex.test(timestamp)) {
        return timestamp;
    };

    let [hour, minute] = timestamp.split(':');
    const suffix = parseInt(hour) >= 12 ? 'pm' : 'am';
    // Convert to 12h format, if midnight replace 0 with 12
    hour = parseInt(hour) % 12;
    hour = hour === 0 ? 12 : hour;
    return `${hour}:${minute} ${suffix}`;
};
