import React from 'react';
import PropTypes from 'prop-types';
import { WifiModalContextProvider } from 'modals/WifiModal';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import { UploadModalContextProvider } from 'modals/UploadModal';
import { RestoreModalContextProvider } from 'modals/RestoreModal';
import { DesktopModalContextProvider } from 'modals/DesktopIntegrationModal';


export const ModalContextProvider = ({ children }) => {
    return (
        <UploadModalContextProvider>
            <ErrorModalContextProvider>
                <DesktopModalContextProvider>
                    <RestoreModalContextProvider>
                        <WifiModalContextProvider>
                            {children}
                        </WifiModalContextProvider>
                    </RestoreModalContextProvider>
                </DesktopModalContextProvider>
            </ErrorModalContextProvider>
        </UploadModalContextProvider>
    );
};

ModalContextProvider.propTypes = {
    children: PropTypes.node,
};
