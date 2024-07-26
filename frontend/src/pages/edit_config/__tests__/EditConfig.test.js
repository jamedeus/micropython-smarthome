import React from 'react';
import EditConfig from '../EditConfig';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { existingConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('EditConfig', () => {
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

    it('warns user before redirecting to overview if schedule rules were changed', async () => {
        // Go to page3, delete a schedule rule
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.container.querySelectorAll('.btn-danger')[0]);

        // Click back button, confirm warning modal appeared, confirm did not redirect
        await user.click(app.getByRole('button', { name: 'Back' }));
        await user.click(app.getByRole('button', { name: 'Back' }));
        await user.click(app.getByRole('button', { name: 'Back' }));
        expect(app.queryByText(/Your changes will be lost/)).not.toBeNull();
        expect(window.location.href).not.toBe('/config_overview');
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
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 409,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Config already exists with identical name'
            })
        }));

        // Get metadata section, friendly name field, enter name
        const metadata = app.getByText('Metadata').parentElement;
        const nameField = within(metadata).getAllByRole('textbox')[0];
        await user.clear(nameField);
        await user.type(nameField, 'Bathroom');

        // Confirm correct request sent
        expect(global.fetch).toHaveBeenCalledWith('/check_duplicate', {
            method: 'POST',
            body: JSON.stringify({ name: "Bathroom" }),
            headers: postHeaders
        });

        // Confirm field is marked invalid, next page button is disabled
        expect(nameField.classList).toContain('is-invalid');
        expect(app.getByRole('button', { name: 'Next' })).toHaveAttribute('disabled');

        // Mock fetch function to simulate available friendly name
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: 'Name available'
            })
        }));

        // Enter unique name in friendly name field
        await user.clear(nameField);
        await user.type(nameField, 'Other Bathroom');

        // Confirm invalid highlight disappeared, next page button not disabled
        expect(nameField.classList).not.toContain('is-invalid');
        expect(app.getByRole('button', { name: 'Next' })).not.toHaveAttribute('disabled');

        // Enter existing name (except for last character)
        await user.clear(nameField);
        await user.type(nameField, 'All devices and sensor');
        // Enter last character, confirm request was NOT sent (don't mark existing as duplicate)
        jest.clearAllMocks();
        await user.type(nameField, 's');
        expect(global.fetch).not.toHaveBeenCalled();
        expect(nameField.classList).not.toContain('is-invalid');
    });

    it('highlights nickname field red if user enters duplicate', async () => {
        // Get device1 and device2 cards and nickname fields
        const device1Card = app.getByText('device1').parentElement.parentElement;
        const device1Nickname = within(device1Card).getByLabelText('Nickname:');
        const device2Card = app.getByText('device1').parentElement.parentElement;
        const device2Nickname = within(device2Card).getByLabelText('Nickname:');

        // Confirm neither nickname field has red highlight
        expect(device1Nickname.classList).not.toContain('is-invalid');
        expect(device2Nickname.classList).not.toContain('is-invalid');

        // Clear device1 nickname, enter nickname of device2
        await user.clear(device1Nickname);
        await user.type(device1Nickname, 'Heater');

        // Confirm both nickname fields now have red highlight
        expect(device1Nickname.classList).toContain('is-invalid');
        expect(device2Nickname.classList).toContain('is-invalid');

        // Confirm next page button is disabled
        expect(app.getByRole('button', { name: 'Next' })).toHaveAttribute('disabled');

        // Change device1 nickname to "Heater2" (unique)
        await user.type(device1Nickname, '2');

        // Confirm next page button enabled, red highlights removed
        expect(app.getByRole('button', { name: 'Next' })).not.toHaveAttribute('disabled');
        expect(device1Nickname.classList).not.toContain('is-invalid');
        expect(device2Nickname.classList).not.toContain('is-invalid');
    });

    it('clears card inputs when device type is changed', async () => {
        // Get device1 card, type select dropdown
        const device1Card = document.getElementById('device1-card');
        const typeSelect = within(device1Card).getByLabelText('Type:');

        // Confirm nickname field has expected value
        expect(within(device1Card).getByLabelText('Nickname:').value).toBe('Humidifier');

        // Change type to pwm, confirm nickname field was cleared
        await user.selectOptions(typeSelect, 'pwm');
        expect(within(device1Card).getByLabelText('Nickname:').value).toBe('');
    });

    it('clears card inputs when sensor type is changed', async () => {
        // Get sensor1 card, type select dropdown
        const sensor1Card = document.getElementById('sensor1-card');
        const typeSelect = within(sensor1Card).getByLabelText('Type:');

        // Confirm nickname field has expected value
        expect(within(sensor1Card).getByLabelText('Nickname:').value).toBe('Door switch');

        // Change type to pir, confirm nickname field was cleared
        await user.selectOptions(typeSelect, 'pir');
        expect(within(sensor1Card).getByLabelText('Nickname:').value).toBe('');
    });

    it('disables pin dropdown options that are already used by other cards', async () => {
        // Get device1 pin select dropdown, sensor1 pin select dropdown
        const device1Pin = within(document.getElementById('device1-card')).getByLabelText('Pin:');
        const sensor1Pin = within(document.getElementById('sensor1-card')).getByLabelText('Pin:');

        // Confirm pin 21 (used by sensor1) is disabled in device1 dropdown, 22 is not
        expect(within(device1Pin).getByText('21').disabled).toBe(true);
        expect(within(device1Pin).getByText('22').disabled).toBe(false);

        // Select pin 22 in sensor1 dropdown
        await user.selectOptions(sensor1Pin, '22');

        // Confirm pin 22 is now disabled, pin 21 is enabled in device1 pin dropdown
        expect(within(device1Pin).getByText('21').disabled).toBe(false);
        expect(within(device1Pin).getByText('22').disabled).toBe(true);
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
        const device1Card = document.getElementById('device1-card');
        const sensor1Card = document.getElementById('sensor1-card');
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

    it('updates device IDs to keep them sequential when cards are deleted', async () => {
        const getNicknameInput = (id) => {
            return within(
                document.getElementById(`${id}-params`)
            ).getByLabelText('Nickname:');
        };

        // Confirm nicknames of first 4 devices
        expect(getNicknameInput('device1').value).toBe('Humidifier');
        expect(getNicknameInput('device2').value).toBe('Heater');
        expect(getNicknameInput('device3').value).toBe('Accent lights');
        expect(getNicknameInput('device4').value).toBe('Computer screen');

        // Delete device2, wait for card to unmount
        await user.click(app.getByText('device2').parentElement.children[2]);
        await waitFor(() => {
            expect(app.queryByText('device10')).toBeNull();
        });

        // Confirm device1 nickname did not change
        expect(getNicknameInput('device1').value).toBe('Humidifier');
        // Confirm device3 is now device2, device4 is now device3
        expect(getNicknameInput('device2').value).toBe('Accent lights');
        expect(getNicknameInput('device3').value).toBe('Computer screen');
    });

    it('updates sensor IDs to keep them sequential when cards are deleted', async () => {
        const getNicknameInput = (id) => {
            return within(
                document.getElementById(`${id}-params`)
            ).getByLabelText('Nickname:');
        };

        // Confirm nicknames of first 4 sensors
        expect(getNicknameInput('sensor1').value).toBe('Door switch');
        expect(getNicknameInput('sensor2').value).toBe('Temp sensor');
        expect(getNicknameInput('sensor3').value).toBe('Thermostat');
        expect(getNicknameInput('sensor4').value).toBe('Computer activity');

        // Delete sensor2, wait for card to unmount
        await user.click(app.getByText('sensor2').parentElement.children[2]);
        await waitFor(() => {
            expect(app.queryByText('sensor6')).toBeNull();
        });

        // Confirm device1 nickname did not change
        expect(getNicknameInput('sensor1').value).toBe('Door switch');
        // Confirm sensor3 is now sensor2, sensor4 is now sensor3
        expect(getNicknameInput('sensor2').value).toBe('Thermostat');
        expect(getNicknameInput('sensor3').value).toBe('Computer activity');
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
        // Mock fetch function to return generate_config success message on
        // first call, upload success message on second call (100ms delay)
        const mockFetchResponses = [
            () => Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({
                    status: 'success',
                    message: 'Config created'
                })
            }),
            () => new Promise((resolve) => {
                setTimeout(() => {
                    resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve({
                            status: 'success',
                            message: 'uploaded'
                        })
                    });
                }, 100);
            })
        ];
        global.fetch = jest.fn(() => {
            const response = mockFetchResponses.shift();
            return response();
        });

        // Click next twice, confirm page3 is visible
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Add schedule rules (optional)')).not.toBeNull();

        // Click submit button, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'Submit' }));
        expect(global.fetch).toHaveBeenCalledWith('/generate_config_file/True', {
            method: 'POST',
            body: JSON.stringify(existingConfigContext.config),
            headers: postHeaders
        });

        // Confirm second request was made to re-upload modified config
        expect(global.fetch).toHaveBeenCalledWith('/upload/True', {
            method: 'POST',
            body: JSON.stringify({
                "config": "all-devices-and-sensors.json",
                "ip": "192.168.1.100"
            }),
            headers: postHeaders
        });

        // Confirm modal with upload animation appears
        await waitFor(() => {
            expect(app.getByText('Uploading...')).toBeInTheDocument();
        });

        // Confirm changes to success animation when request completes
        await waitFor(() => {
            expect(app.getByText('Upload Complete')).toBeInTheDocument();
        });

        // Confirm redirected to overview after success animation completes
        await waitFor(() => {
            expect(window.location.href).toBe('/config_overview');
        }, { timeout: 1500 });
    });

    it('shows error modal if unable to upload config after submitting', async () => {
        // Mock fetch function to succeed on first call (generate_config) and
        // encounter target offline error on second call (reupload config to target IP)
        const mockFetchResponses = [
            () => Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({
                    status: 'success',
                    message: 'Config created'
                })
            }),
            () => new Promise((resolve) => {
                setTimeout(() => {
                    resolve({
                        ok: false,
                        status: 404,
                        json: () => Promise.resolve({
                            status: 'error',
                            message: 'Target node offline'
                        })
                    });
                }, 100);
            })
        ];
        global.fetch = jest.fn(() => {
            const response = mockFetchResponses.shift();
            return response();
        });

        // Click next twice, click submit button on page3
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Submit' }));

        // Confirm modal with upload animation appears
        await waitFor(() => {
            expect(app.getByText('Uploading...')).toBeInTheDocument();
        });

        // Confirm modal closes, error modal appears when error occurs
        await waitFor(() => {
            expect(app.queryByText('Uploading...')).toBeNull();
            expect(app.getByText('Connection Error')).toBeInTheDocument();
        });
    });

    it('shows error toast if unknown error occurs while reuploading submitted config', async () => {
        // Mock fetch function to succeed on first call (generate_config) and
        // encounter unexpected error on second call (reupload config to target IP)
        const mockFetchResponses = [
            Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.resolve({
                    status: 'success',
                    message: 'Config created'
                })
            }),
            Promise.resolve({
                ok: false,
                status: 400,
                json: () => Promise.resolve({
                    status: 'error',
                    message: 'Unexpected error'
                })
            })
        ];
        global.fetch = jest.fn(() => mockFetchResponses.shift());

        // Click next twice, click submit button on page3
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Submit' }));

        // Confirm error toast was shown with response from API
        expect(app.queryByText('Unexpected error')).not.toBeNull();
    });

    it('refuses to create config with blank schedule rules', async () => {
        // Click next twice, confirm page3 is visible
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Add schedule rules (optional)')).not.toBeNull();

        // Confirm invalid highlight is not present
        expect(app.container.querySelector('.is-invalid')).toBeNull();

        // Add a schedule rule, open time/rule popups and close without entering value
        await user.click(app.getAllByRole('button', { name: 'Add Rule'})[0]);
        await user.click(app.getAllByText('Set time')[0]);
        await user.type(app.getByLabelText('Time'), '{enter}');
        await user.click(app.container.querySelectorAll('.form-control')[1]);
        await user.type(app.getByRole('combobox'), '{enter}');

        // Click submit, confirm no request was made, invalid highlight was added
        await user.click(app.getByRole('button', { name: 'Submit' }));
        expect(global.fetch).not.toHaveBeenCalled();
        expect(app.container.querySelector('.is-invalid')).not.toBeNull();
    });

    it('shows error toast when submit button is clicked if unexpected error received', async () => {
        // Mock fetch function to simulate unexpected error
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 418,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unexpected error'
            })
        }));

        // Click next twice, confirm page3 is visible
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Add schedule rules (optional)')).not.toBeNull();

        // Click submit, confirm error toast was shown with text from response
        await user.click(app.getByRole('button', { name: 'Submit' }));
        expect(app.queryByText('"Unexpected error"')).not.toBeNull();

        // Confirm did NOT redirect to overview
        expect(window.location.href).not.toBe('/config_overview');
    });

    it('generates the correct config when default rules are modified', async () => {
        // Change sensor1 default_rule to disabled
        await user.selectOptions(within(
            app.getByText('sensor1').parentElement.parentElement
        ).getByLabelText('Default Rule:'), 'disabled');

        // Change sensor2 default_rule to 73.5
        await user.click(app.getByText('sensor2').parentElement.parentElement
            .querySelector('.bi-dash-lg'));

        // Change sensor5 default_rule to 9.5
        await user.click(app.getByText('sensor5').parentElement.parentElement
            .querySelector('.bi-dash-lg'));

        // Change device3 default_rule to 766
        await user.click(app.getByText('device3').parentElement.parentElement
            .querySelector('.bi-dash-lg'));

        // Change device7 (api-target) default_rule to ignore (both actions)
        await user.click(app.getByText('Set rule'));
        // Change on and off actions to ignore, click submit
        const modal = app.getByText('API Target Rule').parentElement.parentElement;
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'ignore');
        await user.click(app.getByText('Off Action'));
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'ignore');
        await user.click(within(modal).getByRole('button', { name: 'Submit' }));

        // Go to page3, click submit button
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Submit' }));

        // Confirm correct config was submitted
        expect(global.fetch).toHaveBeenCalledWith('/generate_config_file/True', {
            method: 'POST',
            body: JSON.stringify({
                ...existingConfigContext.config,
                sensor1: {
                    ...existingConfigContext.config.sensor1,
                    default_rule: 'disabled'
                },
                sensor2: {
                    ...existingConfigContext.config.sensor2,
                    default_rule: 73.5
                },
                sensor5: {
                    ...existingConfigContext.config.sensor5,
                    default_rule: 9.5
                },
                device3: {
                    ...existingConfigContext.config.device3,
                    default_rule: 766
                },
                device7: {
                    ...existingConfigContext.config.device7,
                    default_rule: {
                        "on": [
                            "ignore"
                        ],
                        "off": [
                            "ignore"
                        ]
                    }
                }
            }),
            headers: postHeaders
        });
    });

    it('generates the correct config when schedule rule are modified', async () => {
        // Click next twice, confirm page3 is visible
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.queryByText('Add schedule rules (optional)')).not.toBeNull();

        // Change sensor5 (motion sensor) first rule to enabled
        const sensor5Rules = app.getByText('Motion (pir)').parentElement;
        await user.click(within(sensor5Rules).getByText('10'));
        // await user.click(app.container.querySelectorAll('.form-control')[1]);
        await user.click(app.getAllByRole('checkbox')[0]);
        await user.selectOptions(app.getByRole('combobox'), 'enabled');
        await user.type(app.getByRole('combobox'), '{enter}');

        // Open device7 (Api Target) rule modal
        await user.click(app.getByText('Click to edit'));
        // Change on and off actions to ignore, click submit
        await user.selectOptions(app.getAllByRole('combobox')[0], 'ignore');
        await user.click(app.getByText('Off Action'));
        await user.selectOptions(app.getAllByRole('combobox')[0], 'ignore');
        await user.click(within(
            app.getByText('API Target Rule').parentElement.parentElement
        ).getByRole('button', { name: 'Submit' }));

        // Delete device9 (TP Link bulb) second rule (relax keyword)
        const device9Rules = app.getByText('Lamp (bulb)').parentElement;
        await user.click(within(device9Rules).getAllByRole('button')[1]);

        // Click submit button, confirm payload contains modified rules
        await user.click(app.getByText('Submit'));
        expect(global.fetch).toHaveBeenCalledWith('/generate_config_file/True', {
            method: 'POST',
            body: JSON.stringify({
                ...existingConfigContext.config,
                sensor5: {
                    ...existingConfigContext.config.sensor5,
                    schedule: {
                        morning: 'enabled',
                        sleep: 1
                    }
                },
                device7: {
                    ...existingConfigContext.config.device7,
                    schedule: {
                        morning: {
                            "on": [
                                "ignore"
                            ],
                            "off": [
                                "ignore"
                            ]
                        }
                    }
                },
                device9: {
                    ...existingConfigContext.config.device9,
                    schedule: {
                        morning: "fade/100/900",
                        sleep: "disabled"
                    }
                }
            }),
            headers: postHeaders
        });
    });

    it('converts thermostat schedule rules when units change', async () => {
        // Change sensor2 (dht22) units to celsius
        const sensor2Card = app.getByText('sensor2').parentElement.parentElement;
        await user.selectOptions(within(sensor2Card).getByLabelText('Units:'), 'celsius');

        // Change sensor3 (si7021) units to kelvin, then to fahrenheit
        const sensor3Card = app.getByText('sensor3').parentElement.parentElement;
        await user.selectOptions(within(sensor3Card).getByLabelText('Units:'), 'kelvin');
        await user.selectOptions(within(sensor3Card).getByLabelText('Units:'), 'fahrenheit');

        // Go to page3, click submit, confirm schedule rules in payload were converted
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByText('Submit'));
        expect(global.fetch).toHaveBeenCalledWith('/generate_config_file/True', {
            method: 'POST',
            body: JSON.stringify({
                ...existingConfigContext.config,
                sensor2: {
                    ...existingConfigContext.config.sensor2,
                    units: 'celsius',
                    default_rule: 23.3,
                    schedule: {
                        morning: 20,
                        relax: 22.2,
                        '12:00': 'disabled'
                    }
                },
                sensor3: {
                    ...existingConfigContext.config.sensor3,
                    units: 'fahrenheit',
                    default_rule: 68.1,
                    schedule: {
                        morning: 73.5,
                        sleep: 68.1
                    }
                }
            }),
            headers: postHeaders
        });
    });

    it('removes targets from config file when boxes are unchecked', async () => {
        // Uncheck IR Blaster TV target, check AC target
        await user.click(app.getByText('TV (Samsung)'));
        await user.click(app.getByText('AC (Whynter)'));

        // Go to page2, uncheck first target
        await user.click(app.getByRole('button', { name: 'Next' }));
        const sensor1Targets = app.container.querySelectorAll('.card-body')[0];
        await user.click(within(sensor1Targets).getByText('Bias lights'));

        // Go to page3, click submit, confirm payload contains correct config
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByText('Submit'));
        expect(global.fetch).toHaveBeenCalledWith('/generate_config_file/True', {
            method: 'POST',
            body: JSON.stringify({
                ...existingConfigContext.config,
                ir_blaster: {
                    ...existingConfigContext.config.ir_blaster,
                    target: [
                        'ac'
                    ]
                },
                sensor1: {
                    ...existingConfigContext.config.sensor1,
                    targets: [
                        'device3',
                        'device4',
                        'device6',
                        'device9'
                    ]
                }
            }),
            headers: postHeaders
        });
    });
});
