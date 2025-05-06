import React, { forwardRef } from 'react';
import styled, { css } from 'styled-components';
import { colors, typography, space } from '../tokens/variables';

/**
 * Input component following the Figma "Input (Default)" mappings
 */

// Input container
const InputContainer = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  position: relative;
  margin-bottom: ${space[4]};
`;

// Input label
const InputLabel = styled.label`
  /* Label layer style */
  font-family: ${typography.fontFamily};
  font-size: ${typography.sm};
  font-weight: ${typography.medium};
  color: ${colors.textTertiary};
  margin-bottom: ${space[1]};
`;

// Input field styles
const InputField = styled.input`
  /* Container layer style */
  background-color: ${colors.surfaceAlt};
  
  /* Border layer style */
  border: 1px solid ${colors.borderSubtle};
  
  /* Text layer style */
  color: ${colors.textPrimary};
  
  /* Other styling */
  font-family: ${typography.fontFamily};
  font-size: ${typography.base};
  line-height: ${typography.leading.normal};
  border-radius: 0.375rem;
  padding: ${space[2]} ${space[3]};
  width: 100%;
  transition: all 0.2s;
  
  &::placeholder {
    color: ${colors.textTertiary};
  }
  
  /* Focus State layer - accent-primary variable */
  &:focus {
    outline: none;
    border-color: ${colors.accentPrimary};
    box-shadow: 0 0 0 2px ${colors.accentPrimary}33;
  }
  
  /* Disabled state */
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    background-color: ${colors.surface};
  }
  
  /* Error state */
  ${props => props.hasError && css`
    border-color: ${colors.error};
    
    &:focus {
      box-shadow: 0 0 0 2px ${colors.error}33;
    }
  `}
`;

// Helper/error text
const HelperText = styled.div`
  font-family: ${typography.fontFamily};
  font-size: ${typography.xs};
  line-height: ${typography.leading.normal};
  margin-top: ${space[1]};
  
  /* Error state */
  color: ${props => props.isError ? colors.error : colors.textTertiary};
`;

// Textarea variant
const TextareaField = styled(InputField).attrs({ as: 'textarea' })`
  min-height: 100px;
  resize: vertical;
`;

/**
 * Input component that follows the Figma "Input (Default)" mappings.
 * 
 * @param {Object} props - Component props
 * @param {string} [props.id] - Input ID
 * @param {string} [props.label] - Input label
 * @param {string} [props.placeholder] - Input placeholder
 * @param {string} [props.value] - Input value
 * @param {string} [props.type="text"] - Input type
 * @param {boolean} [props.disabled=false] - Whether input is disabled
 * @param {boolean} [props.required=false] - Whether input is required
 * @param {boolean} [props.multiline=false] - Whether to render a textarea
 * @param {string} [props.helperText] - Helper text to display below input
 * @param {string} [props.error] - Error message
 * @param {Function} [props.onChange] - Change handler
 * @param {Function} [props.onBlur] - Blur handler
 * @param {Function} [props.onFocus] - Focus handler
 * @returns {React.ReactElement} - Input component
 */
const Input = forwardRef(({
  id,
  label,
  placeholder,
  value,
  type = 'text',
  disabled = false,
  required = false,
  multiline = false,
  helperText,
  error,
  onChange,
  onBlur,
  onFocus,
  ...props
}, ref) => {
  const hasError = !!error;
  const fieldId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const helperId = `${fieldId}-helper`;
  
  const inputProps = {
    id: fieldId,
    placeholder,
    value,
    type,
    disabled,
    required,
    hasError,
    onChange,
    onBlur,
    onFocus,
    'aria-describedby': (helperText || error) ? helperId : undefined,
    ref,
    ...props
  };
  
  return (
    <InputContainer>
      {label && (
        <InputLabel htmlFor={fieldId}>
          {label}
          {required && ' *'}
        </InputLabel>
      )}
      
      {multiline ? (
        <TextareaField {...inputProps} />
      ) : (
        <InputField {...inputProps} />
      )}
      
      {(helperText || error) && (
        <HelperText id={helperId} isError={hasError}>
          {error || helperText}
        </HelperText>
      )}
    </InputContainer>
  );
});

Input.displayName = 'Input';

export default Input;
