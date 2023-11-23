// Takes 2 numbers (int, float, or string) and returns average
function average(a, b) {
    try {
        return parseInt((parseFloat(a) + parseFloat(b)) / 2);
    } catch(err) {
        console.log(err);
    };
};


// Takes temperature, old units, new units (options: celsius, fahrenheit, kelvin)
function convert_temperature(temperature, old_units, new_units) {
    // First convert to Celsius
    if (old_units.toLowerCase() == 'fahrenheit') {
        temperature = (parseFloat(temperature) - 32) * 5 / 9;
    } else if (old_units.toLowerCase() == 'kelvin') {
        temperature = parseFloat(temperature) - 273.15
    };

    // Convert Celsius to requested units
    if (new_units.toLowerCase() == 'fahrenheit') {
        temperature = parseFloat(temperature) * 1.8 + 32;
    } else if (new_units.toLowerCase() == 'kelvin') {
        temperature = parseFloat(temperature) + 273.15;
    };

    return parseFloat(temperature);
};


export { average, convert_temperature };
