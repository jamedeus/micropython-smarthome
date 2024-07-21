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

        // Click "Restore config" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Restore config'));
    });

    it('sends correct request when RestoreModal is submitted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: {
                    friendly_name: 'Old Node',
                    filename: 'old-node.json',
                    ip: '123.123.123.123'
                }
            })
        }));

        // Enter IP address in modal input
        const modal = app.queryByText(/config files from existing nodes/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');

        // Press Restore button, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'Restore' }));
        expect(global.fetch).toHaveBeenCalledWith('/restore_config', {
            method: 'POST',
            body: JSON.stringify({
                "ip": "123.123.123.123"
            }),
            headers: postHeaders
        });

        // Confirm input is replaced by checkmark animation
        await waitFor(() => {
            expect(within(modal).queryByRole('textbox')).toBeNull();
            expect(modal.querySelector('.checkmark')).not.toBeNull();
        }, { timeout: 1500 });

        // Confirm modal closes automatically, node appears in existing nodes table
        await waitFor(() => {
            expect(app.queryByText(/config files from existing nodes/)).toBeNull();
            const existingNodes = app.getByText('Existing Nodes').parentElement;
            expect(within(existingNodes).queryByText('123.123.123.123')).not.toBeNull();
        }, { timeout: 1500 });
    });

    it('submits modal when enter key pressed in input', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: {
                    friendly_name: 'Old Node',
                    filename: 'old-node.json',
                    ip: '123.123.123.123'
                }
            })
        }));

        // Enter IP address in modal input
        const modal = app.queryByText(/config files from existing nodes/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');

        // Press enter key, confirm correct request sent
        await user.type(within(modal).getByRole('textbox'), '{enter}');
        expect(global.fetch).toHaveBeenCalledWith('/restore_config', {
            method: 'POST',
            body: JSON.stringify({
                "ip": "123.123.123.123"
            }),
            headers: postHeaders
        });
    });

    it('shows correct error modal if unable to connect to new IP', async () => {
        // Mock fetch function to simulate failed to connect
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 404,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect to node, please make sure it is connected to wifi and try again.'
            })
        }));

        // Enter IP address in modal input, click submit button
        const modal = app.queryByText(/config files from existing nodes/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');
        await user.click(app.getByRole('button', { name: 'Restore' }));

        // Confirm unable to connect error modal appeared
        expect(app.getByText(/Unable to connect to/)).not.toBeNull();
    });

    it('shows correct error modal if restored config is a duplicate', async () => {
        // Mock fetch function to simulate duplicate config
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 409,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Config already exists with identical name'
            })
        }));

        // Enter IP address in modal input, click submit button
        const modal = app.queryByText(/config files from existing nodes/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');
        await user.click(app.getByRole('button', { name: 'Restore' }));

        // Confirm duplicate error modal appeared
        expect(app.getByText(
            'A node with the same name or filename already exists'
        )).not.toBeNull();
    });

    it('shows alert if unexpected error occur', async () => {
        // Mock fetch function to simulate arbitrary error, mock alert function
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 418,
            json: () => Promise.resolve({
                status: 'error',
                message: "I'm a teapot"
            })
        }));
        global.alert = jest.fn();

        // Enter IP address in modal input, click submit button
        const modal = app.queryByText(/config files from existing nodes/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');
        await user.click(app.getByRole('button', { name: 'Restore' }));

        // Confirm arbitrary error was shown in alert
        expect(global.alert).toHaveBeenCalledWith("I'm a teapot");
    });

    it('closes modal when X button or background is clicked', async () => {
        // Click close button, confirm modal closes
        await user.click(app.getByText(
            /config files from existing nodes/
        ).parentElement.parentElement.children[0].children[2]);
        expect(app.queryByText(/config files from existing nodes/)).toBeNull();

        // Open modal again, click backdrop, confirm modal closes
        await user.click(app.getByText('Restore config'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(app.queryByText(/config files from existing nodes/)).toBeNull();
    });
});
