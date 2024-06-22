import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import InstanceCard from './InstanceCard';

const DeviceCards = ({instances}) => {
    // Get curent state + callback functions from context
    const { addInstance, getKey } = useContext(ConfigContext);

    return (
        <Col sm id="devices">
            <h2 className="text-center">Add Devices</h2>
            {instances.map((id, index) => (
                <InstanceCard key={getKey(id, "devices")} id={id} />
            ))}
            <div id="add_device" className="text-center position-relative mb-3">
                <Button variant="secondary" onClick={() => addInstance('device')}>
                    Add Device
                </Button>
            </div>
        </Col>
    );
};

DeviceCards.propTypes = {
    instances: PropTypes.array,
};

export default DeviceCards;
