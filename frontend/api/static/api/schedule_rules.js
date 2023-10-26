// Initialize toast, allows user to write new/deleted rules to disk
const save_rules_toast = new bootstrap.Toast(document.getElementById("save_rules_toast"));


// Replace 24h timestamps from template with 12h, skip keywords (sunrise etc)
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.schedule-rule.time').forEach(rule => {
        if (timestamp_regex.test(rule.dataset.original)) {
            rule.innerHTML = format12h(rule.dataset.original);
        };
    });
});


// Handler for schedule rules button on each card, opens collapse
function open_rules(button) {
    // Scroll opened card into view
    const id = button.id.split("-")[0];
    document.getElementById(`${id}-card`).scrollIntoView({behavior: 'smooth'});
};


// Handler for add button in schedule rules dropdown, used to create new rules and edit existing
async function add_rule() {
    // Start loading animation
    loading_animation();

    // Get target device/sensor + type
    const target = add_button.dataset.target;
    const type = add_button.dataset.type;

    // Get timestamp or time keyword depending on toggle position
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
            add_new_row(target, timestamp, rule, type);

        // Modified existing rules timestamp
        } else if (original_timestamp != timestamp) {
            // Delete rule with old timestamp
            await delete_rule();

            // Add new rule to schedule rules table
            add_new_row(target, timestamp, rule, type);

        // Modified existing rule without changing timestamp
        } else if (original_timestamp === timestamp) {
            // Modify rule in rule field
            const num = delete_button.dataset.number;
            document.getElementById(`${target}-rule${num}`).dataset.original = rule;
            // Add rule to innerHTML for all instances except api-target
            if (type != "api-target") {
                document.getElementById(`${target}-rule${num}`).innerHTML = rule;
            };
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


// Handler for yes button in save rules toast, gets updated config from node and saves in database
async function sync_schedule_rules() {
    var result = await fetch('/sync_schedule_rules', {
        method: 'POST',
        body: JSON.stringify({"ip": target_node}),
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            "X-CSRFToken": getCookie('csrftoken')
        }
    });
    result = await result.json();
    console.log(result);
};
