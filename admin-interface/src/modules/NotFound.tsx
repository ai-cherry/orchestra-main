import React from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'

/**
 * NotFound component displayed when a route is not found
 */
const NotFound = () => {
  return (
    <div className="flex h-[80vh] flex-col items-center justify-center text-center">
      <h1 className="text-6xl font-bold">404</h1>
      <h2 className="mt-4 text-2xl font-semibold">Page Not Found</h2>
      <p className="mt-2 text-muted-foreground">
        The page you are looking for doesn't exist or has been moved.
      </p>
      <div className="mt-8">
        <Button asChild>
          <Link to="/">Return to Dashboard</Link>
        </Button>
      </div>
    </div>
  )
}

export default NotFound