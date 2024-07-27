import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import { postHeaders } from 'src/testUtils/headers';

describe('App', () => {
    it('sends sync_schedule_keywords request when page is loaded', async () => {
        // Create mock state objects
        createMockContext('status', mockContext.status);
        createMockContext('target_ip', mockContext.target_ip);
        createMockContext('recording', mockContext.recording);
        createMockContext('ir_macros', {});
        createMockContext('instance_metadata', api_card_metadata);
        createMockContext('api_target_options', mockContext.api_target_options);

        // Render app
        render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );

        // Confirm /sync_schedule_keywords request was made
        expect(global.fetch).toHaveBeenCalledWith('/sync_schedule_keywords', {
            method: 'POST',
            body: JSON.stringify({
                ip: '192.168.1.100',
                existing_keywords: {
                    sleep: '23:00',
                    morning: '08:00',
                    sunset: '20:56',
                    relax: '20:00',
                    sunrise: '05:36'
                }
            }),
            headers: postHeaders
        });
    });
});
