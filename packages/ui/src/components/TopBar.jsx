import React from 'react';
import styled, { css } from 'styled-components';
import { colors, typography, space } from '../tokens/variables';

/**
 * TopBar component following the Figma "Top Bar Container" mappings
 */

// Main container
const TopBarContainer = styled.header`
  /* Background layer */
  background-color: ${colors.surface};
  
  /* Border Bottom layer */
  border-bottom: 1px solid ${colors.borderSubtle};
  
  /* Styling */
  width: 100%;
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 ${space[6]};
  position: sticky;
  top: 0;
  z-index: 10;
`;

// Left section - typically contains logo and/or title
const LeftSection = styled.div`
  display: flex;
  align-items: center;
  flex: 1;
`;

// Center section - optional, can contain navigation or search
const CenterSection = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 2;
`;

// Right section - typically contains action buttons and user avatar
const RightSection = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 1;
  gap: ${space[4]};
`;

// Title styles
const Title = styled.h1`
  /* Title layer - page title style */
  font-family: ${typography.fontFamily};
  font-size: ${typography.xl};
  font-weight: ${typography.semibold};
  color: ${colors.textPrimary};
  margin: 0;
`;

// Subtitle styles
const Subtitle = styled.p`
  font-family: ${typography.fontFamily};
  font-size: ${typography.sm};
  color: ${colors.textTertiary};
  margin: 0 0 0 ${space[2]};
`;

// Action icon styles
const ActionIcon = styled.button`
  /* Action Icons layer style */
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${colors.textTertiary};
  background-color: transparent;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    color: ${colors.textPrimary};
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  &:focus-visible {
    outline: none;
    box-shadow: 0 0 0 2px ${colors.accentPrimary};
  }
  
  & > svg {
    width: 20px;
    height: 20px;
  }
`;

// User avatar
const Avatar = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
  
  /* User Avatar Border layer - accent-primary variable */
  border: 2px solid ${colors.accentPrimary};
  
  & > img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

// Logo container
const Logo = styled.div`
  height: 32px;
  margin-right: ${space[4]};
  display: flex;
  align-items: center;
  
  & > img {
    height: 100%;
    width: auto;
  }
`;

/**
 * TopBar component that follows the Figma "Top Bar Container" mappings.
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} [props.logo] - Logo component or element
 * @param {string} [props.title] - Title text
 * @param {string} [props.subtitle] - Subtitle text
 * @param {React.ReactNode} [props.centerContent] - Content for the center section
 * @param {React.ReactNode[]} [props.actionIcons] - Array of action icon elements
 * @param {string} [props.avatarSrc] - Source URL for the user avatar
 * @param {Function} [props.onAvatarClick] - Click handler for avatar
 * @param {React.ReactNode} [props.children] - Optional children to render in the right section
 * @returns {React.ReactElement} - TopBar component
 */
const TopBar = ({
  logo,
  title,
  subtitle,
  centerContent,
  actionIcons = [],
  avatarSrc,
  onAvatarClick,
  children,
  ...props
}) => {
  return (
    <TopBarContainer {...props}>
      {/* Left section */}
      <LeftSection>
        {logo && <Logo>{logo}</Logo>}
        {title && <Title>{title}</Title>}
        {subtitle && <Subtitle>{subtitle}</Subtitle>}
      </LeftSection>
      
      {/* Center section, if provided */}
      {centerContent && (
        <CenterSection>
          {centerContent}
        </CenterSection>
      )}
      
      {/* Right section */}
      <RightSection>
        {/* Action icons */}
        {actionIcons.map((icon, index) => (
          <ActionIcon key={`action-icon-${index}`} aria-label={`Action ${index + 1}`}>
            {icon}
          </ActionIcon>
        ))}
        
        {/* Custom children */}
        {children}
        
        {/* Avatar */}
        {avatarSrc && (
          <Avatar onClick={onAvatarClick} role={onAvatarClick ? "button" : undefined}>
            <img src={avatarSrc} alt="User avatar" />
          </Avatar>
        )}
      </RightSection>
    </TopBarContainer>
  );
};

export default TopBar;
