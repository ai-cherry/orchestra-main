import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusIndicator from './StatusIndicator'; // Adjust path as needed

describe('StatusIndicator', () => {
  it('renders with "active" status and applies correct color', () => {
    render(<StatusIndicator status="active" />);
    const statusText = screen.getByText('active');
    expect(statusText).toBeInTheDocument();

    const dotElement = statusText.previousElementSibling; // The dot span
    expect(dotElement).toHaveClass('bg-green-500');
  });

  it('renders with "idle" status and applies correct color', () => {
    render(<StatusIndicator status="idle" />);
    const statusText = screen.getByText('idle');
    expect(statusText).toBeInTheDocument();

    const dotElement = statusText.previousElementSibling;
    expect(dotElement).toHaveClass('bg-yellow-500');
  });

  it('renders with "error" status and applies correct color', () => {
    render(<StatusIndicator status="error" />);
    const statusText = screen.getByText('error');
    expect(statusText).toBeInTheDocument();

    const dotElement = statusText.previousElementSibling;
    expect(dotElement).toHaveClass('bg-red-500');
  });

  it('renders with "offline" status and applies correct color', () => {
    render(<StatusIndicator status="offline" />);
    const statusText = screen.getByText('offline');
    expect(statusText).toBeInTheDocument();

    const dotElement = statusText.previousElementSibling;
    expect(dotElement).toHaveClass('bg-gray-400');
  });

  it('renders with an unknown status and applies default color', () => {
    render(<StatusIndicator status="unknown_status" />);
    const statusText = screen.getByText('unknown_status'); // Should still render the text
    expect(statusText).toBeInTheDocument();

    const dotElement = statusText.previousElementSibling;
    expect(dotElement).toHaveClass('bg-gray-300');
  });

  it('applies additional className if provided', () => {
    const customClass = "my-custom-class";
    render(<StatusIndicator status="active" className={customClass} />);
    // The component structure is a div wrapping the dot and text.
    // The className is applied to this wrapping div.
    const wrapperDiv = screen.getByText('active').parentElement;
    expect(wrapperDiv).toHaveClass(customClass);
  });

  it('capitalizes the status text', () => {
    render(<StatusIndicator status="active" />);
    // The component itself capitalizes the text for display
    expect(screen.getByText('Active')).toBeInTheDocument();
  });
});
