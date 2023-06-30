class Device {
    constructor(id) {
        this.id = id;

        // Track if page2 + page3 cards need to be created
        this.new = true;

        // Track if page2 + page3 contents need to be updated
        this.modified = false;

        // Track if page2 + page3 titles need to be updated (without removing targets/rules)
        this.name_changed = false;

        this.nickname = "";

        this.getParams();
    };

    // Update all parameters, called before sending to backend
    update() {
        this.clearParams();
        this.getParams();
        this.getScheduleRules();
    };

    // Create property for each field in addDevice section
    getParams() {
        this._type = document.getElementById(`${this.id.replace("device", "deviceType")}`).value;

        const params = document.getElementById(`add${this.id.replace("device", "DeviceOptions")}`).querySelectorAll('input, select');

        for (let input of params) {
            // Get name that will be used in config.json, create property
            try {
                const name = input.id.split("-")[1];
                this[name] = input.value;
            } catch(err) {};
        };

        if (this._type == "ir-blaster") {
            // Remove empty property (checkbox inputs don't have value)
            delete this.tv;
            delete this.ac;
            // Get checkbox inputs selections
            this.getIrTargets();
        } else if (this._type == "dimmer" || this._type == "bulb" || this._type == "pwm" || this._type == "wled") {
            this['default_rule'] = parseInt(document.getElementById(this.id + "-default_rule").value);
        };
    };

    // Remove all properties except id, called when user changes type dropdown
    clearParams() {
        Object.keys(this).forEach(function(key) {
            if (key != "id" && key != "modified" && key != "new" && key != "nickname") {
                delete this[key];
            };
        }, this);
    };

    // Build object containing all schedule rule time:value pairs
    getScheduleRules() {
        var timestamps = document.getElementsByClassName(`time ${this.id}`);
        var rules = document.getElementsByClassName(`rule ${this.id}`);

        this.schedule = {};

        for (let i=0; i < rules.length; i++) {
            // Don't add if either field is empty
            if (timestamps[i].dataset.original.length > 0 && rules[i].dataset.original.length > 0) {
                this.schedule[timestamps[i].dataset.original] = rules[i].dataset.original;
            };
        };
    };

    // Get array containing all selected virtual IR remotes (first page)
    getIrTargets() {
        if (this._type != "ir-blaster") { return };

        var checks = document.getElementsByClassName('ir-target');

        this.target = [];

        for (let i=0; i < checks.length; i++) {
            if (checks[i].checked) {
                this.target.push(checks[i].value.split("-")[1]);
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

        this.getParams();
    };

    // Update all parameters, called before sending to backend
    update() {
        this.clearParams();
        this.getParams();
        this.getTargets();
        this.getScheduleRules();
    };

    // Create property for each field in addDevice section
    getParams() {
        this._type = document.getElementById(`${this.id.replace("sensor", "sensorType")}`).value;

        var params = document.getElementById(`add${this.id.replace("sensor", "SensorOptions")}`).children;

        for (let input of params) {
            // Get name that will be used in config.json, create property
            const name = input.children[1].id.split("-")[1];
            this[name] = input.children[1].value;
        };

        if (this._type == "pir" || this._type == "si7021") {
            this['default_rule'] = parseFloat(document.getElementById(this.id + "-default_rule").value);
        };
    };

    // Remove all properties except id, called when user changes type dropdown
    clearParams() {
        Object.keys(this).forEach(function(key) {
            if (key != "id" && key != "modified" && key != "new") {
                delete this[key];
            };
        }, this);
    };

    // Build object containing all schedule rule time:value pairs
    getScheduleRules() {
        var timestamps = document.getElementsByClassName(`time ${this.id}`);
        var rules = document.getElementsByClassName(`rule ${this.id}`);

        this.schedule = {};

        for (let i=0; i < rules.length; i++) {
            // Don't add if either field is empty
            if (timestamps[i].dataset.original.length > 0 && rules[i].dataset.original.length > 0) {
                this.schedule[timestamps[i].dataset.original] = rules[i].dataset.original;
            };
        };
    };

    // Get array containing all selected target options
    getTargets() {
        var checks = document.getElementsByClassName(`target ${this.id}`);

        this.targets = [];

        for (let i=0; i < checks.length; i++) {
            if (checks[i].checked) {
                this.targets.push(checks[i].value.split("-")[2]);
            };
        };
    };
};



// Called when nickname fields change, causes name shown on pages 2-3 to update
function update_nickname(el) {
    const id = el.id.split("-")[0];

    if (id.startsWith("device")) {
        instances['devices'][id]['nickname'] = el.value;
        instances['devices'][id]['name_changed'] = true;
    } else {
        instances['sensors'][id]['nickname'] = el.value;
        instances['sensors'][id]['name_changed'] = true;
    };
};
