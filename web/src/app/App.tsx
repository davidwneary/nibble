import { Heading } from '../shared/components/Heading';
import '../styles/globals.css';

export function App() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-8">
      <div className="text-center max-w-md">
        <Heading>Nibble</Heading>
        <p className="mt-4 text-text-secondary text-lg">
          Your personal recipe collection
        </p>
      </div>
    </div>
  );
}
