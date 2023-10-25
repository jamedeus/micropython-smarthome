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
}


class Device extends Instance {
    getParams() {
        super.getParams();

        // Int default_rule required by some device types
        if (["dimmer", "bulb", "pwm", "wled"].includes(this.output._type)) {
            this.output.default_rule = parseInt(this.output.default_rule);
        };
    };
};


class Sensor extends Instance {
    getParams() {
        super.getParams();

        // Float default_rule required by some sensor types
        if (["pir", "si7021"].includes(this.output._type)) {
            this.output.default_rule = parseFloat(this.output.default_rule);
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
