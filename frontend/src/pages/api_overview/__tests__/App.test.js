import React from 'react';
import App from '../ApiOverview';
import { ApiOverviewContextProvider } from 'root/ApiOverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockNodes2floors, mockMacros } from './mockContext';

describe('App', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('nodes', mockNodes2floors);
        createMockContext('macros', mockMacros);
        createMockContext('recording', '');
    });

    beforeEach(() => {
        // Render app + create userEvent instance to use in tests
        user = userEvent.setup();
        app = render(
            <ApiOverviewContextProvider>
                <App />
            </ApiOverviewContextProvider>
        );
    });

    it('redirects to config overview when manage button is clicked', async () => {
        // Click manage button at bottom of page, confirm redirected
        await user.click(app.getByRole('button', { name: 'Manage' }));
        expect(window.location.href).toBe('/config_overview');
    });

    it('redirects to api card page when node buttons are clicked', async () => {
        // Click Bedroom button, confirm redirected
        await user.click(app.getByRole('button', { name: 'Bedroom' }));
        expect(window.location.href).toBe('/api/Bedroom');
    });

    it('hides the loading overlay when navigated to with back button', async () => {
        // Click node button, confirm loading overlay appears
        await user.click(app.getByRole('button', { name: 'Bedroom' }));
        expect(document.getElementById('loading_overlay')).toBeInTheDocument();

        // Simulate user returning to overview by pressing back button
        const event = new Event('pageshow');
        Object.defineProperty(event, 'persisted', {
            get: () => true,
        });
        window.dispatchEvent(event);

        // Confirm loading overlay is hidden automatically
        await waitFor(() => {
            expect(document.getElementById('loading_overlay')).not.toBeInTheDocument();
        });
    });

    it('sends the correct request when "Reboot all" option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click "Reboot all" dropdown option in top-right corner menu
        const header = app.getByText('Api Overview').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Reboot all'));

        // Confirm correct request was sent
        expect(global.fetch).toHaveBeenCalledWith('/reboot_all');
    });

    it('sends the correct request when "Reset all rules" option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click "Reset all rules" dropdown option in top-right corner menu
        const header = app.getByText('Api Overview').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Reset all rules'));

        // Confirm correct request was sent
        expect(global.fetch).toHaveBeenCalledWith('/reset_all');
    });

    it('sends the correct request when a macro is run', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true, status: 200 }));

        // Click "Late" macro button, confirm correct request sent
        await user.click(app.getByText('Late'));
        expect(global.fetch).toHaveBeenCalledWith('/run_macro/late');

        // Confirm "Late" text gone, wait for checkmark to replace loading animation
        expect(app.queryByText('Late')).toBeNull();
        await waitFor(() => {
            expect(app.container.querySelector('.loading-animation')).toBeNull();
            expect(app.container.querySelector('.checkmark')).not.toBeNull();
        });
    });

    it('sends the correct request when a macro is deleted', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true, status: 200 }));

        // Get "Late" macro button, open dropdown next to it
        const macroButton = app.getByText('Late').parentElement;
        await user.click(macroButton.parentElement.children[1].children[0]);

        // Click Delete option in dropdown, confirm correct request sent
        await user.click(app.getByText('Delete'));
        expect(global.fetch).toHaveBeenCalledWith('/delete_macro/late');
    });

    it('focuses new macro name field when collapse is opened', async () => {
        // Get macro section, open collapse, confirm field is focused
        const macros = app.container.querySelector('.macro-container');
        await user.click(macros.querySelector('.bi-plus-lg'));
        await waitFor(() => {
            expect(app.getByPlaceholderText('New macro name')).toHaveFocus();
        }, { timeout: 1500 });

        // Close collapse, confirm field is not focused
        await user.click(macros.querySelector('.bi-plus-lg'));
        expect(app.getByPlaceholderText('New macro name')).not.toHaveFocus();
    });

    it('starts recording macro when a new name is entered', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ status: 200 }));

        // Get macro section
        const macros = app.container.querySelector('.macro-container');

        // Open collapse, enter new name, click start
        await user.click(macros.querySelector('.bi-plus-lg'));
        await user.type(app.getByPlaceholderText('New macro name'), 'New macro');
        await user.click(app.getByText('Start Recording'));

        // Confirm sent request to check if macro name is duplicate
        expect(global.fetch).toHaveBeenCalledWith('/macro_name_available/New macro');

        // Confirm start button changed to finish, instructions modal appeared
        expect(app.queryByText('Start Recording')).toBeNull();
        expect(app.queryByText('Finish Recording')).not.toBeNull();
        expect(app.queryByText('Macro Instructions')).not.toBeNull();

        // Confirm URL was changed
        expect(global.history.pushState).toHaveBeenCalledWith(
            {}, '', '/api/recording/New macro'
        );
    });

    it('redirects to different URL if node buttons are clicked while recording', async () => {
        // Get macro section, start recording new macro
        const macros = app.container.querySelector('.macro-container');
        await user.click(within(macros).getAllByRole('button')[5]);
        await user.type(app.getByPlaceholderText('New macro name'), 'Macro');
        await user.click(app.getByText('Start Recording'));
        jest.clearAllMocks();

        // Click Bedroom button, confirm name of new macro is appended to URL
        await user.click(app.getByRole('button', { name: 'Bedroom' }));
        expect(window.location.href).toBe('/api/Bedroom/Macro');
    });

    it('starts recording when enter key is pressed in new name field', async () => {
        // Get macro section, enter new macro name
        const macros = app.container.querySelector('.macro-container');
        await user.click(within(macros).getAllByRole('button')[5]);
        await user.type(app.getByPlaceholderText('New macro name'), 'Macro');

        // Simulate user pressing enter in new name field, confirm started recording
        await user.type(app.getByPlaceholderText('New macro name'), '{enter}');
        expect(global.fetch).toHaveBeenCalledWith('/macro_name_available/Macro');
        expect(global.history.pushState).toHaveBeenCalledWith(
            {}, '', '/api/recording/Macro'
        );
    });

    it('does not start recording when a duplicate name is entered', async () => {
        // Mock fetch to return status indicating duplicate name
        global.fetch = jest.fn(() => Promise.resolve({ status: 409 }));

        // Get macro section, open collapse, enter duplicate name in input
        const macros = app.container.querySelector('.macro-container');
        await user.click(within(macros).getAllByRole('button')[5]);
        await user.type(app.getByPlaceholderText('New macro name'), 'late');

        // Click start, confirm request sent to check if macro name is duplicate
        await user.click(app.getByText('Start Recording'));
        expect(global.fetch).toHaveBeenCalledWith('/macro_name_available/late');

        // Confirm button did not change, red "Name already in use" text appeared
        expect(app.queryByText('Start Recording')).not.toBeNull();
        expect(app.queryByText('Name already in use')).not.toBeNull();

        // Confirm modal did not open, URL was not changed
        expect(app.queryByText('Macro Instructions')).toBeNull();
        expect(global.history.pushState).not.toHaveBeenCalled();
    });

    it('stops recording when "Finish Recording" button is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ status: 200 }));

        // Get macro section, start recording new macro
        const macros = app.container.querySelector('.macro-container');
        await user.click(within(macros).getAllByRole('button')[5]);
        await user.type(app.getByPlaceholderText('New macro name'), 'Macro');
        await user.click(app.getByText('Start Recording'));

        // Click "Finish Recording", confirm button and URL change back
        await user.click(app.getByText('Finish Recording'));
        expect(app.queryByText('Start Recording')).not.toBeNull();
        expect(app.queryByText('Finish Recording')).toBeNull();
        expect(global.history.pushState).toHaveBeenCalledWith({}, '', '/api');
    });

    it('sets cookie when instructions modal closed if dont show again checked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ status: 200 }));

        // Get macro section, start recording new macro
        const macros = app.container.querySelector('.macro-container');
        await user.click(within(macros).getAllByRole('button')[5]);
        await user.type(app.getByPlaceholderText('New macro name'), 'New macro name');
        await user.click(app.getByText('Start Recording'));
        jest.clearAllMocks();

        // Check "Don't show again box", close modal
        await user.click(app.getByText("Don't show again"));
        await user.click(app.getByRole('button', { name: 'OK' }));

        // Confirm correct request was made (returns cookie in production)
        expect(global.fetch).toHaveBeenCalledWith('/skip_instructions');
    });

    it('does not set cookie if instructions modal closed without checking box', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ status: 200 }));

        // Get macro section, start recording new macro
        const macros = app.container.querySelector('.macro-container');
        await user.click(within(macros).getAllByRole('button')[5]);
        await user.type(app.getByPlaceholderText('New macro name'), 'New macro name');
        await user.click(app.getByText('Start Recording'));
        jest.clearAllMocks();

        // Close modal, confirm no request was sent
        await user.click(app.getByRole('button', { name: 'OK' }));
        expect(global.fetch).not.toHaveBeenCalled();
    });

    it('does not open modal if skip_instructions cookie exists', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ status: 200 }));

        // Simulate cookie set when user clicks don't show again
        document.cookie = 'skip_instructions=true; path=/';

        // Get macro section, start recording new macro
        const macros = app.container.querySelector('.macro-container');
        await user.click(within(macros).getAllByRole('button')[5]);
        await user.type(app.getByPlaceholderText('New macro name'), 'New macro name');
        await user.click(app.getByText('Start Recording'));

        // Confirm modal did not appear
        expect(app.queryByText('Macro Instructions')).toBeNull();
    });

    it('opens EditMacroModal when edit dropdown options is clicked', async () => {
        // Get "Late" macro button, open dropdown next to it
        const macroButton = app.getByText('Late').parentElement;
        await user.click(macroButton.parentElement.children[1].children[0]);

        // Click Edit option in dropdown, confirm EditMacroModal appeared
        await user.click(app.getByText('Edit'));
        expect(app.queryByText('Edit Late Macro')).not.toBeNull();

        // Click close button, confirm modal closes
        await user.click(app.getByText('Edit Late Macro').parentElement.children[2]);
        expect(app.queryByText('Edit Late Macro')).toBeNull();

        // Open modal again, click backdrop, confirm modal closes
        await user.click(app.getByText('Edit'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(app.queryByText('Edit Late Macro')).toBeNull();
    });

    it('makes correct request when macro action is deleted', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Open EditMacroModal for "Late" macro, get modal and actions table
        const macroButton = app.getByText('Late').parentElement;
        await user.click(macroButton.parentElement.children[1].children[0]);
        await user.click(app.getByText('Edit'));
        const modal = app.getByText('Edit Late Macro').parentElement.parentElement;
        const actions = modal.children[1];

        // Click delete button next to first action, confirm correct request made
        await user.click(within(actions).getAllByRole('button')[0]);
        expect(global.fetch).toHaveBeenCalledWith('/delete_macro_action/late/0');
    });

    it('deletes macro when last action is deleted in edit modal', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Open EditMacroModal for "Bright" macro, get modal and actions table
        const macroButton = app.getByText('Bright').parentElement;
        await user.click(macroButton.parentElement.children[1].children[0]);
        await user.click(app.getByText('Edit'));
        const modal = app.getByText('Edit Bright Macro').parentElement.parentElement;
        const actions = modal.children[1].children[1].children[1];

        // Confirm 8 actions exist
        expect(actions.children.length).toBe(8);

        // Delete first 7 actions, wait for each row to fade out before next click
        for (let i = 1; i < 8; i++) {
            await user.click(actions.querySelectorAll('.btn-danger')[0]);
            await waitFor(() => {
                expect(actions.children.length).toBe(8 - i)
            });
        }

        // Delete last action, confirm modal closes and request to delete macro is sent
        await user.click(actions.querySelectorAll('.btn-danger')[0]);
        await waitFor(() => {
            expect(app.queryByText('Edit Bright Macro')).toBeNull();
            expect(global.fetch).toHaveBeenCalledWith('/delete_macro/bright');
        });
    });

    it('resumes recording when "Record More" button is clicked', async () => {
        // Get "Late" macro button, open dropdown next to it
        const macroButton = app.getByText('Late').parentElement;
        await user.click(macroButton.parentElement.children[1].children[0]);

        // Click Edit option in dropdown, click "Record More" button
        await user.click(app.getByText('Edit'));
        await user.click(app.getByRole('button', { name: 'Record More' }));

        // Confirm started recording, URL was changed
        expect(app.queryByText('Start Recording')).toBeNull();
        expect(app.queryByText('Finish Recording')).not.toBeNull();
        expect(global.history.pushState).toHaveBeenCalledWith(
            {}, '', '/api/recording/late'
        );
    });

    it('shows an alert when macro API calls fail', async () => {
        // Mock fetch function to simulate failed API call, mock alert function
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 404
        }));
        global.alert = jest.fn();

        // Click the "Bright" macro button, confirm alert was shown
        await user.click(app.getByText('Bright'));
        expect(global.alert).toHaveBeenCalledWith('failed to run bright macro');
        jest.clearAllMocks();

        // Get "Late" macro button, open dropdown next to it
        const macroButton = app.getByText('Late').parentElement;
        await user.click(macroButton.parentElement.children[1].children[0]);

        // Click Delete option in dropdown, confirm alert was shown
        await user.click(app.getByText('Delete'));
        expect(global.alert).toHaveBeenCalledWith('Failed to delete macro');
        jest.clearAllMocks();

        // Click Edit option in dropdown, confirm EditMacroModal appeared
        await user.click(app.getByText('Edit'));
        const modal = app.getByText('Edit Late Macro').parentElement.parentElement;
        const actions = modal.children[1];

        // Click delete button next to first action, confirm alert was shown
        await user.click(within(actions).getAllByRole('button')[0]);
        expect(global.alert).toHaveBeenCalledWith('Failed to delete macro action');
    });
});
