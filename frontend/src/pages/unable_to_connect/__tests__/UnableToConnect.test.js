import React from 'react';
import App from '../UnableToConnect';
import createMockContext from 'src/testUtils/createMockContext';

describe('UnableToConnect', () => {
    beforeAll(() => {
        // Create mock state object
        createMockContext('target_node', 'Bedroom');

        // Mock window.location.reload
        Object.defineProperty(window, 'location', {
            configurable: true,
            value: { reload: jest.fn() },
        });
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('redirects to overview when back button is clicked', async () => {
        // Create user, render app
        const user = userEvent.setup();
        const app = render(<App />);

        // Click back button, confirm redirected
        await user.click(app.getAllByRole('button')[0]);
        expect(window.location.href).toBe('/api');
    });

    it('redirects to overview when "Back to Overview" button is clicked', async () => {
        // Create user, render app
        const user = userEvent.setup();
        const app = render(<App />);

        // Click back button, confirm redirected
        await user.click(app.getByRole('button', { name: 'Back to Overview' }));
        expect(window.location.href).toBe('/api');
    });

    it('tries to reconnect every 5 seconds', () => {
        // Use fake timers
        jest.useFakeTimers();

        // Mock fetch function to simulate target node offline
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 502,
            json: () => Promise.resolve({
                status: 'error',
                message: 'Unable to connect'
            })
        }));

        // Render app, confirm fetch and reload have not been called
        render(<App />);
        expect(global.fetch).not.toHaveBeenCalled();
        expect(window.location.reload).not.toHaveBeenCalled();

        // Fast forward 5 seconds, confirm fetch was called, reload was not
        jest.advanceTimersByTime(5000);
        expect(global.fetch).toHaveBeenCalledWith('/get_status/Bedroom');
        expect(window.location.reload).not.toHaveBeenCalled();
    });

    it('reloads the page when target node back online', async () => {
        // Use fake timers
        jest.useFakeTimers();

        // Mock fetch function to simulate target node online
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
                status: 'success',
                message: {status: 'mock'}
            })
        }));

        // Render app, confirm fetch and reload have not been called
        render(<App />);
        expect(global.fetch).not.toHaveBeenCalled();
        expect(window.location.reload).not.toHaveBeenCalled();

        // Fast forward 5 seconds, confirm fetch and reload were called
        jest.advanceTimersByTime(5000);
        expect(global.fetch).toHaveBeenCalledWith('/get_status/Bedroom');
        jest.useRealTimers();
        await waitFor(() => {
            expect(window.location.reload).toHaveBeenCalled();
        });
    });
});
