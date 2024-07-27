const path = require('path');

module.exports = {
    testEnvironment: 'jsdom',
    transform: {
        '^.+\\.[t|j]sx?$': 'babel-jest',
        '^.+\\.css$': 'jest-css-modules-transform',
    },
    moduleNameMapper: {
        '^src/(.*)$': path.resolve(__dirname, 'src/$1'),
        '^css/(.*)$': '<rootDir>/src/css/$1',
        '^root/(.*)$': '<rootDir>/src/$1',
        '^util/(.*)$': '<rootDir>/src/util/$1',
        '^inputs/(.*)$': '<rootDir>/src/inputs/$1',
        '^modals/(.*)$': '<rootDir>/src/modals/$1',
        '^node_modules/(.*)$': '<rootDir>/node_modules/$1'
    },
    coveragePathIgnorePatterns: [
        'src/css/',
        'src/testUtils/',
        'mockContext.js'
    ],
    testPathIgnorePatterns: [
        'mockContext.js'
    ],
    setupFilesAfterEnv: ['<rootDir>/src/testUtils/jest.setup.js'],
    testTimeout: 15000
};
