import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import Table from 'react-bootstrap/Table';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import DeleteOrEditButton from 'inputs/DeleteOrEditButton';
import ApiTargetRuleButton from 'inputs/ApiTargetRuleButton';
import Button from 'react-bootstrap/Button';

const ScheduleRulesTable = ({ id, schedule }) => {
    const [showNewRule, setShowNewRule] = useState(false);

    // Rendered for each existing rule, pass existingRule=false for new rule row
    const ScheduleRuleRow = ({ id, originalTime='', originalRule='', existingRule=true }) => {
        // Get status object and API call hooks
        const {
            status,
            add_schedule_rule,
            edit_schedule_rule,
            delete_schedule_rule,
            apiTargetOptions
        } = useContext(ApiCardContext);

        // Get instance status section
        const instance = status[`${id.replace(/[0-9]/g, '')}s`][id];

        // Create states to store modified timestamp and rule
        const [newTime, setNewTime] = useState(originalTime);
        const [newRule, setNewRule] = useState(originalRule);

        // Create state for DeleteOrEditButton (values: delete, edit, loading)
        const [loadingButtonState, setLoadingButtonState] = useState('delete');

        // Called after input changes, sets appropriate button state
        const updateLoadingButton = (newTimestamp, newRuleValue) => {
            // Existing rules: Show edit button when either input changed
            if (existingRule) {
                if (newTimestamp != originalTime || newRuleValue != originalRule) {
                    setLoadingButtonState('edit');
                } else {
                    setLoadingButtonState('delete');
                }
            // New rule: Show edit button when both inputs have value
            } else {
                if (newTimestamp && newRuleValue) {
                    setLoadingButtonState('edit');
                } else {
                    setLoadingButtonState('delete');
                }
            }
        };

        // Called by TimeField when user changes value and closes
        const handleNewTimestamp = (newTimestamp, _) => {
            setNewTime(newTimestamp);
            updateLoadingButton(newTimestamp, newRule);
        };

        // Called by RuleField when user changes value and closes
        const handleNewRule = (newRuleValue, fade_rule, duration, range_rule) => {
            if (range_rule && fade_rule) {
                // Fade rule: Combine params into single string
                setNewRule(`fade/${newRuleValue}/${duration}`);
            } else {
                setNewRule(newRuleValue);
            }
            updateLoadingButton(newTime, newRuleValue);
        };

        // New rule field add button handler
        const addRule = async () => {
            // Start loading animation, post new rule to backend
            setLoadingButtonState('loading');
            const result = await add_schedule_rule(id, newTime, newRule);

            // If successful hide new rule field and reset inputs
            if (result) {
                setShowNewRule(false);
                setLoadingButtonState('delete');
                setNewTime('');
                setNewRule('');
            }
        };

        // New rule field delete button handler
        const hideNewRule = async () => {
            // Hide new rule field, reset inputs
            setShowNewRule(false);
            setNewTime('');
            setNewRule('');
        };

        // Existing rule field add button handler
        const editRule = () => {
            setLoadingButtonState('loading');
            edit_schedule_rule(id, originalTime, newTime, newRule);
        };

        // Existing rule field delete button handler
        const deleteRule = () => {
            setLoadingButtonState('loading');
            delete_schedule_rule(id, originalTime);
        };

        // Renders button that opens ApiTarget rule modal
        const ApiTargetRuleField = () => {
            // Receives stringified dropdown selection when modal submitted
            const handleSubmit = (newRule) => {
                handleNewRule(newRule, false, '', false);
            };

            return (
                <ApiTargetRuleButton
                    currentRule={newRule ? newRule : ''}
                    targetNodeOptions={apiTargetOptions[id]}
                    handleSubmit={handleSubmit}
                />
            );
        };

        return (
            <tr className={!existingRule && !showNewRule ? 'd-none' : ''}>
                <td>
                    <TimeField
                        timestamp={newTime}
                        handleChange={handleNewTimestamp}
                        schedule_keywords={status.metadata.schedule_keywords}
                        highlightInvalid={false}
                    />
                </td>
                <td>
                    {instance.type === 'api-target' ? (
                        <ApiTargetRuleField />
                    ) : (
                        <RuleField
                            instance={instance}
                            category={id.replace(/[0-9]/g, '')}
                            type={instance.type}
                            rule={newRule}
                            handleChange={handleNewRule}
                        />
                    )}
                </td>
                <td className="min">
                    <DeleteOrEditButton
                        status={loadingButtonState}
                        handleDelete={existingRule ? deleteRule : hideNewRule}
                        handleEdit={existingRule ? editRule : addRule}
                    />
                </td>
            </tr>
        );
    };

    ScheduleRuleRow.propTypes = {
        id: PropTypes.string,
        originalTime: PropTypes.string,
        originalRule: PropTypes.oneOfType([
            PropTypes.string,
            PropTypes.number,
            PropTypes.object,
        ]),
        existingRule: PropTypes.bool
    };


    return (
        <div className="collapse text-center" id={`${id}-schedule-rules`}>
            <Table borderless>
                <thead>
                    <tr>
                        <th className="w-50">Time</th>
                        <th className="w-50">Rule</th>
                    </tr>
                </thead>
                <tbody>
                    {Object.keys(schedule).map(time => {
                        return (
                            <ScheduleRuleRow
                                key={time}
                                id={id}
                                originalTime={time}
                                originalRule={schedule[time]}
                            />
                        );
                    })}
                    <ScheduleRuleRow
                        key={'new'}
                        id={id}
                        existingRule={false}

                    />
                </tbody>
            </Table>

            <div className="text-center mx-3 mb-3">
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setShowNewRule(true)}
                >
                    <i className="bi-plus-lg"></i>
                </Button>
            </div>
        </div>
    );
};

ScheduleRulesTable.propTypes = {
    id: PropTypes.string,
    schedule: PropTypes.object
};

export default ScheduleRulesTable;
