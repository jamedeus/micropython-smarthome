// Store class instances created when device/sensor types are selected from dropdown
var instances = {"sensors": {}, "devices": {}}

// Populate instances with existing device + sensor cards (if editing config)
Array.from(document.getElementsByClassName("deviceType")).forEach(function(device) {
    const id = device.id.split("-")[0];
    instances["devices"][id] = new Device(id);
    instances["devices"][id].new = false;
});

Array.from(document.getElementsByClassName("sensorType")).forEach(function(sensor) {
    const id = sensor.id.split("-")[0];
    instances["sensors"][id] = new Sensor(id);
    instances["sensors"][id].new = false;
});



async function load_sensor_section(select) {
    // Get ID of sensor
    const id = select.id.split("-")[0];

    // Get user selection
    const selected = document.getElementById(select.id).value

    // Add nickname section to template, other sections added below as needed
    var template = `<div class="mb-2">
                        <label for="${id}-nickname" class="${id}"><b>Nickname:</b></label>
                        <input type="text" class="form-control ${id} nickname" id="${id}-nickname" placeholder="" onchange="update_nickname(this)" oninput="prevent_duplicate_nickname(event)" required>
                    </div>`

    // Get template for sensor type selected by user
    if (selected == "pir") {
        template += `<div class="mb-2">
                        <label for="${id}-pin" class="${id}"><b>Pin:</b></label>
                        <select id="${id}-pin" class="form-select ${id} pin-select" autocomplete="off" onchange="pinSelected(this)" required>
                            <option selected disabled>Select pin</option>
                            <option value="4">4</option>
                            <option value="5">5</option>
                            <option value="13">13</option>
                            <option value="14">14</option>
                            <option value="15">15</option>
                            <option value="16">16</option>
                            <option value="17">17</option>
                            <option value="18">18</option>
                            <option value="19">19</option>
                            <option value="21">21</option>
                            <option value="22">22</option>
                            <option value="23">23</option>
                            <option value="25">25</option>
                            <option value="26">26</option>
                            <option value="27">27</option>
                            <option value="32">32</option>
                            <option value="33">33</option>
                            <option value="34">34</option>
                            <option value="35">35</option>
                            <option value="36">36</option>
                            <option value="39">39</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="mt-1 ${id}"><b>Default Rule:</b></label>
                        <div class="d-flex flex-row align-items-center my-2">
                            <button id="${id}-default_rule-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-dash-lg"></i></button>
                            <input id="${id}-default_rule" type="range" class="${id} mx-auto" min="0" max="60" data-displaymin="0" data-displaymax="60" data-displaytype="float" step="0.5" value="" autocomplete="off">
                            <button id="${id}-default_rule-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-plus-lg"></i></button>
                        </div>
                    </div>`

    } else if (selected == "switch") {
        template += `<div class="mb-2">
                        <label for="${id}-pin" class="${id}"><b>Pin:</b></label>
                        <select id="${id}-pin" class="form-select ${id} pin-select" autocomplete="off" onchange="pinSelected(this)" required>
                            <option selected disabled>Select pin</option>
                            <option value="4">4</option>
                            <option value="5">5</option>
                            <option value="13">13</option>
                            <option value="14">14</option>
                            <option value="15">15</option>
                            <option value="16">16</option>
                            <option value="17">17</option>
                            <option value="18">18</option>
                            <option value="19">19</option>
                            <option value="21">21</option>
                            <option value="22">22</option>
                            <option value="23">23</option>
                            <option value="25">25</option>
                            <option value="26">26</option>
                            <option value="27">27</option>
                            <option value="32">32</option>
                            <option value="33">33</option>
                            <option value="34">34</option>
                            <option value="35">35</option>
                            <option value="36">36</option>
                            <option value="39">39</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="${id}"><b>Default Rule:</b></label>
                        <select id="${id}-default_rule" class="form-select ${id}" autocomplete="off" required>
                            <option value="enabled">Enabled</option>
                            <option value="disabled">Disabled</option>
                    </div>`

    } else if (selected == "desktop") {
        template += `<div class="mb-2">
                        <label for="${id}-ip" class="${id}"><b>IP:</b></label>
                        <input type="text" class="form-control ${id} ip-input" id="${id}-ip" placeholder="" pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$" required>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="${id}"><b>Default Rule:</b></label>
                        <select id="${id}-default_rule" class="form-select ${id}" autocomplete="off" required>
                            <option value="enabled">Enabled</option>
                            <option value="disabled">Disabled</option>
                        </select>
                    </div>`

    } else if (selected == "dummy") {
        template += `<div class="mb-2">
                        <label for="${id}-default_rule" class="${id}"><b>Default Rule:</b></label>
                        <select id="${id}-default_rule" class="form-select ${id}" autocomplete="off" required>
                            <option>Select default rule</option>
                            <option value="on">On</option>
                            <option value="off">Off</option>
                        </select>
                    </div>`
    } else if (selected == "si7021") {
        template += `<div class="mb-2">
                        <label for="${id}-default_rule" class="mt-1 ${id}"><b>Default Rule:</b></label>
                        <div class="d-flex flex-row align-items-center my-2">
                            <button id="${id}-default_rule-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-dash-lg"></i></button>
                            <input id="${id}-default_rule" type="range" class="${id} mx-auto" min="65" max="80" data-displaymin="65" data-displaymax="80" data-displaytype="float" step="0.5" value="" autocomplete="off">
                            <button id="${id}-default_rule-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-plus-lg"></i></button>
                        </div>
                    </div>

                    <div class="mb-2">
                        <label class="form-label ${id}" for="${id}-mode"><b>Mode:</b></label>
                        <select id="${id}-mode" class="form-select mb-3 ${id}" required>
                            <option value="cool" id="cool">Cool</option>
                            <option value="heat" id="heat">Heat</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-tolerance" class="${id}"><b>Tolerance:</b></label>
                        <input type="text" class="form-control ${id} thermostat" id="${id}-tolerance" placeholder="" required>
                    </div>`
    };

    // Disable "Select sensor type" option after selection made
    if (selected != "clear") {
        select.children[0].disabled = true;
    };

    // Insert template into div, scroll down until visible
    document.querySelector(`.${id} .configParams`).innerHTML = template;
    document.querySelector(`.${id} .configParams`).scrollIntoView({behavior: "smooth"});

    if (selected == "pir" || selected == "si7021") {
        add_new_slider(`${id}-default_rule`);
    };

    // Disable already-used pins in the new pin dropdown
    if (selected == "pir" || selected == "switch") {
        preventDuplicatePins();
    };

    // Add listeners to format IP field while typing, validate when focus leaves
    if (selected == "desktop") {
        ip = document.getElementById(`${id}-ip`);
        ip.addEventListener('input', formatIp);
        ip.addEventListener('blur', validateIp);
    };

    // Add listener to constrain tolerance field
    if (selected == "si7021") {
        document.getElementById(`${id}-tolerance`).addEventListener('input', thermostatToleranceLimit);
    };

    // Check if Thermostat selected in any sensor dropdown
    sensors = document.getElementsByClassName("sensorType");

    var found = false;
    for (sensor of sensors) {
        if (sensor.value == "si7021") {
            console.log('found')
            found = true;
        };
    };

    // If Thermostat selected, disable Thermostat option in all dropdowns (cannot have more than 1)
    if (!found) {
        thermostat_configured = false;

        for (sensor of document.getElementsByClassName("sensorType")) {
            for (option of sensor.children) {
                if (option.value == "si7021") {
                    option.disabled = false;
                };
            };
        };

    // If Thermostat not selected enable Thermostat option in all dropdowns
    } else {
        thermostat_configured = true;

        for (sensor of document.getElementsByClassName("sensorType")) {
            if (sensor == select) { continue };
            for (option of sensor.children) {
                if (option.value == "si7021") {
                    option.disabled = true;
                };
            };
        };
    };

    if (instances["sensors"][id]) {
        // If instance already exists, wipe params and re-populate (type changed)
        instances["sensors"][id].getParams();
        instances["sensors"][id].modified = true;
    } else {
        // If new sensor, create instance
        instances["sensors"][id] = new Sensor(id);
    };
};



