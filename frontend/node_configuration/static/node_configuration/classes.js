class Device {
    constructor(id) {
        this.id = id;

        // Track if page2 + page3 cards need to be created
        this.new = true;

        // Track if page2 + page3 contents need to be updated
        this.modified = false;

        this.getParams();
    };

    // Create property for each field in addDevice section
    getParams() {
        this.type = document.getElementById(`${this.id.replace("device", "deviceType")}`).value;

        var params = document.getElementById(`add${this.id.replace("device", "DeviceOptions")}`).children;

        for (let input of params) {
            // Get name that will be used in config.json, create property
            try {
                const name = input.children[1].name.replace(this.id + "-", "");
                this[name] = input.children[1].value;
            } catch(err) {};
        };

        if (this.type == "ir-blaster") {
            this.getIrTargets();
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
        var timestamps = document.getElementsByClassName(`timestamp ${this.id}`);
        var rules = document.getElementsByClassName(`rule ${this.id}`);

        this.schedule = {};

        for (let i=0; i < rules.length; i++) {
            // Don't add if either field is empty
            if (timestamps[i].value.length > 0 && rules[i].value.length > 0) {
                this.schedule[timestamps[i].value] = rules[i].value;
            };
        };
    };

    // Get array containing all selected virtual IR remotes (first page)
    getIrTargets() {
        if (this.type != "ir-blaster") { return };

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

        this.getParams();
    };

    // Create property for each field in addDevice section
    getParams() {
        this.type = document.getElementById(`${this.id.replace("sensor", "sensorType")}`).value;

        var params = document.getElementById(`add${this.id.replace("sensor", "SensorOptions")}`).children;

        for (let input of params) {
            // Get name that will be used in config.json, create property
            const name = input.children[1].name.replace(this.id + "-", "");
            this[name] = input.children[1].value;
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
        var timestamps = document.getElementsByClassName(`timestamp ${this.id}`);
        var rules = document.getElementsByClassName(`rule ${this.id}`);

        this.schedule = {};

        for (let i=0; i < rules.length; i++) {
            // Don't add if either field is empty
            if (timestamps[i].value.length > 0 && rules[i].value.length > 0) {
                this.schedule[timestamps[i].value] = rules[i].value;
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
