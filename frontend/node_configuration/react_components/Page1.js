import React, { useContext } from 'react';
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
            <h1 className="text-center pt-3 pb-4">{document.title}</h1>

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
                <div className="row mt-3">
                    <div id="sensors" className="col-sm">
                        <h2 className="text-center">Add Sensors</h2>
                        {sensorEntries}
                        <div id="add_sensor" className="text-center position-relative">
                            <button className="btn-secondary btn mb-3" onClick={() => addInstance('sensor')}>Add Sensor</button>
                        </div>
                    </div>
                    <div id="devices" className="col-sm">
                        <h2 className="text-center">Add Devices</h2>
                        {deviceEntries}
                        <div id="add_device" className="text-center position-relative">
                            <button className="btn-secondary btn mb-3" onClick={() => addInstance('device')}>Add Device</button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="bottom">
                <button className="log-button" onClick={() => logState()}>Log State</button>
            </div>
        </>
    );
};


export default Page1;
