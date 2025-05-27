import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricsDisplayCard from './MetricsDisplayCard'; // Adjust path as needed
import { Users } from 'lucide-react'; // Example icon

describe('MetricsDisplayCard', () => {
  const mockProps = {
    title: 'Active Users',
    value: '1,234',
    icon: Users, // Pass the icon component itself
    description: 'Users currently online',
  };

  it('renders the title, value, and description', () => {
    render(<MetricsDisplayCard {...mockProps} />);
    
    expect(screen.getByText(mockProps.title)).toBeInTheDocument();
    expect(screen.getByText(mockProps.value)).toBeInTheDocument();
    expect(screen.getByText(mockProps.description)).toBeInTheDocument();
  });

  it('renders the icon', () => {
    render(<MetricsDisplayCard {...mockProps} />);
    
    // Check for the presence of an SVG element, as lucide-react icons are SVGs
    // It's hard to test for a specific icon without adding test-ids or specific class names to the icon wrapper
    const svgElement = screen.getByText(mockProps.title).parentElement?.querySelector('svg');
    expect(svgElement).toBeInTheDocument();
  });

  it('applies default color to icon if none provided', () => {
    render(<MetricsDisplayCard {...mockProps} />);
    const svgElement = screen.getByText(mockProps.title).parentElement?.querySelector('svg');
    // Default color is 'text-theme-accent-primary'
    // Testing exact class names can be brittle. Better to test visual properties if possible,
    // or ensure the class corresponding to default is applied.
    // For this test, we'll check if it does NOT have a specific other color.
    // A more robust test might involve snapshot testing or checking computed styles if set up.
    expect(svgElement).toHaveClass('text-theme-accent-primary');
  });

  it('applies custom color to icon if provided', () => {
    const customColorProps = {
      ...mockProps,
      colorClassName: 'text-green-500',
    };
    render(<MetricsDisplayCard {...customColorProps} />);
    const svgElement = screen.getByText(mockProps.title).parentElement?.querySelector('svg');
    expect(svgElement).toHaveClass('text-green-500');
  });

  it('renders without description if not provided', () => {
    const { description, ...propsWithoutDescription } = mockProps;
    render(<MetricsDisplayCard {...propsWithoutDescription} />);
    
    expect(screen.queryByText(description)).not.toBeInTheDocument();
  });
});
