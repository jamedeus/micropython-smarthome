import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContextIrRemotes } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('IrRemotes', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('status', mockContextIrRemotes.status);
        createMockContext('target_ip', mockContextIrRemotes.target_ip);
        createMockContext('recording', mockContextIrRemotes.recording);
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

        // Reset mock fetch calls (ApiCardContext makes request when rendered)
        jest.clearAllMocks();
    });

    it('sends correct payload when TV remote buttons are pressed', async () => {
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resovle({
                status: 'success',
                message: {
                    'tv': 'key_name'
                }
            })
        }));

        // Get remote div
        const remote = app.getByText('TV Remote').parentElement.parentElement;

        // Click power button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[0]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "power",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click source button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[1]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "source",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click up button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[2]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "up",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click left button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[3]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "left",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click enter button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[4]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "enter",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click right button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[5]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "right",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click down button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[6]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "down",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click vol_down button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[7]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "vol_down",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click mute button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[8]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "mute",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click vol_up button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[9]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "vol_up",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click settings button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[10]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "settings",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click exit button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[11]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "tv",
                "key": "exit",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when AC remote buttons are pressed', async () => {
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resovle({
                status: 'success',
                message: {
                    'ac': 'key_name'
                }
            })
        }));

        // Get remote div
        const remote = app.getByText('AC Remote').parentElement.parentElement;

        // Click stop button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[0]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "ac",
                "key": "stop",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click off button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[1]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "ac",
                "key": "off",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
        jest.clearAllMocks();

        // Click start button, confirm correct payload sent
        await user.click(within(remote).getAllByRole('button')[2]);
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir",
                "ir_target": "ac",
                "key": "start",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('sends correct payload when IR macro button is pressed', async () => {
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resovle({
                status: 'success',
                message: {
                    'Ran macro': 'backlight_on'
                }
            })
        }));

        // Get macros div
        const macros = app.getByText('IR Macros').parentElement.parentElement;

        // Click backlight_on macro, confirm correct payload sent
        await user.click(within(macros).getByText('backlight_on'));
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir_run_macro",
                "macro_name": "backlight_on",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('opens EditIrMacroModal modal when edit option is clicked', async () => {
        // Get macros div, green pencil button next to backlight_off macro
        const macros = app.getByText('IR Macros').parentElement.parentElement;
        const edit = within(macros).getByText('backlight_off').parentElement.children[1];

        // Open dropdown next to backlight_off macro, click edit option
        await user.click(edit.children[0]);
        await user.click(within(macros).getByText('Edit'));

        // Confirm modal appeared
        expect(app.queryByText('Editing backlight_off')).not.toBeNull();

        // Click modal close button, confirm closed
        await user.click(app.getByText('Editing backlight_off').parentElement.children[2]);
        expect(app.queryByText('Editing backlight_off')).toBeNull();

        // Show modal again, click backdrop, confirm closed
        await user.click(within(macros).getByText('Edit'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(app.queryByText('Editing backlight_off')).toBeNull();

        // Show modal again, click cancel button, confirm closed
        await user.click(within(macros).getByText('Edit'));
        await user.click(app.getByRole('button', { name: 'Cancel' }));
        expect(app.queryByText('Editing backlight_off')).toBeNull();
    });

    it('sends correct payload when EditIrMacroModal modal is submitted', async () => {
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resovle({
                status: 'success',
                message: 'Done'
            })
        }));

        // Get macros div, open edit modal for backlight_off macro
        const macros = app.getByText('IR Macros').parentElement.parentElement;
        const edit = within(macros).getByText('backlight_off').parentElement.children[1];
        await user.click(edit.children[0]);
        await user.click(within(macros).getByText('Edit'));

        // Get modal, table of macro actions
        const modal = app.getByText('Editing backlight_off').parentElement.parentElement;
        const table = modal.querySelector('table');

        // Click delete button for first row
        await user.click(within(table).getAllByRole('button')[0]);

        // Set delay for first row to 1000
        await user.clear(within(table).getAllByRole('textbox')[0]);
        await user.type(within(table).getAllByRole('textbox')[0], '1000');

        // Set repeat for first row to 5
        await user.clear(within(table).getAllByRole('textbox')[1]);
        await user.type(within(table).getAllByRole('textbox')[1], '5');

        // Click edit button, confirm correct payload sent
        await user.click(within(modal).getByRole('button', { name: 'Edit' }));
        expect(global.fetch).toHaveBeenCalledWith('/edit_ir_macro', {
            method: 'POST',
            body: JSON.stringify({
                "ip": "192.168.1.100",
                "name": "backlight_off",
                "actions": [
                    "tv right 1000 5",
                    "tv down 500 1",
                    "tv enter 150 1",
                    "tv left 150 14",
                    "tv exit 1 1"
                ]
            }),
            headers: postHeaders
        });
    });

    it('deletes macro when last action in EditIrMacroModal is removed', async () => {
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resovle({
                status: 'success',
                message: 'Done'
            })
        }));

        // Get macros div, open edit modal for backlight_off macro
        const macros = app.getByText('IR Macros').parentElement.parentElement;
        const edit = within(macros).getByText('backlight_off').parentElement.children[1];
        await user.click(edit.children[0]);
        await user.click(within(macros).getByText('Edit'));

        // Get modal, table of macro actions
        const modal = app.getByText('Editing backlight_off').parentElement.parentElement;
        const table = modal.querySelector('table');

        // Click delete buttons for all actions
        await user.click(within(table).getAllByRole('button')[0]);
        await user.click(within(table).getAllByRole('button')[0]);
        await user.click(within(table).getAllByRole('button')[0]);
        await user.click(within(table).getAllByRole('button')[0]);
        await user.click(within(table).getAllByRole('button')[0]);
        await user.click(within(table).getAllByRole('button')[0]);

        // Confirm modal was closed automatically, correct request was made
        expect(app.queryByText('Editing backlight_off')).toBeNull();
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir_delete_macro",
                "macro_name": "backlight_off",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('deletes macro when dropdown option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resovle({
                status: 'success',
                message: 'Done'
            })
        }));

        // Get macros div, click delete option in backlight_off dropdown
        const macros = app.getByText('IR Macros').parentElement.parentElement;
        const edit = within(macros).getByText('backlight_off').parentElement.children[1];
        await user.click(edit.children[0]);
        await user.click(within(macros).getByText('Delete'));

        // Confirm correct request was made
        expect(global.fetch).toHaveBeenCalledWith('/send_command', {
            method: 'POST',
            body: JSON.stringify({
                "command": "ir_delete_macro",
                "macro_name": "backlight_off",
                "target": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('resumes recording when record option in existing macro dropdown is clicked', async () => {
        // Get TV remote, confirm not recording
        const remote = app.getByText('TV Remote').parentElement.parentElement;
        expect(within(remote).getAllByRole('button')[0].classList).not.toContain('blue-glow');

        // Get macros div, click record option in backlight_off dropdown
        const macros = app.getByText('IR Macros').parentElement.parentElement;
        const edit = within(macros).getByText('backlight_off').parentElement.children[1];
        await user.click(edit.children[0]);
        await user.click(within(macros).getByText('Record'));

        // Confirm remote buttons have blue glow, button text changed to Save Macro
        expect(within(remote).getAllByRole('button')[0].classList).toContain('blue-glow');
        expect(within(macros).queryByText('Start Recording')).toBeNull();
        expect(within(macros).queryByText('Save Macro')).not.toBeNull();
    });

    it('starts recording macro when new name entered and button pressed', async () => {
        // Get TV remote, confirm not recording
        const remote = app.getByText('TV Remote').parentElement.parentElement;
        expect(within(remote).getAllByRole('button')[0].classList).not.toContain('blue-glow');

        // Get macros div, open collapse
        const macros = app.getByText('IR Macros').parentElement.parentElement;
        await user.click(macros.children[3]);

        // Enter new macro name, click start recording button
        await user.type(within(macros).getByRole('textbox'), 'New Macro');
        await user.click(app.getByRole('button', { name: 'Start Recording' }));

        // Confirm remote buttons have blue glow, button text changed to Save Macro
        expect(within(remote).getAllByRole('button')[0].classList).toContain('blue-glow');
        expect(within(macros).queryByText('Start Recording')).toBeNull();
        expect(within(macros).queryByText('Save Macro')).not.toBeNull();
    });

    it('sends correct payload when new macro is saved', async () => {
        // Get remote divs, macros div
        const tvRemote = app.getByText('TV Remote').parentElement.parentElement;
        const acRemote = app.getByText('AC Remote').parentElement.parentElement;
        const macros = app.getByText('IR Macros').parentElement.parentElement;

        // Start recording new macro
        await user.click(macros.children[3]);
        await user.type(within(macros).getByRole('textbox'), 'New Macro');
        await user.click(app.getByRole('button', { name: 'Start Recording' }));

        // Click TV power button, AC start cooling button
        await user.click(within(tvRemote).getAllByRole('button')[0]);
        await user.click(within(acRemote).getAllByRole('button')[2]);

        // Click Save Macro, confirm correct payload sent
        await user.click(app.getByRole('button', { name: 'Save Macro' }));
        expect(global.fetch).toHaveBeenCalledWith('/add_ir_macro', {
            method: 'POST',
            body: JSON.stringify({
                "ip": "192.168.1.100",
                "name": "New Macro",
                "actions": [
                    "tv power 100 1",
                    "ac start 100 1"
                ]
            }),
            headers: postHeaders
        });

        // Confirm a button for the new macro was rendered in macros div
        expect(within(macros).getByRole('button', { name: 'New Macro' })).not.toBeNull();
    });

    it('resumes recording if existing macro name entered in new macro field', async () => {
        // Get TV remote div, macros div
        const tvRemote = app.getByText('TV Remote').parentElement.parentElement;
        const macros = app.getByText('IR Macros').parentElement.parentElement;

        // Enter existing macro name in new macro field, press enter to start recording
        await user.click(macros.children[3]);
        await user.type(within(macros).getByRole('textbox'), 'backlight_off');
        await user.type(within(macros).getByRole('textbox'), '{enter}');

        // Click TV mute button
        await user.click(within(tvRemote).getAllByRole('button')[8]);

        // Click Save Macro, confirm edit_ir_macro was called (not add_ir_macro)
        await user.click(app.getByRole('button', { name: 'Save Macro' }));
        expect(global.fetch).toHaveBeenCalledWith('/edit_ir_macro', {
            method: 'POST',
            body: JSON.stringify({
                "ip": "192.168.1.100",
                "name": "backlight_off",
                "actions": [
                    "tv settings 1500 1",
                    "tv right 500 1",
                    "tv down 500 1",
                    "tv enter 150 1",
                    "tv left 150 14",
                    "tv exit 1 1",
                    "tv mute 100 1"
                ]
            }),
            headers: postHeaders
        });
    });
});
