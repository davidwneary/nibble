import { render, screen } from '@testing-library/react';
import { App } from './App';

describe('App', () => {
  it('renders the app name', () => {
    render(<App />);
    expect(screen.getByText('Nibble')).toBeInTheDocument();
  });

  it('renders a welcome message', () => {
    render(<App />);
    expect(
      screen.getByText(/your personal recipe collection/i)
    ).toBeInTheDocument();
  });
});
