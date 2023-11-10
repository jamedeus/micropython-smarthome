// Listens on name input, warns when duplicate name entered
async function prevent_duplicate_friendly_name(el) {
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


// Input listener for all nickname fields, adds red highlight if nickname is duplicate
function prevent_duplicate_nickname(event) {
    // Get ID of modified input (prevent comparing against self)
    const id = event.target.dataset.section;

    // Get nickname that user just entered
    const nickname = event.target.value;

    // Get all existing nicknames in lowercase (case-insensitive comparison)
    const existingNicknames = Object.entries(config).filter(([key, value]) => {
        // Select all keys with nickname attribute except current target
        return value.nickname && key !== id;
    }).map(([key, value]) => value.nickname.toLowerCase());

    // Add invalid highlight + listener to remove if nickname is duplicate
    if (existingNicknames.includes(nickname.toLowerCase())) {
        event.target.classList.add('is-invalid');
        event.target.addEventListener("input", (e) => {
            e.target.classList.remove("is-invalid");
        }, { once: true });
    };
};


// Input listener for floor field, prevents entering letters + limits to 3 digits
function prevent_non_numeric(event) {
    event.target.value = event.target.value.replace(/[^\d]/g, '').substring(0,3);
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
                };
            });
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


// Highlight fields that fail regex, add listener to remove highlight on input
function validateField(event) {
    if (!event.target.validity.valid) {
        event.target.classList.add('is-invalid');
        event.target.addEventListener("input", (e) => {
            e.target.classList.remove("is-invalid");
        }, { once: true });
    };
};
// Validate fields when focus leaves
document.querySelectorAll('.validate').forEach(input => input.addEventListener('blur', validateField));


// Constrain rule max/min fields to valid integer range
function ruleLimits(event) {
    // Read absolute limits from dataset attributes
    const min = parseInt(event.target.dataset.min);
    const max = parseInt(event.target.dataset.max);

    // Remove everything except digits
    let input = parseInt(event.target.value.replace(/[^\d]/g, ''));
    // Constrain to limits from dataset
    if (input > max) {
        input = max;
    } else if (input < min) {
        input = min;
    } else if (isNaN(input)) {
        input = "";
    };

    event.target.value = input;
};
document.querySelectorAll('.rule-limits').forEach(input => input.addEventListener('input', ruleLimits));


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


// Checks if Thermostat selected in any dropdowns (cannot have multiple)
// Disables all Thermostat options if already selected, otherwise enables
// Runs on load and when user selects a sensor type
function preventDuplicateThermostat() {
    // Check if Thermostat selected in any sensor dropdown
    const sensors = [...document.getElementsByClassName("sensorType")];
    thermostat_configured = sensors.some(sensor => sensor.value === "si7021");

    // If Thermostat selected disable option in all dropdowns, otherwise enable
    // Runs every time to catch type change from Thermostat to other
    document.querySelectorAll(".sensorType option[value='si7021']").forEach(
        option => option.disabled = thermostat_configured
    );
}
var thermostat_configured = false;
preventDuplicateThermostat();


// Takes temperature, old units, new units (options: celsius, fahrenheit, kelvin)
function convert_temperature(temperature, old_units, new_units) {
    // First convert to Celsius
    if (old_units.toLowerCase() == 'fahrenheit') {
        temperature = (temperature - 32) * 5 / 9;
    } else if (old_units.toLowerCase() == 'kelvin') {
        temperature = temperature - 273.15
    };

    // Convert Celsius to requested units
    if (new_units.toLowerCase() == 'fahrenheit') {
        temperature = temperature * 1.8 + 32;
    } else if (new_units.toLowerCase() == 'kelvin') {
        temperature = temperature + 273.15;
    };

    return temperature.toFixed(1);
};


// Handler for thermostat units dropdown, converts units displayed on rule sliders
function update_thermostat_slider(input) {
    // Get target sensor ID, config param, selected units, reference to rule slider
    // Get target sensor ID, old units, new units
    const target = input.dataset.section;
    const new_units = input.value;
    old_units = config[target]['units'];

    // Get reference to slider, convert slider value to new units
    const slider = document.querySelector(`[data-section="${target}"][data-param="default_rule"]`);
    const old_rule = slider.value;
    const new_rule = convert_temperature(parseFloat(old_rule), old_units, new_units);

    // Change slider limits to new units
    if (new_units == 'celsius') {
        slider.min = 18;
        slider.max = 27;
        slider.dataset.displaymin = 18;
        slider.dataset.displaymax = 27;

    } else if (new_units == 'kelvin') {
        slider.min = 291.15;
        slider.max = 300.15;
        slider.dataset.displaymin = 291.15;
        slider.dataset.displaymax = 300.15;

    } else if (new_units == 'fahrenheit') {
        slider.min = 65;
        slider.max = 80;
        slider.dataset.displaymin = 65;
        slider.dataset.displaymax = 80;
    };

    // Update slider value and config object to new units
    slider.value = new_rule;
    config[target]['default_rule'] = new_rule;

    // Re-initialize slider so changes take effect
    $('input[type="range"]').rangeslider('update', true);
    const trigger = new Event('input');
    slider.dispatchEvent(trigger);

    console.log(`Old units: ${old_units}, New units: ${new_units}`);
    console.log(`Old rule: ${old_rule}, New rule: ${new_rule}`);
};
