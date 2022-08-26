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
                        <label for="sensor${index}-nickname" class="sensor${index}"><b>Nickname:</b></label>
                        <input type="text" class="form-control sensor${index} nickname" id="sensor${index}-nickname" placeholder="" onchange="update_nickname(this)" required>
                    </div>`

    // Get template for sensor type selected by user
    if (selected == "pir" || selected == "switch") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-pin" class="sensor${index}"><b>Pin:</b></label>
                        <input type="text" class="form-control sensor${index}" id="sensor${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-default_rule" class="sensor${index}"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control sensor${index}" id="sensor${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "desktop") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-ip" class="sensor${index}"><b>IP:</b></label>
                        <input type="text" class="form-control sensor${index}" id="sensor${index}-ip" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-default_rule" class="sensor${index}"><b>Default Rule:</b></label>
                        <input type="text" class="form-control sensor${index}" id="sensor${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "dummy") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-default_rule" class="sensor${index}"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control sensor${index}" id="sensor${index}-default_rule" placeholder="" required>
                    </div>`
    } else if (selected == "si7021") {
        template += `<div class="mb-2">
                        <label for="sensor${index}-default_rule" class="sensor${index}"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control sensor${index}" id="sensor${index}-default_rule" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label class="form-label sensor${index}" for="sensor${index}-mode"><b>Mode:</b></label>
                        <select id="sensor${index}-mode" class="form-select mb-3 sensor${index}" required>
                            <option value="cool" id="cool">Cool</option>
                            <option value="heat" id="heat">Heat</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="sensor${index}-tolerance" class="sensor${index}"><b>Tolerance:</b></label>
                        <input type="text" class="form-control sensor${index}" id="sensor${index}-tolerance" placeholder="" required>
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
                        <label for="device${index}-nickname" class="device${index}"><b>Nickname:</b></label>
                        <input type="text" class="form-control device${index} nickname" id="device${index}-nickname" placeholder="" onchange="update_nickname(this)" required>
                    </div>`

    // Get template for device type selected by user
    if (selected == "dimmer" || selected == "bulb" || selected == "desktop" || selected == "relay") {
        template += `<div class="mb-2">
                        <label for="device${index}-ip" class="device${index}"><b>IP:</b></label>
                        <input type="text" class="form-control device${index}" id="device${index}-ip" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule" class="device${index}"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control device${index}" id="device${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "mosfet" || selected == "dumb-relay") {
        template += `<div class="mb-2">
                        <label for="device${index}-pin" class="device${index}"><b>Pin:</b></label>
                        <input type="text" class="form-control device${index}" id="device${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule" class="device${index}"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control device${index}" id="device${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "pwm") {
        template += `<div class="mb-2">
                        <label for="device${index}-pin" class="device${index}"><b>Pin:</b></label>
                        <input type="text" class="form-control device${index}" id="device${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-min" class="device${index}"><b>Min brightness:</b></label>
                        <input type="min" class="form-control device${index}" id="device${index}-min" placeholder="0" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-max" class="device${index}"><b>Max brightness:</b></label>
                        <input type="text" class="form-control device${index}" id="device${index}-max" placeholder="1023" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-default_rule" class="device${index}"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control device${index}" id="device${index}-default_rule" placeholder="" required>
                    </div>`

    } else if (selected == "api-target") {
        template += `<div class="mb-2">
                        <label for="device${index}-ip" class="device${index}"><b>Target Node:</b></label>
                        <select id="device${index}-ip" class="form-select mb-3 device${index}" onchange="api_target_selected(this)">
                            <option value="" selected="selected" selected></option>`

        for (var x in ApiTargetOptions) {
            if (x == "addresses") { continue };
            template +=    `<option value="${ApiTargetOptions["addresses"][x]}">${x}</option>`
        };

        template +=     `</select>
                    </div>

                    <div class="mb-2 text-center">
                        <button id="device${index}-default_rule-button" class="btn btn-secondary mt-3 device${index}" onclick="open_rule_modal(this);" disabled>Set rule</button>
                    </div>

                    <div class="mb-2 text-center">
                        <label for="device${index}-default_rule" class="device${index}" style="display:none;"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control device${index}" id="device${index}-default_rule" placeholder="" style="display:none;" required>
                    </div>`

    } else if (selected == "ir-blaster") {
        template = `<div class="mb-2">
                        <label for="device${index}-pin" class="device${index}"><b>Pin:</b></label>
                        <input type="text" class="form-control device${index}" id="device${index}-pin" placeholder="" required>
                    </div>

                    <div class="mb-2">
                        <label for="device${index}-remotes" class="device${index}"><b>Virtual remotes:</b></label>
                        <div id="device${index}-remotes" class="form-check device${index}">
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
    var template = `<div id="addDeviceDiv${index + 1}" class="device${index + 1} ${ index ? "mt-5" : "" }">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 class="card-title mx-auto my-auto device${index + 1}">device${index + 1}</h4>
                                    <button class="btn my-auto pe-2 device${index + 1}" id="device${index + 1}-remove" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label for="deviceType${index + 1}" class="form-label device${index + 1}"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_device_section(this)" id="deviceType${index + 1}" class="form-select deviceType device${index + 1}" required>
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

                                <div id="addDeviceOptions${index + 1}" class="card-body device${index + 1}"></div>
                            </div>
                        </div>

                        <div class="text-center">
                            <button onclick="load_next_device(this)" type="button" id="addDeviceButton${index + 1}" class="btn-secondary btn my-3 device${index + 1}">Add another</button>
                        </div>
                    </div>`

    if (index > 0) {
        // Hide clicked button
        button.style.display = "none";
    } else {
        // Remove clicked button
        button.parentElement.remove()
    };

    // Render div, scroll down until visible
    document.getElementById("devices").insertAdjacentHTML('beforeend', template);
    document.getElementById("addDeviceDiv" + (index + 1)).scrollIntoView({behavior: "smooth"});
};



async function load_next_sensor(button) {
    // Get index of clicked button
    const index = parseInt(button.id.replace("addSensorButton", ""));

    // Ternary expression adds top margin to all except first card
    var template = `<div id="addSensorDiv${index + 1}" class="sensor${index + 1} ${ index ? "mt-5" : "" }">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 class="card-title mx-auto my-auto sensor${index + 1}">sensor${index + 1}</h4>
                                    <button class="btn my-auto pe-2 sensor${index + 1}" id="sensor${index + 1}-remove" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label for="sensorType${index + 1}" class="form-label sensor${index + 1}"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_sensor_section(this)" id="sensorType${index + 1}" class="form-select sensorType sensor${index + 1}" required>
                                    <option value="clear">Select sensor type</option>
                                    <option value="pir">Motion Sensor</option>
                                    <option value="switch">Switch</option>
                                    <option value="dummy">Dummy</option>
                                    <option value="desktop">Desktop</option>
                                    <option value="si7021">Thermostat</option>
                                    </select>
                                </div>

                                <div id="addSensorOptions${index + 1}" class="card-body sensor${index + 1}"></div>
                            </div>
                        </div>

                        <div class="text-center">
                            <button onclick="load_next_sensor(this)" type="button" id="addSensorButton${index + 1}" class="btn-secondary btn my-3 sensor${index + 1}">Add another</button>
                        </div>
                    </div>`

    if (index > 0) {
        // Hide clicked button
        button.style.display = "none";
    } else {
        // Remove clicked button
        button.parentElement.remove()
    };

    // Render div, scroll down until visible
    document.getElementById("sensors").insertAdjacentHTML('beforeend', template);
    document.getElementById("addSensorDiv" + (index + 1)).scrollIntoView({behavior: "smooth"});
};



// Called by delete button in top right corner of device/sensor cards
function remove_instance(el) {
    // Instance ID string (device1, sensor2, etc)
    var target = el.id.split("-")[0];

    // Delete target from instances, get object with all cards of same type (device/sensor), get index of deleted card
    if (target.startsWith("device")) {
        delete instances['devices'][target];
        var cards = document.getElementById("devices").children;
        var num = target.replace("device", "");
    } else {
        delete instances['sensors'][target];
        var cards = document.getElementById("sensors").children;
        var num = target.replace("sensor", "");
    };

    // If removing first card, remove top margin from second (new-first) card
    if (num == 1) {
        try {
            cards[2].classList.remove("mt-5");
        } catch(err) {}; // Prevent error when deleting last card
    };

    // Get all elements with deleted instance's class, delete all except card (effects indices of cards object used below)
    let elements = document.querySelectorAll(`.${target}`);
    for (i=1; i<elements.length; i++) {
        elements[i].remove();
    };

    // Iterate all cards after the deleted card
    for (i=parseInt(num)+1; i<cards.length; i++) {
        // Get all elements associated with current card
        let elements = document.querySelectorAll(`.${target.replace(num, i)}`);

        // Decrement all instance ID references (device1, sensor2, etc) by 1
        for (el=0; el<elements.length; el++) {
            if (elements[el].hasAttribute("id")) {
                elements[el].id = elements[el].id.replace(i, i-1);
            };

            if (elements[el].hasAttribute("for")) {
                elements[el].setAttribute("for", elements[el].getAttribute("for").replace(i, i-1));
            };

            if (elements[el].classList.contains("card-title") || elements[el].classList.contains("form-check-label")) {
                if (target.startsWith('device')) {
                    elements[el].innerHTML = elements[el].innerHTML.replace(`device${i}`, `device${i-1}`);
                } else {
                    elements[el].innerHTML = elements[el].innerHTML.replace(`sensor${i}`, `sensor${i-1}`);
                };
            };

            if (elements[el].classList.contains("form-check-input")) {
                if (target.startsWith('device')) {
                    elements[el].value = elements[el].value.replace(`device${i}`, `device${i-1}`);
                } else {
                    elements[el].value = elements[el].value.replace(`sensor${i}`, `sensor${i-1}`);
                };
            };

            // Decrement class
            elements[el].classList.remove(target.replace(num, i))
            elements[el].classList.add(target.replace(num, i-1))
        };

        // Delete class instance, re-instantiate with new ID, set new to false to prevent duplicates on page2 + page3
        if (target.startsWith('device')) {
            delete instances['devices'][`device${i}`];
            instances['devices'][`device${i-1}`] = new Device(`device${i-1}`);
            instances['devices'][`device${i-1}`].new = false;
        } else {
            delete instances['sensors'][`sensor${i}`];
            instances['sensors'][`sensor${i-1}`] = new Sensor(`sensor${i-1}`);
            instances['sensors'][`sensor${i-1}`].new = false;
        };
    };

    // If bottom card deleted, un-hide "Add another" button in new bottom div
    try {
        if (parseInt(num)+1 == cards.length) {
            if (target.startsWith('device')) {
                document.getElementById(`addDeviceButton${num-1}`).style.display = "initial";
            } else {
                document.getElementById(`addSensorButton${num-1}`).style.display = "initial";
            };
        };

    // If no cards remaining, insert button
    } catch(err) {
        if (target.startsWith('device')) {
            template = `<div class="text-center">
                            <button onclick="load_next_device(this)" type="button" id="addDeviceButton0" class="btn-secondary btn my-3">Add another</button>
                        </div>`
            document.getElementById("devices").insertAdjacentHTML('beforeend', template);
        } else {
            template = `<div class="text-center">
                            <button onclick="load_next_sensor(this)" type="button" id="addSensorButton0" class="btn-secondary btn my-3">Add another</button>
                        </div>`
            document.getElementById("sensors").insertAdjacentHTML('beforeend', template);
        };
    };

    // Delete card
    cards[num].remove();

    // Rebuild self target options with new instance IDs
    get_self_target_options();
};
