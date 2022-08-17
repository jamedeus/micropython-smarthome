document.getElementById('page1-button').addEventListener("click", function(e) {
    e.preventDefault();

    // If user added new sensors, create card for each on page2 (sensor target selection) and page3 (schedule rules)
    if (new_sensors.length > 0) {
        // Get array of all device type dropdowns
        devices = document.getElementsByClassName("deviceType");

        // Add card for each sensor that was added on first page
        for (let i = 0; i < new_sensors.length; i++) {
            // Get type of sensor
            const type = document.getElementById(new_sensors[i].replace("sensor", "sensorType")).value;

            // Append card opening div to page2
            document.getElementById("page2-cards").innerHTML +=  `<div class='card'>
                                                                <div class='card-body'>
                                                                    <label for='${new_sensors[i]}-targets' class='card-title sensor-targets-label'><b>${new_sensors[i]} (${type}) targets:</b></label>
                                                                    <div id='${new_sensors[i]}-targets' class='form-check sensor-targets'>`

                // Iterate devices, add checkbox for each to new sensor card
            for (let j = 0; j < devices.length; j++) {
                // Do not add if device is IrBlaster (cannot be targeted)
                if (devices[j].value == "ir-blaster") { continue };

                document.getElementById(new_sensors[i] + "-targets").innerHTML += `<input type='checkbox' class='form-check-input' id='target-${new_sensors[i]}-${devices[j].id.replace("deviceType", "device")}' name='target-${new_sensors[i]}-${devices[j].id.replace("deviceType", "device")}' value='target-${new_sensors[i]}-${devices[j].id.replace("deviceType", "device")}'><label for='target-${new_sensors[i]}-${devices[j].id.replace("deviceType", "device")}' class='form-check-label'>${devices[j].id.replace("deviceType", "device")} (${devices[j].value})</label><br>`;
            };

            // Close div
            document.getElementById("page2-cards").innerHTML += "</div></div></div></br>"

            // Add schedule rule section for the new sensor to page3
            document.getElementById("page3-cards").innerHTML += `<div class='card'>
                                                                    <div class='card-body'>
                                                                        <label class='card-title schedule-rule-card'><b>${new_sensors[i]} (${type}):</b></label>
                                                                        <table id='${new_sensors[i]}-rules' class='table table-borderless'>
                                                                            <tr>
                                                                                <th style='text-align: left;'>Time</th>
                                                                                <th style='text-align: left;'>Rule</th>
                                                                            </tr>
                                                                                <tr id='${new_sensors[i]}-row-1'>
                                                                                    <td><input type='text' class='form-control' id='schedule-${new_sensors[i]}-rule1-time' placeholder='HH:MM' name='schedule-${new_sensors[i]}-rule1-time'></td>
                                                                                    <td><input type='text' class='form-control' id='schedule-${new_sensors[i]}-rule1-value' placeholder='' name='schedule-${new_sensors[i]}-rule1-value'></td>
                                                                                    <td class='min'><button type='button' class='remove btn btn-danger' id='${new_sensors[i]}-remove1'  onclick='remove(this)'>X</button></td>
                                                                                </tr>
                                                                        </table>
                                                                    </div>
                                                                    <div class='text-left mx-3 mb-3'>
                                                                        <button type='button' class='btn btn-secondary add' id='${new_sensors[i]}-add-rule'>Add another</button>
                                                                    </div>
                                                                </div></br>`
        };
    };

    // Clear new_sensors (prevent adding duplicates if user goes back and forth between pages without adding anything)
    new_sensors = []

    // If user changed a sensor's type, update type listed on page2 to reflect
    sensors = document.getElementsByClassName("sensor-targets-label")
    for (let sen = 0; sen < sensors.length; sen++) {
        id = sensors[sen].innerHTML.split(" ")[0].split(">")[1];

        old_type = sensors[sen].innerHTML.split(" ")[1].replace("(", "").replace(")", "");
        new_type = document.getElementById(id.replace("sensor", "sensorType")).value;

        if (old_type != new_type) {
            sensors[sen].innerHTML = sensors[sen].innerHTML.replace(old_type, new_type);

            // Uncheck all target boxes
            for (el of document.getElementById(id + "-targets").children) {
                // Children contains inputs, their labels, and line breaks - only process inputs
                if (el.classList.contains("form-check-input")) {
                    el.checked = false;
                }
            }
        };
    };

    // Get array of all device type dropdowns on page1
    devices = document.getElementsByClassName("deviceType");

    // Get array of all sensor-target cards on page2
    sensors = document.getElementsByClassName("sensor-targets");

    // Iterate device dropdowns
    for (let dev = 0; dev < devices.length; dev++) {

        const dev_id = devices[dev].id.replace("deviceType", "device");
        const dev_type = devices[dev].value;

        // Iterate sensor sections
        for (let sen = 0; sen < sensors.length; sen++) {

            const sen_id = sensors[sen].id.replace("-targets", "");

            var found = false;

            // Iterate options within current sensor section
            for (let opt = 0; opt < sensors[sen].childElementCount; opt++) {
                // Children contains inputs, their labels, and line breaks - only process inputs (first of every 3)
                if (opt % 3) { continue };

                // Check if option is for device from outer loop
                if (sensors[sen].children[opt].id.split("-")[2] == dev_id) {
                    found = true;

                    // If so, check if type has changed
                    if (sensors[sen].children[opt+1].innerHTML.replace(dev_id + " (", "").replace(")", "") == dev_type) {
                        // If type hasn't changed, go to next sensor section
                        break
                    } else if (dev_type == "ir-blaster") {
                        // If device type changed to IrBlaster, remove checkbox (cannot be targeted, API only)
                        sensors[sen].children[opt+2].remove();
                        sensors[sen].children[opt+1].remove();
                        sensors[sen].children[opt].remove();
                    } else {
                        // If type HAS changed, replace and uncheck box
                        sensors[sen].children[opt+1].innerHTML = dev_id + " (" + dev_type + ")"
                        sensors[sen].children[opt].checked = false;

                        // Go to next sensor section
                        break
                    };
                };
            };

            // If no match was found, add the device as an option (unless device is IrBlaster)
            if (!found && dev_type != "ir-blaster") {
                sensors[sen].innerHTML += `<input type='checkbox' class='form-check-input' id='target-${sen_id}-${dev_id}' name='target-${sen_id}-${dev_id}' value='target-${sen_id}-${dev_id}'><label for='target-${sen_id}-${dev_id}' class='form-check-label'>${dev_id} (${dev_type})</label><br>`;
            };
        };
    };

    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page1").classList.remove("d-flex");
    document.getElementById("page1").style.display = "none";
});

