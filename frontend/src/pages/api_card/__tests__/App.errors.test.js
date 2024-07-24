import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';

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

        // Reset mock fetch calls (ApiCardContext makes request when rendered)
        jest.clearAllMocks();
    });

    it('does not change power button class when turn_on API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Get device5 power button (turned off), confirm does not have turn on or turn off class
        const powerButton = app.getByText('Stairway lights').parentElement.children[0];
        expect(powerButton.classList).not.toContain('btn-active-enter');
        expect(powerButton.classList).not.toContain('btn-active-exit');

        // Click power button, confirm request was made but still does not have turn on class
        await user.click(powerButton);
        expect(global.fetch).toHaveBeenCalled();
        expect(powerButton.classList).not.toContain('btn-active-enter');
        expect(powerButton.classList).not.toContain('btn-active-exit');
    });

    it('does not change power button class when turn_off API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Get device3 power button (turned on), confirm does not have turn on or turn off class
        const powerButton = app.getByText('Stairway lights').parentElement.children[0];
        expect(powerButton.classList).not.toContain('btn-active-enter');
        expect(powerButton.classList).not.toContain('btn-active-exit');

        // Click power button, confirm request was made but still does not have turn off class
        await user.click(powerButton);
        expect(global.fetch).toHaveBeenCalled();
        expect(powerButton.classList).not.toContain('btn-active-enter');
        expect(powerButton.classList).not.toContain('btn-active-exit');
    });

    it('does not change trigger button class when trigger_sensor API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Get sensor4 trigger button, confirm does not have either class
        const triggerButton = app.getByText('Computer activity').parentElement.children[0];
        expect(triggerButton.classList).not.toContain('btn-active-enter');
        expect(triggerButton.classList).not.toContain('btn-active-exit');

        // Click trigger button, confirm request was made but still does not have either class
        await user.click(triggerButton);
        expect(global.fetch).toHaveBeenCalled();
        expect(triggerButton.classList).not.toContain('btn-active-enter');
        expect(triggerButton.classList).not.toContain('btn-active-exit');
    });

    it('does not collapse card when disable API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Get device5 card and top-right corner dropdown menu
        const card = app.getByText('Stairway lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Get card body collapse section, confirm open (device enabled)
        const collapse = card.children[1];
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
        });

        // Click dropdown button, click disable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Disable'));

        // Confirm fetch was called, but card did not collapse
        expect(global.fetch).toHaveBeenCalled();
        await waitFor(() => {
            expect(collapse.classList).toContain('show');
        });
    });

    it('does not expand card when enable API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Get device1 card and top-right corner dropdown menu
        const card = app.getByText('Humidifier').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Get card body collapse section, confirm closed (device disabled)
        const collapse = card.children[1];
        await waitFor(() => {
            expect(collapse.classList).not.toContain('show');
        });

        // Click dropdown button, click enable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Enable'));

        // Confirm fetch was called, but card did not expand
        expect(global.fetch).toHaveBeenCalled();
        await waitFor(() => {
            expect(collapse.classList).not.toContain('show');
        });
    });

    it('does not change rule or disable dropdown option when reset_rule API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Get device3 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Confirm current rule is 767 (displays 74, scaled to 1-100 range)
        const sliderHandle = card.querySelector('.sliderHandle');
        expect(sliderHandle.innerHTML).toBe('74');

        // Click dropdown button, get reset option, confirm not disabled
        await user.click(dropdown.children[0]);
        const reset = within(dropdown).getByText('Reset rule');
        expect(reset.classList).not.toContain('disabled');

        // Click reset, confirm request was made but option still enabled
        await user.click(reset);
        expect(global.fetch).toHaveBeenCalled();
        expect(reset.classList).not.toContain('disabled');

        // Confirm current rule did not change
        expect(sliderHandle.innerHTML).toBe('74');
    });

    it('shows alert and resets loading animation if add_rule API call fails', async () => {
        // Mock fetch function to simulate failed API call, mock alert function
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));
        global.alert = jest.fn();

        // Get device3 card, schedule rules button, schedule rules table, new rule button
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const addRule = rulesTable.parentElement.children[1].children[0];

        // Open schedule rules table, click add rule button
        await user.click(scheduleRulesButton);
        await user.click(addRule);
        const newRuleRow = rulesTable.children[1].children[3];

        // Click timestamp field, get PopupDiv, type 10:00 into timestamp field
        await user.click(newRuleRow.children[0].children[0].children[0]);
        const timePopup = newRuleRow.children[0].children[0].children[1];
        await user.type(within(timePopup).getByLabelText('Time'), '10:00');

        // Click add rule button, confirm request was made
        await user.click(newRuleRow.children[2].children[0]);
        expect(global.fetch).toHaveBeenCalled();

        // Confirm alert appeared, button loading animation reset
        expect(global.alert).toHaveBeenCalledWith('Failed to add schedule rule');
        expect(newRuleRow.children[2].children[0].querySelector('.bi-plus-lg')).not.toBeNull();
    });

    it('shows alert and resets loading animation if edit rule API call fails', async () => {
        // Mock fetch function to simulate failed API call, mock alert function
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));
        global.alert = jest.fn();

        // Get device4 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Open schedule rules table, click time field on first row, change keyword
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[0].children[0].children[0]);
        const timePopup = firstRule.children[0].children[0].children[1];
        await user.selectOptions(within(timePopup).getAllByLabelText('Keyword')[0], 'sunrise');

        // Click add rule button, confirm request was made
        await user.click(firstRule.children[2].children[0]);
        expect(global.fetch).toHaveBeenCalled();

        // Confirm alert appeared, button loading animation reset
        expect(global.alert).toHaveBeenCalledWith('Failed to edit schedule rule');
        expect(firstRule.children[2].children[0].querySelector('.bi-pencil')).not.toBeNull();
    });

    it('shows alert and resets loading animation if delete rule API call fails', async () => {
        // Mock fetch function to simulate failed API call, mock alert function
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));
        global.alert = jest.fn();

        // Get device4 card, schedule rules button, schedule rules table, first rule row
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const scheduleRulesButton = within(card).getByText('Schedule rules');
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        const firstRule = rulesTable.children[1].children[0];

        // Click delete button on first row of table, confirm request was made
        await user.click(scheduleRulesButton);
        await user.click(firstRule.children[2].children[0]);
        expect(global.fetch).toHaveBeenCalled();

        // Confirm alert appeared, button loading animation reset
        expect(global.alert).toHaveBeenCalledWith('Failed to delete schedule rule');
        expect(firstRule.children[2].children[0].querySelector('.bi-trash')).not.toBeNull();
    });

    it('throws error when sync_schedule_rules API call fails', async () => {
        // Mock first fetch call to succeed, second to simulate failed API call
        const mockFetchResponses = [
            Promise.resolve({ ok: true }),
            Promise.resolve({
                ok: false,
                status: 500,
                json: () => Promise.resolve({
                    status: 'error',
                    message: 'Failed to save rules'
                })
            })
        ];
        global.fetch = jest.fn(() => mockFetchResponses.shift());
        // Mock console.error
        console.error = jest.fn();

        // Get device4 card, schedule rules table, click first delete button
        const card = app.getByText('Computer screen').parentElement.parentElement;
        const rulesTable = within(card).getByText('Time').parentElement.parentElement.parentElement;
        await user.click(within(rulesTable).getAllByRole('button')[0]);

        // Get toast, click yes, confirm fetch was called
        const toast = app.getByText('Should this rule change persist after reboot?').parentElement;
        await user.click(within(toast).getByText('Yes'));
        expect(global.fetch).toHaveBeenCalled();

        // Confirm console.error was called
        expect(console.error).toHaveBeenCalledWith(
            'Failed to sync schedule rules',
            'Failed to save rules'
        );
    });
});
