"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status?: string;
  error?: string;
}

export default function HomePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const apiUrl =
    process.env.NEXT_PUBLIC_DASHBOARD_API_URL || "http://localhost:8080"; // Placeholder

  useEffect(() => {
    async function fetchHealth() {
      setIsLoading(true);
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: HealthStatus = await response.json();
        setHealth(data);
      } catch (error) {
        console.error("Failed to fetch health:", error);
        setHealth({
          error: error instanceof Error ? error.message : String(error),
        });
      }
      setIsLoading(false);
    }

    fetchHealth();
  }, [apiUrl]);

  const getStatusBadgeColor = () => {
    if (!health || health.error) return "bg-red-500";
    if (health.status === "ok") return "bg-green-500";
    return "bg-yellow-500";
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-800">
      <div className="bg-gray-700 p-8 rounded-lg shadow-xl w-full max-w-md">
        <h1 className="text-3xl font-bold mb-6 text-center text-sky-400">
          AI Agent Dashboard
        </h1>

        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2 text-sky-300">
            Agent API URL
          </h2>
          <a
            href={apiUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 break-all"
          >
            {apiUrl}
          </a>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-3 text-sky-300">
            Agent Health Status
          </h2>
          {isLoading ? (
            <p className="text-gray-400">Loading status...</p>
          ) : (
            <div className="flex items-center">
              <span
                className={`w-4 h-4 rounded-full mr-2 ${getStatusBadgeColor()}`}
                title={health?.status || health?.error || "Unknown status"}
              ></span>
              <span className="text-lg">
                {health?.status
                  ? `Status: ${health.status}`
                  : health?.error
                    ? `Error: ${health.error}`
                    : "Unknown"}
              </span>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
