import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import { EditConfigContext, filterObject } from 'root/EditConfigContext';

const Page2 = () => {
    // Get curent state + callback functions from context
    const { config, handleSensorTargetSelect } = useContext(EditConfigContext);

    // Get objects containing only devices and sensors
    const devices = filterObject(config, 'device');
    const sensors = filterObject(config, 'sensor');

    const TargetCheckbox = ({ sensor, device }) => {
        const handleClick = (e) => {
            handleSensorTargetSelect(sensor, device, e.target.checked);
        };

        return (
            <Form.Check
                type="checkbox"
                id={`${sensor}-${device}-target`}
                key={`${sensor}-${device}-target`}
                label={devices[device]["nickname"]}
                checked={config[sensor]["targets"].includes(device)}
                onChange={handleClick}
            />
        );
    };

    TargetCheckbox.propTypes = {
        sensor: PropTypes.string.isRequired,
        device: PropTypes.string.isRequired
    };

    const TargetSection = ({ sensor }) => {
        const sensorNickname = config[sensor]["nickname"];
        const sensorType = config[sensor]["_type"];

        return (
            <Card key={`${sensor}-targets`} className="mb-4">
                <Card.Body>
                    <h6>
                        <b>{sensorNickname} ({sensorType})</b> targets:
                    </h6>
                    {Object.keys(devices).sort().map(device => {
                        return (
                            <TargetCheckbox
                                key={device}
                                sensor={sensor}
                                device={device}
                            />
                        );
                    })}
                </Card.Body>
            </Card>
        );
    };

    TargetSection.propTypes = {
        sensor: PropTypes.string.isRequired
    };

    return (
        <>
            <h3>Select targets for each sensor</h3>
            {Object.keys(sensors).sort().map(sensor => {
                return <TargetSection key={sensor} sensor={sensor} />;
            })}
        </>
    );
};

export default Page2;
