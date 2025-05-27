import '@testing-library/jest-dom';

// You can add other global setup here if needed
// For example, mock global objects or functions

// Example: Mocking localStorage for tests if not using jsdom's built-in localStorage
// const localStorageMock = (function() {
//   let store: Record<string, string> = {};
//   return {
//     getItem: function(key: string) {
//       return store[key] || null;
//     },
//     setItem: function(key: string, value: string) {
//       store[key] = value.toString();
//     },
//     removeItem: function(key: string) {
//       delete store[key];
//     },
//     clear: function() {
//       store = {};
//     }
//   };
// })();
// Object.defineProperty(window, 'localStorage', {
//   value: localStorageMock
// });

// Silence console.warn and console.error during tests to keep output clean
// You might want to enable these during debugging or for specific tests
// beforeEach(() => {
//   vi.spyOn(console, 'warn').mockImplementation(() => {});
//   vi.spyOn(console, 'error').mockImplementation(() => {});
// });

// afterEach(() => {
//   vi.restoreAllMocks();
// });
