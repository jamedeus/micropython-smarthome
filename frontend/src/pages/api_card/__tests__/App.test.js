import React from 'react';
import App from '../ApiCard';
import { fireEvent } from '@testing-library/react';
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

        // Set correct path
        Object.defineProperty(window, 'location', {
            writable: true,
            value: {
                pathname: '/api/Test Node'
            }
        });
    });

    beforeEach(() => {
        // Use fake timers
        jest.useFakeTimers();

        // Render app + create userEvent instance to use in tests
        user = userEvent.setup({delay: null});
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

    it('sends correct payload when device are turned on and off', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { On: "device4" }
            })
        }));

        // Get device4 power button, confirm does not have turn on or turn off class
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
                "instance": "device4",
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
                "instance": "device4",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when sensor is triggered', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { Triggered: "sensor4" }
            })
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
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { Disabled: "sensor5" }
            })
        }));

        // Get sensor5 card and top-right corner dropdown menu
        const card = app.getByText('Motion').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Get card body collapse section, confirm open (device enabled)
        const collapse = card.children[1];
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
        });

        // Click dropdown button, click disable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Disable'));

        // Confirm correct payload was sent, card is now collapsed
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "disable",
                "instance": "sensor5",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        await waitFor(() => {
            expect(collapse.classList).not.toContain('show');
        });

        // Click dropdown button, click enable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Enable'));

        // Confirm correct payload was sent, card is now open
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "enable",
                "instance": "sensor5",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
        });
    });

    it('sets slider correctly when device with non-int current_rule is enabled', async () => {
        // Mock fetch function to simulate successful enable API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { Enabled: "device8" }
            })
        }));

        // Get device8 card and top-right corner dropdown menu
        // Current rule is "disabled" (causes NaN on slider), but scheduled_rule (72) is valid
        const card = app.getByText('Lamp').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Get card body collapse section, confirm closed (device disabled)
        const collapse = card.children[1];
        await waitFor(() => {
            expect(collapse.classList).not.toContain('show');
        });

        // Click dropdown button, click enable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Enable'));

        // Confirm API call was made, card opened, slider set to scheduled_rule (72)
        expect(global.fetch).toHaveBeenCalled();
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
            expect(card.querySelector('.sliderHandle').innerHTML).toBe('72');
        });
    });

    it('sets slider correctly when device with non-int current and scheduled rules is enabled', async () => {
        // Mock fetch function to simulate successful enable API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { Enabled: "device9" }
            })
        }));

        // Get device9 card and top-right corner dropdown menu
        // Current and scheduled rules are "disabled" (causes NaN on slider), but default (255) is valid
        const card = app.getByText('Bias lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Get card body collapse section, confirm closed (device disabled)
        const collapse = card.children[1];
        await waitFor(() => {
            expect(collapse.classList).not.toContain('show');
        });

        // Click dropdown button, click enable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Enable'));

        // Confirm API call was made, card opened, slider set to default_rule
        // (255, but displays 100 due to scaling)
        expect(global.fetch).toHaveBeenCalled();
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
            expect(card.querySelector('.sliderHandle').innerHTML).toBe('100');
        });
    });

    it('enforces rule slider limits when increment button is clicked', async () => {
        // Mock fetch function to simulate successful enable API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { sensor3: "20.0" }
            })
        }));

        // Get sensor3 card, confirm current rule is 20
        const card = app.getByText('Thermostat').parentElement.parentElement;
        const sliderHandle = card.querySelector('.sliderHandle');
        expect(sliderHandle.innerHTML).toBe('20.0');

        // Click slider plus button 16 times (increases by 0.5 each time, would
        // reach 28.0 but limits should stop at 27.0)
        for (let i = 0; i < 16; i++) {
            await user.click(card.querySelector('.bi-plus-lg'));

            // Wait for re-render before next click (fix intermittent failure)
            const expectedValue = Math.min(27.0, 20.0 + (i + 1) * 0.5);
            await waitFor(() => {
                expect(sliderHandle.innerHTML).toBe(expectedValue.toFixed(1));
            });
        }

        // Confirm current rule is 27.0
        expect(sliderHandle.innerHTML).toBe('27.0');
    });

    it('enforces rule slider limits when decrement button is clicked', async () => {
        // Mock fetch function to simulate successful enable API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { sensor3: "20.0" }
            })
        }));

        // Get sensor3 card, confirm current rule is 20
        const card = app.getByText('Thermostat').parentElement.parentElement;
        const sliderHandle = card.querySelector('.sliderHandle');
        expect(sliderHandle.innerHTML).toBe('20.0');

        // Click slider minus button 10 times (decreases by 0.5 each time, would
        // reach 15.0 but limits should stop at 18.0)
        for (let i = 0; i < 10; i++) {
            await user.click(card.querySelector('.bi-dash-lg'));

            // Wait for re-render before next click (fix intermittent failure)
            const expectedValue = Math.max(18.0, 20.0 - (i + 1) * 0.5);
            await waitFor(() => {
                expect(sliderHandle.innerHTML).toBe(expectedValue.toFixed(1));
            });
        }

        // Confirm current rule is 18
        expect(sliderHandle.innerHTML).toBe('18.0');
    });

    it('sends correct payload when rule is changed', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { device5: "99" }
            })
        }));

        // Get device5 card, slider minus button, slider plus button
        const card = app.getByText('Overhead lights').parentElement.parentElement;
        const minus = card.children[1].children[0].children[0].children[0];
        const plus = card.children[1].children[0].children[0].children[2];

        // Click minus button, confirm correct payload sent
        await user.click(minus);
        jest.advanceTimersByTime(200);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/send_command', {
                method: 'POST',
                body: JSON.stringify({
                    "command": "set_rule",
                    "instance": "device5",
                    "rule": 99,
                    "target": "192.168.1.100"
                }),
                headers: postHeaders
            });
        });

        // Click plus button, confirm correct payload sent
        await user.click(plus);
        jest.advanceTimersByTime(200);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/send_command', {
                method: 'POST',
                body: JSON.stringify({
                    "command": "set_rule",
                    "instance": "device5",
                    "rule": 100,
                    "target": "192.168.1.100"
                }),
                headers: postHeaders
            });
        });
    });

    it('logs error when set_rule API call fails', async () => {
        // Mock fetch function to simulate error response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Spy on console.log to confirm error logged
        const consoleSpy = jest.spyOn(console, 'log');

        // Get device5 card, slider minus button
        const card = app.getByText('Overhead lights').parentElement.parentElement;
        const minus = card.children[1].children[0].children[0].children[0];

        // Click minus button, confirm correct payload sent
        await user.click(minus);
        jest.advanceTimersByTime(200);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/send_command', {
                method: 'POST',
                body: JSON.stringify({
                    "command": "set_rule",
                    "instance": "device5",
                    "rule": 99,
                    "target": "192.168.1.100"
                }),
                headers: postHeaders
            });
        });

        // Confirm error response was logged to console
        await waitFor(() => {
            expect(consoleSpy).toHaveBeenCalledWith(
                'Failed to set rule for device5,', 'Unable to connect'
            );
        });
    });

    it('sends correct payload when rule slider is moved', async () => {
        jest.useRealTimers();

        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: { device2: "512" }
            })
        }));

        // Get device2 card, rule slider elements
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const sliderHandle = card.querySelector('.sliderHandle');
        const sliderTrack = card.querySelector('.sliderTrack');

        // Confirm current rule is 767 (displays 74, scaled to 1-100 range)
        expect(sliderHandle.innerHTML).toBe('74');

        // Mock slider element getBoundingClientRect to trick react-range that
        // slider was moved (can't simulate user input due to jsdom)
        sliderTrack.getBoundingClientRect = jest.fn(() => ({
            bottom: 20,
            height: 20,
            left: 0,
            right: 100,
            top: 0,
            width: 100,
            x: 0,
            y: 0
        }));
        sliderHandle.getBoundingClientRect = jest.fn(() => ({
            bottom: 20,
            height: 20,
            left: 45,
            right: 55,
            top: 0,
            width: 10,
            x: 45,
            y: 0
        }));

        // Simulate user dragging slider to make react-range call mocks above
        fireEvent.mouseDown(sliderHandle, { clientX: 0, clientY: 0 });
        fireEvent.mouseMove(document, { clientX: 50, clientY: 0 });
        fireEvent.mouseUp(document);

        // Confirm correct payload sent after debounce delay
        jest.advanceTimersByTime(200);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/send_command', {
                method: 'POST',
                body: JSON.stringify({
                    "command": "set_rule",
                    "instance": "device2",
                    "rule": 512,
                    "target": "192.168.1.100"
                }),
                headers: postHeaders
            });
        });

        // Confirm rule displayed on slider changed
        await waitFor(() => {
            expect(sliderHandle.innerHTML).toBe('50');
        });
    });

    it('sends correct payload when reset rule dropdown option clicked', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: {
                    device1: "Reverted to scheduled rule",
                    current_rule: 1023
                }
            })
        }));

        // Get device2 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Confirm current rule is 767 (displays 74, scaled to 1-100 range)
        const sliderHandle = card.querySelector('.sliderHandle');
        expect(sliderHandle.innerHTML).toBe('74');

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
                "instance": "device2",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm reset option is now disabled, current rule changed to 1023
        // (displays 100, scaled to 1-100 range)
        await waitFor(() => {
            expect(reset.classList).toContain('disabled');
            expect(sliderHandle.innerHTML).toBe('100');
        });
    });

    it('cancels slider edit mode immediately when reset rule clicked', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: {
                    device1: "Reverted to scheduled rule",
                    current_rule: 1023
                }
            })
        }));

        // Get device2 card, top-right corner dropdown menu, and slider elements
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];
        const sliderHandle = card.querySelector('.sliderHandle');
        const sliderTrack = card.querySelector('.sliderTrack');

        // Confirm current rule is 767 (displays 74, scaled to 1-100 range)
        expect(sliderHandle.innerHTML).toBe('74');

        // Mock slider element getBoundingClientRect to trick react-range that
        // slider was moved (can't simulate user input due to jsdom)
        sliderTrack.getBoundingClientRect = jest.fn(() => ({
            bottom: 20,
            height: 20,
            left: 0,
            right: 100,
            top: 0,
            width: 100,
            x: 0,
            y: 0
        }));
        sliderHandle.getBoundingClientRect = jest.fn(() => ({
            bottom: 20,
            height: 20,
            left: 45,
            right: 55,
            top: 0,
            width: 10,
            x: 45,
            y: 0
        }));

        // Simulate user dragging slider to make react-range call mocks above
        fireEvent.mouseDown(sliderHandle, { clientX: 0, clientY: 0 });
        fireEvent.mouseMove(document, { clientX: 50, clientY: 0 });
        fireEvent.mouseUp(document);

        // Confirm rule changed (now in edit mode, slider will not change when
        // main state updates until 6 seconds after slider move)
        expect(sliderHandle.innerHTML).not.toBe('74');

        // Click dropdown button, click reset option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Reset rule'));

        // Confirm rule changed immediately (canceled edit mode)
        waitFor(() => {
            expect(sliderHandle.innerHTML).toBe('100');
        });
    });

    it('sends correct payload when new schedule rule is added', async () => {
        jest.useRealTimers();

        // Mock fetch function to return expected response after 100ms delay
        global.fetch = jest.fn(() => new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({
                        status: 'success',
                        message: {
                            "time": "10:00",
                            "Rule added": "enabled"
                        }
                    })
                });
            }, 100);
        }));

        // Get device2 card, schedule rules button, schedule rules table, new rule button
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
                "instance": "device2",
                "time": "10:00",
                "rule": "enabled",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm loading animation appeared
        expect(app.container.querySelector('.spinner-border')).not.toBeNull();
    });

    it('sends correct payload when schedule rule value is edited', async () => {
        jest.useRealTimers();

        // Mock fetch function to return expected response after 100ms delay
        global.fetch = jest.fn(() => new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({
                        status: 'success',
                        message: {
                            "time": "sunrise",
                            "Rule added": "enabled"
                        }
                    })
                });
            }, 100);
        }));

        // Get device3 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click rule field on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[1].children[0].children[0]);
        const rulePopup = firstRule.children[1].children[0].children[1];

        // Change keyword dropdown to sunrise
        await user.selectOptions(within(rulePopup).getByLabelText('Rule'), 'disabled');

        // Click add rule button
        await user.click(firstRule.children[2].children[0]);

        // Confirm a single API call was made to overwrite rule with new value
        expect(global.fetch).toHaveBeenCalledTimes(1);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "add_rule",
                "instance": "device3",
                "time": "morning",
                "rule": "disabled",
                "overwrite": "overwrite",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm loading animation appeared
        expect(app.container.querySelector('.spinner-border')).not.toBeNull();
    });

    it('sends correct payload when schedule rule timestamp is edited', async () => {
        jest.useRealTimers();

        // Mock fetch function to return expected response after 100ms delay
        global.fetch = jest.fn(() => new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({
                        status: 'success',
                        message: {
                            "time": "sunrise",
                            "Rule added": "enabled"
                        }
                    })
                });
            }, 100);
        }));

        // Get device3 card, schedule rules button, schedule rules table, first rule row
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

        // Click add rule button, confirm loading animation appeared
        await user.click(firstRule.children[2].children[0]);
        expect(app.container.querySelector('.spinner-border')).not.toBeNull();

        // Confirm API call was made to add rule with new timestamp
        expect(global.fetch).toHaveBeenNthCalledWith(1, '/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "add_rule",
                "instance": "device3",
                "time": "sunrise",
                "rule": "enabled",
                "overwrite": "overwrite",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm second API call is made to remove rule with original timestamp
        await waitFor(() => {
            expect(global.fetch).toHaveBeenNthCalledWith(2, '/send_command', {
                method: 'POST',
                body: JSON.stringify({
                    "command": "remove_rule",
                    "instance": "device3",
                    "rule": "morning",
                    "target": "192.168.1.100"
                }),
                headers: postHeaders
            });
        });
    });

    it('sends correct payload when a schedule rule is deleted', async () => {
        // Mock fetch function to return expected response after 100ms delay
        global.fetch = jest.fn(() => new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({
                        status: 'success',
                        message: {
                            deleted: "morning"
                        }
                    })
                });
            }, 100);
        }));

        // Get device3 card, schedule rules button, schedule rules table, first rule row
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
                "instance": "device3",
                "rule": "morning",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('disables edit schedule rule button when time field is blank', async () => {
        // Get device3 card, schedule rules button, schedule rules table, first rule row
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
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: 'Done syncing schedule rules'
            })
        }));

        // Get device3 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click delete button on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[2].children[0]);

        // Confirm toast appeared
        await waitFor(() => {
            expect(app.queryByText(/persist after reboot/)).not.toBeNull();
        });

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
        // Get device3 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click delete button on first row
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[2].children[0]);
        jest.clearAllMocks();

        // Confirm toast appeared
        await waitFor(() => {
            expect(app.queryByText(/persist after reboot/)).not.toBeNull();
        });

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
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: {
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
                    "name": "device2",
                    "bright": 0,
                    "fading": false
                }
            })
        }));

        // Get device2 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click debug option, confirm correct request made
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Debug'));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "get_attributes",
                "instance": "device2",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm debug modal appeared with mock response text
        await waitFor(() => {
            expect(app.queryByText(/"nickname": "Accent lights"/)).not.toBeNull();
            // Confirm text does not include JSON wrapper
            expect(app.queryByText(/"status": "success"/)).toBeNull();
        });

        // Click modal close button, confirm closed
        await user.click(app.getAllByText('Debug')[1].parentElement.children[2]);
        await waitFor(() => {
            expect(app.queryByText(/"nickname": "Accent lights"/)).toBeNull();
        });

        // Show modal again, click backdrop, confirm closed
        await user.click(within(dropdown).getByText('Debug'));
        await user.click(document.querySelector('.modal-backdrop'));
        await waitFor(() => {
            expect(app.queryByText(/"nickname": "Accent lights"/)).toBeNull();
        });
    });

    it('shows schedule toggle modal when dropdown option clicked', async () => {
        // Get device2 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click schedule toggle option, confirm modal appeared
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Schedule Toggle'));
        expect(app.queryByText('Enable or disable after a delay.')).not.toBeNull();
    });

    it('shows start fade modal when dropdown option clicked', async () => {
        // Get device2 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click start fade option, confirm modal appeared
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Start Fade'));
        expect(app.queryByText('Duration (seconds)')).not.toBeNull();
    });

    it('highlights correct devices when sensor Show triggers option clicked', async () => {
        // Get sensor2 card, device6 card, device7 card
        const sensor2 = app.getByText('Temp sensor').parentElement.parentElement;
        const device6 = app.getByText('Air Conditioner').parentElement.parentElement;
        const device7 = app.getByText('Fan').parentElement.parentElement;

        // Confirm device cards do not have highlight class
        expect(device6.parentElement.classList).not.toContain('highlight-enter');
        expect(device7.parentElement.classList).not.toContain('highlight-enter');
        expect(app.container.querySelectorAll('.highlight-enter').length).toBe(0);

        // Click sensor2 "Show targets" dropdown option
        const dropdown = sensor2.children[0].children[2];
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Show targets'));

        // Confirm both target devices have highlight class, but no other cards
        await waitFor(() => {
            expect(device6.parentElement.classList).toContain('highlight-enter');
            expect(device7.parentElement.classList).toContain('highlight-enter');
            expect(app.container.querySelectorAll('.highlight-enter').length).toBe(2);
            expect(app.container.querySelectorAll('.highlight-enter-done').length).toBe(0);
        });

        // Wait for highlight animation to complete
        jest.advanceTimersByTime(1000);
        await waitFor(() => {
            expect(device6.parentElement.classList).toContain('highlight-enter-done');
            expect(device7.parentElement.classList).toContain('highlight-enter-done');
            expect(app.container.querySelectorAll('.highlight-enter').length).toBe(0);
            expect(app.container.querySelectorAll('.highlight-enter-done').length).toBe(2);
        });

        // Click anywhere in page, confirm highlight fades out
        await user.click(app.getByText('Motion'));
        expect(device6.parentElement.classList).not.toContain('highlight-enter');
        expect(device7.parentElement.classList).not.toContain('highlight-enter');
        expect(device6.parentElement.classList).toContain('highlight-exit');
        expect(device7.parentElement.classList).toContain('highlight-exit');
        expect(app.container.querySelectorAll('.highlight-exit').length).toBe(2);
    });

    it('shows ApiTargetRuleModal when "Change rule" dropdown option clicked', async () => {
        // Get device6 card and top-right corner dropdown menu
        const card = app.getByText('Air Conditioner').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Click dropdown button, click Change rule option, confirm modal appeared
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Change rule'));
        expect(app.queryByText('API Target Rule')).not.toBeNull();
    });

    it('sends the correct payload when ApiTarget rule is changed', async () => {
        // Get device6 card, open change rule modal
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
                "instance": "device6",
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
});
