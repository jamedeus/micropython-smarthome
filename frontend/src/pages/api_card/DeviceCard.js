import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { DebugModalContext } from 'modals/DebugModal';
import { ApiCardContext } from 'root/ApiCardContext';
import { FadeContext } from 'modals/FadeModal';
import { ScheduleToggleContext } from 'modals/ScheduleToggleModal';
import InstanceCard from './InstanceCard';
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

    // Get function to open debug modal
    const { showDebugModal } = useContext(DebugModalContext);

    // Get function to open schedule toggle modal
    const { showScheduleToggle } = useContext(ScheduleToggleContext);

    // Get function to open fade modal
    const { showFadeModal } = useContext(FadeContext);

    // Create local state for prompt type (not included in
    // status updates, will remove nodes if allowed to update)
    const [prompt] = useState(params.prompt);

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
            {(() => {
                if (prompt === "int_or_fade") {
                    return (
                        <Dropdown.Item onClick={() => showFadeModal(id)}>
                            Start Fade
                        </Dropdown.Item>
                    )
                }
            })()}
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

DeviceCard.propTypes = {
    id: PropTypes.string
};


export default DeviceCard;
