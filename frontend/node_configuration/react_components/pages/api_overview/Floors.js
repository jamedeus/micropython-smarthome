import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { ApiOverviewContext } from 'root/ApiOverviewContext';


const Floors = () => {
    // Get django context, recording mode state, callback to show loading overlay
    const { context, recording, setLoading } = useContext(ApiOverviewContext);

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
        return (
            <Button variant="primary" className="m-1" onClick={() => open(friendlyName)}>
                {friendlyName}
            </Button>
        );
    };

    NodeButton.propTypes = {
        friendlyName: PropTypes.string,
    };

    // Takes section label and array of friendly names on floor
    // Returns section with button for each friendly name
    const FloorSection = ({ label, nodes }) => {
        return (
            <div className="section mt-3 mb-4 p-3">
                <h5 className="mb-3"><b>{label}</b></h5>

                {nodes.map((node) => {
                    return <NodeButton key={node} friendlyName={node} />;
                })}
            </div>
        );
    };

    FloorSection.propTypes = {
        label: PropTypes.string,
        nodes: PropTypes.array
    };

    // Get array of floor numbers (used to determine layout)
    const floorNumbers = Object.keys(context.nodes);

    // Exactly 2 floors: Label sections "Upstairs" and "Downstairs", switch order
    // Default: Sequential "Floor #" labels, lowest to highest
    switch(floorNumbers.length) {
        case(2):
            return (
                <>
                    <FloorSection
                        key={floorNumbers[1]}
                        label="Upstairs"
                        nodes={context.nodes[floorNumbers[1]]}
                    />
                    <FloorSection
                        key={floorNumbers[0]}
                        label="Downstairs"
                        nodes={context.nodes[floorNumbers[0]]}
                    />
                </>
            );
        default:
            return (
                <>
                    {floorNumbers.map((floor) => {
                        return (
                            <FloorSection
                                key={context.nodes[floor]}
                                label={`Floor ${floor}`}
                                nodes={context.nodes[floor]}
                            />
                        );
                    })}
                </>
            );
    }
};


export default Floors;
