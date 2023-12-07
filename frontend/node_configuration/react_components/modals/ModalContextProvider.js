import React from 'react';
import PropTypes from 'prop-types';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import { UploadModalContextProvider } from 'modals/UploadModal';
import { ChangeIpModalContextProvider } from 'modals/ChangeIpModal';


export const ModalContextProvider = ({ children }) => {
    return (
        <UploadModalContextProvider>
            <ErrorModalContextProvider>
                <ChangeIpModalContextProvider>
                    {children}
                </ChangeIpModalContextProvider>
            </ErrorModalContextProvider>
        </UploadModalContextProvider>
    );
};

ModalContextProvider.propTypes = {
    children: PropTypes.node,
};
