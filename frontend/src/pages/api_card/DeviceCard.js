import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { showDebugModal } from 'modals/DebugModal';
import { ApiCardContext } from 'root/ApiCardContext';
import { showFadeModal } from 'modals/FadeModal';
import { showScheduleToggle } from 'modals/ScheduleToggleModal';
import InstanceCard from './InstanceCard';
import ChangeApiTargetRule from './ChangeApiTargetRule';
import { get_instance_metadata } from 'util/metadata';
import 'css/PowerButton.css';


const PowerButton = ({ on, onClick }) => {
    return (
        <Button
            variant="outline-primary"
            className={on ? "power-button my-auto me-auto toggle-on" : "power-button my-auto me-auto"}
            onClick={onClick}
        >
            <i className="bi-lightbulb"></i>
        </Button>
    );
};

PowerButton.propTypes = {
    on: PropTypes.bool,
    onClick: PropTypes.func
};


const DeviceCard = ({ id }) => {
    // Get status object
    const {status, enable_instance, turn_on, reset_rule} = useContext(ApiCardContext);
    const params = status["devices"][id];

    // Get metadata containing rule_prompt
    const [metadata] = useState(get_instance_metadata(
        id.startsWith("device") ? "device" : "sensor",
        params.type
    ));

    // Create callback for power button
    const turn_on_off = () => {
        turn_on(id, !params.turned_on);
    };


    const ActionButton = <PowerButton on={params.turned_on} onClick={turn_on_off} />;
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
            {metadata.rule_prompt === "int_or_fade" ? (
                <Dropdown.Item onClick={() => showFadeModal(id)}>
                    Start Fade
                </Dropdown.Item>
            ) : ( null )}
            {params.type === "api-target" ? (
                <ChangeApiTargetRule id={id} rule={params.current_rule} />
            ) : (null) }
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

DeviceCard.propTypes = {
    id: PropTypes.string
};


export default DeviceCard;
