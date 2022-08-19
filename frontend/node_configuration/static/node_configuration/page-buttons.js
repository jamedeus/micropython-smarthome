document.getElementById('page1-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Get array of all sensor target selection divs on page2
    sensors = document.getElementsByClassName("sensor-targets");

    // Find device instances that require updates
    for (device in instances['devices']) {

        // If device is new, add target select options on page2, add schedule rules card on page3
        if (instances['devices'][device].new) {
            // Skip IrBlaster (can't be targeted, doesn't support schedule rules)
            if (instances['devices'][device]['type'] == 'ir-blaster') { continue };

            // Add option to all sensor target select cards on page2
            for (sensor of sensors) {
                const sen_id = sensor.id.split("-")[0];

                template = `<input type='checkbox' class='form-check-input ${sen_id} target' id='target-${sen_id}-${device}' value='target-${sen_id}-${device}'>
                            <label for='target-${sen_id}-${device}' class='form-check-label'>${device} (${instances['devices'][device]['type']})</label><br>`;

                sensor.insertAdjacentHTML('beforeend', template);
            };

            // Add schedule rule section for the new device to page3
            template = `<div class='card'>
                            <div class='card-body'>
                                <label id='${device}-rules-label' class='card-title schedule-rule-card'><b>${device} (${instances['devices'][device]['type']})</b></label>
                                <table id='${device}-rules' class='table table-borderless'>
                                    <tr>
                                        <th style='text-align: left;'>Time</th>
                                        <th style='text-align: left;'>Rule</th>
                                    </tr>
                                        <tr id='${device}-row-1'>
                                            <td style="width: 50%"><input type='text' class='form-control ${device} timestamp' id='schedule-${device}-rule1-time' placeholder='HH:MM'></td>`

            // ApiTarget: add button that opens rule modal + hidden input field that receives value from modal
            if (instances['devices'][device]['type'] == 'api-target') {
                template +=                `<td style="width: 50%"><button id="schedule-${device}-rule1-button" class="form-control" onclick="open_rule_modal(this);" type="button">Set rule</button>
                                            <input type="text" class="form-control ${device} rule" id="schedule-${device}-rule1-value" placeholder="" style="display:none;"></td>`

            // All other device types: add input field
            } else {
                template +=                 `<td><input type='text' class='form-control ${device} rule' id='schedule-${device}-rule1-value' placeholder=''></td>`
            };

            template +=                     `<td class='min'><button type='button' class='remove btn btn-danger' id='${device}-remove1'  onclick='remove(this)'>X</button></td>
                                        </tr>
                                </table>
                            </div>
                            <div class='text-left mx-3 mb-3'>
                                <button type='button' class='btn btn-secondary add' id='${device}-add-rule' onclick='add(this)'>Add another</button>
                            </div>
                        </div></br>`;

            document.getElementById("page3-cards").insertAdjacentHTML('beforeend', template);

            // Prevent adding duplicates
            instances['devices'][device].new = false;

        // If device type changed, change type displayed on page2 and page3
        } else if (instances['devices'][device].modified) {
            // Change type displayed on page2 target select cards
            for (sensor of sensors) {

                // Iterate options within current sensor section
                for (let opt = 0; opt < sensor.childElementCount; opt++) {
                    // Children contains inputs, their labels, and line breaks - only process inputs (first of every 3)
                    if (opt % 3) { continue };

                    // Find option for the device that changed
                    if (sensor.children[opt].id.split("-")[2] == device) {

                        // If device was changed to IrBlaster, remove option
                        if (instances['devices'][device]['type'] == 'ir-blaster') {
                            sensors.children[opt+2].remove();
                            sensors.children[opt+1].remove();
                            sensors.children[opt].remove();

                        // Otherwise, uncheck and change label
                        } else {
                            sensor.children[opt].checked = false;
                            // Change label text
                            sensor.children[opt+1].innerHTML = `${device} (${instances['devices'][device]['type']}}`;
                        };

                    };
                };
            };

            // Change type on schedule rules card
            document.getElementById(`${device}-rules-label`).innerHTML = `<b>${device} (${instances['devices'][device]['type']})</b>`;

            // Clear existing schedule rules (likely invalid after type change)
            document.getElementById(`${device}-rules`).innerHTML = `<tr>
                                                                    <th style='text-align: left;'>Time</th>
                                                                    <th style='text-align: left;'>Rule</th>
                                                                </tr>
                                                                <tr id='${device}-row-1'>
                                                                    <td><input type='text' class='form-control' id='schedule-${device}-rule1-time' placeholder='HH:MM'></td>
                                                                    <td><input type='text' class='form-control' id='schedule-${device}-rule1-value' placeholder=''></td>
                                                                    <td class='min'><button type='button' class='btn btn-danger' id='placeholder_button' style='visibility: hidden;'>X</button></td>
                                                                </tr>`;

            // Prevent running again (unless device type changes again)
            instances['devices'][device].modified = false;
        };
    };



    // Find sensor instances that require updates
    for (sensor in instances['sensors']) {
        // If sensor is new, add target select card to page2
        if (instances['sensors'][sensor].new) {

            // Card opening div
            var template =  `<div class='card'>
                                <div class='card-body'>
                                    <label id='${sensor}-targets-label' for='${sensor}-targets' class='card-title sensor-targets-label'><b>${sensor} (${instances['sensors'][sensor]["type"]}) targets:</b></label>
                                    <div id='${sensor}-targets' class='form-check sensor-targets'>`

            // Iterate devices, add checkbox for each to new sensor card
            for (device in instances['devices']) {
                // Do not add if device is IrBlaster (cannot be targeted)
                if (instances['devices'][device]['type'] == "ir-blaster") { continue };

                template += `<input type='checkbox' class='form-check-input ${sensor} target' id='target-${sensor}-${device}' value='target-${sensor}-${device}'>
                            <label for='target-${sensor}-${device}' class='form-check-label'>${device} (${instances['devices'][device]['type']})</label><br>`;
            };

            // Close div, add to DOM
            template += "</div></div></div></br>"
            document.getElementById("page2-cards").insertAdjacentHTML('beforeend', template);

            // Add schedule rule section for the new sensor to page3
            template = `<div class='card'>
                            <div class='card-body'>
                                <label id='${sensor}-rules-label' class='card-title schedule-rule-card'><b>${sensor} (${instances['sensors'][sensor]['type']})</b></label>
                                <table id='${sensor}-rules' class='table table-borderless'>
                                    <tr>
                                        <th style='text-align: left;'>Time</th>
                                        <th style='text-align: left;'>Rule</th>
                                    </tr>
                                        <tr id='${sensor}-row-1'>
                                            <td><input type='text' class='form-control ${sensor} timestamp' id='schedule-${sensor}-rule1-time' placeholder='HH:MM'></td>
                                            <td><input type='text' class='form-control ${sensor} rule' id='schedule-${sensor}-rule1-value' placeholder=''></td>
                                            <td class='min'><button type='button' class='remove btn btn-danger' id='${sensor}-remove1'  onclick='remove(this)'>X</button></td>
                                        </tr>
                                </table>
                            </div>
                            <div class='text-left mx-3 mb-3'>
                                <button type='button' class='btn btn-secondary add' id='${sensor}-add-rule' onclick='add(this)'>Add another</button>
                            </div>
                        </div></br>`

            document.getElementById("page3-cards").insertAdjacentHTML('beforeend', template);

            // Prevent adding duplicates if user goes back to page1
            instances['sensors'][sensor].new = false;

        // If sensor type changed, change type displayed on page2 and page3
        } else if (instances['sensors'][sensor].modified) {
            document.getElementById(`${sensor}-targets-label`).innerHTML = `<b>${sensor} (${instances['sensors'][sensor]['type']}) targets:</b>`;

            // Uncheck all target boxes
            for (el of document.getElementById(`${sensor}-targets`).children) {
                // Children contains inputs, their labels, and line breaks - only process inputs
                if (el.classList.contains("form-check-input")) {
                    el.checked = false;
                };
            };

            // Change type on schedule rules card
            document.getElementById(`${sensor}-rules-label`).innerHTML = `<b>${sensor} (${instances['sensors'][sensor]['type']})</b>`;

            // Clear existing schedule rules (likely invalid after type change)
            document.getElementById(`${sensor}-rules`).innerHTML = `<tr>
                                                                        <th style='text-align: left;'>Time</th>
                                                                        <th style='text-align: left;'>Rule</th>
                                                                    </tr>
                                                                    <tr id='${sensor}-row-1'>
                                                                        <td><input type='text' class='form-control' id='schedule-${sensor}-rule1-time' placeholder='HH:MM'></td>
                                                                        <td><input type='text' class='form-control' id='schedule-${sensor}-rule1-value' placeholder=''></td>
                                                                        <td class='min'><button type='button' class='btn btn-danger' id='placeholder_button' style='visibility: hidden;'>X</button></td>
                                                                    </tr>`;

            // Prevent running again (unless user changes type again)
            instances['sensors'][sensor].modified = false;
        };
    };

    // Show page2
    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page1").classList.remove("d-flex");
    document.getElementById("page1").style.display = "none";
});



document.getElementById('page2-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page3
    document.getElementById("page3").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";
});

document.getElementById('page1-back-button').addEventListener("click", function(e) {
    window.location.replace("/node_configuration");
});

document.getElementById('page2-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page1
    document.getElementById("page1").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";
});

document.getElementById('page3-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page2
    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page3").classList.remove("d-flex");
    document.getElementById("page3").style.display = "none";
});
