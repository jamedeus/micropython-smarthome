// Hidden checkbox that determines whether IR Blaster added to config
const irblaster_configured = document.getElementById('irblaster_configured');

// Set correct config section for IR Blaster pin input
document.getElementById('device0-pin').dataset.section = 'ir_blaster';

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
            'pin': document.getElementById('device0-pin').value,
            'target': []
        };
    };
};

// Called when user checks/unchecks IR Blaster target, adds/removes target from config
function update_config_ir_target(input) {
    if (config.ir_blaster) {
        const target = input.id.split('-')[1];
        if (input.checked) {
            config['ir_blaster']['target'].push(target);
        } else {
            config['ir_blaster']['target'] = config['ir_blaster']['target'].filter(item => item !== target);
        };
    };
};
