// Store class instances created when device/sensor types are selected from dropdown
var instances = {"sensors": {}, "devices": {}}

// Populate instances with existing device + sensor cards (if editing config)
Array.from(document.getElementsByClassName("deviceType")).forEach(function(device) {
    const id = device.id.replace("deviceType", "device");
    instances["devices"][id] = new Device(id);
    instances["devices"][id].new = false;
});

Array.from(document.getElementsByClassName("sensorType")).forEach(function(sensor) {
    const id = sensor.id.replace("sensorType", "sensor");
    instances["sensors"][id] = new Sensor(id);
    instances["sensors"][id].new = false;
});



async function load_sensor_section(select) {
    // Get index of sensor
    const index = parseInt(select.id.replace("sensorType", ""));

    // Get user selection
    const selected = document.getElementById(select.id).value

    // Add nickname section to template, other sections added below as needed
    var template = `<div class="mb-2">
                        <label for="sensor${index}-nickname"><b>Nickname:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-nickname" placeholder="" required>
                    </div>`

    // Get template for sensor type selected by user
    if (selected == "pir" || selected == "switch") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="sensor${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "desktop") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-ip"><b>IP:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-ip" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "dummy") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="sensor${index}-default_rule" placeholder="" required>
                    </div>`
    } else if (selected == "si7021") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="sensor${index}-default_rule" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label class="form-label" for="sensor${index}-mode"><b>Mode:</b></label>
                        <select id="sensor${index}-mode" class="form-select mb-3" required>
                            <option value="cool" id="cool">Cool</option>
                            <option value="heat" id="heat">Heat</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-tolerance"><b>Tolerance:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-tolerance" placeholder="" required>
                    </div>`
    } else {
        // User selected first option ("Select sensor type"), clear form
        template = "";
    };

    // Render div, scroll down until visible
    document.getElementById("addSensorOptions" + index).innerHTML = template;
    document.getElementById("addSensorOptions" + index).scrollIntoView({behavior: "smooth"});

    if (instances["sensors"]["sensor" + index]) {
        // If instance already exists, wipe params and re-populate (type changed)
        instances["sensors"]["sensor" + index].clearParams();
        instances["sensors"]["sensor" + index].getParams();
        instances["sensors"]["sensor" + index].modified = true;
    } else {
        // If new sensor, create instance
        instances["sensors"]["sensor" + index] = new Sensor("sensor" + index);
    };
};



