import React, { useContext } from 'react';
import Row from 'react-bootstrap/Row';
import { ConfigContext } from 'root/ConfigContext';
import MetadataSection from './MetadataSection';
import IrBlasterSection from './IrBlasterSection';
import DeviceCards from './DeviceCards';
import SensorCards from './SensorCards';

const Page1 = () => {
    // Get curent state from context
    const { config } = useContext(ConfigContext);

    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <>
            <MetadataSection />

            <IrBlasterSection />

            <div id="page1" className="d-flex flex-column">
                <Row className="mt-3">
                    <SensorCards instances={Object.keys(config)
                        .filter(id => id.startsWith('sensor'))
                        .sort((a, b) => {
                            // Sort by index (avoids 1, 10, 11, 2, 3, etc)
                            const indexA = parseInt(a.replace(/[a-zA-z]/g, ''));
                            const indexB = parseInt(b.replace(/[a-zA-z]/g, ''));
                            return indexA - indexB;
                        })
                    }
                    />
                    <DeviceCards instances={Object.keys(config)
                        .filter(id => id.startsWith('device'))
                        .sort((a, b) => {
                            // Sort by index (avoids 1, 10, 11, 2, 3, etc)
                            const indexA = parseInt(a.replace(/[a-zA-z]/g, ''));
                            const indexB = parseInt(b.replace(/[a-zA-z]/g, ''));
                            return indexA - indexB;
                        })
                    }
                    />
                </Row>
            </div>
        </>
    );
};

export default Page1;
