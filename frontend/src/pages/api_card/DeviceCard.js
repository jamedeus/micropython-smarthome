import React, { useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { showDebugModal } from './DebugModal';
import { ApiCardContext } from 'root/ApiCardContext';
import { showFadeModal } from './FadeModal';
import { showScheduleToggle } from './ScheduleToggleModal';
import InstanceCard from './InstanceCard';
import ChangeApiTargetRule from './ChangeApiTargetRule';
import { get_instance_metadata } from 'util/metadata';
import 'css/PowerButton.css';

const PowerButton = ({ on, onClick }) => {
    return (
        <Button
            variant="outline-primary"
            className={`power-button my-auto me-auto ${on ? 'toggle-on' : ''}`}
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
    // Get function that returns status params, hooks to update status
    const {
        get_instance_section,
        enable_instance,
        turn_on,
        set_rule,
        reset_rule
    } = useContext(ApiCardContext);

    // Get device status params, create local state
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

    // Get metadata containing rule_prompt
    const [metadata] = useState(get_instance_metadata("device", params.type));

    // Create callback for power button
    const turn_on_off = () => {
        turn_on(id, !params.turned_on);
    };

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
            params={localState}
            actionButton={ActionButton}
            dropdownOptions={DropdownOptions}
            setRule={setRule}
            onBlur={onBlur}
        />
    );
};

DeviceCard.propTypes = {
    id: PropTypes.string
};

export default DeviceCard;
