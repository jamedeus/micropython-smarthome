import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { ApiOverviewContext } from 'root/ApiOverviewContext';


const Floors = () => {
    // Get django context, recording mode state
    const { context, recording } = useContext(ApiOverviewContext);

    // Takes node friendly name, redirects to card interface
    function open(friendlyName) {
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

    // Takes floor number and array of friendly names on floor
    // Returns section with button for each friendly name
    const FloorSection = ({ floor, nodes }) => {
        return (
            <div className="section mt-3 mb-4 p-3">
            <h5 className="mb-3"><b>Floor {floor}</b></h5>

            {nodes.map((node) => {
                return <NodeButton key={node} friendlyName={node} />;
            })}
            </div>
        );
    };

    return (
        <div id="container" className="text-center">
            {Object.keys(context.nodes).map((floor) => {
                return (
                    <FloorSection
                        key={context.nodes[floor]}
                        floor={floor}
                        nodes={context.nodes[floor]}
                    />
                );
            })}
        </div>
    );
};


export default Floors;
