import React, { useContext } from 'react';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import { ConfigContext, filterObject } from './ConfigContext';


const Page2 = () => {
    // Get curent state + callback functions from context
    const { config, handleSensorTargetSelect } = useContext(ConfigContext);

    // Get objects containing only devices and sensors
    const devices = filterObject(config, 'device');
    const sensors = filterObject(config, 'sensor');

    function targetSection(sensor) {
        return (
            <Card className="mb-4">
                <Card.Body>
                    <h6><b>{config[sensor]["nickname"]} ({config[sensor]["_type"]})</b> targets:</h6>
                    {/* Iterate devices, add checkbox for each */}
                    {(() => {
                        let inputs = [];
                        for (let device in devices) {
                            inputs.push(
                                <Form.Check
                                    type="checkbox"
                                    id={`${sensor}-${device}-target`}
                                    label={devices[device]["nickname"]}
                                    checked={config[sensor]["targets"].includes(device)}
                                    onChange={(e) => handleSensorTargetSelect(sensor, device, e.target.checked)}
                                />
                            );
                        }
                        return inputs;
                    })()}
                </Card.Body>
            </Card>
        );
    }

    return (
        <>
            <h3>Select targets for each sensor</h3>
            {/* Iterate sensors, add card for each */}
            {(() => {
                let cards = [];
                for (let sensor in sensors) {
                    cards.push(targetSection(sensor, config[sensor]));
                }
                return cards;
            })()}
        </>
    );
};


export default Page2;
