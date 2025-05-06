import React from 'react';
import styled, { css } from 'styled-components';
import { colors, typography, space } from '../tokens/variables';

/**
 * SidebarItem component following the Figma "Sidebar Item" mappings
 */

// Container styles
const SidebarItemContainer = styled.div`
  /* Container layer style - transparent background */
  background-color: transparent;
  
  /* Styling */
  display: flex;
  align-items: center;
  padding: ${space[2]} ${space[3]};
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s;
  user-select: none;
  
  /* Hover state */
  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  /* Active state container */
  ${props => props.active && css`
    background-color: ${colors.accentPrimary};
  `}
`;

// Icon styles
const IconWrapper = styled.div`
  /* Icon layer style - navigation icon style */
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  margin-right: ${space[3]};
  
  /* Default state - Gray 400 */
  color: ${colors.textTertiary};
  
  /* Active state text/icon */
  ${props => props.active && css`
    color: ${colors.accentText};
  `}
  
  & > svg {
    width: 100%;
    height: 100%;
  }
`;

// Text styles
const Text = styled.span`
  /* Text layer style - navigation text style */
  font-family: ${typography.fontFamily};
  font-size: ${typography.base};
  font-weight: ${typography.medium};
  
  /* Default state - Gray 300 */
  color: ${colors.textSecondary};
  
  /* Active state text/icon */
  ${props => props.active && css`
    color: ${colors.accentText};
  `}
`;

// Badge for notifications or indicators
const Badge = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 ${space[1]};
  margin-left: auto;
  border-radius: 10px;
  background-color: ${props => 
    props.variant === 'primary' ? colors.accentPrimary : 
    props.variant === 'error' ? colors.error :
    props.variant === 'warning' ? colors.warning : 
    colors.textTertiary
  };
  color: ${colors.textPrimary};
  font-size: ${typography.xs};
  font-weight: ${typography.bold};
`;

/**
 * SidebarItem component that follows the Figma "Sidebar Item" mappings.
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - The text to display
 * @param {React.ReactNode} [props.icon] - Icon to display
 * @param {boolean} [props.active=false] - Whether the item is active
 * @param {Function} [props.onClick] - Click handler
 * @param {string|number} [props.badge] - Badge content to display
 * @param {string} [props.badgeVariant='default'] - Badge variant (primary, error, warning, default)
 * @returns {React.ReactElement} - SidebarItem component
 */
const SidebarItem = ({
  label,
  icon,
  active = false,
  onClick,
  badge,
  badgeVariant = 'default',
  ...props
}) => {
  return (
    <SidebarItemContainer
      active={active}
      onClick={onClick}
      role="button"
      tabIndex={0}
      {...props}
    >
      {icon && (
        <IconWrapper active={active}>
          {icon}
        </IconWrapper>
      )}
      
      <Text active={active}>{label}</Text>
      
      {badge && (
        <Badge variant={badgeVariant}>
          {badge}
        </Badge>
      )}
    </SidebarItemContainer>
  );
};

export default SidebarItem;
