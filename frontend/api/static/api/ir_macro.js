// Stores actions from IR buttons clicked while recording macro
var new_macro_actions = [];


// Called by start recording button under macro name input
function start_recording_ir_macro() {
    // Change start button to finish button, disable input
    document.getElementById('start-recording').innerHTML = 'Save Macro';
    document.getElementById('start-recording').onclick = add_new_macro;
    document.getElementById('new-macro-name').disabled = true;

    // Replace send_command with function that appends commands to new_macro_actions
    window.send_command = record_macro_send_command;

    // Add glow effect on IR buttons, scroll into view
    Array.from(document.getElementsByClassName('ir-btn')).forEach(button => button.classList.add('blue-glow'));
    document.getElementById('ir-tv').scrollIntoView({behavior: 'smooth'})
};


// Replaces send_command while recording macro
function record_macro_send_command(value) {
    // Default to 100ms delay, no repeat
    new_macro_actions.push(`${value.ir_target} ${value.key} 100 1`);
};


// Called by submit button after recording new macro
async function add_new_macro() {
    // Submit new macro actions
    var result = await fetch('/add_ir_macro', {
        method: 'POST',
        body: JSON.stringify({
        ip: target_node,
        name: document.getElementById('new-macro-name').value,
        actions: new_macro_actions}),
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            "X-CSRFToken": getCookie('csrftoken')
        }
    });
    result = await result.json();

    // Refresh page
    location.reload();
};


// Store macro name + changes made to macro in edit modal
var editing_macro_name = "";
var editing_macro_actions = {};


// Called when user clicks edit IR macro button
// Adds existing macro actions to modal and shows
function populate_edit_modal(button) {
    // Add macro name to modal heading dataset attribute, variable
    document.getElementById('edit-ir-macro-title').innerHTML = `Editing ${button.dataset.name}`;
    editing_macro_name = button.dataset.name;

    // Parse actions string into array
    const actions = JSON.parse(button.dataset.actions.replace(/'/g, '"'));

    // Clear table contents, object used to track changes
    document.getElementById('edit-ir-macro-actions').innerHTML = "";
    editing_macro_actions = {};

    // Add table row for each existing macro action
    actions.forEach((action, index) => {
        const [target, key, delay, repeat] = action.split(' ');
        document.getElementById('edit-ir-macro-actions').insertAdjacentHTML('beforeend', `
        <tr>
            <td>${target} ${key}</td>
            <td class="edit-ir-macro-cell"><input type="text" class="form-control text-center" data-index="${index}" oninput="edit_action_delay(this);" value="${delay}"></td>
            <td class="edit-ir-macro-cell"><input type="text" class="form-control text-center" data-index="${index}" oninput="edit_action_repeat(this);" value="${repeat}"></td>
            <td><button id="delete_${index}" class="btn btn-sm btn-danger" data-index="${index}" onclick="delete_macro_action(this);"><i class="bi-trash"></i></button></td>
        </tr>`
        );

        // Add each action to object used to track changes
        // Convert action string to array so fields can be edited
        editing_macro_actions[index] = action.split(' ');
    })

    // Show modal
    editMacroModal.show();
};


// Called by delete button on each row of table
async function delete_macro_action(button) {
    // Remove row from table, remove action from object used to track changes
    button.parentElement.parentElement.remove();
    delete editing_macro_actions[button.dataset.index];

    // If last action deleted, delete macro and refresh page
    if (Object.keys(editing_macro_actions).length == 0) {
        await send_command({'command': 'ir_delete_macro', 'macro_name': editing_macro_name});
        location.reload();
    };
};


// Called when user edits value in delay input
function edit_action_delay(input) {
    // Overwrite delay field in object used to track changes
    editing_macro_actions[input.dataset.index][2] = input.value;
};


// Called when user edits value in repeat input
function edit_action_repeat(input) {
    // Overwrite repeat field in object used to track changes
    editing_macro_actions[input.dataset.index][3] = input.value;
};


// Called when user clicks edit IR macro submit button
async function edit_macro_submit(button) {
    // Convert action objects to strings with syntax "target key delay repeat"
    let payload = Object.values(editing_macro_actions).map(item => item.join(' '));

    // Submit new macro actions
    var result = await fetch('/edit_ir_macro', {
        method: 'POST',
        body: JSON.stringify({ip: target_node, name: editing_macro_name, actions: payload}),
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            "X-CSRFToken": getCookie('csrftoken')
        }
    });
    result = await result.json();

    // Refresh page
    location.reload();
};
