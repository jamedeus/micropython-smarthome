// Get device/sensor metadata object, used to determine input elements for each type
// Contains config templates for each device/sensor, added to output object when selected
var metadata = JSON.parse(document.getElementById("instance_metadata").textContent);


// Takes category ("device" or "sensor") and type, returns full metadata object
function get_instance_metadata(category, type) {
    return metadata[`${category}s`][type];
};


// Takes category ("device" or "sensor") and type, returns config template
function get_config_template(category, type) {
    return metadata[`${category}s`][type]['config_template'];
};


// Takes category ("device" or "sensor"), returns array of dropdown options
// containing every driver type in category
function get_type_dropdown_options(category) {
    return Object.entries(metadata[`${category}s`]).map(([key, type]) => (
        <option key={key} value={type.config_name}>{type.class_name}</option>
    ));
};


export { get_instance_metadata, get_config_template, get_type_dropdown_options };
