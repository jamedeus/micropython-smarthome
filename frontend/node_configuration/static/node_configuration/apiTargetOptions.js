function switch_page(el) {
    if (el.id == "on-button") {
        document.getElementById("on-action").style.display = "initial";
        document.getElementById("off-action").style.display = "none";
    } else {
        document.getElementById("on-action").style.display = "none";
        document.getElementById("off-action").style.display = "initial";
    };
};

function submit_api_rule(el) {
    var value = Object.fromEntries(new FormData(document.getElementById("api_rule_form")).entries());
    // Remove friendly name, leave only instance id (device1, sensor1, etc)
    value["instance-on"] = value["instance-on"].split("-")[0]
    value["instance-off"] = value["instance-off"].split("-")[0]
    document.getElementById(el.dataset.target).value = JSON.stringify(value);
    var event = new Event('change');
    document.getElementById(el.dataset.target).dispatchEvent(event);
};


function api_target_selected(el) {
    if (el.value) {
        document.getElementById(el.id.split("-")[0] + "-set-rule").disabled = false;
        // Clear old rule so menu doesn't populate when opened
        document.getElementById(el.id.split("-")[0] + "-default_rule").value = "";
    } else {
        document.getElementById(el.id.split("-")[0] + "-set-rule").disabled = true;
    };
}


// Modal fields
var instance_select_on = document.getElementById("instance-on");
var instance_select_off = document.getElementById("instance-off");
var command_select_on = document.getElementById("command-on");
var command_select_off = document.getElementById("command-off");
var sub_command_select_on = document.getElementById("sub-command-on");
var sub_command_select_off = document.getElementById("sub-command-off");
var command_arg_on = document.getElementById("command-arg-on");
var command_arg_off = document.getElementById("command-arg-off");

function populate_command_on(target) {
    // Hide fields that are only used by certain commands
    command_arg_on.disabled = true;
    command_arg_on.style.display = "none";
    sub_command_select_on.disabled = true;
    sub_command_select_on.style.display = "none";

    // empty command dropdown
    command_select_on.length = 1;

    var selected = instance_select_on.value;

    var y = ApiTargetOptions[target][selected];

    // Populate command dropdown
    if (y instanceof Array) {
        for (var i = 0; i < y.length; i++) {
            command_select_on.options[command_select_on.options.length] = new Option(y[i], y[i]);
        }

        sub_command_select_on.disabled = true;
        sub_command_select_on.style.display = "none";

    } else if (y instanceof Object) {
        sub_command_select_on.disabled = false;
        sub_command_select_on.style.display = "initial";

        for (opt in y) {
            command_select_on.options[command_select_on.options.length] = new Option(opt, opt);
        };
    };
}

function populate_command_off(target) {
    // Hide fields that are only used by certain commands
    command_arg_off.disabled = true;
    command_arg_off.style.display = "none";
    sub_command_select_off.disabled = true;
    sub_command_select_off.style.display = "none";

    // empty command dropdown
    command_select_off.length = 1;

    var selected = instance_select_off.value;

    var y = ApiTargetOptions[target][selected];

    // Populate command dropdown
    if (y instanceof Array) {
        for (var i = 0; i < y.length; i++) {
            command_select_off.options[command_select_off.options.length] = new Option(y[i], y[i]);
        }

        sub_command_select_off.disabled = true;
        sub_command_select_off.style.display = "none";

    } else if (y instanceof Object) {
        sub_command_select_off.disabled = false;
        sub_command_select_off.style.display = "initial";

        for (opt in y) {
            command_select_off.options[command_select_off.options.length] = new Option(opt, opt);
        };
    };
}


