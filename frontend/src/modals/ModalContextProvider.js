import React from 'react';
import PropTypes from 'prop-types';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import { ChangeIpModalContextProvider } from 'modals/ChangeIpModal';


export const ModalContextProvider = ({ children }) => {
    return (
        <ErrorModalContextProvider>
            <ChangeIpModalContextProvider>
                {children}
            </ChangeIpModalContextProvider>
        </ErrorModalContextProvider>
    );
};

ModalContextProvider.propTypes = {
    children: PropTypes.node,
};
