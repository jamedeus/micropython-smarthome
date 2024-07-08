import React, { useState, useContext } from 'react';
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
            className={on ? "trigger-button my-auto me-auto trigger-on" : "trigger-button my-auto me-auto"}
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
    // Get status object
    const {status, enable_instance, trigger_sensor, reset_rule} = useContext(ApiCardContext);
    const params = status["sensors"][id];

    // Get metadata containing triggerable bool
    const [metadata] = useState(get_instance_metadata("sensor", params.type));

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
            params={params}
            actionButton={ActionButton}
            dropdownOptions={DropdownOptions}
        />
    );
};

SensorCard.propTypes = {
    id: PropTypes.string
};

export default SensorCard;
