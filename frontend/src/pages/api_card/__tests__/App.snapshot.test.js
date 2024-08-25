import React from 'react';
import App from '../ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import createMockContext from 'src/testUtils/createMockContext';
import { api_card_metadata } from 'src/testUtils/mockMetadataContext';
import {
    mockContext,
    mockContextIrRemotes,
    mockContextNoDevicesOrSensors
} from './mockContext';

describe('App', () => {
    beforeAll(() => {
        // Create all mock state objects except status
        createMockContext('target_ip', mockContext.target_ip);
        createMockContext('recording', mockContext.recording);
        createMockContext('ir_macros', {});
        createMockContext('instance_metadata', api_card_metadata);
        createMockContext('api_target_options', mockContext.api_target_options);

        // Set correct path
        Object.defineProperty(window, 'location', {
            writable: true,
            value: {
                pathname: '/api/Test Node'
            }
        });
    });

    // Remove status context after each to prevent interference between tests
    afterEach(() => {
        document.getElementById('status').remove();
    });

    it('matches snapshot', () => {
        // Create mock status with all devices and sensors, no IR remotes
        createMockContext('status', mockContext.status);

        // Render App, confirm matches snapshot
        const component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
        expect(component).toMatchSnapshot();
    });

    it('matches snapshot when both IR remotes are configured', () => {
        // Create mock status object with both IR remotes
        createMockContext('status', mockContextIrRemotes.status);

        // Render App, confirm matches snapshot
        const component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
        expect(component).toMatchSnapshot();
    });

    it('matches snapshot when only TV remote is configured', () => {
        // Create mock status object with only TV remote
        createMockContext('status', {
            ...mockContextIrRemotes.status, metadata: {
                ...mockContextIrRemotes.status.metadata, ir_targets: [ 'samsung_tv' ]
            }
        });

        // Render App, confirm matches snapshot
        const component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
        expect(component).toMatchSnapshot();
    });

    it('matches snapshot when only AC remote is configured', () => {
        // Create mock status object with only AC remote
        createMockContext('status', {
            ...mockContextIrRemotes.status, metadata: {
                ...mockContextIrRemotes.status.metadata, ir_targets: [ 'whynter_ac' ]
            }
        });

        // Render App, confirm matches snapshot
        const component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
        expect(component).toMatchSnapshot();
    });

    it('matches snapshot when no devices, sensors, or ir_blaster configured', () => {
        // Create mock status object with no devices, sensors, or ir_blaster
        createMockContext('status', mockContextNoDevicesOrSensors.status);

        // Set correct path (reads node name from URL, adds to edit link)
        Object.defineProperty(window, 'location', {
            writable: true,
            value: {
                pathname: '/api/Test Node'
            }
        });

        // Render App, confirm matches snapshot
        const component = render(
            <MetadataContextProvider>
                <ApiCardContextProvider>
                    <App />
                </ApiCardContextProvider>
            </MetadataContextProvider>
        );
        expect(component).toMatchSnapshot();
    });
});
