import React from 'react';
import App from '../Overview';
import { OverviewContextProvider } from 'root/OverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';

describe('App', () => {
    it('matches snapshot with no configs or nodes', () => {
        // Create mock state objects
        createMockContext('not_uploaded', []);
        createMockContext('uploaded', []);
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
