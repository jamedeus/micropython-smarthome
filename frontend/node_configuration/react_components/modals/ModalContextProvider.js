import React from 'react';
import PropTypes from 'prop-types';
import { GpsModalContextProvider } from 'modals/GpsModal';
import { WifiModalContextProvider } from 'modals/WifiModal';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import { UploadModalContextProvider } from 'modals/UploadModal';
import { RestoreModalContextProvider } from 'modals/RestoreModal';
import { ChangeIpModalContextProvider } from 'modals/ChangeIpModal';
import { DesktopModalContextProvider } from 'modals/DesktopIntegrationModal';


export const ModalContextProvider = ({ children }) => {
    return (
        <UploadModalContextProvider>
            <ErrorModalContextProvider>
                <DesktopModalContextProvider>
                    <RestoreModalContextProvider>
                        <GpsModalContextProvider>
                            <WifiModalContextProvider>
                                <ChangeIpModalContextProvider>
                                    {children}
                                </ChangeIpModalContextProvider>
                            </WifiModalContextProvider>
                        </GpsModalContextProvider>
                    </RestoreModalContextProvider>
                </DesktopModalContextProvider>
            </ErrorModalContextProvider>
        </UploadModalContextProvider>
    );
};

ModalContextProvider.propTypes = {
    children: PropTypes.node,
};
