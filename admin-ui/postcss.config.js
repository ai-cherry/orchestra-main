export default {
  plugins: {
    'tailwindcss': {},
    'autoprefixer': {
      // Add more specific browser targets if needed
      overrideBrowserslist: ['> 1%', 'last 2 versions', 'not dead'],
      grid: true
    },
    // Only enable cssnano in production to avoid development slowdowns
    ...process.env.NODE_ENV === 'production' ? {
      'cssnano': {
        preset: ['default', {
          // Disable SVG optimization which can cause issues
          svgo: false,
          // Disable discardComments to preserve license comments
          discardComments: { removeAll: true, preserveImportant: true },
          // Disable mergeLonghand which can cause issues with Tailwind
          mergeLonghand: false,
          // Ensure proper calc() handling
          calc: false,
          // Optimize color values
          colormin: true
        }]
      }
    } : {}
  },
  // Source maps for better debugging in development
  ...(process.env.NODE_ENV !== 'production' ? { map: { inline: true } } : {})
};
