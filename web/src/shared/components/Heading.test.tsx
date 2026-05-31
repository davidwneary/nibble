import { render, screen } from '@testing-library/react';
import { Heading } from './Heading';

describe('Heading', () => {
  it('renders children text', () => {
    render(<Heading>Hello World</Heading>);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('renders as an h1 by default', () => {
    render(<Heading>Title</Heading>);
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });

  it('renders as specified heading level', () => {
    render(<Heading level={2}>Subtitle</Heading>);
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
  });
});
