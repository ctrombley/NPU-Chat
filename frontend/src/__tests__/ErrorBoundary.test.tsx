import { render, screen, fireEvent } from '../test-utils';
import ErrorBoundary from '../components/ErrorBoundary';

const ThrowingChild = () => {
  throw new Error('Test error');
};

const GoodChild = () => <div>Working fine</div>;

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <GoodChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Working fine')).toBeInTheDocument();
  });

  it('renders fallback UI when a child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('resets error state when Try Again is clicked', () => {
    // Use a flag to control whether the child throws
    let shouldThrow = true;

    const ConditionalChild = () => {
      if (shouldThrow) throw new Error('Test error');
      return <div>Working fine</div>;
    };

    render(
      <ErrorBoundary>
        <ConditionalChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    // Stop throwing, then click Try Again
    shouldThrow = false;
    fireEvent.click(screen.getByText('Try Again'));

    expect(screen.getByText('Working fine')).toBeInTheDocument();
  });
});
