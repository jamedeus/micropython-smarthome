import React, { useContext } from 'react';
import { ApiCardContext } from 'root/ApiCardContext';

const LayoutEmpty = () => {
    const {status} = useContext(ApiCardContext);

    const editLink = `/edit_config/${status.metadata.id}`;

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
