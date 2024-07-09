import React, { useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { showDebugModal } from './DebugModal';
import { ApiCardContext } from 'root/ApiCardContext';
import { showScheduleToggle } from './ScheduleToggleModal';
import InstanceCard from './InstanceCard';
import { get_instance_metadata } from 'util/metadata';
import 'css/TriggerButton.css';

const TriggerButton = ({ on, onClick, disabled }) => {
    return (
        <Button
            variant="outline-primary"
            className={`trigger-button my-auto me-auto ${on ? 'trigger-on' : ''}`}
            onClick={onClick}
            disabled={disabled}
        >
            <i className="bi-exclamation-lg"></i>
        </Button>
    );
};

TriggerButton.propTypes = {
    on: PropTypes.bool,
    onClick: PropTypes.func.isRequired,
    disabled: PropTypes.bool.isRequired
};

const SensorCard = ({ id }) => {
    // Get function that returns status params, hooks to update status
    const {
        get_instance_section,
        enable_instance,
        trigger_sensor,
        set_rule,
        reset_rule
    } = useContext(ApiCardContext);

    // Get sensor status params, create local state
    const params = get_instance_section(id);
    const [localState, setlocalState] = useState({ ...params });

    // Create state that blocks automatic status updates while true
    const [editing, setEditing] = useState(false);

    // Update local state when upstream status changes unless user is modifying
    // inputs (apply updates immediately when editing switches back to false)
    useEffect(() => {
        if (!editing) {
            setlocalState(params);
        }
    }, [params, editing]);

    // Get metadata containing triggerable bool
    const [metadata] = useState(get_instance_metadata("sensor", params.type));

    // Rule slider handler
    const setRule = (newRule) => {
        // Prevent slider jumping if status updates while moving
        setEditing(true);
        // Set local state (move slider)
        setlocalState({ ...localState, current_rule: newRule });
        // Set upstream state (sends debounced API call to node)
        set_rule(id, newRule);
    };

    // Called when user releases click on slider, resumes status updates
    const onBlur = () => {
        setEditing(false);
    };

    const ActionButton = (
        <TriggerButton
            on={params.condition_met}
            onClick={() => trigger_sensor(id)}
            disabled={!metadata.triggerable}
        />
    );
    const DropdownOptions = (
        <>
            <Dropdown.Item
                onClick={() => enable_instance(id, !params.enabled)}
            >
                {params.enabled ? "Disable" : "Enable"}
            </Dropdown.Item>
            <Dropdown.Item onClick={() => showScheduleToggle(id, params.enabled)}>
                Schedule Toggle
            </Dropdown.Item>
            <Dropdown.Item
                disabled={params.current_rule === params.scheduled_rule}
                onClick={() => reset_rule(id)}
            >
                Reset rule
            </Dropdown.Item>
            <Dropdown.Item>Show targets</Dropdown.Item>
            <Dropdown.Item onClick={() => showDebugModal(id)}>
                Debug
            </Dropdown.Item>
        </>
    );

    return (
        <InstanceCard
            id={id}
            params={localState}
            actionButton={ActionButton}
            dropdownOptions={DropdownOptions}
            setRule={setRule}
            onBlur={onBlur}
        />
    );
};

SensorCard.propTypes = {
    id: PropTypes.string
};

export default SensorCard;
