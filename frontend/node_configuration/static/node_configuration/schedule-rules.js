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
    cell_time.innerHTML = `<input type='text' class='form-control ${instance} timestamp' id='schedule-${instance}-rule${next_row}-time' placeholder='HH:MM'>`;

    // For ApiTarget, add button that opens rule modal + hidden input field that receives value from modal
    if (instance.startsWith("device") && document.getElementById(instance.replace("device", "deviceType")).value == "api-target") {
        cell_value.innerHTML = `<button id="schedule-${instance}-rule${next_row}-button" class="form-control" onclick="open_rule_modal(this);" type="button">Set rule</button>
                                <input type="text" class="form-control ${instance} rule" id="schedule-${instance}-rule${next_row}-value" placeholder="" style="display:none;">`

    // For all other instance types, add input field
    } else {
        cell_value.innerHTML = `<input type='text' class='form-control ${instance} rule' id='schedule-${instance}-rule${next_row}-value' placeholder=''>`;
    };

    // Add delete button
    cell_del.innerHTML = `<button type='button' class='remove btn btn-danger' id='${instance}-remove${next_row}' onclick='remove(this)'>X</button>`;
};

function remove(e) {
    var instance = e.id;
    var index = e.parentElement.parentElement.rowIndex

    table = document.getElementById(instance.split("-", 1) + "-rules")
    table.deleteRow(index)
};
