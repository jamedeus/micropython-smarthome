import React from 'react';
import PropTypes from 'prop-types';
import { ErrorModalContextProvider } from 'modals/ErrorModal';


export const ModalContextProvider = ({ children }) => {
    return (
        <ErrorModalContextProvider>
            {children}
        </ErrorModalContextProvider>
    );
};

ModalContextProvider.propTypes = {
    children: PropTypes.node,
};
