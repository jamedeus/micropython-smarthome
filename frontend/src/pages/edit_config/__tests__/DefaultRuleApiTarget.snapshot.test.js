import React from 'react';
import EditConfig from '../EditConfig';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { existingConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';

describe('App', () => {
    it('matches snapshot when existing rule targets IR Blaster', async () => {
        // Create mock state objects
        createMockContext('config', existingConfigContext.config);
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', existingConfigContext.edit_existing);
        createMockContext('target_node_ip', existingConfigContext.IP);

        // Create user, render EditConfig
        const user = userEvent.setup();
        const app = render(
            <MetadataContextProvider>
                <ConfigProvider>
                    <EditConfig />
                </ConfigProvider>
            </MetadataContextProvider>
        );

        // Click button to open ApiTargetRuleModal
        await user.click(app.getByRole('button', { name: 'Set rule' }));

        // Get modal, confirm correct options were rendered
        const modal = app.getByText('API Target Rule').parentElement.parentElement;
        expect(modal).toMatchSnapshot();
    });

    it('matches snapshot when existing rule targets device', async () => {
        // Create mock state objects
        createMockContext('config', existingConfigContext.config);
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', existingConfigContext.edit_existing);
        createMockContext('target_node_ip', existingConfigContext.IP);

        // Create user, render EditConfig
        const user = userEvent.setup();
        const app = render(
            <MetadataContextProvider>
                <ConfigProvider>
                    <EditConfig />
                </ConfigProvider>
            </MetadataContextProvider>
        );

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
