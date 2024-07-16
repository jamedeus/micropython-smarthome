import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';

describe('App', () => {
    it('matches snapshot', () => {
        // Create mock state objects
        createMockContext('status', mockContext.status);
        createMockContext('target_ip', mockContext.target_ip);
        createMockContext('recording', mockContext.recording);
        createMockContext('ir_macros', {});
        createMockContext('instance_metadata', api_card_metadata);
        createMockContext('api_target_options', mockContext.api_target_options);

        // Render App, confirm matches snapshot
        const component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
        expect(component).toMatchSnapshot();
    });
});
