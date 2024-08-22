import React, { useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import DeleteOrEditButton from 'inputs/DeleteOrEditButton';
import ApiTargetRuleButton from 'inputs/ApiTargetRuleButton';
import { showErrorToast } from 'util/ErrorToast';

// Rendered for each existing rule, pass existingRule=false for new rule row
const ScheduleRuleRow = ({
    id,
    instance,
    originalTime='',
    originalRule='',
    existingRule=true,
    showNewRule,
    setShowNewRule
}) => {
    // Get API call hooks
    const {
        status,
        add_schedule_rule,
        edit_schedule_rule,
        delete_schedule_rule,
        apiTargetOptions
    } = useContext(ApiCardContext);

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

    // Update loading button state when inputs change
    useEffect(() => {
        updateLoadingButton(newTime, newRule);
    }, [newTime, newRule]);

    // New rule field add button handler
    const addRule = async () => {
        // Start loading animation, post new rule to backend
        setLoadingButtonState('loading');
        const success = await add_schedule_rule(id, newTime, newRule);

        // If successful hide new rule field and reset inputs
        if (success) {
            setShowNewRule(false);
            setLoadingButtonState('delete');
            setNewTime('');
            setNewRule('');
        } else {
            showErrorToast('Failed to add schedule rule');
            setLoadingButtonState('edit');
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
    const editRule = async () => {
        setLoadingButtonState('loading');
        const success = await edit_schedule_rule(id, originalTime, newTime, newRule);
        if (success) {
            setLoadingButtonState('delete');
        } else {
            showErrorToast('Failed to edit schedule rule');
            setLoadingButtonState('edit');
        }
    };

    // Existing rule field delete button handler
    const deleteRule = async () => {
        setLoadingButtonState('loading');
        const success = await delete_schedule_rule(id, originalTime);
        if (!success) {
            showErrorToast('Failed to delete schedule rule');
            setLoadingButtonState('delete');
        }
    };

    // Renders button that opens ApiTarget rule modal
    const ApiTargetRuleField = () => {
        return (
            <ApiTargetRuleButton
                currentRule={newRule}
                targetNodeOptions={apiTargetOptions[id]}
                handleSubmit={setNewRule}
            />
        );
    };

    return (
        <tr className={!existingRule && !showNewRule ? 'd-none' : ''}>
            <td>
                <TimeField
                    timestamp={newTime}
                    setTimestamp={setNewTime}
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
                        setRule={setNewRule}
                    />
                )}
            </td>
            <td className="min">
                <DeleteOrEditButton
                    status={loadingButtonState}
                    handleDelete={existingRule ? deleteRule : hideNewRule}
                    handleEdit={existingRule ? editRule : addRule}
                    disabled={existingRule && !newTime}
                    editIcon={existingRule ? "bi-pencil" : "bi-plus-lg"}
                />
            </td>
        </tr>
    );
};

ScheduleRuleRow.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired,
    originalTime: PropTypes.string,
    originalRule: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.object,
    ]),
    existingRule: PropTypes.bool,
    showNewRule: PropTypes.bool.isRequired,
    setShowNewRule: PropTypes.func.isRequired
};

const ScheduleRulesTable = ({ id, instance, openCollapse }) => {
    const [showNewRule, setShowNewRule] = useState(false);

    return (
        <Collapse in={openCollapse} className="text-center">
            <div>
                <Table borderless>
                    <thead>
                        <tr>
                            <th className="w-50">Time</th>
                            <th className="w-50">Rule</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(instance.schedule).map(([time, rule]) => {
                            return (
                                <ScheduleRuleRow
                                    key={`${time}-${rule}`}
                                    id={id}
                                    instance={instance}
                                    originalTime={time}
                                    originalRule={rule}
                                    showNewRule={showNewRule}
                                    setShowNewRule={setShowNewRule}
                                />
                            );
                        })}
                        <ScheduleRuleRow
                            key={'new'}
                            id={id}
                            instance={instance}
                            existingRule={false}
                            showNewRule={showNewRule}
                            setShowNewRule={setShowNewRule}
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
        </Collapse>
    );
};

ScheduleRulesTable.propTypes = {
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired,
    openCollapse: PropTypes.bool.isRequired
};

export default ScheduleRulesTable;
