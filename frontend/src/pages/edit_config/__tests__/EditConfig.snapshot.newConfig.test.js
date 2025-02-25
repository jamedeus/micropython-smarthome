import React from 'react';
import EditConfig from '../EditConfig';
import { EditConfigProvider } from 'root/EditConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { newConfigContext, apiTargetOptionsContext } from './mockContext';
import { edit_config_metadata } from 'src/testUtils/mockMetadataContext';

describe('App', () => {
    it('matches snapshot when creating new config file', () => {
        // Create mock state objects
        createMockContext('config', newConfigContext.config);
        createMockContext('api_target_options', apiTargetOptionsContext);
        createMockContext('instance_metadata', edit_config_metadata);
        createMockContext('edit_existing', newConfigContext.edit_existing);
        createMockContext('ir_blaster_targets', newConfigContext.ir_blaster_targets);

        // Render App, confirm matches snapshot
        const component = render(
            <MetadataContextProvider>
                <EditConfigProvider>
                    <EditConfig />
                </EditConfigProvider>
            </MetadataContextProvider>
        );
        expect(component).toMatchSnapshot();
    });
});
