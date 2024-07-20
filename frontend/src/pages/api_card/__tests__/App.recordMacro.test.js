import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('App in record mode', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects including recording (contains macro name)
        createMockContext('status', mockContext.status);
        createMockContext('target_ip', mockContext.target_ip);
        createMockContext('recording', 'relax');
        createMockContext('ir_macros', {});
        createMockContext('instance_metadata', api_card_metadata);
        createMockContext('api_target_options', mockContext.api_target_options);
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

        // Reset mock fetch calls (ApiCardContext makes request when rendered)
        jest.clearAllMocks();
    });

    it('redirects to overview with macro name in URL when back button is clicked', async () => {
        // Click back button, confirm redirected, confirm URL contains macro name
        await user.click(app.getAllByRole('button')[0]);
        expect(window.location.href).toBe('/api/recording/relax');
    });

    it('sends correct payload when device are turned on and off while recording', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ On: "device5" })
        }));

        // Get device5 power button, confirm does not have turn on or turn off class
        const powerButton = app.getByText('Stairway lights').parentElement.children[0];
        expect(powerButton.classList).not.toContain('btn-active-enter');
        expect(powerButton.classList).not.toContain('btn-active-exit');

        // Click power button, confirm has turn on class + correct payload sent
        await user.click(powerButton);
        await waitFor(() => {
            expect(powerButton.classList).toContain('btn-active-enter');
            expect(powerButton.classList).not.toContain('btn-active-exit');
        });
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "turn_on",
                    "instance": "device5",
                    "target": "192.168.1.100",
                    "friendly_name": "Stairway lights"
                }
            }),
            headers: postHeaders
        });

        // Click button again, confirm has turn off class + correct payload sent
        await user.click(powerButton);
        await waitFor(() => {
            expect(powerButton.classList).not.toContain('btn-active-enter');
            expect(powerButton.classList).toContain('btn-active-exit');
        });
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "turn_off",
                    "instance": "device5",
                    "target": "192.168.1.100",
                    "friendly_name": "Stairway lights"
                }
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when sensor is triggered while recording', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ Triggered: "sensor4" })
        }));

        // Get sensor4 trigger button, confirm does not have either class
        const triggerButton = app.getByText('Computer activity').parentElement.children[0];
        expect(triggerButton.classList).not.toContain('btn-active-enter');
        expect(triggerButton.classList).not.toContain('btn-active-exit');

        // Click trigger button, confirm has on class + correct payload sent
        await user.click(triggerButton);
        await waitFor(() => {
            expect(triggerButton.classList).toContain('btn-active-enter');
            expect(triggerButton.classList).not.toContain('btn-active-exit');
        });
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "trigger_sensor",
                    "instance": "sensor4",
                    "target": "192.168.1.100",
                    "friendly_name": "Computer activity"
                }
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when instance is enabled or disabled while recording', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ Disabled: "device5" })
        }));

        // Get device5 card and top-right corner dropdown menu
        const card = app.getByText('Stairway lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Get card body collapse section, confirm open (device enabled)
        const collapse = card.children[1];
        expect(collapse.classList).toContain('show');

        // Click dropdown button, click disable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Disable'));

        // Confirm correct payload was sent, card is now collapsed
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "disable",
                    "instance": "device5",
                    "target": "192.168.1.100",
                    "friendly_name": "Stairway lights"
                }
            }),
            headers: postHeaders
        });
        expect(collapse.classList).not.toContain('show');

        // Click dropdown button, click enable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Enable'));

        // Confirm correct payload was sent, card is now open
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "enable",
                    "instance": "device5",
                    "target": "192.168.1.100",
                    "friendly_name": "Stairway lights"
                }
            }),
            headers: postHeaders
        });
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
        });
    });

    it('sends correct payload when rule is changed while recording', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ device6: 99 })
        }));

        // Get device6 card, slider minus button, slider plus button
        const card = app.getByText('Overhead lights').parentElement.parentElement;
        const minus = card.children[1].children[0].children[0].children[0];
        const plus = card.children[1].children[0].children[0].children[2];

        // Click minus button, confirm correct payload sent
        await user.click(minus);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
                method: 'POST',
                body: JSON.stringify({
                    name: "relax",
                    action: {
                        "command": "set_rule",
                        "instance": "device6",
                        "rule": 99,
                        "target": "192.168.1.100",
                        "friendly_name": "Overhead lights"
                    }
                }),
                headers: postHeaders
            });
        });

        // Click plus button, confirm correct payload sent
        await user.click(plus);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
                method: 'POST',
                body: JSON.stringify({
                    name: "relax",
                    action: {
                        "command": "set_rule",
                        "instance": "device6",
                        "rule": 100,
                        "target": "192.168.1.100",
                        "friendly_name": "Overhead lights"
                    }
                }),
                headers: postHeaders
            });
        });
    });

    it('sends correct payload when reset rule dropdown option clicked while recording', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "device1": "Reverted to scheduled rule",
                "current_rule": 98
            })
        }));

        // Get device3 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, get reset option, confirm not disabled
        await user.click(dropdown.children[0]);
        const reset = within(dropdown).getByText('Reset rule');
        expect(reset.classList).not.toContain('disabled');

        // Click reset, confirm correct payload sent
        await user.click(reset);
        expect(global.fetch).toHaveBeenCalledWith('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify({
                name: "relax",
                action: {
                    "command": "reset_rule",
                    "instance": "device3",
                    "target": "192.168.1.100",
                    "friendly_name": "Accent lights"
                }
            }),
            headers: postHeaders
        });

        // Confirm reset option is now disabled
        expect(reset.classList).toContain('disabled');
    });
});
