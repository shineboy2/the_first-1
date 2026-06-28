"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an API endpoint or console
    console.error(error);
  }, [error]);

  return (
    <div className="p-8 space-y-4">
      <h2 className="text-2xl font-bold text-red-600">یک خطای غیرمنتظره در داشبورد رخ داد!</h2>
      <div className="bg-red-50 p-4 rounded-md border border-red-200">
        <p className="font-mono text-sm text-red-800 break-all">{error.message}</p>
        {error.stack && (
          <pre className="mt-4 text-xs text-red-700 whitespace-pre-wrap overflow-auto max-h-64">
            {error.stack}
          </pre>
        )}
      </div>
      <button
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        onClick={() => reset()}
      >
        تلاش مجدد
      </button>
    </div>
  );
}