document.getElementById('page2-button').addEventListener("click", function(e) {
    e.preventDefault();

    // If user added new devices, create card for each on page3 (schedule rules)
    if (new_devices.length > 0) {
        // Get array of all device type dropdowns
        devices = document.getElementsByClassName("deviceType");

        // Add card for each device that was added on first page
        for (let i = 0; i < new_devices.length; i++) {
            // Get type of device
            const type = document.getElementById(new_devices[i].replace("device", "deviceType")).value;

            // Do not add IrBlaster (doesn't support schedule rules)
            if (type == "ir-blaster") { continue };

            // Add schedule rule section for the new device to page3
            document.getElementById("page3-cards").innerHTML += `<div class='card'>
                                                                    <div class='card-body'>
                                                                        <label class='card-title schedule-rule-card'><b>${new_devices[i]} (${type}):</b></label>
                                                                        <table id='${new_devices[i]}-rules' class='table table-borderless'>
                                                                            <tr>
                                                                                <th style='text-align: left;'>Time</th>
                                                                                <th style='text-align: left;'>Rule</th>
                                                                            </tr>
                                                                                <tr id='${new_devices[i]}-row-1'>
                                                                                    <td><input type='text' class='form-control' id='schedule-${new_devices[i]}-rule1-time' placeholder='HH:MM' name='schedule-${new_devices[i]}-rule1-time'></td>
                                                                                    <td><input type='text' class='form-control' id='schedule-${new_devices[i]}-rule1-value' placeholder='' name='schedule-${new_devices[i]}-rule1-value'></td>
                                                                                    <td class='min'><button type='button' class='remove btn btn-danger' id='${new_devices[i]}-remove1'  onclick='remove(this)'>X</button></td>
                                                                                </tr>
                                                                        </table>
                                                                    </div>
                                                                    <div class='text-left mx-3 mb-3'>
                                                                        <button type='button' class='btn btn-secondary add' id='${new_devices[i]}-add-rule'>Add another</button>
                                                                    </div>
                                                                </div></br>`;
        };
    };

    // Clear new_devices (prevent adding duplicates if user goes back and forth between pages without adding anything)
    new_devices = []

    // If user changed a sensor or device's type, update type listed on page3 to reflect
    instances = document.getElementsByClassName("schedule-rule-card");
    for (let i = 0; i < instances.length; i++) {
        id = instances[i].innerHTML.split(" ")[0].split(">")[1];

        old_type = instances[i].innerHTML.split(" ")[1].replace("(", "").replace(")", "").split(":")[0];

        if (id.startsWith("device")) {
            new_type = document.getElementById(id.replace("device", "deviceType")).value;
        } else if (id.startsWith("sensor")) {
            new_type = document.getElementById(id.replace("sensor", "sensorType")).value;
        } else {
            // Should not be possible, prevent error if somehow happens
            continue
        };

        if (old_type != new_type) {
            // If changed to IrBlaster, remove card (doesn't support schedule rules)
            if (new_type == "ir-blaster") {
                instances[i].parentElement.parentElement.remove();
                continue;
            }

            instances[i].innerHTML = instances[i].innerHTML.replace(old_type, new_type);

            // Clear all existing schedule rules (likely invalid for new type)
            document.getElementById(id + "-rules").innerHTML = `<tr>
                                                                    <th style='text-align: left;'>Time</th>
                                                                    <th style='text-align: left;'>Rule</th>
                                                                </tr>
                                                                <tr id='${id}-row-1'>
                                                                    <td><input type='text' class='form-control' id='schedule-${id}-rule1-time' placeholder='HH:MM' name='schedule-${id}-rule1-time'></td>
                                                                    <td><input type='text' class='form-control' id='schedule-${id}-rule1-value' placeholder='' name='schedule-${id}-rule1-value'></td>
                                                                    <td class='min'><button type='button' class='btn btn-danger' id='placeholder_button' style='visibility: hidden;'>X</button></td>
                                                                </tr>`;
        };
    };

    document.getElementById("page3").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";
});

document.getElementById('page1-back-button').addEventListener("click", function(e) {
    window.location.replace("/node_configuration");
});

document.getElementById('page2-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    document.getElementById("page1").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";
});

document.getElementById('page3-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page3").classList.remove("d-flex");
    document.getElementById("page3").style.display = "none";
});
