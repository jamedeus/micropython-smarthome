import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { parse_dom_context } from 'util/django_util';

export const MetadataContext = createContext();

export const MetadataContextProvider = ({ children }) => {
    // Takes metadata entry, replaces "placeholder" with "" in config template
    // TODO probably not necessary to use placeholder in metadata anyway
    // Think only config_generator.py relies on them, can just check for "" instead
    const remove_placeholders = (template) => {
        for (let param in template.config_template) {
            if (template.config_template[param] === "placeholder") {
                template.config_template[param] = "";
            }
        }
        return template;
    };

    // Get device/sensor metadata object, contains rule types and config templates
    // Edit_config appends config template to state when device/sensor type selected
    // Rule prompts and limits used to render correct inputs, set slider ranges, etc
    const [metadata] = useState(() => {
        const metadata = parse_dom_context("instance_metadata");

        /* istanbul ignore else */
        if (metadata) {
            // Remove "placeholder" string from config templates in metadata object
            for (let device in metadata.devices) {
                metadata.devices[device] = remove_placeholders(metadata.devices[device]);
            }
            for (let sensor in metadata.sensors) {
                metadata.sensors[sensor] = remove_placeholders(metadata.sensors[sensor]);
            }
        }

        return metadata;
    });

    // Takes category ("device" or "sensor") and type, returns full metadata object
    // Creates deep copy so modifying object does not affect other components
    const get_instance_metadata = (category, type) => {
        return { ...metadata[`${category}s`][type],
            config_template: get_config_template(category, type)
        };
    };

    // Takes category ("device" or "sensor") and type, returns config template
    // Creates copy so modifying template does not affect other components
    const get_config_template = (category, type) => {
        if (category && type) {
            return { ...metadata[`${category}s`][type]['config_template'] };
        } else {
            return null;
        }
    };

    return (
        <MetadataContext.Provider value={{ metadata, get_instance_metadata }}>
            {children}
        </MetadataContext.Provider>
    );
};

MetadataContextProvider.propTypes = {
    children: PropTypes.node,
};
