"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

export default function ExportsPage() {
    const router = useRouter();

    useEffect(() => {
        // Redirect to storage-settings page
        router.push("/dashboard/storage-settings");
    }, [router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
            <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                <p className="text-gray-600 dark:text-gray-400">
                    در حال انتقال به تنظیمات Storage...
                </p>
            </div>
        </div>
    );
}
