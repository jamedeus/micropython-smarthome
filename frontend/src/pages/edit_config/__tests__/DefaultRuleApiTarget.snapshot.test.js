import React from 'react';
import EditConfig from '../EditConfig';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { existingConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';

describe('DefaultRuleApiTarget', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('config', existingConfigContext.config);
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', existingConfigContext.edit_existing);
        createMockContext('target_node_ip', existingConfigContext.IP);
    });

    beforeEach(async () => {
        // Create user, render EditConfig
        user = userEvent.setup();
        app = render(
            <MetadataContextProvider>
                <ConfigProvider>
                    <EditConfig />
                </ConfigProvider>
            </MetadataContextProvider>
        );
    });

    it('matches snapshot when existing rule targets IR Blaster', async () => {
        // Click button to open ApiTargetRuleModal
        await user.click(app.getByRole('button', { name: 'Set rule' }));

        // Get modal, confirm correct options were rendered
        const modal = app.getByText('API Target Rule').parentElement.parentElement;
        expect(modal).toMatchSnapshot();
    });

    it('matches snapshot when existing rule targets device', async () => {
        // Click button to open ApiTargetRuleModal
        await user.click(app.getByRole('button', { name: 'Set rule' }));

        // Get modal, change target instance to device1, change action to turn_on
        const modal = app.getByText('API Target Rule').parentElement.parentElement;
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'device1');
        await user.selectOptions(within(modal).getAllByRole('combobox')[1], 'turn_on');

        // Change Off action target instance to device1, change action to turn_off
        await user.click(app.getByText('Off Action'));
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'device1');
        await user.selectOptions(within(modal).getAllByRole('combobox')[1], 'turn_off');

        // Confirm correct options were rendered
        expect(modal).toMatchSnapshot();
    });

    it('matches snapshot when self targetting', async () => {
        // Change target node to self
        await user.selectOptions(app.getByLabelText('Target Node:'), '127.0.0.1');

        // Click button to open ApiTargetRuleModal
        await user.click(app.getByRole('button', { name: 'Set rule' }));

        // Get modal, change target instance to device1, change action to turn_on
        const modal = app.getByText('API Target Rule').parentElement.parentElement;
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'device1');
        await user.selectOptions(within(modal).getAllByRole('combobox')[1], 'turn_on');

        // Change Off action target instance to device1, change action to turn_off
        await user.click(app.getByText('Off Action'));
        await user.selectOptions(within(modal).getAllByRole('combobox')[0], 'device1');
        await user.selectOptions(within(modal).getAllByRole('combobox')[1], 'turn_off');

        // Confirm correct options were rendered
        expect(modal).toMatchSnapshot();
    });
});
