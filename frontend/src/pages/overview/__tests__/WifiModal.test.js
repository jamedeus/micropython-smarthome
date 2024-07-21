import React from 'react';
import App from '../Overview';
import { OverviewContextProvider } from 'root/OverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { postHeaders } from 'src/testUtils/headers';

describe('WifiModal', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('not_uploaded', mockContext.not_uploaded);
        createMockContext('uploaded', mockContext.uploaded);
        createMockContext('schedule_keywords', mockContext.schedule_keywords);
        createMockContext('desktop_integration_link', mockContext.desktop_integration_link);
        createMockContext('client_ip', mockContext.client_ip);
    });

    beforeEach(async () => {
        // Render app + create userEvent instance to use in tests
        user = userEvent.setup();
        app = render(
            <OverviewContextProvider>
                <App />
            </OverviewContextProvider>
        );

        // Click "Set GPS coordinates" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Set WIFI credentials'));
    });

    it('makes correct request when credentials submitted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve('Default credentials set')
        }));

        // Simulate user typing ssid and password
        await user.type(app.getByLabelText('Network:'), 'mywifi');
        await user.type(app.getByLabelText('Password:'), 'hunter2');

        // Click OK button, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'OK' }));
        expect(global.fetch).toHaveBeenCalledWith('/set_default_credentials', {
            method: 'POST',
            body: JSON.stringify({
                "ssid": "mywifi",
                "password": "hunter2"
            }),
            headers: postHeaders
        });
    });

    it('submits modal when user presses enter key in either field', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve('Default credentials set')
        }));

        // Simulate user typing ssid and password
        await user.type(app.getByLabelText('Network:'), 'mywifi');
        await user.type(app.getByLabelText('Password:'), 'hunter2');

        // Simulate user pressing enter in ssid field, confirm request sent
        await user.type(app.getByLabelText('Network:'), '{enter}');
        expect(global.fetch).toHaveBeenCalledWith('/set_default_credentials', {
            method: 'POST',
            body: JSON.stringify({
                "ssid": "mywifi",
                "password": "hunter2"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Open modal again, simulate user pressing enter in password field
        await user.click(app.getByText('Set WIFI credentials'));
        await user.type(app.getByLabelText('Password:'), '{enter}');
        expect(global.fetch).toHaveBeenCalledWith('/set_default_credentials', {
            method: 'POST',
            body: JSON.stringify({
                "ssid": "mywifi",
                "password": "hunter2"
            }),
            headers: postHeaders
        });
    });

    it('closes modal when X button or background is clicked', async () => {
        // Click close button, confirm modal closes
        await user.click(app.getByText('Set Default Wifi').parentElement.children[2]);
        expect(app.queryByText('Set Default Wifi')).toBeNull();

        // Open modal again, click cancel button, confirm modal closes
        await user.click(app.getByText('Set WIFI credentials'));
        await user.click(app.getByRole('button', { name: 'Cancel' }));
        expect(app.queryByText('Set Default Wifi')).toBeNull();

        // Open modal again, click backdrop, confirm modal closes
        await user.click(app.getByText('Set WIFI credentials'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(app.queryByText('Set Default Wifi')).toBeNull();
    });
});
