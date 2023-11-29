import React, { useContext } from 'react';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from './ConfigContext';
import { ScheduleRuleModalContext, ScheduleRuleModal } from './ScheduleRuleModal';
import { TimeField } from './TimeField';
import { RuleField } from './RuleField';


const Page3 = () => {
    // Get curent state + callback functions from context
    const { config } = useContext(ConfigContext);

    // Get callback to open schedule rule modal
    const { handleShow } = useContext(ScheduleRuleModalContext);

    // Takes instance ID (device1, sensor3, etc) and rule timestamp
    // Returns table row with timestamp and rule columns + edit button
    function scheduleRuleRow(instance, rule) {
        return (
            <tr>
                <td>
                    <TimeField instance={instance} timestamp={rule} />
                </td>
                <td>
                    <RuleField instance={instance} timestamp={rule} />
                </td>
            </tr>
        );
    }

    // Takes instance ID (device1, sensor3, etc), returns schedule rule card
    function scheduleRuleSection(instance) {
        return (
            <Card className="mb-4">
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
                    <Button variant="secondary" onClick={() => handleShow(instance, "")}>
                        Add Rule
                    </Button>
                </Card.Body>
            </Card>
        );
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
            <ScheduleRuleModal />
        </>
    );
}


export default Page3;
