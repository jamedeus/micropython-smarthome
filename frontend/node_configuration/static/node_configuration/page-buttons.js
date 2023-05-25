document.getElementById('page1-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Confirm all nickname fields are populated (prevent blank titles on page2-3)
    var nicknames = document.getElementsByClassName('nickname');
    var valid = true;

    for (i=0; i<nicknames.length; i++) {
        // If field is blank, add red highlight + listener to remove highlight on input
        if (nicknames[i].value == "") {
            nicknames[i].classList.add("is-invalid");
            nicknames[i].scrollIntoView({behavior: "smooth"});
            nicknames[i].addEventListener("input", (e) => {
                e.target.classList.remove("is-invalid");
            }, { once: true });
            valid = false;
        };
    };

    // If blank fields exist, don't proceed to page2
    if (!valid) { return };

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

                template = `<input type='checkbox' class='form-check-input ${sen_id} ${device} target' id='target-${sen_id}-${device}' value='target-${sen_id}-${device}'>
                            <label for='target-${sen_id}-${device}' class='form-check-label ${sen_id} ${device} target-label'>${instances['devices'][device]['nickname']}</label>
                            <br class='${device}'>`;

                sensor.insertAdjacentHTML('beforeend', template);
            };

            // Add schedule rule section for the new device to page3
            template = `<div class='card mb-4 ${device}'>
                            <div class='card-body text-center'>
                                <label id='${device}-rules-label' class='card-title schedule-rule-card ${device}' title='${device} - ${instances['devices'][device]['type']}'>
                                    <b>${instances['devices'][device]['nickname']}</b>
                                </label>
                                <table id='${device}-rules' class='table table-borderless ${device} d-none'>
                                    <tr>
                                        <th style='text-align: center;'>Time</th>
                                        <th style='text-align: center;'>Rule</th>
                                    </tr>
                                </table>
                                <div>
                                    <button type="button" class="btn btn-secondary add ${device}" id="${device}-add-rule" data-type="${instances['devices'][device]['type']}" onclick="add_new_rule(this)">Add Rule</i></button>
                                </div>
                            </div>
                        </div>`;

            document.getElementById("page3-cards").insertAdjacentHTML('beforeend', template);

            // Prevent adding duplicates
            instances['devices'][device].new = false;

        // If device nickname changed, but type did not change (targets + rules don't need to be cleared)
        } else if (instances['devices'][device].name_changed && ! instances['devices'][device].modified) {
            // Change name on schedule rules card
            document.getElementById(`${device}-rules-label`).innerHTML = `<b>${instances['devices'][device]['nickname']}</b>`;

            // Change text on all target options
            target_labels = document.getElementsByClassName(`${device} target-label`);
            for (i=0; i<target_labels.length; i++) {
                target_labels[i].innerHTML = `${instances['devices'][device]['nickname']}`;
            };

            instances['devices'][device].name_changed = false;

        // If device type changed, change type displayed on page2 and page3
        } else if (instances['devices'][device].modified) {
            target_checks = document.getElementsByClassName(`${device} target`);
            target_labels = document.getElementsByClassName(`${device} target-label`);

            // If device was changed to IrBlaster, remove all target options
            if (instances['devices'][device]['type'] == 'ir-blaster') {
                const max = target_checks.length;
                for (i=0; i<max; i++) {
                    target_checks[0].remove();
                    target_labels[0].nextSibling.remove();
                    target_labels[0].nextSibling.remove();
                    target_labels[0].remove();
                };

            // Otherwise, uncheck all target option boxes and change label text
            } else {
                for (i=0; i<target_checks.length; i++) {
                    target_checks[i].checked = false;
                    target_labels[i].innerHTML = `${instances['devices'][device]['nickname']}`;
                };
            };

            // Change name and tooltip on schedule rules card
            document.getElementById(`${device}-rules-label`).title = `${device} - ${instances['devices'][device]['type']}`;
            document.getElementById(`${device}-rules-label`).innerHTML = `<b>${instances['devices'][device]['nickname']}</b>`;

            // Clear existing schedule rules (likely invalid after type change)
            template = `<tr>
                            <th style='text-align: center;'>Time</th>
                            <th style='text-align: center;'>Rule</th>
                        </tr>`;
            document.getElementById(`${device}-rules`).innerHTML = template
            document.getElementById(`${device}-rules`).classList.add('d-none');

            // Prevent running again (unless device type changes again)
            instances['devices'][device].modified = false;
        };
    };



    // Find sensor instances that require updates
    for (sensor in instances['sensors']) {
        // If sensor is new, add target select card to page2
        if (instances['sensors'][sensor].new) {
            // Card opening div
            var template =  `<div class='card ${sensor}'>
                                <div class='card-body'>
                                    <label id='${sensor}-targets-label' for='${sensor}-targets' class='card-title sensor-targets-label ${sensor}'><b>${instances['sensors'][sensor]["nickname"]}</b> targets:</label>
                                    <div id='${sensor}-targets' class='form-check sensor-targets ${sensor}'>`

            // Iterate devices, add checkbox for each to new sensor card
            for (device in instances['devices']) {
                // Do not add if device is IrBlaster (cannot be targeted)
                if (instances['devices'][device]['type'] == "ir-blaster") { continue };

                template += `<input type='checkbox' class='form-check-input ${device} ${sensor} target' id='target-${sensor}-${device}' value='target-${sensor}-${device}'>
                            <label for='target-${sensor}-${device}' class='form-check-label ${device} ${sensor} target-label'>${instances['devices'][device]['nickname']}</label><br>`;
            };

            // Close div, add to DOM
            template += "</div></div></div></br>"
            document.getElementById("page2-cards").insertAdjacentHTML('beforeend', template);

            // Add schedule rule section for the new sensor to page3
            template = `<div class='card mb-4 ${sensor}'>
                            <div class='card-body text-center'>
                                <label id='${sensor}-rules-label' class='card-title schedule-rule-card ${sensor}' title='${sensor} - ${instances['sensors'][sensor]['type']}'>
                                    <b>${instances['sensors'][sensor]['nickname']}</b>
                                </label>
                                <table id='${sensor}-rules' class='table table-borderless ${sensor} d-none'>
                                    <tr>
                                        <th style='text-align: center;'>Time</th>
                                        <th style='text-align: center;'>Rule</th>
                                    </tr>
                                </table>
                                <div>
                                    <button type="button" class="btn btn-secondary add ${sensor}" id="${sensor}-add-rule" data-type="${instances['sensors'][sensor]['type']}" onclick="add_new_rule(this)">Add Rule</i></button>
                                </div>
                            </div>
                        </div>`;
            document.getElementById("page3-cards").insertAdjacentHTML('beforeend', template);

            // Prevent adding duplicates if user goes back to page1
            instances['sensors'][sensor].new = false;

        // If sensor nickname changed, but type did not change (targets + rules don't need to be cleared)
        } else if (instances['sensors'][sensor].name_changed && ! instances['sensors'][sensor].modified) {
            // Change name on schedule rules card
            document.getElementById(`${sensor}-rules-label`).innerHTML = `<b>${instances['sensors'][sensor]['nickname']}</b>`;

            // Change name on targets card
            document.getElementById(`${sensor}-targets-label`).innerHTML = `<b>${instances['sensors'][sensor]['nickname']}</b> targets:`;

            instances['sensors'][sensor].name_changed = false;

        // If sensor type changed, change type displayed on page2 and page3
        } else if (instances['sensors'][sensor].modified) {
            // Uncheck all target boxes
            for (el of document.getElementById(`${sensor}-targets`).children) {
                // Children contains inputs, their labels, and line breaks - only process inputs
                if (el.classList.contains("form-check-input")) {
                    el.checked = false;
                };
            };

            // Change nickname and type on target card
            document.getElementById(`${sensor}-targets-label`).innerHTML = `<b>${instances['sensors'][sensor]['nickname']}</b> targets:`;

            // Change name and tooltip on schedule rules card
            document.getElementById(`${sensor}-rules-label`).title = `${sensor} - ${instances['sensors'][sensor]['type']}`;
            document.getElementById(`${sensor}-rules-label`).innerHTML = `<b>${instances['sensors'][sensor]['nickname']}</b>`;

            // Clear existing schedule rules (likely invalid after type change)
            template = `<tr>
                            <th style='text-align: center;'>Time</th>
                            <th style='text-align: center;'>Rule</th>
                        </tr>`;
            document.getElementById(`${sensor}-rules`).innerHTML = template
            document.getElementById(`${sensor}-rules`).classList.add('d-none');

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

    // Update sliders (fix incorrect width caused by display: none)
    $('input[type="range"]').rangeslider('update', true);
});

document.getElementById('page1-back-button').addEventListener("click", function(e) {
    // If user changed any inputs, show warning before redirecting to overview
    if (changes_made) {
        const body = "<p class='text-center'>Your changes will be lost if you go back - are you sure?</p>";
        const footer = `<button type="button" id="yes-button" class="btn btn-danger" data-bs-dismiss="modal" onclick="window.location.replace('/config_overview');">Go Back</button>
                        <button type="button" id="no-button" class="btn btn-secondary" data-bs-dismiss="modal">Keep Editing</button>`;
        show_modal(errorModal, "Warning", body, footer);

    // Skip warning if no changes
    } else {
        window.location.replace("/config_overview");
    };
});

document.getElementById('page2-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page1
    document.getElementById("page1").classList.add("d-flex");
    document.getElementById("page2").classList.remove("d-flex");
    document.getElementById("page2").style.display = "none";

    // Update sliders (fix incorrect width caused by display: none)
    $('input[type="range"]').rangeslider('update', true);
});

document.getElementById('page3-back-button').addEventListener("click", function(e) {
    e.preventDefault();

    // Show page2
    document.getElementById("page2").classList.add("d-flex");
    document.getElementById("page3").classList.remove("d-flex");
    document.getElementById("page3").style.display = "none";
});
