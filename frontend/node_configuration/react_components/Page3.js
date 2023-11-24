import React, { useContext } from 'react';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { ConfigContext } from './ConfigContext';
import { ModalContext, ScheduleRuleModal } from './ScheduleRuleModal';

// Used to identify HH:MM timestamp
const timestamp_regex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;


// Takes 24h timestamp, returns 12h with am/pm suffix
function format12h(timestamp) {
    // Return keywords unchanged
    if ( ! timestamp_regex.test(timestamp)) {
        return timestamp;
    };

    let [hour, minute] = timestamp.split(':');
    const suffix = parseInt(hour) >= 12 ? 'pm' : 'am';
    // Convert to 12h format, if midnight replace 0 with 12
    hour = parseInt(hour) % 12;
    hour = hour === 0 ? 12 : hour;
    return `${hour}:${minute} ${suffix}`;
};


const Page3 = () => {
    // Get curent state + callback functions from context
    const { config } = useContext(ConfigContext);

    // Get context for schedule rule modal
    const { handleShow } = useContext(ModalContext);

    // Takes instance ID (device1, sensor3, etc) and rule timestamp
    // Returns table row with timestamp and rule columns + edit button
    function scheduleRuleRow(instance, rule) {
        return (
            <tr>
                <td>
                    <span
                        className="form-control"
                        onClick={() => handleShow(instance, rule)}
                    >
                        {format12h(rule)}
                    </span>
                </td>
                <td>
                    <span
                        className="form-control"
                        onClick={() => handleShow(instance, rule)}
                    >
                        {config[instance]["schedule"][rule]}
                    </span>
                </td>
                <td className="min">
                    <Button
                        variant="primary"
                        size="sm"
                        className="mb-1"
                        onClick={() => handleShow(instance, rule)}
                    >
                        <i class="bi-pencil"></i>
                    </Button>
                </td>
            </tr>
        );
    };

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
                                            };
                                            return rows;
                                        })()}
                                    </thead>
                                </Table>
                            );
                        };
                    })()}
                    <Button variant="secondary">Add Rule</Button>
                </Card.Body>
            </Card>
        );
    };

    return (
        <>
            <h3>Add schedule rules (optional)</h3>
            {/* Iterate devices and sensors, add card for each */}
            {(() => {
                let cards = [];
                for (let instance in config) {
                    if (instance.startsWith("device") || instance.startsWith("sensor")) {
                        cards.push(scheduleRuleSection(instance));
                    };
                };
                return cards;
            })()}
            <ScheduleRuleModal />
        </>
    );
}


export default Page3;
