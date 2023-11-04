// Hidden checkbox that determines whether IR Blaster added to config
const irblaster_configured = document.getElementById('irblaster_configured');

// Maps name of IR target to array of available keys
// TODO remove hardcoded keys once IrBlaster metadata written
ir_keys = {
    'tv': ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source'],
    'ac': ['start', 'stop', 'off']
}

// Called when user expands/collapses IR Blaster div
// Toggles hidden checkbox and adds/remove ir_blaster config section
function select_ir_blaster(button) {
    if (button.dataset.selected === 'true') {
        button.dataset.selected = 'false';
        irblaster_configured.checked = false;
        delete config['ir_blaster'];
    } else {
        button.dataset.selected = 'true';
        irblaster_configured.checked = true;
        config['ir_blaster'] = {
            'pin': get_input_element('ir_blaster', 'pin').value,
            'target': []
        };
    };
};


// Called when user checks/unchecks IR Blaster target, adds/removes target from config
function update_config_ir_target(input) {
    if (config.ir_blaster) {
        if (input.checked) {
            config['ir_blaster']['target'].push(input.dataset.target);
        } else {
            config['ir_blaster']['target'] = config['ir_blaster']['target'].filter(item => item !== input.dataset.target);
        };
    };
};
