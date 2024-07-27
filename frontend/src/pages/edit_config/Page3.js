import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import { EditConfigContext } from 'root/EditConfigContext';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import ApiTargetRuleButton from 'inputs/ApiTargetRuleButton';

const Page3 = () => {
    // Get curent state + callback functions from context
    const {
        config,
        handleInputChange,
        getTargetNodeOptions,
        highlightInvalid
    } = useContext(EditConfigContext);

    const deleteRule = (instance, timestamp) => {
        let rules = { ...config[instance]["schedule"] };
        delete rules[timestamp];
        handleInputChange(instance, "schedule", rules);
    };

    // Handler for add rule button, creates new row
    const addNewRuleRow = (instance) => {
        // Get existing rules
        const rules = { ...config[instance]["schedule"] };

        // Add rule with blank timestamp, default_rule value
        rules[""] = config[instance]["default_rule"];
        handleInputChange(instance, "schedule", rules);
    };

    // Takes instance ID (device1, sensor3, etc) and rule timestamp
    // Returns table row with timestamp and rule columns + edit button
    const ScheduleRuleRow = ({ instance, timestamp, rule }) => {
        // Create local states for popup inputs (also shown on table cells)
        // Prevents full page re-render (closes popup) on each keystroke
        const [localTimestamp, setLocalTimestamp] = useState(timestamp);
        const [localRule, setLocalRule] = useState(rule);

        // Called when timestamp popup closes, updates main state (re-render)
        const handleCloseTime = () => {
            // Only update state if timestamp changed
            if (localTimestamp != timestamp) {
                // Get existing rules, value of edited rule
                const rules = { ...config[instance]["schedule"] };
                const rule_value = rules[timestamp];

                // Delete original timestamp, add new, update state
                delete rules[timestamp];
                rules[localTimestamp] = rule_value;
                handleInputChange(instance, "schedule", rules);
            }
        };

        // Called when rule popup closes, updates main state (re-render)
        const handleCloseRule = () => {
            // Only update state if rule changed
            if (localRule != rule) {
                const newRules = { ...config[instance]["schedule"],
                    [timestamp]: localRule
                };
                handleInputChange(instance, "schedule", newRules);
            }
        };

        // Renders button that opens ApiTargetRuleModal
        const ApiTargetRuleField = () => {
            // Get dropdown options for current target IP
            const options = getTargetNodeOptions(config[instance]['ip']);

            // Receives stringified dropdown selection when modal submitted
            const handleSubmit = (newRule) => {
                const newScheduleRules = { ...config[instance]["schedule"],
                    [timestamp]: newRule
                };
                handleInputChange(instance, "schedule", newScheduleRules);
            };

            return (
                <ApiTargetRuleButton
                    currentRule={rule}
                    targetNodeOptions={options}
                    handleSubmit={handleSubmit}
                />
            );
        };

        return (
            <tr>
                <td className="schedule-rule-field">
                    <TimeField
                        timestamp={localTimestamp}
                        setTimestamp={setLocalTimestamp}
                        schedule_keywords={config.metadata.schedule_keywords}
                        highlightInvalid={highlightInvalid}
                        handleClose={handleCloseTime}
                    />
                </td>
                <td className="schedule-rule-field">
                    {/* ApiTarget: Button to open modal, otherwise RuleField */}
                    {config[instance]['_type'] === "api-target" ? (
                        <ApiTargetRuleField />
                    ) : (
                        <RuleField
                            instance={config[instance]}
                            category={instance.replace(/[0-9]/g, '')}
                            type={config[instance]._type}
                            rule={localRule}
                            setRule={setLocalRule}
                            handleClose={handleCloseRule}
                        />
                    )}
                </td>
                <td className="min">
                    <Button
                        variant="danger"
                        size="sm"
                        className="mb-1"
                        onClick={() => deleteRule(instance, timestamp)}
                    >
                        <i className="bi bi-trash-fill"></i>
                    </Button>
                </td>
            </tr>
        );
    };

    ScheduleRuleRow.propTypes = {
        instance: PropTypes.string.isRequired,
        timestamp: PropTypes.string.isRequired,
        rule: PropTypes.oneOfType([
            PropTypes.string,
            PropTypes.number,
            PropTypes.object,
        ]).isRequired
    };

    const RulesTable = ({ instance }) => {
        const rules = config[instance]["schedule"];

        return (
            <Table className="table-borderless">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Rule</th>
                        <th></th>
                    </tr>
                    {Object.entries(rules).map(([timestamp, rule]) => {
                        return (
                            <ScheduleRuleRow
                                key={timestamp}
                                instance={instance}
                                timestamp={timestamp}
                                rule={rule}
                            />
                        );
                    })}
                </thead>
            </Table>
        );
    };

    RulesTable.propTypes = {
        instance: PropTypes.string.isRequired
    };

    // Takes instance ID (device1, sensor3, etc), returns schedule rule card
    const ScheduleRuleSection = ({ instance }) => {
        const instanceNickname = config[instance]["nickname"];
        const instanceType = config[instance]["_type"];

        return (
            <Card key={`${instance}-schedule-rules`} className="mb-4">
                <Card.Body className="text-center">
                    <h6 className="fw-bold">
                        {instanceNickname} ({instanceType})
                    </h6>
                    {Object.entries(config[instance]['schedule']).length ?
                        <RulesTable instance={instance} /> : null
                    }
                    <Button
                        variant="secondary"
                        onClick={() => addNewRuleRow(instance)}
                    >
                        Add Rule
                    </Button>
                </Card.Body>
            </Card>
        );
    };

    ScheduleRuleSection.propTypes = {
        instance: PropTypes.string.isRequired
    };

    return (
        <>
            <h3>Add schedule rules (optional)</h3>
            {Object.keys(config).sort().map(instance => {
                if (instance.startsWith("device") || instance.startsWith("sensor")) {
                    return (
                        <ScheduleRuleSection
                            key={instance}
                            instance={instance}
                        />
                    );
                }
            })}
        </>
    );
};

export default Page3;
