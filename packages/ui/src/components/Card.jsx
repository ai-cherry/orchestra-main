import React from 'react';
import styled, { css } from 'styled-components';
import { colors, typography, space } from '../tokens/variables';

/**
 * Card component following the Figma "Card (Default)" mappings
 */

// Base card styles
const CardContainer = styled.div`
  /* Container Background layer */
  background-color: ${colors.surface};
  
  /* Border (Optional) layer */
  border: 1px solid ${colors.borderSubtle};
  
  /* Card styling */
  border-radius: 0.5rem;
  overflow: hidden;
  width: 100%;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s ease-in-out;
  
  /* Optional box shadow */
  ${props => props.elevated && css`
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  `}
  
  /* Interactive card */
  ${props => props.interactive && css`
    cursor: pointer;
    
    &:hover {
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    &:active {
      transform: translateY(1px);
    }
  `}
`;

// Card header
const CardHeader = styled.div`
  padding: ${space[4]} ${space[4]} ${props => props.withDivider ? space[3] : space[0]};
  ${props => props.withDivider && css`
    border-bottom: 1px solid ${colors.borderSubtle};
  `}
  
  /* Header Text layer using the semibold heading text style */
  h3 {
    font-family: ${typography.fontFamily};
    font-size: ${typography.lg};
    font-weight: ${typography.semibold};
    color: ${colors.textPrimary};
    margin: 0;
  }

  /* Subtitle */
  p {
    font-size: ${typography.sm};
    color: ${colors.textTertiary};
    margin: ${space[1]} 0 0 0;
  }
`;

// Card content
const CardContent = styled.div`
  padding: ${space[4]};
  flex: 1;
  
  /* Body Text layer using the regular body text style */
  color: ${colors.textSecondary};
  font-family: ${typography.fontFamily};
  font-size: ${typography.base};
  font-weight: ${typography.regular};
  line-height: ${typography.leading.normal};
`;

// Card footer
const CardFooter = styled.div`
  padding: ${space[3]} ${space[4]};
  ${props => props.withDivider && css`
    border-top: 1px solid ${colors.borderSubtle};
  `}
  display: flex;
  align-items: center;
  justify-content: ${props => props.alignEnd ? 'flex-end' : 'flex-start'};
  gap: ${space[2]};
`;

/**
 * Card component that follows the Figma "Card (Default)" mappings.
 * 
 * @param {Object} props - Component props
 * @param {boolean} [props.elevated=false] - Whether the card has elevation (box-shadow)
 * @param {boolean} [props.interactive=false] - Whether the card is interactive
 * @param {React.ReactNode} [props.header] - Card header content
 * @param {string} [props.title] - Card title (used in header)
 * @param {string} [props.subtitle] - Card subtitle (used in header)
 * @param {boolean} [props.headerDivider=false] - Whether to show a divider after the header
 * @param {React.ReactNode} props.children - Card content
 * @param {React.ReactNode} [props.footer] - Card footer content
 * @param {boolean} [props.footerDivider=false] - Whether to show a divider before the footer
 * @param {boolean} [props.footerAlignEnd=false] - Whether to align footer content to the end
 * @param {Function} [props.onClick] - Click handler when interactive is true
 * @returns {React.ReactElement} - Card component
 */
const Card = ({
  elevated = false,
  interactive = false,
  header,
  title,
  subtitle,
  headerDivider = false,
  children,
  footer,
  footerDivider = false,
  footerAlignEnd = false,
  onClick,
  ...props
}) => {
  const handleClick = interactive && onClick ? onClick : undefined;
  
  return (
    <CardContainer
      elevated={elevated}
      interactive={interactive}
      onClick={handleClick}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      {...props}
    >
      {/* Render header if provided or if title exists */}
      {(header || title) && (
        <CardHeader withDivider={headerDivider}>
          {header || (
            <>
              <h3>{title}</h3>
              {subtitle && <p>{subtitle}</p>}
            </>
          )}
        </CardHeader>
      )}
      
      {/* Main content */}
      <CardContent>
        {children}
      </CardContent>
      
      {/* Render footer if provided */}
      {footer && (
        <CardFooter withDivider={footerDivider} alignEnd={footerAlignEnd}>
          {footer}
        </CardFooter>
      )}
    </CardContainer>
  );
};

export default Card;
