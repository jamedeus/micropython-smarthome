import React from 'react';
import App from '../Overview';
import { OverviewContextProvider } from 'root/OverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { postHeaders } from 'src/testUtils/headers';

describe('ChangeIpModal', () => {
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
        // Use fake timers
        jest.useFakeTimers();

        // Render app + create userEvent instance to use in tests
        user = userEvent.setup({delay: null});
        app = render(
            <OverviewContextProvider>
                <App />
            </OverviewContextProvider>
        );

        // Get existing nodes, click "Change IP" option in first row dropdown
        const existingNodes = app.getByText('Existing Nodes').parentElement;
        await user.click(within(existingNodes).getAllByRole('button')[0]);
        await user.click(app.getByText('Change IP'));
    });

    it('sends correct request when ChangeIpModal is submitted', async () => {
        // Mock fetch function to return expected response after 100ms delay
        global.fetch = jest.fn(() => new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({
                        status: 'success',
                        message: 'Successfully uploaded to new IP'
                    })
                });
            }, 100);
        }));

        // Enter new IP address in modal input
        const modal = app.queryByText(/file to a new IP/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');

        // Press Change button, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'Change' }));
        expect(global.fetch).toHaveBeenCalledWith('/change_node_ip', {
            method: 'POST',
            body: JSON.stringify({
                "new_ip": "123.123.123.123",
                "friendly_name": "Bathroom",
                "reupload": true
            }),
            headers: postHeaders
        });

        // Confirm input was replaced by loading animation
        await waitFor(() => {
            expect(within(modal).queryByRole('textbox')).toBeNull();
            expect(modal.querySelector('.loading-animation')).not.toBeNull();
        });

        // Confirm loading animation changes to checkmark when request complete
        await waitFor(() => {
            expect(modal.querySelector('.loading-animation')).toBeNull();
            expect(modal.querySelector('.checkmark')).not.toBeNull();
        });

        // Confirm modal closed, IP changed in existing nodes table
        jest.advanceTimersByTime(1200);
        await waitFor(() => {
            expect(app.queryByText(/file to a new IP/)).toBeNull();
            const existingNodes = app.getByText('Existing Nodes').parentElement;
            expect(within(existingNodes).queryByText('192.168.1.100')).toBeNull();
            expect(within(existingNodes).queryByText('123.123.123.123')).not.toBeNull();
        });
    });

    it('submits modal when enter key pressed in input', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: 'Successfully uploaded to new IP'
            })
        }));

        // Enter new IP address in modal input
        const modal = app.queryByText(/file to a new IP/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');

        // Press enter key, confirm correct request sent
        await user.type(within(modal).getByRole('textbox'), '{enter}');
        expect(global.fetch).toHaveBeenCalledWith('/change_node_ip', {
            method: 'POST',
            body: JSON.stringify({
                "new_ip": "123.123.123.123",
                "friendly_name": "Bathroom",
                "reupload": true
            }),
            headers: postHeaders
        });
    });

    it('shows correct error modal if unable to connect to new IP', async () => {
        // Mock fetch function to simulate failed to connect
        global.fetch = jest.fn(() => new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    ok: false,
                    status: 404,
                    json: () => Promise.resolve({
                        status: 'error',
                        message: 'Unable to change IP, node does not exist'
                    })
                });
            }, 100);
        }));

        // Enter new IP address in modal input, click submnit button
        const modal = app.queryByText(/file to a new IP/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');
        await user.click(app.getByRole('button', { name: 'Change' }));

        // Confirm input was replaced by loading animation
        await waitFor(() => {
            expect(within(modal).queryByRole('textbox')).toBeNull();
            expect(modal.querySelector('.loading-animation')).not.toBeNull();
        });

        // Confirm modal closed, unable to connect error modal appeared
        jest.advanceTimersByTime(1200);
        await waitFor(() => {
            expect(app.queryByText(/file to a new IP/)).toBeNull();
            expect(app.getByText(/Unable to connect to/)).not.toBeNull();
        });
    });

    it('shows generic error modal if other errors occur', async () => {
        // Mock fetch function to simulate arbitrary error
        global.fetch = jest.fn(() => new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    ok: false,
                    status: 418,
                    json: () => Promise.resolve({
                        status: 'error',
                        message: "I'm a teapot"
                    })
                });
            }, 100);
        }));

        // Enter new IP address in modal input, click submnit button
        const modal = app.queryByText(/file to a new IP/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');
        await user.click(app.getByRole('button', { name: 'Change' }));

        // Confirm input was replaced by loading animation
        await waitFor(() => {
            expect(within(modal).queryByRole('textbox')).toBeNull();
            expect(modal.querySelector('.loading-animation')).not.toBeNull();
        });

        // Confirm modal closed, error modal with arbitrary error text appeared
        jest.advanceTimersByTime(1200);
        await waitFor(() => {
            expect(app.queryByText(/file to a new IP/)).toBeNull();
            expect(app.getByText("I'm a teapot")).not.toBeNull();
        });
    });

    it('closes modal when X button or background is clicked', async () => {
        // Click close button, confirm modal closes
        await user.click(app.getByText(
            /to a new IP/
        ).parentElement.parentElement.children[0].children[2]);
        await waitFor(() => {
            expect(app.queryByText(/to a new IP/)).toBeNull();
        });

        // Open modal again, click backdrop, confirm modal closes
        await user.click(app.getByText('Change IP'));
        await user.click(document.querySelector('.modal-backdrop'));
        await waitFor(() => {
            expect(app.queryByText(/to a new IP/)).toBeNull();
        });
    });
});