async function load_device_section(select) {
    // Get index of device
    const index = parseInt(select.id.replace("deviceType", ""));

    // Get user selection
    const selected = document.getElementById(select.id).value

    // Add nickname section to template, other sections added below as needed
    var template = `<div class="mb-2">
                        <label for="device${index}-nickname"><b>Nickname:</b></label>
                        <input type="text" class="form-control" id="device${index}-nickname" placeholder="" required>
                    </div>`

    // Get template for device type selected by user
    if (selected == "dimmer" || selected == "bulb" || selected == "desktop" || selected == "relay") {
        template += `<div class="mb-2">
                        <label for="device${index}-ip"><b>IP:</b></label>
                        <input type="text" class="form-control" id="device${index}-ip" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "mosfet" || selected == "dumb-relay") {
        template += `<div class="mb-2">
                        <label for="device${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="device${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "pwm") {
        template += `<div class="mb-2">
                        <label for="device${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="device${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-min"><b>Min brightness:</b></label>
                        <input type="min" class="form-control" id="device${index}-min" placeholder="0" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-max"><b>Max brightness:</b></label>
                        <input type="text" class="form-control" id="device${index}-max" placeholder="1023" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "api-target") {
        template += `<div class="mb-2">
                        <label for="device${index}-ip"><b>Target:</b></label>
                        <select id="device${index}-ip" class="form-select mb-3" onchange="api_target_selected(this)">
                            <option value="" selected="selected" selected></option>`

        for (var x in ApiTargetOptions) {
            template +=    `<option value="${x}">${x.split("-")[1]}</option>`
        };

        template +=     `</select>
                    </div>

                    <div class="mb-2 text-center">
                        <button id="device${index}-set-rule" class="btn btn-secondary mt-3" onclick="open_rule_modal(this);" disabled>Set rule</button>
                    </div>

                    <div class="mb-2 text-center">
                        <label for="device${index}-default_rule" style="display:none;"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" style="display:none;" required>
                    </div>`

    } else if (selected == "ir-blaster") {
        template = `<div class="mb-2">
                        <label for="device${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="device${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-min"><b>Virtual remotes:</b></label>
                        <div class="form-check">
                            <input class="form-check-input ir-target" type="checkbox" value="irblaster-tv" id="checkbox-tv">
                            <label class="form-check-label" for="checkbox-tv">TV (Samsung)</label></br>
                            <input class="form-check-input ir-target" type="checkbox" value="irblaster-ac" id="checkbox-ac">
                            <label class="form-check-label" for="checkbox-ac">AC (Whynter)</label>
                        </div>
                    </div>`

    } else {
        // User selected first option ("Select device type"), clear form
        template = "";
    };

    // Render div, scroll down until visible
    document.getElementById("addDeviceOptions" + index).innerHTML = template;
    document.getElementById("addDeviceOptions" + index).scrollIntoView({behavior: "smooth"});

    // Check if IrBlaster selected in any device dropdown
    devices = document.getElementsByClassName("deviceType");

    var found = false;
    for (device of devices) {
        if (device.value == "ir-blaster") {
            found = true;
        };
    };

    // If IrBlaster selected, disable all IrBlaster options. Otherwise, re-enable all
    if (!found) {
        ir_blaster_configured = false;

        for (device of document.getElementsByClassName("deviceType")) {
            for (option of device.children) {
                if (option.value == "ir-blaster") {
                    option.disabled = false;
                };
            };
        };
    } else {
        ir_blaster_configured = true;

        for (device of document.getElementsByClassName("deviceType")) {
            if (device == select) { continue };
            for (option of device.children) {
                if (option.value == "ir-blaster") {
                    option.disabled = true;
                };
            };
        };
    };

    if (instances["devices"]["device" + index]) {
        // If instance already exists, wipe params and re-populate (type changed)
        instances["devices"]["device" + index].clearParams();
        instances["devices"]["device" + index].getParams();
        instances["devices"]["device" + index].modified = true;
    } else {
        // If new device, create instance
        instances["devices"]["device" + index] = new Device("device" + index);
    };
};



async function load_next_device(button) {
    // Get index of clicked button
    const index = parseInt(button.id.replace("addDeviceButton", ""));

    // Ternary expression adds top margin to all except first card
    var template = `<div ${ index ? 'class="mt-5"' : "" }>
                        <div class="card">
                            <div class="card-body">
                                <h4 class="card-title">device${index + 1}</h4>
                                <label for="deviceType${index + 1}" class="form-label"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_device_section(this)" id="deviceType${index + 1}" class="form-select deviceType" required>
                                    <option value="clear">Select device type</option>
                                    <option value="dimmer">TP-Link Dimmer</option>
                                    <option value="bulb">TP-Link Bulb</option>
                                    <option value="relay">Smart Relay</option>
                                    <option value="dumb-relay">Relay</option>
                                    <option value="desktop">Desktop</option>
                                    <option value="pwm">LED Strip</option>
                                    <option value="mosfet">Mosfet</option>
                                    <option value="api-target">Api Command</option>
                                    <option value="ir-blaster" ${ ir_blaster_configured ? "disabled" : ""}>IR Blaster</option>
                                    </select>
                                </div>

                                <div id="addDeviceOptions${index + 1}" class="card-body"></div>
                            </div>
                        </div>

                        <div class="text-center">
                            <button onclick="load_next_device(this)" type="button" id="addDeviceButton${index + 1}" class="btn-secondary btn my-3">Add another</button>
                        </div>

                        <div id="addDeviceDiv${index + 2}">
                        </div>
                    </div>`

    // Hide clicked button
    document.getElementById("addDeviceButton" + index).style.display = "none";

    // Render div, scroll down until visible
    document.getElementById("addDeviceDiv" + (index + 1)).innerHTML = template;
    document.getElementById("addDeviceDiv" + (index + 1)).scrollIntoView({behavior: "smooth"});
};



async function load_next_sensor(button) {
    // Get index of clicked button
    const index = parseInt(button.id.replace("addSensorButton", ""));

    // Ternary expression adds top margin to all except first card
    var template = `<div ${ index ? 'class="mt-5"' : "" }>
                        <div class="card">
                            <div class="card-body">
                                <h4 class="card-title">sensor${index + 1}</h4>
                                <label for="sensorType${index + 1}" class="form-label"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_sensor_section(this)" id="sensorType${index + 1}" class="form-select sensorType" required>
                                    <option value="clear">Select sensor type</option>
                                    <option value="pir">Motion Sensor</option>
                                    <option value="switch">Switch</option>
                                    <option value="dummy">Dummy</option>
                                    <option value="desktop">Desktop</option>
                                    <option value="si7021">Thermostat</option>
                                    </select>
                                </div>

                                <div id="addSensorOptions${index + 1}" class="card-body"></div>
                            </div>
                        </div>

                        <div class="text-center">
                            <button onclick="load_next_sensor(this)" type="button" id="addSensorButton${index + 1}" class="btn-secondary btn my-3">Add another</button>
                        </div>

                        <div id="addSensorDiv${index + 2}">
                        </div>
                    </div>`

    // Hide clicked button
    document.getElementById("addSensorButton" + index).style.display = "none";

    // Render div, scroll down until visible
    document.getElementById("addSensorDiv" + (index + 1)).innerHTML = template;
    document.getElementById("addSensorDiv" + (index + 1)).scrollIntoView({behavior: "smooth"});
};
