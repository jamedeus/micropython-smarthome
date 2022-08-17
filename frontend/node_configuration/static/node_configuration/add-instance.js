async function load_sensor_section(select) {
    // Get index of sensor
    const index = parseInt(select.id.replace("sensorType", ""));

    // Get user selection
    const selected = document.getElementById(select.id).value

    // Add nickname section to template, other sections added below as needed
    var template = `<div class="mb-2">
                        <label for="sensor${index}-nickname"><b>Nickname:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-nickname" placeholder="" name="sensor${index}-nickname" required>
                    </div>`

    // Get template for sensor type selected by user
    if (selected == "pir" || selected == "switch") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-pin" placeholder="" name="sensor${index}-pin" required>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="sensor${index}-default_rule" placeholder="" name="sensor${index}-default_rule" required>
                    </div>`

    } else if (selected == "desktop") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-ip"><b>IP:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-ip" placeholder="" name="sensor${index}-ip" required>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-default_rule" placeholder="" name="sensor${index}-default_rule" required>
                    </div>`

    } else if (selected == "dummy") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="sensor${index}-default_rule" placeholder="" name="sensor${index}-default_rule" required>
                    </div>`
    } else if (selected == "si7021") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="sensor${index}-default_rule" placeholder="" name="sensor${index}-default_rule" required>
                    </div>

                    <div class="mb-2">
                        <label class="form-label" for="sensor${index}-mode"><b>Mode:</b></label>
                        <select name="sensor${index}-mode" id="sensor${index}-mode" class="form-select mb-3" required>
                            <option value="cool" id="cool">Cool</option>
                            <option value="heat" id="heat">Heat</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-tolerance"><b>Tolerance:</b></label>
                        <input type="text" class="form-control" id="sensor${index}-tolerance" placeholder="" name="sensor${index}-tolerance" required>
                    </div>`
    } else {
        // User selected first option ("Select sensor type"), clear form
        template = "";
    };

    // Render div, scroll down until visible
    document.getElementById("addSensorOptions" + index).innerHTML = template;
    document.getElementById("addSensorOptions" + index).scrollIntoView({behavior: "smooth"});
};

async function load_device_section(select) {
    // Get index of device
    const index = parseInt(select.id.replace("deviceType", ""));

    // Get user selection
    const selected = document.getElementById(select.id).value

    // Add nickname section to template, other sections added below as needed
    var template = `<div class="mb-2">
                        <label for="device${index}-nickname"><b>Nickname:</b></label>
                        <input type="text" class="form-control" id="device${index}-nickname" placeholder="" name="device${index}-nickname" required>
                    </div>`

    // Get template for device type selected by user
    if (selected == "dimmer" || selected == "bulb" || selected == "desktop" || selected == "relay") {
        template += `<div class="mb-2">
                        <label for="device${index}-ip"><b>IP:</b></label>
                        <input type="text" class="form-control" id="device${index}-ip" placeholder="" name="device${index}-ip" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" name="device${index}-default_rule" required>
                    </div>`

    } else if (selected == "mosfet" || selected == "dumb-relay") {
        template += `<div class="mb-2">
                        <label for="device${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="device${index}-pin" placeholder="" name="device${index}-pin" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" name="device${index}-default_rule" required>
                    </div>`

    } else if (selected == "pwm") {
        template += `<div class="mb-2">
                        <label for="device${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="device${index}-pin" placeholder="" name="device${index}-pin" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-min"><b>Min brightness:</b></label>
                        <input type="min" class="form-control" id="device${index}-min" placeholder="0" name="device${index}-min" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-max"><b>Max brightness:</b></label>
                        <input type="text" class="form-control" id="device${index}-max" placeholder="1023" name="device${index}-max" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" name="device${index}-default_rule" required>
                    </div>`

    } else if (selected == "api-target") {
        template += `<label for="device${index}-ip"><b>Target:</b></label>
                    <select name="device${index}-ip" id="device${index}-ip" class="form-select mb-3" onchange="api_target_selected(this)">
                        <option value="" selected="selected" selected></option>`

        for (var x in ApiTargetOptions) {
            template += `<option value="${x}">${x.split("-")[1]}</option>`
        };

        template += `</select>

                    <div class="mb-2 text-center">
                        <button id="device${index}-set-rule" class="btn btn-secondary mt-3" onclick="open_rule_modal(this);" disabled>Set rule</button>
                    </div>

                    <div class="mb-2 text-center">
                        <label for="device${index}-default_rule" style="display:none;"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control" id="device${index}-default_rule" placeholder="" name="device${index}-default_rule" style="display:none;" required>
                    </div>`

    } else if (selected == "ir-blaster") {
        template = `<div class="mb-2">
                        <label for="device${index}-pin"><b>Pin:</b></label>
                        <input type="text" class="form-control" id="device${index}-pin" placeholder="" name="device${index}-pin" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-min"><b>Virtual remotes:</b></label>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="irblaster-tv" value="irblaster-tv" id="irblaster-tv">
                            <label class="form-check-label" for="checkbox-tv">TV (Samsung)</label></br>
                            <input class="form-check-input" type="checkbox" name="irblaster-ac" value="irblaster-ac" id="irblaster-ac">
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
};

// Store sensors added on first page, use to populate later pages
var new_devices = []

async function load_next_device(button) {
    // Get index of clicked button
    const index = parseInt(button.id.replace("addDeviceButton", ""));

    var template = `<div ${ index ? 'class="mt-5"' : "" }>
                        <div class="card">
                            <div class="card-body">
                                <h4 class="card-title">device${index + 1}</h4>
                                <label for="deviceType${index + 1}" class="form-label"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_device_section(this)" name="deviceType${index + 1}" id="deviceType${index + 1}" class="form-select deviceType" required>
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

    new_devices.push("device" + (index + 1));
};

// Store sensors added on first page, use to populate later pages
var new_sensors = []

async function load_next_sensor(button) {
    // Get index of clicked button
    const index = parseInt(button.id.replace("addSensorButton", ""));

    var template = `<div ${ index ? 'class="mt-5"' : "" }>
                        <div class="card">
                            <div class="card-body">
                                <h4 class="card-title">sensor${index + 1}</h4>
                                <label for="sensorType${index + 1}" class="form-label"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_sensor_section(this)" name="sensorType${index + 1}" id="sensorType${index + 1}" class="form-select sensorType" required>
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

    // Add sensor to list used to populate page 2 and 3
    new_sensors.push("sensor" + (index + 1));
};
