import React from 'react';

// Map IR Blaster targets to list of key options
// TODO remove once IR Blaster metadata added
const ir_keys = {
    'tv': ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source'],
    'ac': ['start', 'stop', 'off']
};

// Get device/sensor metadata object, used to determine input elements for each type
// Contains config templates for each device/sensor, added to output object when selected
let metadata = JSON.parse(document.getElementById("instance_metadata").textContent);


// Takes metadata entry, replaces "placeholder" with "" in config template
// TODO probably not necessary to use placeholder in metadata anyway
// Think only config_generator.py relies on them, can just check for "" instead
function remove_placeholders(template) {
    for (let param in template.config_template) {
        if (template.config_template[param] === "placeholder") {
            template.config_template[param] = "";
        }
    }
    return template;
}


// Remove "placeholder" string from config templates in metadata object
for (let device in metadata.devices) {
    metadata["devices"][device] = remove_placeholders(metadata["devices"][device]);
}
for (let sensor in metadata.sensors) {
    metadata["sensors"][sensor] = remove_placeholders(metadata["sensors"][sensor]);
}


// Takes category ("device" or "sensor") and type, returns full metadata object
// Creates deep copy so modifying object does not affect other components
function get_instance_metadata(category, type) {
    return { ...metadata[`${category}s`][type],
        config_template: get_config_template(category, type)
    };
}


// Takes category ("device" or "sensor") and type, returns config template
// Creates copy so modifying template does not affect other components
function get_config_template(category, type) {
    if (category && type) {
        return { ...metadata[`${category}s`][type]['config_template'] };
    } else {
        return null;
    }
}


// Takes category ("device" or "sensor"), returns array of dropdown options
// containing every driver type in category.
// Optional exclude array can contain config_names that should be skipped.
function get_type_dropdown_options(category, exclude=[]) {
    return Object.entries(metadata[`${category}s`])
        .filter(([key, _]) =>
            !exclude.includes(key)
        ).map(([key, type]) => (
            <option key={key} value={type.config_name}>{type.class_name}</option>
        ));
}


export { ir_keys, get_instance_metadata, get_config_template, get_type_dropdown_options };