async function load_device_section(select) {
    // Get ID of device
    const id = select.id.split("-")[0];

    // Get user selection
    const selected = document.getElementById(select.id).value

    // Add nickname section to template, other sections added below as needed
    var template = `<div class="mb-2">
                        <label for="${id}-nickname" class="${id}"><b>Nickname:</b></label>
                        <input type="text" class="form-control ${id} nickname" id="${id}-nickname" placeholder="" onchange="update_nickname(this)" oninput="prevent_duplicate_nickname(event)" required>
                    </div>`

    // Get template for device type selected by user
    if (selected == "dimmer" || selected == "bulb") {
        template += `<div class="mb-2">
                        <label for="${id}-ip" class="${id}"><b>IP:</b></label>
                        <input type="text" class="form-control ${id} ip-input" id="${id}-ip" placeholder="" pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$" required>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="mt-1 ${id}"><b>Default Rule:</b></label>
                        <div class="d-flex flex-row align-items-center my-2">
                            <button id="${id}-default_rule-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="1"><i class="bi-dash-lg"></i></button>
                            <input id="${id}-default_rule" type="range" class="${id} mx-auto" min="1" max="100" data-displaymin="1" data-displaymax="100" data-displaytype="int" step="1" value="" autocomplete="off">
                            <button id="${id}-default_rule-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="1"><i class="bi-plus-lg"></i></button>
                        </div>
                    </div>

                    <div class="mt-3 text-center">
                        <a class="text-decoration-none text-dim" data-bs-toggle="collapse" href="#${id}-advanced_settings" role="button" aria-expanded="false" aria-controls="${id}-advanced_settings">Advanced</a>
                    </div>

                    <div id="${id}-advanced_settings" class="collapse">
                        <div class="mb-2">
                            <label for="${id}-min_bright" class="${id}"><b>Min brightness:</b></label>
                            <input type="min" class="form-control ${id} pwm-limits" id="${id}-min_bright" placeholder="1" value="1" required>
                        </div>

                        <div class="mb-2">
                            <label for="${id}-max_bright" class="${id}"><b>Max brightness:</b></label>
                            <input type="text" class="form-control ${id} pwm-limits" id="${id}-max_bright" placeholder="100" value="100" required>
                        </div>
                    </div>`

    } else if (selected == "wled") {
        template += `<div class="mb-2">
                        <label for="${id}-ip" class="${id}"><b>IP:</b></label>
                        <input type="text" class="form-control ${id} ip-input" id="${id}-ip" placeholder="" pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$" required>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="mt-1 ${id}"><b>Default Rule:</b></label>
                        <div class="d-flex flex-row align-items-center my-2">
                            <button id="${id}-default_rule-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="1"><i class="bi-dash-lg"></i></button>
                            <input id="${id}-default_rule" type="range" class="${id} mx-auto" min="1" max="255" data-displaymin="1" data-displaymax="100" data-displaytype="int" step="1" value="" autocomplete="off">
                            <button id="${id}-default_rule-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="1"><i class="bi-plus-lg"></i></button>
                        </div>
                    </div>

                    <div class="mt-3 text-center">
                        <a class="text-decoration-none text-dim" data-bs-toggle="collapse" href="#${id}-advanced_settings" role="button" aria-expanded="false" aria-controls="${id}-advanced_settings">Advanced</a>
                    </div>

                    <div id="${id}-advanced_settings" class="collapse">
                        <div class="mb-2">
                            <label for="${id}-min_bright" class="${id}"><b>Min brightness:</b></label>
                            <input type="min" class="form-control ${id} pwm-limits" id="${id}-min_bright" placeholder="1" value="1" required>
                        </div>

                        <div class="mb-2">
                            <label for="${id}-max_bright" class="${id}"><b>Max brightness:</b></label>
                            <input type="text" class="form-control ${id} pwm-limits" id="${id}-max_bright" placeholder="255" value="255" required>
                        </div>
                    </div>`

    } else if (selected == "desktop" || selected == "relay") {
        template += `<div class="mb-2">
                        <label for="${id}-ip" class="${id}"><b>IP:</b></label>
                        <input type="text" class="form-control ${id} ip-input" id="${id}-ip" placeholder="" pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$" required>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="${id}"><b>Default Rule:</b></label>
                        <select id="${id}-default_rule" class="form-select ${id}" autocomplete="off" required>
                            <option value="enabled">Enabled</option>
                            <option value="disabled">Disabled</option>
                        </select>
                    </div>`

    } else if (selected == "mosfet" || selected == "dumb-relay") {
        template += `<div class="mb-2">
                        <label for="${id}-pin" class="${id}"><b>Pin:</b></label>
                        <select id="${id}-pin" class="form-select ${id} pin-select" autocomplete="off" onchange="pinSelected(this)" required>
                            <option selected disabled>Select pin</option>
                            <option value="4">4</option>
                            <option value="13">13</option>
                            <option value="16">16</option>
                            <option value="17">17</option>
                            <option value="18">18</option>
                            <option value="19">19</option>
                            <option value="21">21</option>
                            <option value="22">22</option>
                            <option value="23">23</option>
                            <option value="25">25</option>
                            <option value="26">26</option>
                            <option value="27">27</option>
                            <option value="32">32</option>
                            <option value="33">33</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="${id}"><b>Default Rule:</b></label>
                        <select id="${id}-default_rule" class="form-select ${id}" autocomplete="off" required>
                            <option value="enabled">Enabled</option>
                            <option value="disabled">Disabled</option>
                        </select>
                    </div>`

    } else if (selected == "pwm") {
        template += `<div class="mb-2">
                        <label for="${id}-pin" class="${id}"><b>Pin:</b></label>
                        <select id="${id}-pin" class="form-select ${id} pin-select" autocomplete="off" onchange="pinSelected(this)" required>
                            <option selected disabled>Select pin</option>
                            <option value="4">4</option>
                            <option value="13">13</option>
                            <option value="16">16</option>
                            <option value="17">17</option>
                            <option value="18">18</option>
                            <option value="19">19</option>
                            <option value="21">21</option>
                            <option value="22">22</option>
                            <option value="23">23</option>
                            <option value="25">25</option>
                            <option value="26">26</option>
                            <option value="27">27</option>
                            <option value="32">32</option>
                            <option value="33">33</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-default_rule" class="mt-1 ${id}"><b>Default Rule:</b></label>
                        <div class="d-flex flex-row align-items-center my-2">
                            <button id="${id}-default_rule-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="10"><i class="bi-dash-lg"></i></button>
                            <input id="${id}-default_rule" type="range" class="${id} mx-auto" min="0" max="1023" data-displaymin="0" data-displaymax="100" data-displaytype="int" step="0.5" value="512" autocomplete="off">
                            <button id="${id}-default_rule-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="10"><i class="bi-plus-lg"></i></button>
                        </div>
                    </div>

                    <div class="mt-3 text-center">
                        <a class="text-decoration-none text-dim" data-bs-toggle="collapse" href="#${id}-advanced_settings" role="button" aria-expanded="false" aria-controls="${id}-advanced_settings">Advanced</a>
                    </div>

                    <div id="${id}-advanced_settings" class="collapse">
                        <div class="mb-2">
                            <label for="${id}-min_bright" class="${id}"><b>Min brightness:</b></label>
                            <input type="min" class="form-control ${id} pwm-limits" id="${id}-min_bright" placeholder="1" value="1" required>
                        </div>

                        <div class="mb-2">
                            <label for="${id}-max_bright" class="${id}"><b>Max brightness:</b></label>
                            <input type="text" class="form-control ${id} pwm-limits" id="${id}-max_bright" placeholder="1023" value="1023" required>
                        </div>
                    </div>`

    } else if (selected == "api-target") {
        template += `<div class="mb-2">
                        <label for="${id}-ip" class="${id}"><b>Target Node:</b></label>
                        <select id="${id}-ip" class="form-select mb-3 ${id}" onchange="api_target_selected(this)">
                            <option value="" selected="selected" selected></option>`

        for (var x in ApiTargetOptions) {
            if (x == "addresses") { continue };
            template +=    `<option value="${ApiTargetOptions["addresses"][x]}">${x}</option>`
        };

        template +=     `</select>
                    </div>

                    <div class="mb-2 text-center">
                        <button id="${id}-default_rule-button" class="btn btn-secondary mt-3 ${id}" onclick="open_rule_modal(this);" data-target="${id}-default_rule" disabled>Set rule</button>
                    </div>

                    <div class="mb-2 text-center">
                        <label for="${id}-default_rule" class="${id}" style="display:none;"><b>Default Rule:</b></label>
                        <input type="default_rule" class="form-control ${id}" id="${id}-default_rule" placeholder="" style="display:none;" onchange="document.getElementById('${id}-default_rule-button').dataset.original = this.value;" required>
                    </div>`

    } else if (selected == "ir-blaster") {
        template = `<div class="mb-2">
                        <label for="${id}-pin" class="${id}"><b>Pin:</b></label>
                        <select id="${id}-pin" class="form-select ${id} pin-select" autocomplete="off" onchange="pinSelected(this)" required>
                            <option selected disabled>Select pin</option>
                            <option value="4">4</option>
                            <option value="13">13</option>
                            <option value="16">16</option>
                            <option value="17">17</option>
                            <option value="18">18</option>
                            <option value="19">19</option>
                            <option value="21">21</option>
                            <option value="22">22</option>
                            <option value="23">23</option>
                            <option value="25">25</option>
                            <option value="26">26</option>
                            <option value="27">27</option>
                            <option value="32">32</option>
                            <option value="33">33</option>
                        </select>
                    </div>

                    <div class="mb-2">
                        <label for="${id}-remotes" class="${id}"><b>Virtual remotes:</b></label>
                        <div id="${id}-remotes" class="form-check ${id}">
                            <input class="form-check-input ir-target" type="checkbox" value="irblaster-tv" id="checkbox-tv">
                            <label class="form-check-label" for="checkbox-tv">TV (Samsung)</label></br>
                            <input class="form-check-input ir-target" type="checkbox" value="irblaster-ac" id="checkbox-ac">
                            <label class="form-check-label" for="checkbox-ac">AC (Whynter)</label>
                        </div>
                    </div>`

    };

    // Disable "Select device type" option after selection made
    if (selected != "clear") {
        select.children[0].disabled = true;
    };

    // Insert template into div, scroll down until visible
    document.querySelector(`.${id} .configParams`).innerHTML = template;
    document.querySelector(`.${id} .configParams`).scrollIntoView({behavior: "smooth"});

    if (selected == "dimmer" || selected == "bulb" || selected == "pwm" || selected == "wled") {
        add_new_slider(`${id}-default_rule`);
    };

    // Disable already-used pins in the new pin dropdown
    if (selected == "mosfet" || selected == "dumb-relay" || selected == "pwm" || selected == "ir-blaster") {
        preventDuplicatePins();
    };

    // Add listeners to format IP field while typing, validate when focus leaves
    if (selected == "dimmer" || selected == "bulb" || selected == "desktop" || selected == "relay" || selected == "wled") {
        ip = document.getElementById(`${id}-ip`);
        ip.addEventListener('input', formatIp);
        ip.addEventListener('blur', validateIp);
    };

    // Add listener for PWM max/min fields
    if (selected == "pwm") {
        document.getElementById(`${id}-max_bright`).addEventListener('input', pwmLimits);
        document.getElementById(`${id}-min_bright`).addEventListener('input', pwmLimits);
    };

    // Check if IrBlaster selected in any device dropdown
    devices = document.getElementsByClassName("deviceType");

    var found = false;
    for (device of devices) {
        if (device.value == "ir-blaster") {
            found = true;
        };
    };

    // If IrBlaster selected, disable IrBlaster option in all dropdowns (cannot have more than 1)
    if (!found) {
        ir_blaster_configured = false;

        for (device of document.getElementsByClassName("deviceType")) {
            for (option of device.children) {
                if (option.value == "ir-blaster") {
                    option.disabled = false;
                };
            };
        };

    // If IrBlaster not selected enable IrBlaster option in all dropdowns
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

    if (instances["devices"][id]) {
        // If instance already exists, wipe params and re-populate (type changed)
        instances["devices"][id].getParams();
        instances["devices"][id].modified = true;
    } else {
        // If new device, create instance
        instances["devices"][id] = new Device(id);
    };
};



async function load_next_device(button) {
    // Get index of clicked button
    const index = parseInt(button.id.replace("addDeviceButton", ""));

    // Ternary expression adds top margin to all except first card
    var template = `<div id="addDeviceDiv${index + 1}" class="device${index + 1} fade-in ${ index ? "mt-5" : "" }">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 class="card-title mx-auto my-auto device${index + 1}">device${index + 1}</h4>
                                    <button class="btn my-auto pe-2 device${index + 1} delete" id="device${index + 1}-remove" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label for="device${index + 1}-type" class="form-label device${index + 1}"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_device_section(this)" id="device${index + 1}-type" class="form-select deviceType device${index + 1} instanceType" required>
                                    <option value="clear">Select device type</option>
                                    <option value="dimmer">TP-Link Dimmer</option>
                                    <option value="bulb">TP-Link Bulb</option>
                                    <option value="relay">Smart Relay</option>
                                    <option value="dumb-relay">Relay</option>
                                    <option value="desktop">Desktop</option>
                                    <option value="pwm">LED Strip</option>
                                    <option value="mosfet">Mosfet</option>
                                    <option value="wled">WLED</option>
                                    <option value="api-target">Api Command</option>
                                    <option value="ir-blaster" ${ ir_blaster_configured ? "disabled" : ""}>IR Blaster</option>
                                    </select>
                                </div>

                                <div class="card-body device${index + 1} configParams"></div>
                            </div>
                        </div>

                        <div class="text-center position-relative">
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

    // Wait for fade animation to complete, remove class (prevent conflict with fade-out if card is deleted)
    await sleep(400);
    document.getElementById(`addDeviceDiv${index + 1}`).classList.remove('fade-in');
};



async function load_next_sensor(button) {
    // Get index of clicked button
    const index = parseInt(button.id.replace("addSensorButton", ""));

    // Ternary expression adds top margin to all except first card
    var template = `<div id="addSensorDiv${index + 1}" class="sensor${index + 1} fade-in ${ index ? "mt-5" : "" }">
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <button class="btn ps-2" style="visibility:hidden;"><i class="bi-x-lg"></i></button>
                                    <h4 class="card-title mx-auto my-auto sensor${index + 1}">sensor${index + 1}</h4>
                                    <button class="btn my-auto pe-2 sensor${index + 1} delete" id="sensor${index + 1}-remove" onclick="remove_instance(this)"><i class="bi-x-lg"></i></button>
                                </div>
                                <label for="sensor${index + 1}-type" class="form-label sensor${index + 1}"><b>Type:</b></label>
                                <div>
                                    <select onchange="load_sensor_section(this)" id="sensor${index + 1}-type" class="form-select sensorType sensor${index + 1} instanceType" required>
                                    <option value="clear">Select sensor type</option>
                                    <option value="pir">Motion Sensor</option>
                                    <option value="switch">Switch</option>
                                    <option value="dummy">Dummy</option>
                                    <option value="desktop">Desktop</option>
                                    <option value="si7021" ${ thermostat_configured ? "disabled" : ""}>Thermostat</option>
                                    </select>
                                </div>

                                <div class="card-body sensor${index + 1} configParams"></div>
                            </div>
                        </div>

                        <div class="text-center position-relative">
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

    // Wait for fade animation to complete, remove class (prevent conflict with fade-out if card is deleted)
    await sleep(400);
    document.getElementById(`addSensorDiv${index + 1}`).classList.remove('fade-in');
};



// Delete instance animation - takes array of divs + num, fades out the div at num, slides up all subsequent divs
async function delete_animation(cards, num) {
    return new Promise(async resolve => {
        // Fade out card to be deleted
        cards[num].classList.add('fade-out');

        // Slide up all cards below, wait for animation to complete
        for (i=parseInt(num)+1; i<cards.length; i++) {
            cards[i].children[0].classList.add('slide-up');
            cards[i].children[1].classList.add('slide-up');
        };
        await sleep(800);

        // Prevent cards jumping higher when hidden card is actually deleted
        for (i=parseInt(num)+1; i<cards.length; i++) {
            cards[i].children[0].classList.remove('slide-up');
            cards[i].children[1].classList.remove('slide-up');
        };

        // If removing first card, remove top margin from second (new-first) card
        if (num == 1) {
            try {
                cards[2].classList.remove("mt-5");
            } catch(err) {}; // Prevent error when deleting last card
        };
        resolve();
    });
};



// Runs when card deleted, decrement references to instance ID of all subsequent cards to prevent gap in indices
// Example: If device2 is deleted, device3 becomes device2, device4 becomes device3, etc
function update_ids(cards, num, target) {
    return new Promise(resolve => {
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
        resolve();
    });
};



// Called by delete button in top right corner of device/sensor cards
async function remove_instance(el) {
    // Instance ID string (device1, sensor2, etc)
    var target = el.id.split("-")[0];

    // Get pixel value of 1rem (used in animation)
    remPx = parseFloat(getComputedStyle(document.documentElement).fontSize)

    // Delete target from instances, get object with all cards of same type (device/sensor), get index of deleted card
    if (target.startsWith("device")) {
        delete instances['devices'][target];
        var num = target.replace("device", "");
        var cards = Array.from(document.getElementById("devices").children);
        // Get height of card to be deleted + 3rem (gap between cards)
        animation_height = document.getElementById(`addDeviceDiv${num}`).clientHeight / remPx + 3;
    } else {
        delete instances['sensors'][target];
        var num = target.replace("sensor", "");
        var cards = Array.from(document.getElementById("sensors").children);
        // Get height of card to be deleted + 3rem (gap between cards)
        animation_height = document.getElementById(`addSensorDiv${num}`).clientHeight / remPx + 3;
    };

    // Set CSS var used in slide-up animation
    document.documentElement.style.setProperty('--animation-height', `${animation_height}rem`);

    // Disable all delete buttons until finished, prevent user deleting multiple at same time
    for (button of document.getElementsByClassName("delete")) {
        button.disabled = true;
    }

    // Get all elements with deleted card's class (used to delete later, must get before other card classes change)
    let elements = document.querySelectorAll(`.${target}`);

    // Update all other card's IDs and classes while running animation
    await Promise.all([delete_animation(cards, num), update_ids(cards, num, target)])

    // Delete card + all options on page2-3
    for (i=0; i<elements.length; i++) {
        elements[i].remove();
    };

    // If bottom card deleted, un-hide "Add another" button in new bottom div
    try {
        if (parseInt(num)+1 == cards.length) {
            if (target.startsWith('device')) {
                document.getElementById(`addDeviceButton${num-1}`).classList.add('fade-in');
                document.getElementById(`addDeviceButton${num-1}`).style.display = "initial";
            } else {
                document.getElementById(`addSensorButton${num-1}`).classList.add('fade-in');
                document.getElementById(`addSensorButton${num-1}`).style.display = "initial";
            };
        };

    // If no cards remaining, insert button
    } catch(err) {
        if (target.startsWith('device')) {
            template = `<div class="text-center">
                            <button onclick="load_next_device(this)" type="button" id="addDeviceButton0" class="btn-secondary btn my-3 fade-in">Add</button>
                        </div>`
            document.getElementById("devices").insertAdjacentHTML('beforeend', template);
        } else {
            template = `<div class="text-center">
                            <button onclick="load_next_sensor(this)" type="button" id="addSensorButton0" class="btn-secondary btn my-3 fade-in">Add</button>
                        </div>`
            document.getElementById("sensors").insertAdjacentHTML('beforeend', template);
        };
    };

    // Re-enable delete buttons
    for (button of document.getElementsByClassName("delete")) {
        button.disabled = false;
    }

    // Rebuild self-target options with new instance IDs
    get_self_target_options();
};