function populate_sub_command_on(target) {
    var selected = command_select_on.value;

    if (["enable_in", "disable_in", "set_rule"].includes(selected)) {
        command_arg_on.disabled = false;
        command_arg_on.style.display = "initial";
    } else {
        command_arg_on.disabled = true;
        command_arg_on.style.display = "none";
    };

    // Only run if sub-command dropdown is visible (shown when certain commands selected above)
    if (sub_command_select_on.disabled) {return};

    // empty sub-command dropdown
    sub_command_select_on.length = 1;

    var z = ApiTargetOptions[target][instance_select_on.value][selected];

    // Populate sub-command options
    for (var i = 0; i < z.length; i++) {
        sub_command_select_on.options[sub_command_select_on.options.length] = new Option(z[i], z[i]);
    }
}

function populate_sub_command_off(target) {
    var selected = command_select_off.value;

    if (["enable_in", "disable_in", "set_rule"].includes(selected)) {
        command_arg_off.disabled = false;
        command_arg_off.style.display = "initial";
    } else {
        command_arg_off.disabled = true;
        command_arg_off.style.display = "none";
    };

    // Only run if sub-command dropdown is visible (shown when certain commands selected above)
    if (sub_command_select_off.disabled) {return};

    // empty sub-command dropdown
    sub_command_select_off.length = 1;

    console.log()
    console.log(target)
    console.log(instance_select_off.value)
    console.log(selected)
    console.log()

    var z = ApiTargetOptions[target][instance_select_off.value][selected];

    //display correct values
    for (var i = 0; i < z.length; i++) {
        sub_command_select_off.options[sub_command_select_off.options.length] = new Option(z[i], z[i]);
    }
}

function open_rule_modal(el) {
    $('#api-rule-modal').modal('show')

    if (el.id.endsWith("set_rule")) {
        // Frontend (change rule option in device dropdown)
        document.getElementById('submit-api-rule').dataset.target = el.id.split("-")[0] + "-rule";
        var target = el.id.split("-")[0];

    } else if (el.id.endsWith("button")) {
        // Frontend schedule rules section
        document.getElementById('submit-api-rule').dataset.target = el.id.replace("button", "value");
        var target = el.id.split("-")[1];

    } else if (el.id.startsWith("device")) {
        // Provisioning default rule (configure page 1)
        document.getElementById('submit-api-rule').dataset.target = el.id.split("-")[0] + "-default_rule";
        var target = document.getElementById(el.id.split("-")[0] + "-ip").value;

    } else {
        // Provisioning schedule rules (configure page 3)
        document.getElementById('submit-api-rule').dataset.target = el.id.replace("button", "value");
        var target = document.getElementById(el.id.split("-")[1] + "-ip").value;
    };

    // Clear all options from last time menu was opened
    instance_select_on.length = 1;
    instance_select_off.length = 1;
    command_select_on.length = 1;
    command_select_off.length = 1;
    sub_command_select_on.length = 1;
    sub_command_select_off.length = 1;
    command_arg_on.value = "";
    command_arg_off.value = "";

    // Show on tab, hide off tab
    document.getElementById("on-button").checked = true;
    document.getElementById("on-action").style.display = "initial";
    document.getElementById("off-action").style.display = "none";

    // Hide fields that are only used by certain commands
    command_arg_on.disabled = true;
    command_arg_on.style.display = "none";
    sub_command_select_on.disabled = true;
    sub_command_select_on.style.display = "none";

    command_arg_off.disabled = true;
    command_arg_off.style.display = "none";
    sub_command_select_off.disabled = true;
    sub_command_select_off.style.display = "none";

    // Populate instance dropdown
    for (var x in ApiTargetOptions[target]) {
        instance_select_on.options[instance_select_on.options.length] = new Option(x.split("-")[1], x);
        instance_select_off.options[instance_select_off.options.length] = new Option(x.split("-")[1], x);
    };

    // Attach listeners to populate next dropdown after each selection
    instance_select_on.onchange = function() {populate_command_on(target)};
    instance_select_off.onchange = function() {populate_command_off(target)};
    command_select_on.onchange = function() {populate_sub_command_on(target)};
    command_select_off.onchange = function() {populate_sub_command_off(target)};

    // Load existing rule (if present) into dropdowns
    try {
        if (el.id.startsWith("device")) {
            var restore = JSON.parse(document.getElementById(el.id.split("-")[0] + "-default_rule").value);
        } else {
            var restore = JSON.parse(document.getElementById(el.id.replace("button", "value")).value);
        }
        console.log(restore)
    } catch(err) {
        // Skip if no rule set
        console.log("No existing rule")
        return
    };

    // Re-populate dropdowns from existing rule
    Array.from(instance_select_on.options).forEach( function(option) {
        if (option.value.split("-")[0] == restore["instance-on"]) {
            option.selected = true;
            populate_command_on(target);
        }
    });

    Array.from(instance_select_off.options).forEach( function(option) {
        if (option.value.split("-")[0] == restore["instance-off"]) {
            option.selected = true;
            populate_command_off(target);
        }
    });

    Array.from(command_select_on.options).forEach( function(option) {
        if (option.value == restore["command-on"]) {
            option.selected = true;
            populate_sub_command_on(target);
        }
    });

    Array.from(command_select_off.options).forEach( function(option) {
        if (option.value == restore["command-off"]) {
            option.selected = true;
            populate_sub_command_off(target);
        }
    });

    Array.from(sub_command_select_on.options).forEach( function(option) {
        if (option.value == restore["sub-command-on"]) {
            option.selected = true;
        }
    });

    Array.from(sub_command_select_off.options).forEach( function(option) {
        if (option.value == restore["sub-command-off"]) {
            option.selected = true;
        }
    });

    if (restore["command-arg-on"]) {
        command_arg_on.value = restore["command-arg-on"];
    };

    if (restore["command-arg-off"]) {
        command_arg_off.value = restore["command-arg-off"];
    };
};

