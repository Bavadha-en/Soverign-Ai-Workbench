import React from 'react';
import { RotateCcw, TriangleAlert } from 'lucide-react';

interface Props {
  children: React.ReactNode;
  /** Changing this value resets the boundary — used to recover on navigation. */
  resetKey?: string;
}

interface State {
  error: Error | null;
}

/**
 * Keeps a render failure in one panel from taking the whole console down.
 * Important during a live demo: a bad payload should degrade, not white-screen.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Render error:', error, info.componentStack);
  }

  private handleReset = () => this.setState({ error: null });

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <section className="card">
        <div className="card-body">
          <div className="empty">
            <div className="empty-icon" style={{ background: 'var(--danger-50)', color: 'var(--danger-600)' }}>
              <TriangleAlert size={20} />
            </div>
            <p className="empty-title">This panel could not be displayed</p>
            <p className="empty-text">
              The rest of the console is unaffected. Retry the panel, or switch to another module.
            </p>
            <code className="text-xs mono muted" style={{ marginTop: 10 }}>
              {error.message}
            </code>
            <button type="button" className="btn btn-secondary btn-sm" onClick={this.handleReset} style={{ marginTop: 14 }}>
              <RotateCcw size={13} />
              Retry
            </button>
          </div>
        </div>
      </section>
    );
  }
}
