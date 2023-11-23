import React, { useContext } from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from './ConfigContext';
import InstanceCard from './InstanceCard';
import MetadataSection from './MetadataSection';
import IrBlasterSection from './IrBlasterSection';


const Page1 = () => {
    // Get curent state + callback functions from context
    const {
        config,
        addInstance,
        logState,
        handleInputChange,
        handleIrTargetSelect
    } = useContext(ConfigContext);

    // Render list of device cards
    const deviceEntries = (
        <>
            {Object.entries(config)
            .filter(([id, _]) => id.startsWith('device'))
            .map(([id, config]) => (
                <InstanceCard
                    key={config.uniqueID}
                    id={id}
                />
            ))}
        </>
    );

    // Render list of sensor cards
    const sensorEntries = (
        <>
            {Object.entries(config)
            .filter(([id, _]) => id.startsWith('sensor'))
            .map(([id, config]) => (
                <InstanceCard
                    key={config.uniqueID}
                    id={id}
                />
            ))}
        </>
    );

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <>
            <MetadataSection />

            <IrBlasterSection
                key="ir_blaster"
                configured={config.ir_blaster.configured}
                pin={config.ir_blaster.pin}
                target={config.ir_blaster.target}
                onChange={handleInputChange}
                onTargetSelect={handleIrTargetSelect}
            />

            <div id="page1" className="d-flex flex-column">
                <Row className="mt-3">
                    <Col sm id="sensors">
                        <h2 className="text-center">Add Sensors</h2>
                        {sensorEntries}
                        <div id="add_sensor" className="text-center position-relative mb-3">
                            <Button variant="secondary" onClick={() => addInstance('sensor')}>
                                Add Sensor
                            </Button>
                        </div>
                    </Col>
                    <Col sm id="devices">
                        <h2 className="text-center">Add Devices</h2>
                        {deviceEntries}
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
