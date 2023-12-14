import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { DebugModalContext } from 'modals/DebugModal';
import { ApiCardContext } from 'root/ApiCardContext';
import { ScheduleToggleContext } from 'modals/ScheduleToggleModal';
import InstanceCard from './InstanceCard';
import 'css/TriggerButton.css';


const TriggerButton = ({ on, onClick }) => {
    return (
        <Button
            variant="outline-primary"
            className={on ? "trigger-button my-auto me-auto trigger-on" : "trigger-button my-auto me-auto"}
            onClick={onClick}
        >
            <i className="bi-exclamation-lg"></i>
        </Button>
    );
};

TriggerButton.propTypes = {
    on: PropTypes.bool,
    onClick: PropTypes.func
};


const SensorCard = ({ id }) => {
    // Get status object
    const {status, enable_instance, trigger_sensor, reset_rule} = useContext(ApiCardContext);
    const params = status["sensors"][id];

    // Get function to open debug modal
    const { showDebugModal } = useContext(DebugModalContext);

    // Get function to open schedule toggle modal
    const { showScheduleToggle } = useContext(ScheduleToggleContext);

    // Create callback for trigger button
    const trigger = () => {
        trigger_sensor(id);
    };

    const ActionButton = <TriggerButton on={params.condition_met} onClick={trigger} />;
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

    return <InstanceCard
                id={id}
                params={params}
                actionButton={ActionButton}
                dropdownOptions={DropdownOptions}
            />;
};

SensorCard.propTypes = {
    id: PropTypes.string
};


export default SensorCard;
