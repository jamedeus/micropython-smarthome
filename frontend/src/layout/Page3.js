import React, { useContext } from 'react';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import { TimeField } from 'inputs/TimeField';
import { RuleField } from 'inputs/RuleField';
import { ApiTargetModalContext } from 'modals/ApiTargetRuleModal';
import { v4 as uuid } from 'uuid';


const Page3 = () => {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get callback to open ApiTarget rule modal
    const { handleShow } = useContext(ApiTargetModalContext);

    const deleteRule = (instance, timestamp) => {
        let rules = { ...config[instance]["schedule"] };
        delete rules[timestamp];
        handleInputChange(instance, "schedule", rules);
    };

    // Takes instance ID (device1, sensor3, etc) and rule timestamp
    // Returns table row with timestamp and rule columns + edit button
    function scheduleRuleRow(instance, rule) {
        return (
            <tr key={uuid()}>
                <td>
                    <TimeField instance={instance} timestamp={rule} />
                </td>
                <td>
                    {(() => {
                        // ApiTarget: Add button to open rule modal
                        if (config[instance]['_type'] === "api-target") {
                            return (
                                <span className="form-control" onClick={() => handleShow(instance, rule)}>
                                    Click to edit
                                </span>
                            );
                        // All other instances: Add RuleField, set rule in PopupDiv
                        } else {
                            return <RuleField instance={instance} timestamp={rule} />;
                        }
                    })()}
                </td>
                <td className="min">
                    <Button
                        variant="danger"
                        size="sm"
                        className="mb-1"
                        onClick={() => deleteRule(instance, rule)}
                    >
                        <i className="bi bi-trash-fill"></i>
                    </Button>
                </td>
            </tr>
        );
    }

    // Takes instance ID (device1, sensor3, etc), returns schedule rule card
    function scheduleRuleSection(instance) {
        return (
            <Card key={`${instance}-schedule-rules`} className="mb-4">
                <Card.Body className="text-center">
                    <h6><b>{config[instance]["nickname"]} ({config[instance]["_type"]})</b></h6>
                    {(() => {
                        // Don't render table if no rules exist
                        if (Object.entries(config[instance]['schedule']).length) {
                            return (
                                <Table className="table-borderless">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Rule</th>
                                            <th></th>
                                        </tr>
                                        {/* Iterate existing rules, add row for each */}
                                        {(() => {
                                            let rows = [];
                                            for (let rule in config[instance]["schedule"]) {
                                                rows.push(scheduleRuleRow(instance, rule));
                                            }
                                            return rows;
                                        })()}
                                    </thead>
                                </Table>
                            );
                        }
                    })()}
                    <Button variant="secondary" onClick={() => addNewRuleRow(instance)}>
                        Add Rule
                    </Button>
                </Card.Body>
            </Card>
        );
    }

    // Handler for add rule button, creates new row
    function addNewRuleRow(instance) {
        // Get existing rules
        const rules = { ...config[instance]["schedule"] };

        // Add rule with placeholder timestamp, default_rule value
        rules["Set time"] = config[instance]["default_rule"];
        handleInputChange(instance, "schedule", rules);
    }

    return (
        <>
            <h3>Add schedule rules (optional)</h3>
            {/* Iterate devices and sensors, add card for each */}
            {(() => {
                let cards = [];
                for (let instance in config) {
                    if (instance.startsWith("device") || instance.startsWith("sensor")) {
                        cards.push(scheduleRuleSection(instance));
                    }
                }
                return cards;
            })()}
        </>
    );
};


export default Page3;
