// Listens on name input, warns when duplicate name entered
async function check_duplicate(el) {
    // Skip check if editing and name is original name
    if (!edit_existing || el.value.toLowerCase() != orig_name) {
        // Send input value to backend
        response = await send_post_request('/check_duplicate', {'name': el.value})

        // If name is duplicate, add invalid highlight + listener to remove highlight
        if (!response.ok) {
            el.classList.add('is-invalid');
            el.addEventListener("input", (e) => {
                e.target.classList.remove("is-invalid");
            }, { once: true });
        };
    };
};

// Called on input for all nickname fields, highlight red if same as existing nickname
function prevent_duplicate_nickname(event) {
    // Get ID of modified input (prevent comparing against self)
    const id = event.target.id.split("-")[0];

    // Iterate all other devices/sensors, check if identical name exists
    for (const category in instances) {
        for (const item in instances[category]) {
            // If not same instance and same nickname, add highlight + listener to remove
            if (item != id && instances[category][item].nickname.toLowerCase() == event.target.value.toLowerCase()) {
                event.target.classList.add('is-invalid');
                event.target.addEventListener("input", (e) => {
                    e.target.classList.remove("is-invalid");
                }, { once: true });
            };
        };
    };
};

// Called when pin is selected, disables same pin in all other dropdowns to prevent duplicates
function pinSelected(element) {
    const dropdowns = document.querySelectorAll('.pin-select');
    const usedPins = new Set();

    // Get all pins currently selected
    dropdowns.forEach(dropdown => {
        if (dropdown.value) {
            usedPins.add(dropdown.value);
        }
    });

    // Disable selected pins in all other dropdowns
    dropdowns.forEach(dropdown => {
        if (dropdown !== element) {
        const currentValue = dropdown.value;
        dropdown.querySelectorAll('option').forEach(option => {
            // Disable if pin already used, enable if available
            if (option.value && !usedPins.has(option.value)) {
                option.disabled = false;
            } else if (option.value && option.value !== currentValue) {
                option.disabled = true;
            }});
        };
    });
};

// Iterate all pin dropdowns and disable already-used pins
function preventDuplicatePins() {
    dropdowns = document.querySelectorAll('.pin-select');
    dropdowns.forEach(dropdown => {
        pinSelected(dropdown);
    });
};
// Run on load if editing
if (edit_existing) { preventDuplicatePins() };

// Format IP address as user types in field
function formatIp(event) {
    // Backspace and delete bypass formatting
    if (event.inputType === 'deleteContentBackward' || event.inputType === 'deleteContentForward') { return };

    // Remove everything except digits and period, 15 char max
    const input = event.target.value.replace(/[^\d.]/g, '').substring(0,15);;
    let output = '';
    let block = '';

    // Iterate input and format character by character
    for (let i = 0; i < input.length; i++) {
        const char = input[i];

        // Delimiter character handling
        if (char === '.') {
            // Drop if first char is delim, otherwise add to end of current block + start new block
            if (block.length > 0) {
                output += block + '.';
                block = '';
            };

        // Numeric character handling
        } else {
            // Add to current block
            block += char;
            // If current block reached limit, add to output + start new block
            if (block.length === 3) {
                output += block + '.';
                block = '';
            };
        };
    };

    // Add final block
    output += block;

    // Prevent >4 blocks (char limit may not be reached if single-digit blocks present)
    output = output.split('.').slice(0, 4).join('.');

    // Replace field contents with formatted string
    event.target.value = output;
};
// Add listener to all IP fields
document.querySelectorAll('.ip-input').forEach(input => input.addEventListener('input', formatIp));

// Highlight IP fields that fail regex
function validateIp(event) {
    if (!event.target.validity.valid) {
        event.target.classList.add('is-invalid');
        event.target.addEventListener("input", (e) => {
            e.target.classList.remove("is-invalid");
        }, { once: true });
    };
};
// Validate IP fields when focus leaves
document.querySelectorAll('.ip-input').forEach(input => input.addEventListener('blur', validateIp));

// Constrain PWM max/min fields to valid integer range
function pwmLimits(event) {
    // Remove everything except digits, 4 digit max
    let input = parseInt(event.target.value.replace(/[^\d]/g, '').substring(0,4));
    if (input > 1023) {
        input = 1023;
    } else if (input < 0) {
        input = 0;
    } else if (isNaN(input)) {
        input = "";
    };

    event.target.value = input;
};
document.querySelectorAll('.pwm-limits').forEach(input => input.addEventListener('input', pwmLimits));

// Constrain Thermostat tolerance field to 0.1 - 10.0 degrees
function thermostatToleranceLimit(event) {
    // Skip if key was backsace, delete, or period
    if (event.inputType === 'deleteContentBackward' || event.inputType === 'deleteContentForward' || event.data == ".") { return };

    // Remove everything except digits and period, 4 digit max
    let input = parseFloat(event.target.value.replace(/[^\d.]/g, '').substring(0,4));
    if (input > 10) {
        input = 10;
    } else if (input < 0.1) {
        input = 0.1
    } else if (isNaN(input)) {
        input = "";
    };

    event.target.value = input;
};
document.querySelectorAll('.thermostat').forEach(input => input.addEventListener('input', thermostatToleranceLimit));
