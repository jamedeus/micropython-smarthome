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
    };

    // Remove all properties except id, called when user changes type dropdown
    clearParams() {
        Object.keys(this).forEach(function(key) {
            if (key != "id" && key != "modified" && key != "new") {
                delete this[key];
            };
        }, this);
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
};
