import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { parse_dom_context } from 'util/django_util';
import { ApiOverviewContext } from 'root/ApiOverviewContext';

const Floors = () => {
    // Get recording mode state, callback to show loading overlay
    const { recording, setLoading } = useContext(ApiOverviewContext);

    // Parse nodes context set by django template
    const [nodes] = useState(() => {
        return parse_dom_context("nodes");
    });

    // Takes node friendly name, redirects to card interface
    function open(friendlyName) {
        setLoading(true);
        if (recording === "") {
            window.location.href = `/api/${friendlyName}`;
        } else {
            window.location.href = `/api/${friendlyName}/${recording}`;
        }
    }

    // Takes node friendly name, returns button
    const NodeButton = ({ friendlyName }) => {
        const openNode = () => open(friendlyName);
        return (
            <Button variant="primary" className="m-1" onClick={openNode}>
                {friendlyName}
            </Button>
        );
    };

    NodeButton.propTypes = {
        friendlyName: PropTypes.string.isRequired,
    };

    // Takes section label and array of friendly names on floor
    // Returns section with button for each friendly name
    const FloorSection = ({ label, nodeList }) => {
        return (
            <div className="text-center section mt-3 mb-4 p-3">
                <h5 className="mb-3 fw-bold">{label}</h5>

                {nodeList.map((node) => {
                    return <NodeButton key={node} friendlyName={node} />;
                })}
            </div>
        );
    };

    FloorSection.propTypes = {
        label: PropTypes.string.isRequired,
        nodeList: PropTypes.array.isRequired
    };

    // Exactly 2 floors: Label sections "Upstairs" and "Downstairs", swap order
    // Default: Sequential "Floor #" labels, lowest to highest
    switch(Object.keys(nodes).length) {
        case(2):
            return (
                <>
                    <FloorSection
                        label="Upstairs"
                        nodeList={nodes[Object.keys(nodes)[1]]}
                    />
                    <FloorSection
                        label="Downstairs"
                        nodeList={nodes[Object.keys(nodes)[0]]}
                    />
                </>
            );
        default:
            return (
                <>
                    {Object.entries(nodes).map(([floor, nodeList]) => {
                        return (
                            <FloorSection
                                key={floor}
                                label={`Floor ${floor}`}
                                nodeList={nodeList}
                            />
                        );
                    })}
                </>
            );
    }
};

export default Floors;
