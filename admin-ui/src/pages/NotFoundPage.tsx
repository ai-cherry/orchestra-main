import PageWrapper from '@/components/layout/PageWrapper';
import { Link } from '@tanstack/react-router';

export function NotFoundPage() {
  return (
    <PageWrapper title="404 - Page Not Found">
      <div className="text-center">
        <p className="text-xl text-muted-foreground mb-4">
          Oops! The page you're looking for doesn't exist.
        </p>
        <Link to="/" className="text-theme-accent-primary hover:underline">
          Go back to Dashboard
        </Link>
      </div>
    </PageWrapper>
  );
}
