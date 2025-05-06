/**
 * Orchestra Design System Variables
 * 
 * This file defines the color and typography variables used across
 * the Orchestra design system, mapped from Figma variables.
 */

// Color Variables - these match the Orchestra-Color-Semantic variables from Figma
export const colors = {
  // Theme colors
  accentPrimary: 'var(--orchestra-accent-primary, #8B5CF6)', // Purple default
  accentSecondary: 'var(--orchestra-accent-secondary, #6D28D9)',
  accentText: 'var(--orchestra-accent-text, #FFFFFF)',
  
  // Background colors
  background: 'var(--orchestra-background, #111827)', // Dark background
  surface: 'var(--orchestra-surface, #1F2937)', // Gray 800/900
  surfaceAlt: 'var(--orchestra-surface-alt, #374151)', // Gray 700
  
  // Text colors
  textPrimary: 'var(--orchestra-text-primary, #FFFFFF)', // White
  textSecondary: 'var(--orchestra-text-secondary, #D1D5DB)', // Gray 300
  textTertiary: 'var(--orchestra-text-tertiary, #9CA3AF)', // Gray 400
  
  // Border colors
  borderSubtle: 'var(--orchestra-border-subtle, #4B5563)', // Gray 600
  borderDefault: 'var(--orchestra-border-default, #6B7280)', // Gray 500
  
  // Status colors
  success: 'var(--orchestra-success, #10B981)',
  warning: 'var(--orchestra-warning, #F59E0B)',
  error: 'var(--orchestra-error, #EF4444)',
  info: 'var(--orchestra-info, #3B82F6)'
};

// Typography variables
export const typography = {
  fontFamily: 'var(--orchestra-font-family, "Inter", sans-serif)',
  
  // Font weights
  regular: 'var(--orchestra-font-weight-regular, 400)',
  medium: 'var(--orchestra-font-weight-medium, 500)',
  semibold: 'var(--orchestra-font-weight-semibold, 600)',
  bold: 'var(--orchestra-font-weight-bold, 700)',
  
  // Font sizes
  xs: 'var(--orchestra-font-size-xs, 0.75rem)',
  sm: 'var(--orchestra-font-size-sm, 0.875rem)',
  base: 'var(--orchestra-font-size-base, 1rem)',
  lg: 'var(--orchestra-font-size-lg, 1.125rem)',
  xl: 'var(--orchestra-font-size-xl, 1.25rem)',
  '2xl': 'var(--orchestra-font-size-2xl, 1.5rem)',
  '3xl': 'var(--orchestra-font-size-3xl, 1.875rem)',
  '4xl': 'var(--orchestra-font-size-4xl, 2.25rem)',
  
  // Line heights
  leading: {
    none: 'var(--orchestra-line-height-none, 1)',
    tight: 'var(--orchestra-line-height-tight, 1.25)',
    snug: 'var(--orchestra-line-height-snug, 1.375)',
    normal: 'var(--orchestra-line-height-normal, 1.5)',
    relaxed: 'var(--orchestra-line-height-relaxed, 1.625)',
    loose: 'var(--orchestra-line-height-loose, 2)'
  }
};

// Space variables
export const space = {
  px: '1px',
  0: '0',
  0.5: '0.125rem',
  1: '0.25rem',
  1.5: '0.375rem',
  2: '0.5rem',
  2.5: '0.625rem',
  3: '0.75rem',
  3.5: '0.875rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  7: '1.75rem',
  8: '2rem',
  9: '2.25rem',
  10: '2.5rem',
  12: '3rem',
  14: '3.5rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  28: '7rem',
  32: '8rem',
  36: '9rem',
  40: '10rem',
  44: '11rem',
  48: '12rem',
  52: '13rem',
  56: '14rem',
  60: '15rem',
  64: '16rem',
  72: '18rem',
  80: '20rem',
  96: '24rem'
};

// Themes - Different personas can have their own theme
export const themes = {
  neutral: {
    accentPrimary: '#8B5CF6', // Purple
    accentSecondary: '#6D28D9'
  },
  cherry: {
    accentPrimary: '#EC4899', // Pink
    accentSecondary: '#DB2777'
  },
  sophia: {
    accentPrimary: '#3B82F6', // Blue
    accentSecondary: '#2563EB'
  },
  gordonGekko: {
    accentPrimary: '#F59E0B', // Orange
    accentSecondary: '#D97706'
  }
};

export default {
  colors,
  typography,
  space,
  themes
};
