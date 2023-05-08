// Handler for add button in schedule rules dropdown, used to create new rules and edit existing
async function add_rule() {
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

    // New rule added
    if (original_timestamp == '') {
        // Add to schedule rules table
        add_new_row(target, timestamp, rule, type);

    // Modified existing rule
    } else if (original_timestamp != timestamp) {
        // Modify rule in rule field
        const num = delete_button.dataset.number;
        document.getElementById(`${target}-rule${num}`).dataset.original = rule;
        document.getElementById(`${target}-rule${num}`).innerHTML = rule;
        document.getElementById(`${target}-rule${num}-time`).dataset.original = timestamp;
        document.getElementById(`${target}-rule${num}-time`).innerHTML = timestamp;
    };

    // Hide modal
    ruleModal.hide();
};


// Handler for delete button in schedule rules dropdown, removes row after deleting rule
async function delete_rule() {
    // Get target device/sensor and rule index
    const target = delete_button.dataset.target;
    const rule = delete_button.dataset.number;

    // Delete row from schedule rules table
    document.getElementById(`${target}-row-${rule}`).remove();

    // Hide schedule rules table if last rule deleted
    if (document.getElementById(target + "-rules").rows.length == 1) {
        document.getElementById(target + "-rules").classList.add('d-none');
    };

    // Hide modal
    ruleModal.hide();
};
