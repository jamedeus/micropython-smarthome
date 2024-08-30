import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { EditConfigContext } from 'root/EditConfigContext';
import ThermostatParamInputs from './ThermostatParamInputs';
import ThermostatRuleInput from 'inputs/ThermostatRuleInput';

const DefaultRuleThermostat = ({ id, instance, metadata }) => {
    const { handleInputChange } = useContext(EditConfigContext);

    // Get slider limits from metadata object
    const min_rule = parseFloat(metadata.rule_limits[0], 10);
    const max_rule = parseFloat(metadata.rule_limits[1], 10);

    // Handler for slider move events
    const onSliderMove = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    // Instantiate slider, convert metadata min/max (celsius) to configured units
    return (
        <>
            <div className="mb-2">
                <label className="w-100 fw-bold">
                    Default Rule
                </label>
                <ThermostatRuleInput
                    rule={String(instance.default_rule)}
                    setRule={onSliderMove}
                    min={min_rule}
                    max={max_rule}
                    units={instance.units ? instance.units : "celsius"}
                    sliderStep={0.1}
                />
            </div>
            <ThermostatParamInputs id={id} />
        </>
    );
};

DefaultRuleThermostat.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired,
    metadata: PropTypes.object.isRequired
};

export default DefaultRuleThermostat;
