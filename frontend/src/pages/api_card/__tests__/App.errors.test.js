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

    it('does not change power button class when turn_on API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve('Error: Unable to connect.')
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
            json: () => Promise.resolve('Error: Unable to connect.')
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
            json: () => Promise.resolve('Error: Unable to connect.')
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
            json: () => Promise.resolve('Error: Unable to connect.')
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

        // Confirm fetch was called, but card did not collapse
        expect(global.fetch).toHaveBeenCalled();
        expect(collapse.classList).toContain('show');
    });

    it('does not expand card when enable API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve('Error: Unable to connect.')
        }));

        // Get device1 card and top-right corner dropdown menu
        const card = app.getByText('Humidifier').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Get card body collapse section, confirm closed (device disabled)
        const collapse = card.children[1];
        expect(collapse.classList).not.toContain('show');

        // Click dropdown button, click enable option
        await user.click(dropdown.children[0]);
        await user.click(within(dropdown).getByText('Enable'));

        // Confirm fetch was called, but card did not expand
        expect(global.fetch).toHaveBeenCalled();
        expect(collapse.classList).not.toContain('show');
    });

    it('does not change rule or disable dropdown option when reset_rule API call fails', async () => {
        // Mock fetch function to simulate failed API call
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve('Error: Unable to connect.')
        }));

        // Get device3 card and top-right corner dropdown menu
        const card = app.getByText('Accent lights').parentElement.parentElement;
        const dropdown = card.children[0].children[2];

        // Confirm current rule is 767
        const sliderHandle = card.querySelector('.sliderHandle');
        expect(sliderHandle.innerHTML).toBe('767');

        // Confirm current rule is 767
        expect(within(card).getByText('767')).toBeInTheDocument();

        // Click dropdown button, get reset option, confirm not disabled
        await user.click(dropdown.children[0]);
        const reset = within(dropdown).getByText('Reset rule');
        expect(reset.classList).not.toContain('disabled');

        // Click reset, confirm request was made but option still enabled
        await user.click(reset);
        expect(global.fetch).toHaveBeenCalled();
        expect(reset.classList).not.toContain('disabled');

        // Confirm current rule did not change
        expect(sliderHandle.innerHTML).toBe('767');
    });
});
