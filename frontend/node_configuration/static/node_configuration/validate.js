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
    const id = event.target.id.split("-")[0];

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
