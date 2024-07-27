import React from 'react';
import EditConfig from '../EditConfig';
import { EditConfigProvider } from 'root/EditConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { existingConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';

describe('EditConfig', () => {
    it('clears ApiTarget IP, rule, and schedule if IP does not match existing node', async () => {
        // Create mock state objects
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', existingConfigContext.edit_existing);
        createMockContext('target_node_ip', existingConfigContext.IP);
        // Change ApiTarget (device7) IP to one that isn't in apiTargetOptionsContext
        createMockContext('config', {
            ...existingConfigContext.config,
            device7: {
                ...existingConfigContext.config.device7,
                ip: '10.0.0.69'
            }
        });

        // Create user, render app
        const user = userEvent.setup();
        const app = render(
            <MetadataContextProvider>
                <EditConfigProvider>
                    <EditConfig />
                </EditConfigProvider>
            </MetadataContextProvider>
        );

        // Confirm target node input is blank, set rule button is disabled
        expect(app.getByLabelText('Target Node:').value).toBe('');
        expect(app.getByRole('button', { name: 'Set rule' }).disabled).toBe(true);

        // Try to go to page2, confirm target dropdown and Set rule button marked invalid
        await user.click(app.getByRole('button', { name: 'Next' }));
        expect(app.getByLabelText('Target Node:').classList).toContain('is-invalid');
        expect(app.getByRole('button', { name: 'Set rule' }).classList).toContain(
            'btn-outline-danger'
        );
    });
});
