import React from 'react';
import styled, { css } from 'styled-components';
import { colors, typography } from '../tokens/variables';

/**
 * Button variants following the Figma component "Button (Primary)" mappings
 */
const ButtonVariants = {
  PRIMARY: 'primary',
  SECONDARY: 'secondary',
  OUTLINE: 'outline',
  GHOST: 'ghost',
};

/**
 * Button sizes
 */
const ButtonSizes = {
  SMALL: 'small',
  MEDIUM: 'medium',
  LARGE: 'large',
};

// Base button styles
const BaseButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: ${typography.fontFamily};
  font-weight: ${typography.semibold};
  border-radius: 0.375rem;
  transition: all 0.2s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  
  /* Disable default button styles */
  border: none;
  outline: none;
  
  /* Prevent text selection */
  user-select: none;
  
  /* Disabled state */
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  /* Icon + Text spacing */
  svg + span, span + svg {
    margin-left: 0.5rem;
  }
`;

// Primary button styles following the Figma mapping
const PrimaryStyles = css`
  /* Background layer with accent-primary variable */
  background-color: ${colors.accentPrimary};
  
  /* Text layer with accent-text variable */
  color: ${colors.accentText};
  
  /* Border layer - no border as specified in mapping */
  border: none;
  
  /* Icon layer with accent-text variable (will apply to SVG icons) */
  svg {
    fill: ${colors.accentText};
    stroke: ${colors.accentText};
  }
  
  &:hover {
    background-color: ${colors.accentSecondary};
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
  }
  
  &:active {
    transform: translateY(1px);
  }
  
  &:focus-visible {
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.4);
  }
`;

// Secondary button styles
const SecondaryStyles = css`
  background-color: ${colors.surfaceAlt};
  color: ${colors.textPrimary};
  
  &:hover {
    background-color: ${colors.surface};
  }
`;

// Outline button styles
const OutlineStyles = css`
  background-color: transparent;
  color: ${colors.accentPrimary};
  border: 1px solid ${colors.accentPrimary};
  
  &:hover {
    background-color: rgba(139, 92, 246, 0.1);
  }
`;

// Ghost button styles
const GhostStyles = css`
  background-color: transparent;
  color: ${colors.textSecondary};
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: ${colors.textPrimary};
  }
`;

// Size styles
const SizeStyles = {
  [ButtonSizes.SMALL]: css`
    height: 2rem;
    padding: 0 0.75rem;
    font-size: ${typography.sm};
  `,
  [ButtonSizes.MEDIUM]: css`
    height: 2.5rem;
    padding: 0 1rem;
    font-size: ${typography.base};
  `,
  [ButtonSizes.LARGE]: css`
    height: 3rem;
    padding: 0 1.25rem;
    font-size: ${typography.lg};
  `,
};

// Apply variant styles based on prop
const getVariantStyles = (variant) => {
  switch (variant) {
    case ButtonVariants.PRIMARY:
      return PrimaryStyles;
    case ButtonVariants.SECONDARY:
      return SecondaryStyles;
    case ButtonVariants.OUTLINE:
      return OutlineStyles;
    case ButtonVariants.GHOST:
      return GhostStyles;
    default:
      return PrimaryStyles;
  }
};

// Styled button with variants, sizes, etc.
const StyledButton = styled(BaseButton)`
  ${props => getVariantStyles(props.variant)}
  ${props => SizeStyles[props.size]}
  width: ${props => props.fullWidth ? '100%' : 'auto'};
`;

/**
 * Button component that follows the Figma component "Button (Primary)" mappings.
 * 
 * @param {Object} props - The component props
 * @param {string} [props.variant="primary"] - Button variant (primary, secondary, outline, ghost)
 * @param {string} [props.size="medium"] - Button size (small, medium, large)
 * @param {boolean} [props.fullWidth=false] - Whether button takes full width
 * @param {React.ReactNode} props.children - Button content
 * @param {React.ReactNode} [props.icon] - Optional icon
 * @param {boolean} [props.disabled=false] - Whether button is disabled
 * @param {Function} [props.onClick] - Click handler
 * @returns {React.ReactElement} - The button component
 */
const Button = ({
  variant = ButtonVariants.PRIMARY,
  size = ButtonSizes.MEDIUM,
  fullWidth = false,
  children,
  icon,
  disabled = false,
  onClick,
  ...props
}) => {
  return (
    <StyledButton
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      disabled={disabled}
      onClick={disabled ? undefined : onClick}
      {...props}
    >
      {icon && icon}
      {children && <span>{children}</span>}
    </StyledButton>
  );
};

// Export button component and its variants/sizes
export { Button as default, ButtonVariants, ButtonSizes };
