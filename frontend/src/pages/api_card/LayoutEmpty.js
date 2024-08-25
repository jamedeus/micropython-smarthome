import React, { useState } from 'react';

const LayoutEmpty = () => {
    // Get node name from URL (status.metadata.id may contain a different name
    // than django database if new config was uploaded without updating django)
    const [nodeName] = useState(window.location.pathname.split('/')[2]);

    const editLink = `/edit_config/${nodeName}`;

    return (
        <div className={`h-75 d-flex flex-column
                         justify-content-center align-items-center`}
        >
            <h3>Setup Mode</h3>
            <p className="mt-2">This node has no devices or sensors</p>
            <p>Click <a href={editLink}>here</a> to configure</p>
        </div>
    );
};

export default LayoutEmpty;