function convert_api_target_rule(input) {
    var output = {'on': [], 'off': []};

    // Convert to correct format
    if (input['instance-on'] == 'ir_blaster') {
        output['on'].push('ir_key');
        output['on'].push(input['command-on']);
        output['on'].push(input['sub-command-on']);
    } else {
        output['on'].push(input['command-on']);
        output['on'].push(input['instance-on']);

        if (input['command-arg-on']) {
            output['on'].push(input['command-arg-on']);
        };
    };

    if (input['instance-off'] == 'ir_blaster') {
        output['off'].push('ir_key');
        output['off'].push(input['command-off']);
        output['off'].push(input['sub-command-off']);
    } else {
        output['off'].push(input['command-off']);
        output['off'].push(input['instance-off']);

        if (input['command-arg-off']) {
            output['off'].push(input['command-arg-off']);
        };
    };

    return JSON.stringify(output);
};

// Handler for change rule option in Api frontend
async function change_api_target_rule(el) {
    console.log("Changing rule");

    const target = el.id.split("-")[0];

    var rule = JSON.parse(document.getElementById(`${target}-rule`).value);
    console.log("Old:");
    console.log(rule);
    rule = convert_api_target_rule(rule);
    console.log("New:");
    console.log(rule);

    var result = await send_command({'command': 'set_rule', 'instance': target, 'rule': rule});
    result = await result.json();

    if (JSON.stringify(result).startsWith('{"ERROR')) {
        console.log(JSON.stringify(result));
    };
};

function add_rule_api(el) {
    // Get target device/sensor
    const target = el.id.split("-")[0];

    // Get rule number
    const num = el.id.split("add")[1];

    // Get old rule
    var old_rule = JSON.parse(document.getElementById(`schedule-${target}-rule${num}-value`).value);

    // Convert, overwrite field value
    var new_rule = convert_api_target_rule(old_rule);
    document.getElementById(`schedule-${target}-rule${num}-value`).value = new_rule;

    // Call function to add rule (reads from field set above)
    add_rule(el);

    // Revert field value (used to re-populate dropdowns if user edits rule again)
    document.getElementById(`schedule-${target}-rule${num}-value`).value = old_rule;
};
