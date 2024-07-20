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
        await waitFor(() => {
            expect(powerButton.classList).toContain('btn-active-enter');
            expect(powerButton.classList).not.toContain('btn-active-exit');
        });
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
        await waitFor(() => {
            expect(powerButton.classList).not.toContain('btn-active-enter');
            expect(powerButton.classList).toContain('btn-active-exit');
        });
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
        await waitFor(() => {
            expect(triggerButton.classList).toContain('btn-active-enter');
            expect(triggerButton.classList).not.toContain('btn-active-exit');
        });
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

        // Confirm current rule is 767
        const sliderHandle = card.querySelector('.sliderHandle');
        expect(sliderHandle.innerHTML).toBe('767');

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

        // Confirm reset option is now disabled, current rule changed to 1023
        expect(reset.classList).toContain('disabled');
        expect(sliderHandle.innerHTML).toBe('1023');
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

    it('disables edit schedule rule button when time field is blank', async () => {
        // Get device4 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Confirm edit/delete button on first row is not disabled
        expect(firstRule.children[2].children[0]).not.toHaveAttribute('disabled');

        // Open schedule rules table, click time field on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[0].children[0].children[0]);
        const timePopup = firstRule.children[0].children[0].children[1];

        // Click keyword toggle (change to timestamp), press enter without typing timestamp
        await user.click(within(timePopup).getAllByLabelText('Keyword')[1]);
        await user.type(within(timePopup).getByLabelText('Time'), '{enter}');

        // Confirm add rule button is disabled
        expect(firstRule.children[2].children[0]).toHaveAttribute('disabled');
    });

    it('hides new rule field when delete button is clicked', async () => {
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const addRule = rulesTable.parentElement.children[1].children[0];

        // Open schedule rules table, click add rule button
        await user.click(scheduleRulesButton);
        await user.click(addRule);
        const newRuleRow = rulesTable.children[1].children[3];
        expect(newRuleRow.classList).not.toContain('d-none');

        // Click delete button, confirm new rule row is hidden, request not made
        await user.click(within(newRuleRow).getByRole('button'));
        expect(newRuleRow.classList).toContain('d-none');
        expect(global.fetch).not.toHaveBeenCalled();
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

        // Get toast, click yes, confirm correct payload sent
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

    it('does not make API call when user clicks no in save rules toast', async () => {
        // Get device4 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click delete button on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[2].children[0]);
        jest.clearAllMocks();

        // Get toast, click no, confirm no request was made
        const toast = app.getByText('Should this rule change persist after reboot?').parentElement;
        await user.click(within(toast).getByText('No'));
        expect(global.fetch).not.toHaveBeenCalled();
    });

    it('shows temperature history chart modal when climate data card clicked', async () => {
        // Confirm chart modal is not mounted
        expect(app.queryByText('Temperature History')).toBeNull();

        // Click climate data card, confirm chart modal appears
        await user.click(app.getAllByText('Climate Data')[0]);
        expect(app.queryByText('Temperature History')).not.toBeNull();
    });

    it('shows debug modal when debug dropdown option clicked', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                "group": "group1",
                "nickname": "Accent lights",
                "_type": "pwm",
                "current_rule": 767,
                "scheduled_rule": 1023,
                "max_rule": 1023,
                "enabled": true,
                "rule_queue": [
                    "fade/512/1800",
                    "disabled",
                    1023
                ],
                "min_rule": 0,
                "state": false,
                "triggered_by": [
                    "sensor1",
                    "sensor5"
                ],
                "default_rule": 1023,
                "name": "device3",
                "bright": 0,
                "fading": false
            })
        }));

        // Get device3 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click debug option, confirm correct request made
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Debug'));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "get_attributes",
                "instance": "device3",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm debug modal appeared with mock response text
        expect(app.queryByText(/"nickname": "Accent lights"/)).not.toBeNull();

        // Click modal close button, confirm closed
        await user.click(app.getAllByText('Debug')[1].parentElement.children[2]);
        expect(app.queryByText(/"nickname": "Accent lights"/)).toBeNull();

        // Show modal again, click backdrop, confirm closed
        await user.click(within(dropdown).getByText('Debug'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(app.queryByText(/"nickname": "Accent lights"/)).toBeNull();
    });

    it('shows schedule toggle modal when dropdown option clicked', async () => {
        // Get device3 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click schedule toggle option, confirm modal appeared
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Schedule Toggle'));
        expect(app.queryByText('Enable or disable after a delay.')).not.toBeNull();
    });

    it('shows start fade modal when dropdown option clicked', async () => {
        // Get device3 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click start fade option, confirm modal appeared
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Start Fade'));
        expect(app.queryByText('Duration (seconds)')).not.toBeNull();
    });

    it('highlights correct devices when sensor Show triggers option clicked', async () => {
        // Get sensor2 card, device7 card, device8 card
        const sensor2 = app.getByText('Temp sensor').parentElement.parentElement;
        const device7 = app.getByText('Air Conditioner').parentElement.parentElement;
        const device8 = app.getByText('Fan').parentElement.parentElement;

        // Confirm device cards do not have highlight class
        expect(device7.parentElement.classList).not.toContain('highlight-enter');
        expect(device8.parentElement.classList).not.toContain('highlight-enter');
        expect(app.container.querySelectorAll('.highlight-enter').length).toBe(0);

        // Click sensor2 "Show targets" dropdown option
        const dropdown = sensor2.children[0].children[2];
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Show targets'));

        // Confirm both target devices have highlight class, but no other cards
        await waitFor(() => {
            expect(device7.parentElement.classList).toContain('highlight-enter');
            expect(device8.parentElement.classList).toContain('highlight-enter');
            expect(app.container.querySelectorAll('.highlight-enter').length).toBe(2);
            expect(app.container.querySelectorAll('.highlight-enter-done').length).toBe(0);
        });

        // Wait for highlight animation to complete
        await waitFor(() => {
            expect(device7.parentElement.classList).toContain('highlight-enter-done');
            expect(device8.parentElement.classList).toContain('highlight-enter-done');
            expect(app.container.querySelectorAll('.highlight-enter').length).toBe(0);
            expect(app.container.querySelectorAll('.highlight-enter-done').length).toBe(2);
        });

        // Click anywhere in page, confirm highlight fades out
        await user.click(app.getByText('Motion'));
        expect(device7.parentElement.classList).not.toContain('highlight-enter');
        expect(device8.parentElement.classList).not.toContain('highlight-enter');
        expect(device7.parentElement.classList).toContain('highlight-exit');
        expect(device8.parentElement.classList).toContain('highlight-exit');
        expect(app.container.querySelectorAll('.highlight-exit').length).toBe(2);
    });

    it('shows ApiTargetRuleModal when "Change rule" dropdown option clicked', async () => {
        // Get device7 card and top-right corner dropdown menu
        const card = app.getByText('Air Conditioner').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click Change rule option, confirm modal appeared
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Change rule'));
        expect(app.queryByText('API Target Rule')).not.toBeNull();
    });

    it('sends the correct payload when ApiTarget rule is changed', async () => {
        // Get device7 card, open change rule modal
        const card = app.getByText('Air Conditioner').parentElement.parentElement;
        const dropdown = card.children[0].children[2];
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Change rule'));

        // Change both actions to ignore
        const modal = app.getByText('API Target Rule').parentElement.parentElement;
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'ignore');
        await user.click(app.getByText('Off Action'));
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'ignore');

        // Click Submit button, confirm correct payload sent
        await user.click(app.getByRole('button', { name: 'Submit' }));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "set_rule",
                "instance": "device7",
                "rule": {
                    "on": [
                        "ignore"
                    ],
                    "off": [
                        "ignore"
                    ]
                },
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('requests a status update every 5 seconds', async () => {
        // Mock fetch function to return simulated status update
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockContext.status)
        }));

        // Confirm fetch has not been called
        expect(global.fetch).not.toHaveBeenCalled();

        // Wait 5 seconds, confirm fetched status update
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/get_status/Thermostat');
        }, { timeout: 5500 });
    });

    it('shows error modal if status update fails', async () => {
        // Mock fetch function to simulate offline node
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve("Error: Unable to connect.")
        }));

        // Wait 5 seconds, confirm fetched status update
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/get_status/Thermostat');
        }, { timeout: 5500 });

        // Confirm error modal is visible
        expect(app.queryByText('Attempting to reestablish connection...')).not.toBeNull();
    });

    it('hides error modal once able to update status', async () => {
        // Mock fetch function to simulate offline node
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve("Error: Unable to connect.")
        }));

        // Wait 5 seconds, confirm error modal is visible
        await waitFor(() => {
            expect(app.queryByText('Attempting to reestablish connection...')).not.toBeNull();
        }, { timeout: 5500 });

        // Mock fetch function to simualte node coming back online
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockContext.status)
        }));

        // Wait 5 seconds, confirm error modal disappeared
        await waitFor(() => {
            expect(app.queryByText('Attempting to reestablish connection...')).toBeNull();
        }, { timeout: 5500 });
    });
});
