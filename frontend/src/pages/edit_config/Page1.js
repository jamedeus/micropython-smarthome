import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { ConfigContext } from 'root/ConfigContext';
import MetadataSection from './MetadataSection';
import IrBlasterSection from './IrBlasterSection';
import InstanceCard from './InstanceCard';

const CardColumn = ({ category }) => {
    const { config, deleteing, getKey, addInstance } = useContext(ConfigContext);

    // Slide add button up if card delete animation in progress
    const buttonClass = deleteing.category === category ? 'slide-up' : '';

    // Capitalize category for header and add button
    const capitalCategory = category.charAt(0).toUpperCase() + category.slice(1);

    return (
        <Col sm>
            <h2 className="text-center">
                Add {capitalCategory}s
            </h2>
            {Object.keys(config)
                .filter(id => id.startsWith(category))
                .sort((a, b) => {
                    // Sort by index (avoids 1, 10, 11, 2, 3, etc)
                    const indexA = parseInt(a.replace(/[a-zA-z]/g, ''));
                    const indexB = parseInt(b.replace(/[a-zA-z]/g, ''));
                    return indexA - indexB;
                })
                .map(id => (
                    <InstanceCard key={getKey(id, category)} id={id} />
                ))
            }
            <div className={`text-center position-relative mb-3 ${buttonClass}`}>
                <Button
                    variant="secondary"
                    onClick={() => addInstance(category)}
                >
                    Add {capitalCategory}
                </Button>
            </div>
        </Col>
    );
};

CardColumn.propTypes = {
    category: PropTypes.oneOf([
        'device',
        'sensor'
    ]).isRequired
};

const Page1 = () => {
    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <>
            <MetadataSection />
            <IrBlasterSection />
            <div className="d-flex flex-column">
                <Row className="mt-3">
                    <CardColumn category="sensor" />
                    <CardColumn category="device" />
                </Row>
            </div>
        </>
    );
};

export default Page1;
