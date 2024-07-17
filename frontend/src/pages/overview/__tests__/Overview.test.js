import React from 'react';
import App from '../Overview';
import { OverviewContextProvider } from 'root/OverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { postHeaders } from 'src/testUtils/headers';

describe('App', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('not_uploaded', mockContext.not_uploaded);
        createMockContext('uploaded', mockContext.uploaded);
        createMockContext('schedule_keywords', mockContext.schedule_keywords);
        createMockContext('desktop_integration_link', mockContext.desktop_integration_link);
        createMockContext('client_ip', mockContext.client_ip);
    });

    beforeEach(() => {
        // Render app + create userEvent instance to use in tests
        user = userEvent.setup();
        app = render(
            <OverviewContextProvider>
                <App />
            </OverviewContextProvider>
        );
    });

    it('redirects to api overview when "Frontend" button is clicked', async () => {
        // Click frontend button at bottom of page, confirm redirected
        await user.click(app.getByRole('button', { name: 'Frontend' }));
        expect(window.location.href).toBe('/api');
    });

    it('redirects edit config when "Create new config" button is clicked', async () => {
        // Click Create new config button, confirm redirected
        await user.click(app.getByRole('button', { name: 'Create new config' }));
        expect(window.location.href).toBe('/new_config');
    });

    it('opens WifiModal when "Set WIFI credentials" option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click "Set WIFI credentials" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Set WIFI credentials'));

        // Confirm WifiModal appeared
        expect(app.queryByText('Set Default Wifi')).not.toBeNull();
    });

    it('opens GpsModal when "Set GPS coordinates" option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click "Set GPS coordinates" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Set GPS coordinates'));

        // Confirm GpsModal appeared
        expect(app.queryByText('Set Default Location')).not.toBeNull();
    });

    it('sends the correct request when "Re-upload all" option is clicked', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({'success': [], 'failed': {}})
        }));

        // Click "Reboot all" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Re-upload all'));

        // Confirm correct request was sent
        expect(global.fetch).toHaveBeenCalledWith('/reupload_all');
    });

    it('opens RestoreModal when "Restore config" option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click "Restore config" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Restore config'));

        // Confirm RestoreModal appeared
        expect(app.queryByText(/This menu downloads config files from existing nodes/)).not.toBeNull();
    });

    it('opens DesktopIntegrationModal when "Desktop integration" option is clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Click "Desktop integration" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Desktop integration'));

        // Confirm DesktopIntegrationModal.js appeared
        expect(app.queryByText('Install Desktop Integration')).not.toBeNull();
    });

    it('sends the correct request when a new config is uploaded', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve('uploaded')
        }));

        // Get new config table, enter IP in first input
        const newConfigs = app.getByText('Configs Ready to Upload').parentElement;
        await user.type(within(newConfigs).getAllByRole('textbox')[0], '192.168.1.105');

        // Click upload button, confirm correct request sent
        await user.click(within(newConfigs).getAllByText('Upload')[0]);
        expect(global.fetch).toHaveBeenCalledWith('upload', {
            method: 'POST',
            body: JSON.stringify({
                "config": "new-config.json",
                "ip": "192.168.1.105"
            }),
            headers: postHeaders
        });

        // Confirm upload complete animation appears in modal
        await waitFor(() => {
            expect(app.queryByText('Upload Complete')).not.toBeNull();
        });

        // Confirm upload complete modal closes automatically
        await waitFor(() => {
            expect(app.queryByText('Upload Complete')).toBeNull();
        });

        // Confirm new config table is removed from page (last new config uploaded)
        // Confirm new config appeared in the existing nodes table
        await waitFor(() => {
            expect(app.queryByText('Configs Ready to Upload')).toBeNull();
            const existingNodes = app.getByText('Existing Nodes').parentElement;
            expect(within(existingNodes).queryByText('192.168.1.105')).not.toBeNull();
        }, { timeout: 2000 });
    });

    it('uploads new config when enter key is pressed in IP field', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve('uploaded')
        }));

        // Get new config table, enter IP in first input and then press enter
        const newConfigs = app.getByText('Configs Ready to Upload').parentElement;
        await user.type(within(newConfigs).getAllByRole('textbox')[0], '192.168.1.105');
        await user.type(within(newConfigs).getAllByRole('textbox')[0], '{enter}');

        // Confirm upload request was sent
        expect(global.fetch).toHaveBeenCalledWith('upload', {
            method: 'POST',
            body: JSON.stringify({
                "config": "new-config.json",
                "ip": "192.168.1.105"
            }),
            headers: postHeaders
        });
    });

    it('sends the correct payload when a new config is deleted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve('Deleted new-config.json')
        }));

        // Get new config table, click first delete button
        const newConfigs = app.getByText('Configs Ready to Upload').parentElement;
        await user.click(within(newConfigs).getAllByRole('button')[1]);

        // Confirm modal opened with confirmation prompt, click delete button
        expect(app.queryByText('Confirm Delete')).not.toBeNull();
        await user.click(app.getByRole('button', { name: 'Delete' }));

        // Confirm correct request sent
        expect(global.fetch).toHaveBeenCalledWith('delete_config', {
            method: 'POST',
            body: JSON.stringify('new-config.json'),
            headers: postHeaders
        });
    });

    it('redirects to edit page when existing node edit option clicked', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Get existing nodes table, click button on first row
        const existingNodes = app.getByText('Existing Nodes').parentElement;
        await user.click(within(existingNodes).getAllByRole('button')[0]);

        // Click "Edit" option, confirm redirected to edit config page
        await user.click(app.getByText('Edit'));
        expect(window.location.href).toBe('/edit_config/Bathroom');
    });

    it('sends correct request when an existing node is reuploaded', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve('uploaded')
        }));

        // Get existing nodes table, click button on first row
        const existingNodes = app.getByText('Existing Nodes').parentElement;
        await user.click(within(existingNodes).getAllByRole('button')[0]);

        // Click "Re-upload" option, confirm correct request sent
        await user.click(app.getByText('Re-upload'));
        expect(global.fetch).toHaveBeenCalledWith('upload/True', {
            method: 'POST',
            body: JSON.stringify({
                "config": "bathroom.json",
                "ip": "192.168.1.100"
            }),
            headers: postHeaders
        });
    });

    it('opens ChangeIpModal when existing node dropdown option is clicked', async () => {
        // Get existing nodes table, click button on first row
        const existingNodes = app.getByText('Existing Nodes').parentElement;
        await user.click(within(existingNodes).getAllByRole('button')[0]);

        // Click "Change IP" option, confirm modal appears
        await user.click(app.getByText('Change IP'));
        expect(app.queryByText('Upload an existing config file to a new IP')).not.toBeNull();
    });

    it('sends correct request when ChangeIpModal is submitted', async () => {
        // Open ChangeIpModal for first existing node
        const existingNodes = app.getByText('Existing Nodes').parentElement;
        await user.click(within(existingNodes).getAllByRole('button')[0]);
        await user.click(app.getByText('Change IP'));

        // Enter new IP address in modal input
        const modal = app.queryByText(/file to a new IP/).parentElement;
        await user.clear(within(modal).getByRole('textbox'));
        await user.type(within(modal).getByRole('textbox'), '123.123.123.123');

        // Press Change button, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'Change' }));
        expect(global.fetch).toHaveBeenCalledWith('change_node_ip', {
            method: 'POST',
            body: JSON.stringify({
                "new_ip": "123.123.123.123",
                "friendly_name": "Bathroom"
            }),
            headers: postHeaders
        });

        // Confirm IP changed in existing nodes table
        await waitFor(() => {
            expect(within(existingNodes).queryByText('192.168.1.100')).toBeNull();
            expect(within(existingNodes).queryByText('123.123.123.123')).not.toBeNull();
        });
    });

    it('sends correct request when existing node is deleted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve('Deleted Bathroom')
        }));

        // Get existing nodes table, click button on first row, click "Delete" option
        const existingNodes = app.getByText('Existing Nodes').parentElement;
        await user.click(within(existingNodes).getAllByRole('button')[0]);
        await user.click(app.getByText('Delete'));

        // Confirm modal opened with confirmation prompt
        expect(app.queryByText('Confirm Delete')).not.toBeNull();
        const modal = app.getByText('Confirm Delete').parentElement.parentElement;

        // Click delete, confirm correct request sent
        await user.click(within(modal).getByRole('button', { name: 'Delete' }));
        expect(global.fetch).toHaveBeenCalledWith('delete_node', {
            method: 'POST',
            body: JSON.stringify('Bathroom'),
            headers: postHeaders
        });

        // Confirm node was removed from existing nodes table
        expect(within(existingNodes).queryByText('Bathroom')).toBeNull();
    });

    it('sends correct request when a schedule keyword is added', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve('Keyword created')
        }));

        // Get keywords section, keywords table (tbody tag)
        const keywords = app.getByText('Schedule Keywords').parentElement;
        const table = keywords.children[1].children[0].children[1];

        // Get new keyword row, enter keyword name and timestamp
        const newKeywordRow = table.children[3];
        await user.type(newKeywordRow.children[0].children[0], 'New Keyword');
        await user.type(newKeywordRow.children[1].children[0], '12:34');

        // Click add button, confirm correct request made
        await user.click(within(newKeywordRow).getByRole('button'));
        expect(global.fetch).toHaveBeenCalledWith('add_schedule_keyword', {
            method: 'POST',
            body: JSON.stringify({
                keyword: 'New Keyword',
                timestamp: '12:34'
            }),
            headers: postHeaders
        });
    });

    it('sends correct request when existing schedule keyword is modified', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve('Keyword updated')
        }));

        // Get keywords section, keywords table (tbody tag)
        const keywords = app.getByText('Schedule Keywords').parentElement;
        const table = keywords.children[1].children[0].children[1];

        // Get first keyword, change name and timestamp
        const firstRow = table.children[0];
        await user.clear(firstRow.children[0].children[0]);
        await user.type(firstRow.children[0].children[0], 'New Name');
        await user.clear(firstRow.children[1].children[0]);
        await user.type(firstRow.children[1].children[0], '12:34');

        // Click edit button, confirm correct request made
        await user.click(within(firstRow).getByRole('button'));
        expect(global.fetch).toHaveBeenCalledWith('edit_schedule_keyword', {
            method: 'POST',
            body: JSON.stringify({
                keyword_old: 'morning',
                keyword_new: 'New Name',
                timestamp_new: '12:34'
            }),
            headers: postHeaders
        });
    });

    it('sends correct request when existing schedule keyword is deleted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve('Keyword deleted')
        }));

        // Get keywords section, keywords table (tbody tag)
        const keywords = app.getByText('Schedule Keywords').parentElement;
        const table = keywords.children[1].children[0].children[1];

        // Click delete button on first row, confirm correct request sent
        await user.click(within(table.children[0]).getByRole('button'));
        expect(global.fetch).toHaveBeenCalledWith('delete_schedule_keyword', {
            method: 'POST',
            body: JSON.stringify({
                keyword: 'morning'
            }),
            headers: postHeaders
        });
    });
});
