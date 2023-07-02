class Device {
    constructor(id) {
        this.id = id;

        // Track if page2 + page3 cards need to be created
        this.new = true;

        // Track if page2 + page3 contents need to be updated
        this.modified = false;

        // Track if page2 + page3 titles need to be updated (without removing targets/rules)
        this.name_changed = false;

        this.output = {};

        this.getParams();
    };

    // Update all parameters, called before sending to backend
    update() {
        this.getParams();
        this.getScheduleRules();
    };

    // Create JSON config object from user parameters
    getParams() {
        // Clear old output parameters
        this.output = {};

        this.output._type = document.getElementById(`${this.id.replace("device", "deviceType")}`).value;

        const params = document.querySelector(`.${this.id} .configParams`).querySelectorAll('input, select');

        for (let input of params) {
            // Get name that will be used in config.json, create property
            try {
                const name = input.id.split("-")[1];
                this.output[name] = input.value;
            } catch(err) {};
        };

        if (this.output._type == "ir-blaster") {
            // Remove empty property (checkbox inputs don't have value)
            delete this.output.tv;
            delete this.output.ac;
            // Get checkbox inputs selections
            this.getIrTargets();
        } else if (this.output._type == "dimmer" || this.output._type == "bulb" || this.output._type == "pwm" || this.output._type == "wled") {
            this.output.default_rule = parseInt(document.getElementById(this.id + "-default_rule").value);
        };
    };

    // Build object containing all schedule rule time:value pairs
    getScheduleRules() {
        // IR Blaster does not support schedule rules
        if (this.output._type == "ir-blaster") {
            return;
        };

        var timestamps = document.getElementsByClassName(`time ${this.id}`);
        var rules = document.getElementsByClassName(`rule ${this.id}`);

        this.output.schedule = {};

        for (let i=0; i < rules.length; i++) {
            // Don't add if either field is empty
            if (timestamps[i].dataset.original.length > 0 && rules[i].dataset.original.length > 0) {
                this.output.schedule[timestamps[i].dataset.original] = rules[i].dataset.original;
            };
        };
    };

    // Get array containing all selected virtual IR remotes (first page)
    getIrTargets() {
        if (this.output._type != "ir-blaster") { return };

        var checks = document.getElementsByClassName('ir-target');

        this.output.target = [];

        for (let i=0; i < checks.length; i++) {
            if (checks[i].checked) {
                this.output.target.push(checks[i].value.split("-")[1]);
            };
        };
    };
};



class Sensor {
    constructor(id) {
        this.id = id;

        // Track if page2 + page3 cards need to be created
        this.new = true;

        // Track if page2 + page3 contents need to be updated
        this.modified = false;

        // Track if page2 + page3 titles need to be updated (without removing targets/rules)
        this.name_changed = false;

        this.output = {};

        this.getParams();
    };

    // Update all parameters, called before sending to backend
    update() {
        this.getParams();
        this.getTargets();
        this.getScheduleRules();
    };

    // Create JSON config object from user parameters
    getParams() {
        // Clear old output parameters
        this.output = {};

        this.output._type = document.getElementById(`${this.id.replace("sensor", "sensorType")}`).value;

        const params = document.querySelector(`.${this.id} .configParams`).querySelectorAll('input, select');

        for (let input of params) {
            // Get name that will be used in config.json, create property
            try {
                const name = input.id.split("-")[1];
                this.output[name] = input.value;
            } catch(err) {};
        };

        if (this.output._type == "pir" || this.output._type == "si7021") {
            this.output['default_rule'] = parseFloat(document.getElementById(this.id + "-default_rule").value);
        };
    };

    // Build object containing all schedule rule time:value pairs
    getScheduleRules() {
        var timestamps = document.getElementsByClassName(`time ${this.id}`);
        var rules = document.getElementsByClassName(`rule ${this.id}`);

        this.output.schedule = {};

        for (let i=0; i < rules.length; i++) {
            // Don't add if either field is empty
            if (timestamps[i].dataset.original.length > 0 && rules[i].dataset.original.length > 0) {
                this.output.schedule[timestamps[i].dataset.original] = rules[i].dataset.original;
            };
        };
    };

    // Get array containing all selected target options
    getTargets() {
        var checks = document.getElementsByClassName(`target ${this.id}`);

        this.output.targets = [];

        for (let i=0; i < checks.length; i++) {
            if (checks[i].checked) {
                this.output.targets.push(checks[i].value.split("-")[2]);
            };
        };
    };
};



// Called when nickname fields change, causes name shown on pages 2-3 to update
function update_nickname(el) {
    const id = el.id.split("-")[0];

    if (id.startsWith("device")) {
        instances['devices'][id]['output']['nickname'] = el.value;
        instances['devices'][id]['name_changed'] = true;
    } else {
        instances['sensors'][id]['output']['nickname'] = el.value;
        instances['sensors'][id]['name_changed'] = true;
    };
};
