// Parent class for both Device and Sensor
class Instance {
    constructor(id) {
        // device1, sensor3, etc
        this.id = id;

        // Track if page2 + page3 cards need to be created
        this.new = true;

        // Track if page2 + page3 contents need to be updated
        this.modified = false;

        // Track if page2 + page3 titles need to be updated (without removing targets/rules)
        this.name_changed = false;

        // Final config object sent to backend
        this.output = {};

        // Read user selection from inputs
        this.getParams();
    };

    // Update all parameters, called before sending to backend
    update() {
        this.getParams();
        this.getScheduleRules();
    };

    // Create JSON config object from user-selected parameters
    getParams() {
        // Clear old output parameters
        this.output = {};

        // Get type from dropdown
        this.output._type = document.querySelector(`.${this.id} .instanceType`).value;

        // Get array of other parameters, add to output object
        const params = document.querySelector(`.${this.id} .configParams`).querySelectorAll('input, select');
        for (let input of params) {
            // Get name that will be used in config.json, create property
            try {
                const name = input.id.split("-")[1];
                this.output[name] = input.value;
            } catch(err) {};
        };
    };

    // Add schedule rule time:value pairs to all instances in output JSON config
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
}


class Device extends Instance {
    getParams() {
        super.getParams();

        // Populate IrBlaster target list from checkbox inputs
        if (this.output._type == "ir-blaster") {
            delete this.output.tv;
            delete this.output.ac;
            this.getIrTargets();

        // Int default_rule required by some device types
        } else if (["dimmer", "bulb", "pwm", "wled"].includes(this.output._type)) {
            this.output.default_rule = parseInt(this.output.default_rule);
        };
    };

    getScheduleRules() {
        // IR Blaster does not support schedule rules
        if (this.output._type != "ir-blaster") {
            super.getScheduleRules()
        };
    };

    // Populate target parameter in output JSON config with list of IR targets
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


class Sensor extends Instance {
    update() {
        super.update();
        this.getTargets();
    };

    getParams() {
        super.getParams();

        // Float default_rule required by some sensor types
        if (["pir", "si7021"].includes(this.output._type)) {
            this.output.default_rule = parseFloat(this.output.default_rule);
        };
    };

    // Populate target parameter in output JSON config with list of device IDs
    getTargets() {
        // Get array of target check boxes
        var checks = document.getElementsByClassName(`target ${this.id}`);

        // Add ID of all checked targets to list in config object
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
