import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('App', () => {
    let app, user;

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
        app = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
    });

    it('sends correct payload when device are turned on and off', async () => {
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
        expect(powerButton.classList).toContain('btn-active-enter');
        expect(powerButton.classList).not.toContain('btn-active-exit');
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "turn_on",
                "instance": "device5",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Click button again, confirm has turn off class + correct payload sent
        await user.click(powerButton);
        expect(powerButton.classList).not.toContain('btn-active-enter');
        expect(powerButton.classList).toContain('btn-active-exit');
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "turn_off",
                "instance": "device5",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when sensor is triggered', async () => {
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
        expect(triggerButton.classList).toContain('btn-active-enter');
        expect(triggerButton.classList).not.toContain('btn-active-exit');
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "trigger_sensor",
                "instance": "sensor4",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when instance is enabled or disabled', async () => {
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
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "disable",
                "instance": "device5",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        expect(collapse.classList).not.toContain('show');

        // Click dropdown button, click enable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Enable'));

        // Confirm correct payload was sent, card is now open
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "enable",
                "instance": "device5",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
        });
    });

    it('sends correct payload when rule is changed', async () => {
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
            expect(global.fetch).toHaveBeenCalledWith('/send_command', {
                method: 'POST',
                body: JSON.stringify({
                    "command": "set_rule",
                    "instance": "device6",
                    "rule": 99,
                    "target": "192.168.1.100"
                }),
                headers: postHeaders
            });
        });

        // Click plus button, confirm correct payload sent
        await user.click(plus);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/send_command', {
                method: 'POST',
                body: JSON.stringify({
                    "command": "set_rule",
                    "instance": "device6",
                    "rule": 100,
                    "target": "192.168.1.100"
                }),
                headers: postHeaders
            });
        });
    });

    it('sends correct payload when reset rule dropdown option clicked', async () => {
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
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "reset_rule",
                "instance": "device3",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm reset option is now disabled
        expect(reset.classList).toContain('disabled');
    });

    it('sends correct payload when new schedule rule is added', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "time": "10:00",
                "Rule added": "enabled"
            })
        }));

        // Get device3 card, schedule rules button, schedule rules table, new rule button
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const addRule = rulesTable.parentElement.children[1].children[0];

        // Open schedule rules table, click add rule button
        await user.click(scheduleRulesButton);
        await user.click(addRule);
        const newRuleRow = rulesTable.children[1].children[3];

        // Click timestamp field, get PopupDiv
        await user.click(newRuleRow.children[0].children[0].children[0]);
        const timePopup = newRuleRow.children[0].children[0].children[1];

        // Simulate user typing '10:00' in timestamp
        await user.type(within(timePopup).getByLabelText('Time'), '10:00');

        // Click add rule button, confirm correct payload sent
        await user.click(newRuleRow.children[2].children[0]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "add_rule",
                "instance": "device3",
                "time": "10:00",
                "rule": "enabled",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when a schedule rule is edited', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "time": "sunrise",
                "Rule added": "enabled"
            })
        }));

        // Get device4 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click time field on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[0].children[0].children[0]);
        const timePopup = firstRule.children[0].children[0].children[1];

        // Change keyword dropdown to sunrise
        await user.selectOptions(within(timePopup).getAllByLabelText('Keyword')[0], 'sunrise');

        // Click add rule button
        await user.click(firstRule.children[2].children[0]);

        // Confirm 2 API calls were made:
        // - add_rule with new timestamp
        // - remove_rule with original timestamp
        expect(global.fetch).toHaveBeenNthCalledWith(1, '/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "add_rule",
                "instance": "device4",
                "time": "sunrise",
                "rule": "enabled",
                "overwrite": "overwrite",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        expect(global.fetch).toHaveBeenNthCalledWith(2, '/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "remove_rule",
                "instance": "device4",
                "rule": "morning",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when a schedule rule is deleted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "deleted": "morning"
            })
        }));

        // Get device4 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click delete button on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[2].children[0]);

        // Confirm correct payload was sent
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "remove_rule",
                "instance": "device4",
                "rule": "morning",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when user clicks yes in save rules toast', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Get device4 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click delete button on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[2].children[0]);

        // Get toast, click yet, confirm correct payload sent
        const toast = app.getByText('Should this rule change persist after reboot?').parentElement;
        await user.click(within(toast).getByText('Yes'));
        expect(global.fetch).toHaveBeenCalledWith('/sync_schedule_rules', {
            method: 'POST',
            body: JSON.stringify({
                "ip": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });
});
