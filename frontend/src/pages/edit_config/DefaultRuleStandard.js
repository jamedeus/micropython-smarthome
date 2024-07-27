import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { EditConfigContext } from 'root/EditConfigContext';
import StandardRuleInput from 'inputs/StandardRuleInput';

const DefaultRuleStandard = ({ id, instance }) => {
    const { handleInputChange, highlightInvalid } = useContext(EditConfigContext);

    const onChange = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    return (
        <StandardRuleInput
            rule={instance.default_rule}
            setRule={onChange}
            label="Default Rule"
            isInvalid={(highlightInvalid && !instance.default_rule)}
        />
    );
};

DefaultRuleStandard.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired
};

export default DefaultRuleStandard;
