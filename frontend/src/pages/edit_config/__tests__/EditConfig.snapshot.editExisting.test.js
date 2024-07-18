import React from 'react';
import EditConfig from '../EditConfig';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { existingConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';

describe('EditConfig', () => {
    it('matches snapshot when editing existing config file', () => {
        // Create mock state objects
        createMockContext('config', existingConfigContext.config);
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', existingConfigContext.edit_existing);
        createMockContext('target_node_ip', existingConfigContext.IP);

        // Render EditConfig, confirm matches snapshot
        const app = render(
            <MetadataContextProvider>
                <ConfigProvider>
                    <EditConfig />
                </ConfigProvider>
            </MetadataContextProvider>
        );
        expect(app).toMatchSnapshot();
    });
});
