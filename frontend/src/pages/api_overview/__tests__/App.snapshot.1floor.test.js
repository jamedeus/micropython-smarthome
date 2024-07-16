import React from 'react';
import App from '../ApiOverview';
import { ApiOverviewContextProvider } from 'root/ApiOverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockNodes1floor, mockMacros } from './mockContext';

describe('App', () => {
    it('matches snapshot when nodes are on 2 floors', () => {
        // Create mock state objects
        createMockContext('nodes', mockNodes1floor);
        createMockContext('macros', mockMacros);
        createMockContext('recording', '');

        // Render App, confirm matches snapshot
        const component = render(
            <ApiOverviewContextProvider>
                <App />
            </ApiOverviewContextProvider>
        );
        expect(component).toMatchSnapshot();
    });
});
