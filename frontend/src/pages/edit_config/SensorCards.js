import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import InstanceCard from './InstanceCard';

const SensorCards = ({instances}) => {
    // Get curent state + callback functions from context
    const { addInstance, getKey } = useContext(ConfigContext);

    return (
        <Col sm id="sensors">
            <h2 className="text-center">Add Sensors</h2>
            {instances.map((id) => (
                <InstanceCard key={getKey(id, "sensors")} id={id} />
            ))}
            <div id="add_sensor" className="text-center position-relative mb-3">
                <Button variant="secondary" onClick={() => addInstance('sensor')}>
                    Add Sensor
                </Button>
            </div>
        </Col>
    );
};

SensorCards.propTypes = {
    instances: PropTypes.array.isRequired
};

export default SensorCards;
