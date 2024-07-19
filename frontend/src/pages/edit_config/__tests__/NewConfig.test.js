import React from 'react';
import EditConfig from '../EditConfig';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { newConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('App', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('config', newConfigContext.config);
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', newConfigContext.edit_existing);
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
        window.location.href = '/new_config';
    });

    it('sends correct request when a new config is created', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ On: "Config created." })
        }));

        // Fill out metadata section
        await user.type(app.getAllByRole('textbox')[0], 'Basement');
        await user.type(app.getByLabelText('Location:'), 'Under staircase');
        await user.type(app.getByLabelText('Floor:'), '-1');

        // Fill out wifi section
        await user.clear(app.getByLabelText('SSID:'));
        await user.type(app.getByLabelText('SSID:'), 'mywifi');
        await user.clear(app.getByLabelText('Password:'));
        await user.type(app.getByLabelText('Password:'), 'hunter2');
        jest.clearAllMocks();

        // Add IR Blaster with TV codes
        await user.click(app.getByRole('button', { name: 'Add IR Blaster' }));
        await user.selectOptions(app.getByRole('combobox'), '16');
        await user.click(app.getByText('TV (Samsung)'));

        // Add si7021 temperature sensor
        await user.click(app.getByRole('button', { name: 'Add Sensor' }));
        const sensor1Card = app.getByText('sensor1').parentElement.parentElement;
        await user.selectOptions(within(sensor1Card).getByRole('combobox'), 'si7021');
        await user.type(within(sensor1Card).getByLabelText('Nickname:'), 'Thermostat');
        await user.selectOptions(within(sensor1Card).getByLabelText('Mode:'), 'cool');
        await user.selectOptions(within(sensor1Card).getByLabelText('Units:'), 'fahrenheit');
        await user.type(within(sensor1Card).getByLabelText('Tolerance:'), '1');

        // Add HttpGet device
        await user.click(app.getByRole('button', { name: 'Add Device' }));
        const device1Card = app.getByText('device1').parentElement.parentElement;
        await user.selectOptions(within(device1Card).getByRole('combobox'), 'http-get');
        await user.type(within(device1Card).getByLabelText('Nickname:'), 'Air Conditioner');
        await user.type(within(device1Card).getByLabelText('URI:'), 'http://192.168.1.123');
        await user.type(within(device1Card).getByLabelText('On path:'), 'api/state/on');
        await user.type(within(device1Card).getByLabelText('Off path:'), 'api/state/off');
        await user.selectOptions(within(device1Card).getByLabelText('Default Rule:'), 'enabled');

        // Go to page 2, check Air Conditioner target box
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByText('Air Conditioner'));

        // Go to page 3
        await user.click(app.getByRole('button', { name: 'Next' }));

        // Add a timestamp rule for device1 (10:00: disabled)
        await user.click(within(
            app.getByText('Air Conditioner (http-get)').parentElement
        ).getByRole('button', { name: 'Add Rule' }));
        await user.click(app.getByText('Set time'));
        await user.type(app.getByLabelText('Time'), '10:00');
        await user.type(app.getByLabelText('Time'), '{enter}');
        await user.click(app.getByText('enabled'));
        await user.selectOptions(app.getByLabelText('Rule'), 'disabled');
        await user.type(app.getByLabelText('Rule'), '{enter}');

        // Add a keyword rule for device1 (sleep: enabled)
        await user.click(within(
            app.getByText('Air Conditioner (http-get)').parentElement
        ).getByRole('button', { name: 'Add Rule' }));
        await user.click(app.getByText('Set time'));
        await user.click(app.getByText('Keyword'));
        await user.selectOptions(app.getAllByLabelText('Keyword')[0], 'sleep');
        await user.type(app.getAllByLabelText('Keyword')[0], '{enter}');

        // Add a keyword rule for sensor1 (sleep: 70.6)
        await user.click(within(
            app.getByText('Thermostat (si7021)').parentElement
        ).getByRole('button', { name: 'Add Rule' }));
        await user.click(app.getByText('Set time'));
        await user.click(app.getByText('Keyword'));
        await user.selectOptions(app.getAllByLabelText('Keyword')[0], 'sleep');
        await user.type(app.getAllByLabelText('Keyword')[0], '{enter}');
        // Open rule field, press minus button next to slider twice
        await user.click(app.getByText('71.6'));
        await user.click(within(
            document.querySelector('.schedule-rule-param-popup')
        ).getAllByRole('button')[0]);
        await user.click(within(
            document.querySelector('.schedule-rule-param-popup')
        ).getAllByRole('button')[0]);
        // Click outside popup to close
        await user.click(app.getByText('Thermostat (si7021)'));

        // Click submit, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'Submit' }));
        expect(global.fetch).toHaveBeenCalledWith('generate_config_file', {
            method: 'POST',
            body: JSON.stringify({
                "metadata": {
                    "id": "Basement",
                    "floor": "-1",
                    "location": "Under staircase",
                    "schedule_keywords": {
                        "morning": "08:00",
                        "sleep": "23:00",
                        "sunrise": "06:00",
                        "sunset": "18:00",
                        "relax": "20:00"
                    }
                },
                "wifi": {
                    "ssid": "mywifi",
                    "password": "hunter2"
                },
                "ir_blaster": {
                    "pin": "16",
                    "target": [
                        "tv"
                    ]
                },
                "sensor1": {
                    "_type": "si7021",
                    "nickname": "Thermostat",
                    "units": "fahrenheit",
                    "default_rule": 71.6,
                    "mode": "cool",
                    "tolerance": 1,
                    "schedule": {
                        "sleep": 70.6
                    },
                    "targets": [
                        "device1"
                    ]
                },
                "device1": {
                    "_type": "http-get",
                    "nickname": "Air Conditioner",
                    "default_rule": "enabled",
                    "uri": "http://192.168.1.123",
                    "on_path": "api/state/on",
                    "off_path": "api/state/off",
                    "schedule": {
                        "10:00": "disabled",
                        "sleep": "enabled"
                    }
                }
            }),
            headers: postHeaders
        });

        // Confirm redirected to overview page
        expect(window.location.href).toBe('/config_overview');
    });

    it('sends the correct payload when a config with wled and dummy sensor is created', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ On: "Config created." })
        }));

        // Fill out metadata section
        await user.type(app.getAllByRole('textbox')[0], 'Basement');
        await user.type(app.getByLabelText('Location:'), 'Under staircase');
        await user.type(app.getByLabelText('Floor:'), '-1');

        // Fill out wifi section
        await user.clear(app.getByLabelText('SSID:'));
        await user.type(app.getByLabelText('SSID:'), 'mywifi');
        await user.clear(app.getByLabelText('Password:'));
        await user.type(app.getByLabelText('Password:'), 'hunter2');
        jest.clearAllMocks();

        // Add Wled device
        await user.click(app.getByRole('button', { name: 'Add Device' }));
        const device1Card = app.getByText('device1').parentElement.parentElement;
        await user.selectOptions(within(device1Card).getByRole('combobox'), 'wled');
        await user.type(within(device1Card).getByLabelText('Nickname:'), 'TV Backlight');
        await user.type(within(device1Card).getByLabelText('IP:'), '192.168.1.123');
        await user.click(app.getByText('Advanced'));
        // Clearing min/max fields automatically sets their value to 1
        await user.clear(app.getByLabelText('Max brightness:'));
        await user.clear(app.getByLabelText('Min brightness:'));
        // Set min to 100, max to 192 (fields already contain 1)
        await user.type(app.getByLabelText('Max brightness:'), '92');
        await user.type(app.getByLabelText('Min brightness:'), '00');
        // Set default_rule to 192 by clicking slider + button
        // Can't simulate moving slider due to jsdom limitations
        for (let i = 0; i < 92; i++) {
            user.click(app.container.querySelector('.bi-plus-lg'));
        }

        // Add Dummy sensor
        await user.click(app.getByRole('button', { name: 'Add Sensor' }));
        const sensor1Card = app.getByText('sensor1').parentElement.parentElement;
        await user.selectOptions(within(sensor1Card).getByRole('combobox'), 'dummy');
        await user.type(within(sensor1Card).getByLabelText('Nickname:'), 'Turn on lights');
        await user.selectOptions(within(sensor1Card).getByLabelText('Default Rule:'), 'off');

        // Go to page 2, check TV Backlight target box
        await user.click(app.getByRole('button', { name: 'Next' }));
        await user.click(app.getByText('TV Backlight'));

        // Go to page3
        await user.click(app.getByRole('button', { name: 'Next' }));

        // Add a keyword rule for device1 (relax: enabled)
        await user.click(within(
            app.getByText('TV Backlight (wled)').parentElement
        ).getByRole('button', { name: 'Add Rule' }));
        await user.click(app.getByText('Set time'));
        await user.click(app.getByText('Keyword'));
        await user.selectOptions(app.getAllByLabelText('Keyword')[0], 'relax');
        await user.type(app.getAllByLabelText('Keyword')[0], '{enter}');
        // Click rule field, toggle range switch, select disabled
        await user.click(app.container.querySelectorAll('.form-control')[1]);
        await user.click(app.getAllByRole('checkbox')[0]);
        await user.selectOptions(app.getByRole('combobox'), 'enabled');
        await user.type(app.getByRole('combobox'), '{enter}');

        // Add another keyword rule (sleep: fade/100/1800)
        await user.click(within(
            app.getByText('TV Backlight (wled)').parentElement
        ).getByRole('button', { name: 'Add Rule' }));
        await user.click(app.getByText('Set time'));
        await user.click(app.getByText('Keyword'));
        await user.selectOptions(app.getAllByLabelText('Keyword')[0], 'sleep');
        await user.type(app.getAllByLabelText('Keyword')[0], '{enter}');
        // Click rule field, press minus button until rule is 100
        await user.click(app.container.querySelectorAll('.form-control')[3]);
        for (let i = 0; i < 92; i++) {
            user.click(app.container.querySelector('.bi-dash-lg'));
        }
        // Toggle fade switch, enter 1800 in delay input
        await user.click(app.getAllByRole('checkbox')[1]);
        await user.clear(app.getByText('Duration (seconds)').parentElement.children[1]);
        await user.type(app.getByText('Duration (seconds)').parentElement.children[1], '1800');
        await user.type(app.getByText('Duration (seconds)').parentElement.children[1], '{enter}');

        // Add a keyword rule for sensor1 (relax: on)
        await user.click(within(
            app.getByText('Turn on lights (dummy)').parentElement
        ).getByRole('button', { name: 'Add Rule' }));
        await user.click(app.getByText('Set time'));
        await user.click(app.getByText('Keyword'));
        await user.selectOptions(app.getAllByLabelText('Keyword')[0], 'relax');
        await user.type(app.getAllByLabelText('Keyword')[0], '{enter}');
        await user.click(app.container.querySelectorAll('.form-control')[5]);
        await user.selectOptions(app.getByRole('combobox'), 'on');
        await user.type(app.getByRole('combobox'), '{enter}');

        // Add a timestamp rule for sensor1 (00:00: disabled)
        await user.click(within(
            app.getByText('Turn on lights (dummy)').parentElement
        ).getByRole('button', { name: 'Add Rule' }));
        await user.click(app.getByText('Set time'));
        await user.type(app.getByLabelText('Time'), '0:00');
        await user.type(app.getByLabelText('Time'), '{enter}');
        await user.click(app.container.querySelectorAll('.form-control')[7]);
        await user.selectOptions(app.getByRole('combobox'), 'disabled');
        await user.type(app.getByRole('combobox'), '{enter}');

        // Click submit, confirm correct request sent
        await user.click(app.getByRole('button', { name: 'Submit' }));
        expect(global.fetch).toHaveBeenCalledWith('generate_config_file', {
            method: 'POST',
            body: JSON.stringify({
                "metadata": {
                    "id": "Basement",
                    "floor": "-1",
                    "location": "Under staircase",
                    "schedule_keywords": {
                        "morning": "08:00",
                        "sleep": "23:00",
                        "sunrise": "06:00",
                        "sunset": "18:00",
                        "relax": "20:00"
                    }
                },
                "wifi": {
                    "ssid": "mywifi",
                    "password": "hunter2"
                },
                "device1": {
                    "_type": "wled",
                    "nickname": "TV Backlight",
                    "ip": "192.168.1.123",
                    "min_rule": 100,
                    "max_rule": 192,
                    "default_rule": 192,
                    "schedule": {
                        "relax": "enabled",
                        "sleep": "fade/100/1800"
                    }
                },
                "sensor1": {
                    "_type": "dummy",
                    "nickname": "Turn on lights",
                    "default_rule": "off",
                    "schedule": {
                        "relax": "on",
                        "00:00": "disabled"
                    },
                    "targets": [
                        "device1"
                    ]
                }
            }),
            headers: postHeaders
        });

        // Confirm redirected to overview page
        expect(window.location.href).toBe('/config_overview');
    });
});
