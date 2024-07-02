import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import { ApiTargetModalContext } from 'modals/ApiTargetRuleModal';


const Page3 = () => {
    // Get curent state + callback functions from context
    const {
        config,
        handleInputChange,
        highlightInvalid
    } = useContext(ConfigContext);

    // Get callback to open ApiTarget rule modal
    const { handleShow } = useContext(ApiTargetModalContext);

    const deleteRule = (instance, timestamp) => {
        let rules = { ...config[instance]["schedule"] };
        delete rules[timestamp];
        handleInputChange(instance, "schedule", rules);
    };

    // Handler for add rule button, creates new row
    function addNewRuleRow(instance) {
        // Get existing rules
        const rules = { ...config[instance]["schedule"] };

        // Add rule with blank timestamp, default_rule value
        rules[""] = config[instance]["default_rule"];
        handleInputChange(instance, "schedule", rules);
    }

    const ApiTargetRuleButton = ({ instance, rule }) => {
        return (
            <span
                className="form-control"
                onClick={() => handleShow(instance, rule)}
            >
                Click to edit
            </span>
        );
    };

    ApiTargetRuleButton.propTypes = {
        instance: PropTypes.string,
        rule: PropTypes.string,
    };

    // Takes instance ID (device1, sensor3, etc) and rule timestamp
    // Returns table row with timestamp and rule columns + edit button
    const ScheduleRuleRow = ({ instance, timestamp }) => {
        // Called by TimeField when user changes value and closes
        const handleNewTimestamp = (newTimestamp, oldTimestamp) => {
            // Only update state if timestamp changed
            if (newTimestamp != oldTimestamp) {
                // Get existing rules, value of edited rule
                const rules = { ...config[instance]["schedule"] };
                const rule_value = rules[oldTimestamp];

                // Delete original timestamp, add new, update state
                delete rules[oldTimestamp];
                rules[newTimestamp] = rule_value;
                handleInputChange(instance, "schedule", rules);
            }
        };

        // Called by RuleField when user changes value and closes
        const handleNewRule = (rule, fade_rule, duration, range_rule) => {
            // Only update state if rule changed
            if (rule != config[instance]["schedule"][timestamp]) {
                // Get existing schedule rules
                const rules = config[instance]["schedule"];

                // Overwrite edited rule
                if (range_rule && fade_rule) {
                    // Fade rule: Combine params into single string
                    rules[timestamp] = `fade/${rule}/${duration}`;
                } else {
                    rules[timestamp] = rule;
                }

                // Update state
                handleInputChange(instance, "schedule", rules);
            }
        };

        return (
            <tr>
                <td className="schedule-rule-field">
                    <TimeField
                        timestamp={timestamp}
                        handleChange={handleNewTimestamp}
                        schedule_keywords={config.metadata.schedule_keywords}
                        highlightInvalid={highlightInvalid}
                    />
                </td>
                <td className="schedule-rule-field">
                    {/* ApiTarget: Button to open modal, otherwise RuleField */}
                    {config[instance]['_type'] === "api-target" ?
                        <ApiTargetRuleButton instance={instance} rule={timestamp} /> :
                        <RuleField
                            instance={config[instance]}
                            category={instance.replace(/[0-9]/g, '')}
                            type={config[instance]._type}
                            rule={config[instance]["schedule"][timestamp]}
                            handleChange={handleNewRule}
                        />
                    }
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
        instance: PropTypes.string,
        timestamp: PropTypes.string,
    };

    const RulesTable = ({ instance }) => {
        return (
            <Table className="table-borderless">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Rule</th>
                        <th></th>
                    </tr>
                    {Object.keys(config[instance]["schedule"]).map(timestamp => {
                        return (
                            <ScheduleRuleRow
                                key={timestamp}
                                instance={instance}
                                timestamp={timestamp}
                            />
                        );
                    })}
                </thead>
            </Table>
        );
    };

    RulesTable.propTypes = {
        instance: PropTypes.string
    };

    // Takes instance ID (device1, sensor3, etc), returns schedule rule card
    const ScheduleRuleSection = ({ instance }) => {
        const instanceNickname = config[instance]["nickname"];
        const instanceType = config[instance]["_type"];

        return (
            <Card key={`${instance}-schedule-rules`} className="mb-4">
                <Card.Body className="text-center">
                    <h6>
                        <b>{instanceNickname} ({instanceType})</b>
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
        instance: PropTypes.string
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
