"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Users,
  Zap,
  LogOut,
  Menu,
  Moon,
  Sun,
  Shield,
  FileCode,
  Server,
  ListTodo,
  Download,
  Globe,
  Database,
  Network,
  Settings as SettingsIcon,
} from "lucide-react";
import { useTheme } from "next-themes";

const navigation = [
  {
    name: "داشبورد",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "انواع پروفایل",
    href: "/dashboard/profile-types",
    icon: Shield,
  },
  {
    name: "کاربران",
    href: "/dashboard/users",
    icon: Users,
  },
  {
    name: "انواع درخواست",
    href: "/dashboard/request-types",
    icon: FileCode,
  },
  {
    name: "API‌های خارجی",
    href: "/dashboard/external-apis",
    icon: Globe,
  },
  {
    name: "درخواست‌ها",
    href: "/dashboard/requests",
    icon: Zap,
  },
  {
    name: "تنظیمات همگام‌سازی",
    href: "/dashboard/exports",
    icon: Download,
  },
  {
    name: "تنظیمات Elasticsearch",
    href: "/dashboard/elasticsearch-configs",
    icon: Database,
  },
  {
    name: "مدیریت تسک‌ها و ورکرها",
    href: "/dashboard/workers",
    icon: Network,
  },
];

const settingsNavigation = [
  {
    name: "تنظیمات",
    href: "/dashboard/settings",
    icon: SettingsIcon,
  },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user, logout, isLoading } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = () => {
    // auth store handles clearing cookie, localStorage, and redirect
    logout();
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile Sidebar Toggle */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <span className="flex-1 font-semibold text-gray-900 dark:text-white">
          Response Admin
        </span>
      </div>

      <div className="flex h-screen flex-col lg:flex-row lg:overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`${sidebarOpen ? "block" : "hidden"
            } lg:block fixed lg:relative w-64 h-screen bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto z-10 mt-14 lg:mt-0`}
        >
          <nav className="space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              // Check if current path matches or if it's exports page redirecting to storage-settings
              const isActive = pathname === item.href || 
                (item.href === "/dashboard/exports" && pathname === "/dashboard/storage-settings");
              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={isActive ? "default" : "ghost"}
                    className="w-full justify-start gap-3"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Button>
                </Link>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-4 absolute bottom-0 left-0 right-0 bg-white dark:bg-gray-800">
            <div className="mb-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {user?.username}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.email}
                  </p>
                </div>
                <Link href="/dashboard/settings">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <SettingsIcon className="h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setTheme(theme === "dark" ? "light" : "dark")
                }
                className="flex-1"
              >
                {theme === "dark" ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="flex-1"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto pt-14 lg:pt-0">
          {children}
        </main>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-0 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
