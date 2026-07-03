import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface Props { children: ReactNode; }
interface State { hasError: boolean; message: string; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 p-8">
          <Card className="max-w-md w-full">
            <CardContent className="flex flex-col items-center gap-4 pt-6 text-center">
              <div className="flex size-14 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="size-7 text-destructive" aria-hidden />
              </div>
              <h2 className="text-xl font-bold">Something went wrong</h2>
              <p className="text-muted-foreground text-sm max-w-md">
                {this.state.message || 'An unexpected error occurred.'}
              </p>
              <Button
                onClick={() => { this.setState({ hasError: false, message: '' }); window.location.reload(); }}
              >
                <RefreshCw className="size-3.5" /> Reload Page
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
    return this.props.children;
  }
}