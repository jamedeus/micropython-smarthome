import React from 'react';
import App from '../Offline';

describe('Offline', () => {
    beforeAll(() => {
        // Mock window.location.reload
        Object.defineProperty(window, 'location', {
            configurable: true,
            value: { reload: jest.fn() },
        });

        // Use fake timers
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
    });

    it('tries to reconnect every 15 seconds', () => {
        // Mock fetch function to simulate backend offline
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 404
        }));

        // Render app, confirm fetch and reload have not been called
        render(<App />);
        expect(global.fetch).not.toHaveBeenCalled();
        expect(window.location.reload).not.toHaveBeenCalled();

        // Fast forward 15 seconds, confirm fetch was called, reload was not
        jest.advanceTimersByTime(15000);
        expect(global.fetch).toHaveBeenCalledWith('/');
        expect(window.location.reload).not.toHaveBeenCalled();
    });

    it('reloads the page when able to connect to backend', async () => {
        // Mock fetch function to simulate backend available
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200
        }));

        // Render app, confirm fetch and reload have not been called
        render(<App />);
        expect(global.fetch).not.toHaveBeenCalled();
        expect(window.location.reload).not.toHaveBeenCalled();

        // Fast forward 15 seconds, confirm fetch and reload were called
        jest.advanceTimersByTime(15000);
        expect(global.fetch).toHaveBeenCalledWith('/');
        jest.useRealTimers();
        await waitFor(() => {
            expect(window.location.reload).toHaveBeenCalled();
        });
    });
});
