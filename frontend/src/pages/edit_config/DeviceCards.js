import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import InstanceCard from './InstanceCard';

const DeviceCards = ({instances}) => {
    // Get curent state + callback functions from context
    const { addInstance, getKey, deleteing } = useContext(ConfigContext);

    // Slide add button up if device card delete animation in progress
    const buttonClass = deleteing.category === 'device' ? 'slide-up' : '';

    return (
        <Col sm id="devices">
            <h2 className="text-center">Add Devices</h2>
            {instances.map((id) => (
                <InstanceCard key={getKey(id, "devices")} id={id} />
            ))}
            <div className={`text-center position-relative mb-3 ${buttonClass}`}>
                <Button variant="secondary" onClick={() => addInstance('device')}>
                    Add Device
                </Button>
            </div>
        </Col>
    );
};

DeviceCards.propTypes = {
    instances: PropTypes.array.isRequired
};

export default DeviceCards;
