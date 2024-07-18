import React from 'react';
import EditConfig from '../EditConfig';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { existingConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('App', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('config', existingConfigContext.config);
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', existingConfigContext.edit_existing);
        createMockContext('target_node_ip', existingConfigContext.IP);
    });

    beforeEach(() => {
        // Render app + create userEvent instance to use in tests
        user = userEvent.setup();
        app = render(
            <MetadataContextProvider>
                <ConfigProvider>
                    <EditConfig />
                </ConfigProvider>
            </MetadataContextProvider>
        );

        // Set correct URL
        window.location.href = '/edit_config/All devices and sensors';
    });

    it('redirects to overview when back button is clicked', async () => {
        await user.click(app.getByRole('button', { name: 'Back' }));
        expect(window.location.href).toBe('/config_overview');
    });

    it('warns user before redirecting to overview if changes were made', async () => {
        // Clear location field in metadata section
        const metadata = app.getByText('Metadata').parentElement;
        await user.clear(within(metadata).getAllByRole('textbox')[1]);

        // Click back button, confirm warning modal appeared, confirm did not redirect
        await user.click(app.getByRole('button', { name: 'Back' }));
        expect(app.queryByText(/Your changes will be lost/)).not.toBeNull();
        expect(window.location.href).not.toBe('/config_overview');

        // Click Go Back button, confirm redirected to overview
        await user.click(app.getByRole('button', { name: 'Go Back' }));
        expect(window.location.href).toBe('/config_overview');
    });

    it('shows/hides IR blaster section when "Add IR Blaster" button is clicked', async () => {
        // Get IR Blaster section, confirm collapse is open
        const irBlaster = app.getByText('IR Blaster').parentElement.parentElement.parentElement;
        expect(irBlaster.classList).toContain('show');

        // Click "Add IR Blaster" button, confirm collapse closes
        await user.click(app.getByRole('button', { name: 'Add IR Blaster' }));
        expect(irBlaster.classList).not.toContain('show');

        // Click "Add IR Blaster" button again, confirm collapse opens
        await user.click(app.getByRole('button', { name: 'Add IR Blaster' }));
        expect(irBlaster.classList).toContain('show');
    });

    it('checks for duplicate names when user types in name field', async () => {
        // Mock fetch function to simulate duplicate friendly name
        global.fetch = jest.fn(() => Promise.resolve({ ok: false }));

        // Get metadata section, enter name in friendly name field
        const metadata = app.getByText('Metadata').parentElement;
        await user.clear(within(metadata).getAllByRole('textbox')[0]);
        await user.type(within(metadata).getAllByRole('textbox')[0], 'Bathroom');

        // Confirm correct request sent, field was marked invalid
        expect(global.fetch).toHaveBeenCalledWith('/check_duplicate', {
            method: 'POST',
            body: JSON.stringify({ name: "Bathroom" }),
            headers: postHeaders
        });
        expect(within(metadata).getAllByRole('textbox')[0].classList).toContain('is-invalid');

        // Mock fetch function to simulate available friendly name
        global.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        // Enter name in friendly name field, confirm invalid highlight disappeared
        await user.clear(within(metadata).getAllByRole('textbox')[0]);
        await user.type(within(metadata).getAllByRole('textbox')[0], 'Other Bathroom');
        expect(within(metadata).getAllByRole('textbox')[0].classList).not.toContain('is-invalid');
    });

    it('highlights nickname field red if user enters duplicate', async () => {
        // Get device1 and device2 cards and nickname fields
        const device1Card = app.getByText('device1').parentElement.parentElement;
        const device1Nickname = within(device1Card).getAllByRole('textbox')[0];
        const device2Card = app.getByText('device1').parentElement.parentElement;
        const device2Nickname = within(device2Card).getAllByRole('textbox')[0];

        // Confirm neither nickname field has red highlight
        expect(device1Nickname.classList).not.toContain('is-invalid');
        expect(device2Nickname.classList).not.toContain('is-invalid');

        // Clear device1 nickname, enter nickname of device2
        await user.clear(device1Nickname);
        await user.type(device1Nickname, 'Heater');

        // Confirm both nickname fields now have red highlight
        expect(device1Nickname.classList).toContain('is-invalid');
        expect(device2Nickname.classList).toContain('is-invalid');
    });

    it('adds cards when "Add Device" and "Add Sensor" buttons are clicked', async () => {
        // Confirm device11 and sensor7 don't exist
        expect(app.queryByText('device11')).toBeNull();
        expect(app.queryByText('sensor7')).toBeNull();

        // Click "Add Device", confirm device11 card appears
        await user.click(app.getByRole('button', { name: 'Add Device' }));
        expect(app.queryByText('device11')).not.toBeNull();

        // Click "Add Sensor", confirm sensor7 card appears
        await user.click(app.getByRole('button', { name: 'Add Sensor' }));
        expect(app.queryByText('sensor7')).not.toBeNull();
    });

    it('fades out device and sensor cards when they are deleted', async () => {
        // Get first device and sensor cards, confirm both start with fade-in class
        const device1Card = app.getByText('device1').parentElement.parentElement.parentElement.parentElement;
        const sensor1Card = app.getByText('sensor1').parentElement.parentElement.parentElement.parentElement;
        expect(device1Card.classList).toContain('fade-in-card');
        expect(sensor1Card.classList).toContain('fade-in-card');

        // Click device1 delete button, confirm fades out
        await user.click(app.getByText('device1').parentElement.children[2]);
        expect(device1Card.classList).not.toContain('fade-in-card');
        expect(device1Card.classList).toContain('fade-out-card');

        // Click sensor1 delete button, confirm fades out
        await user.click(app.getByText('sensor1').parentElement.children[2]);
        expect(sensor1Card.classList).not.toContain('fade-in-card');
        expect(sensor1Card.classList).toContain('fade-out-card');
    });

    // TODO refactor InputWrapper to allow targeting by label
    it('updates device IDs to keep them sequential when cards are deleted', async () => {
        // Confirm nicknames of first 4 devices
        let device1NicknameDiv = within(document.getElementById('device1-params')).getByText('Nickname:').parentElement;
        expect(within(device1NicknameDiv).getByRole('textbox').value).toBe('Humidifier');
        let device2NicknameDiv = within(document.getElementById('device2-params')).getByText('Nickname:').parentElement;
        expect(within(device2NicknameDiv).getByRole('textbox').value).toBe('Heater');
        let device3NicknameDiv = within(document.getElementById('device3-params')).getByText('Nickname:').parentElement;
        expect(within(device3NicknameDiv).getByRole('textbox').value).toBe('Accent lights');
        let device4NicknameDiv = within(document.getElementById('device4-params')).getByText('Nickname:').parentElement;
        expect(within(device4NicknameDiv).getByRole('textbox').value).toBe('Computer screen');

        // Delete device2, wait for card to unmount
        await user.click(app.getByText('device2').parentElement.children[2]);
        await waitFor(() => {
            expect(app.queryByText('device10')).toBeNull();
        });

        // Confirm device1 nickname did not change
        device1NicknameDiv = within(document.getElementById('device1-params')).getByText('Nickname:').parentElement;
        expect(within(device1NicknameDiv).getByRole('textbox').value).toBe('Humidifier');
        // Confirm device3 is now device2, device4 is now device3
        device2NicknameDiv = within(document.getElementById('device2-params')).getByText('Nickname:').parentElement;
        expect(within(device2NicknameDiv).getByRole('textbox').value).toBe('Accent lights');
        device3NicknameDiv = within(document.getElementById('device3-params')).getByText('Nickname:').parentElement;
        expect(within(device3NicknameDiv).getByRole('textbox').value).toBe('Computer screen');
    });

    it('updates sensor IDs to keep them sequential when cards are deleted', async () => {
        // Confirm nicknames of first 4 sensors
        let sensor1NicknameDiv = within(document.getElementById('sensor1-params')).getByText('Nickname:').parentElement;
        expect(within(sensor1NicknameDiv).getByRole('textbox').value).toBe('Door switch');
        let sensor2NicknameDiv = within(document.getElementById('sensor2-params')).getByText('Nickname:').parentElement;
        expect(within(sensor2NicknameDiv).getByRole('textbox').value).toBe('Temp sensor');
        let sensor3NicknameDiv = within(document.getElementById('sensor3-params')).getByText('Nickname:').parentElement;
        expect(within(sensor3NicknameDiv).getByRole('textbox').value).toBe('Thermostat');
        let sensor4NicknameDiv = within(document.getElementById('sensor4-params')).getByText('Nickname:').parentElement;
        expect(within(sensor4NicknameDiv).getByRole('textbox').value).toBe('Computer activity');

        // Delete device2, wait for card to unmount
        await user.click(app.getByText('sensor2').parentElement.children[2]);
        await waitFor(() => {
            expect(app.queryByText('sensor6')).toBeNull();
        });

        // Confirm device1 nickname did not change
        sensor1NicknameDiv = within(document.getElementById('sensor1-params')).getByText('Nickname:').parentElement;
        expect(within(sensor1NicknameDiv).getByRole('textbox').value).toBe('Door switch');
        // Confirm sensor3 is now sensor2, sensor4 is now sensor3
        sensor2NicknameDiv = within(document.getElementById('sensor2-params')).getByText('Nickname:').parentElement;
        expect(within(sensor2NicknameDiv).getByRole('textbox').value).toBe('Thermostat');
        sensor3NicknameDiv = within(document.getElementById('sensor3-params')).getByText('Nickname:').parentElement;
        expect(within(sensor3NicknameDiv).getByRole('textbox').value).toBe('Computer activity');
    });

    it('changes pages when next and back buttons are clicked', async () => {
        // Confirm page1 is visible
        expect(app.queryByText('Add Devices')).not.toBeNull();
        expect(app.queryByText('Select targets for each sensor')).toBeNull();
        expect(app.queryByText('Add schedule rules (optional)')).toBeNull();

        // Click next button, confirm page2 is visible
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Add Devices')).toBeNull();
        expect(app.queryByText('Select targets for each sensor')).not.toBeNull();
        expect(app.queryByText('Add schedule rules (optional)')).toBeNull();

        // Click next button, confirm page3 is visible
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Add Devices')).toBeNull();
        expect(app.queryByText('Select targets for each sensor')).toBeNull();
        expect(app.queryByText('Add schedule rules (optional)')).not.toBeNull();

        // Click back button, confirm page2 is visible
        await user.click(app.getByRole('button', { name: 'Back' }));
        expect(app.queryByText('Add Devices')).toBeNull();
        expect(app.queryByText('Select targets for each sensor')).not.toBeNull();
        expect(app.queryByText('Add schedule rules (optional)')).toBeNull();
    });

    it('refuses to go to page2 if blank fields exist on page1', async () => {
        // Click "Add Device" to create a blank card
        await user.click(app.getByRole('button', { name: 'Add Device' }));

        // Confirm no fields in blank card have invalid highlight
        const newDeviceCard = document.getElementById('device11-card');
        expect(newDeviceCard.querySelectorAll('.is-invalid').length).toBe(0);

        // Click next button, confirm page2 is not shown
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Select targets for each sensor')).toBeNull();

        // Confirm new device card now has invalid highlight
        expect(newDeviceCard.querySelectorAll('.is-invalid').length).toBe(1);
    });

    it('sends correct request when config is submitted', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ On: "Config created." })
        }));

        // Click next twice, confirm page3 is visible
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Add schedule rules (optional)')).not.toBeNull();

        // Click submit button, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'Submit' }));
        expect(global.fetch).toHaveBeenCalledWith('generate_config_file/True', {
            method: 'POST',
            body: JSON.stringify(existingConfigContext.config),
            headers: postHeaders
        });

        // Confirm second request was made to re-upload modified config
        expect(global.fetch).toHaveBeenCalledWith('upload/True', {
            method: 'POST',
            body: JSON.stringify({
                "config": "all-devices-and-sensors.json",
                "ip": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm shows upload modal, redirects to overview when animation completes
        expect(app.getByText('Upload Complete')).not.toBeNull();
        await waitFor(() => {
            expect(window.location.href).toBe('/config_overview');
        }, { timeout: 1500 });
    });
});
