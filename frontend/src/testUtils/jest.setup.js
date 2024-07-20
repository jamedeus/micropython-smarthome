import { render, within } from '@testing-library/react';
import userEvent from "@testing-library/user-event";
import { act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

beforeAll(() => {
    // Mock methods not implemented in jsdom
    window.HTMLElement.prototype.scrollIntoView = jest.fn();

    // Make available in all tests
    global.render = render;
    global.within = within;
    global.userEvent = userEvent;
    global.act = act;
    global.waitFor = waitFor;

    // Mock method called when window.location.href set
    Object.defineProperty(window, 'location', {
        value: {
            assign: jest.fn(),
        },
    });

    global.history.pushState = jest.fn();

    // Silence error (maybe from chart.js?)
    HTMLCanvasElement.prototype.getContext = jest.fn();
});

beforeEach(() => {
    // Reset number of calls for each mock to isolate test
    jest.clearAllMocks();
});
