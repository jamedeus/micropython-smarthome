import React from 'react';
import App from '../ApiOverview';
import { ApiOverviewContextProvider } from 'root/ApiOverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockNodes2floors } from './mockContext';

describe('App', () => {
    it('matches snapshot when no macros exist', () => {
        // Create mock state objects
        createMockContext('nodes', mockNodes2floors);
        createMockContext('macros', {});
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
