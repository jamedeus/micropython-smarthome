import React from 'react';
import createMockContext from 'src/testUtils/createMockContext';
import App from '../Overview';
import { OverviewContextProvider } from 'root/OverviewContext';
import { mockContext } from './mockContext';

describe('App', () => {
    it('matches snapshot with new configs and existing nodes', () => {
        // Create mock state objects
        createMockContext('not_uploaded', mockContext.not_uploaded);
        createMockContext('uploaded', mockContext.uploaded);
        createMockContext('schedule_keywords', mockContext.schedule_keywords);
        createMockContext('desktop_integration_link', mockContext.desktop_integration_link);
        createMockContext('client_ip', mockContext.client_ip);

        // Render App, confirm matches snapshot
        const component = render(
            <OverviewContextProvider>
                <App />
            </OverviewContextProvider>
        );
        expect(component).toMatchSnapshot();
    });
});
