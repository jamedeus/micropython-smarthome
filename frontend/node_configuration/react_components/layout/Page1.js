import React, { useContext } from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import InstanceCard from './InstanceCard';
import MetadataSection from './MetadataSection';
import IrBlasterSection from './IrBlasterSection';
import { v4 as uuid } from 'uuid';

const Page1 = () => {
    // Get curent state + callback functions from context
    const { config, addInstance, logState } = useContext(ConfigContext);

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <>
            <MetadataSection />

            <IrBlasterSection />

            <div id="page1" className="d-flex flex-column">
                <Row className="mt-3">
                    <Col sm id="sensors">
                        <h2 className="text-center">Add Sensors</h2>
                        {Object.entries(config)
                            .filter(([id]) => id.startsWith('sensor'))
                            .map(([id]) => (
                                <InstanceCard key={uuid()} id={id} />
                            ))
                        }
                        <div id="add_sensor" className="text-center position-relative mb-3">
                            <Button variant="secondary" onClick={() => addInstance('sensor')}>
                                Add Sensor
                            </Button>
                        </div>
                    </Col>
                    <Col sm id="devices">
                        <h2 className="text-center">Add Devices</h2>
                        {Object.entries(config)
                            .filter(([id]) => id.startsWith('device'))
                            .map(([id]) => (
                                <InstanceCard key={uuid()} id={id} />
                            ))
                        }
                        <div id="add_device" className="text-center position-relative mb-3">
                            <Button variant="secondary" onClick={() => addInstance('device')}>
                                Add Device
                            </Button>
                        </div>
                    </Col>
                </Row>
            </div>

            <div className="mb-3">
                <Button variant="info" onClick={() => logState()}>Log State</Button>
            </div>
        </>
    );
};

export default Page1;
