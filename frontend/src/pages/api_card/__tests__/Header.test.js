import React from 'react';
import Header from '../Header';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('Header', () => {
    let component, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('status', mockContext.status);
        createMockContext('target_ip', mockContext.target_ip);
        createMockContext('recording', mockContext.recording);
        createMockContext('ir_macros', {});
        createMockContext('instance_metadata', api_card_metadata);
        createMockContext('api_target_options', mockContext.api_target_options);
    });

    beforeEach(() => {
        // Render app + create userEvent instance to use in tests
        user = userEvent.setup();
        component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <Header />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
    });

    it('redirects to overview when back button is clicked', async () => {
        // Click back button, confirm redirected
        await user.click(component.getAllByRole('button')[0]);
        expect(window.location.href).toBe('/api');
    });

    it('sends correct payload when reboot option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click dropdown, click reboot option
        await user.click(component.getAllByRole('button')[1]);
        await user.click(component.getByText('Reboot'));

        // Confirm correct payload was sent
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "reboot",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when clear log option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click dropdown, click clear log option
        await user.click(component.getAllByRole('button')[1]);
        await user.click(component.getByText('Clear Log'));

        // Confirm correct payload was sent
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "clear_log",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when reset all rules option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click dropdown, click reset all rules option
        await user.click(component.getAllByRole('button')[1]);
        await user.click(component.getByText('Reset all rules'));

        // Confirm correct payload was sent
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "reset_all_rules",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });
});
