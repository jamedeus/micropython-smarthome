function add(button) {
    var instance = button.id.split("-", 1)[0];

    table = document.getElementById(instance + "-rules")

    // Rows are numbered sequentially. Get number of last row and increment
    var next_row = parseInt($('#' + instance + '-rules tr:last').attr('id').split("-").pop()) + 1;

    var row = table.insertRow();
    row.setAttribute("id", instance + "-row-" + next_row)

    var cell_time = row.insertCell(0);
    var cell_value = row.insertCell(1);
    var cell_del = row.insertCell(2);

    // Add timestamp field
    cell_time.innerHTML = `<input type='time' class='form-control ${instance} timestamp' id='${instance}-rule${next_row}-time' placeholder='HH:MM'>`;

    // Get instance type
    if (instance.startsWith("device")) {
        var type = document.getElementById(instance.replace("device", "deviceType")).value;
    } else {
        var type = document.getElementById(instance.replace("sensor", "sensorType")).value;
    };

    // Add appropriate input for given instance type
    if (type == "pir") {
        // Add range slider
        cell_value.innerHTML = `<div class="d-flex flex-row align-items-center my-2">
                                    <button id="${instance}-rule${next_row}-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-dash-lg"></i></button>
                                    <input id="${instance}-rule${next_row}" type="range" class="${instance} rule mx-auto" min="0" max="60" data-displaymin="0" data-displaymax="60" data-displaytype="float" step="0.5" value="{{rule}}" value="{{rule}}" autocomplete="off">
                                    <button id="${instance}-rule${next_row}-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-plus-lg"></i></button>
                                </div>`
        add_new_slider(`${instance}-rule${next_row}`);

    } else if (type == "si7021") {
        // Add range slider
        cell_value.innerHTML = `<div class="d-flex flex-row align-items-center my-2">
                                    <button id="${instance}-rule${next_row}-down" class="btn btn-sm me-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-dash-lg"></i></button>
                                    <input id="${instance}-rule${next_row}" type="range" class="${instance} rule mx-auto" min="65" max="80" data-displaymin="65" data-displaymax="80" data-displaytype="float" step="0.5" value="{{rule}}" value="{{rule}}" autocomplete="off">
                                    <button id="${instance}-rule${next_row}-up" class="btn btn-sm ms-1" onclick="rule_slider_increment(this);" data-stepsize="0.5"><i class="bi-plus-lg"></i></button>
                                </div>`
        add_new_slider(`${instance}-rule${next_row}`);

    } else if (type == "dimmer" || type == "bulb" || type == "pwm") {
        // Add text field for instances that take both enabled/disabled and integer
        cell_value.innerHTML = `<input type='text' class='form-control ${instance} rule' id='${instance}-rule${next_row}' placeholder=''>`;

    } else if (type == "switch" || type == "desktop" || type == "relay" || type == "dumb-relay" || type == "mosfet") {
        // Add dropdown for instances that only take enabled/disabled
        cell_value.innerHTML = `<select id="${instance}-rule${next_row}" class="form-select rule ${instance} autocomplete="off">
                                    <option>Select rule</option>
                                    <option value='enabled'>Enabled</option>
                                    <option value='disabled'>Disabled</option>
                                </select>`

    } else if (type == "dummy") {
        // Add dropdown with additional options for dummy
        cell_value.innerHTML = `<select id="${instance}-rule${next_row}" class="form-select rule ${instance} autocomplete="off">
                                    <option>Select rule</option>
                                    <option value='enabled'>Enabled</option>
                                    <option value='disabled'>Disabled</option>
                                    <option value='on'>On</option>
                                    <option value='off'>Off</option>
                                </select>`

    } else if (type == "api-target") {
        // Add button that opens rule modal + hidden input field that receives value from modal for ApiTarget
        cell_value.innerHTML = `<button id="${instance}-rule${next_row}-button" class="form-control" onclick="open_rule_modal(this);" type="button">Set rule</button>
                                <input type="text" class="form-control ${instance} rule" id="${instance}-rule${next_row}" placeholder="" style="display:none;">`
    };

    // Add delete button
    cell_del.innerHTML = `<button type='button' class='remove btn btn-sm btn-danger mt-1 ${instance}' id='${instance}-remove${next_row}' onclick='remove(this)'><i class="bi-x-lg"></i></button>`;
};

function remove(e) {
    var instance = e.id;
    var index = e.parentElement.parentElement.rowIndex

    table = document.getElementById(instance.split("-", 1) + "-rules")
    table.deleteRow(index)
};
