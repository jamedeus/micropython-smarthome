import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContextIrRemotes } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

// NOTE: Multi-node macro (stored in django model), not IR macro (stored in node config.json)
describe('IrRemotes while recording macro', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects including recording (contains macro name)
        createMockContext('status', mockContextIrRemotes.status);
        createMockContext('target_ip', mockContextIrRemotes.target_ip);
        createMockContext('recording', 'relax');
        createMockContext('ir_macros', mockContextIrRemotes.ir_macros);
        createMockContext('instance_metadata', api_card_metadata);
        createMockContext('api_target_options', {});
    });

    beforeEach(() => {
        // Render app + create userEvent instance to use in tests
        user = userEvent.setup();
        app = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
    });

    it('sends correct payload when TV remote buttons are pressed', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Get remote div
        const remote = app.getByText('TV Remote').parentElement.parentElement;

        // Click power button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[0]);
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "ir",
                    "ir_target": "tv",
                    "key": "power",
                    "target": "192.168.1.100"
                }
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when AC remote buttons are pressed', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Get remote div
        const remote = app.getByText('AC Remote').parentElement.parentElement;

        // Click stop button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[0]);
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "ir",
                    "ir_target": "ac",
                    "key": "stop",
                    "target": "192.168.1.100"
                }
            }),
            headers: postHeaders
        });
    });
});
