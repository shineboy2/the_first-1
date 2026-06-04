"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
  Search,
  MoreHorizontal,
  RefreshCw,
  AlertCircle,
  ArrowUpDown,
  UserCog,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";

import { userService } from "@/lib/services/admin-api";
import type { User } from "@/lib/services/admin-api";

interface UsersState {
  users: User[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  sortBy: "name" | "email" | "created" | "role";
  sortOrder: "asc" | "desc";
}

export default function UsersPage() {
  const router = useRouter();
  const { user: currentUser, isLoading: authLoading } = useAuthStore();
  const [state, setState] = useState<UsersState>({
    users: [],
    loading: true,
    error: null,
    searchTerm: "",
    sortBy: "created",
    sortOrder: "desc",
  });

  // Fetch users
  const fetchUsers = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      const data = await userService.getUsers();
      setState((prev) => ({
        ...prev,
        users: Array.isArray(data) ? data : [],
        loading: false,
      }));
    } catch (error) {
      console.error("Error fetching users:", error);
      setState((prev) => ({
        ...prev,
        loading: false,
        error: "خطا در دریافت لیست کاربران",
      }));
    }
  };

  useEffect(() => {
    if (!authLoading) {
      fetchUsers();
    }
  }, [authLoading]);

  const handleRefresh = async () => {
    fetchUsers();
  };

  const handleDetailsClick = (user: User) => {
    router.push(`/dashboard/users/${user.id}`);
  };

  // Filter and sort users
  const filteredUsers = state.users
    .filter(
      (user) =>
        user.username.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
        (user.full_name && user.full_name.toLowerCase().includes(state.searchTerm.toLowerCase()))
    )
    .sort((a, b) => {
      let aValue: string | number, bValue: string | number;

      switch (state.sortBy) {
        case "name":
          aValue = a.username.toLowerCase();
          bValue = b.username.toLowerCase();
          break;
        case "email":
          aValue = a.email.toLowerCase();
          bValue = b.email.toLowerCase();
          break;
        case "created":
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
        case "role":
          aValue = a.is_superuser ? 1 : 0;
          bValue = b.is_superuser ? 1 : 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return state.sortOrder === "asc" ? -1 : 1;
      if (aValue > bValue) return state.sortOrder === "asc" ? 1 : -1;
      return 0;
    });

  // Check auth
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!currentUser) {
    router.push("/login");
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b bg-white dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                مدیریت دسترسی کاربران
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                مشاهده و تخصیص کلیدهای API برای کلاینت‌ها
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={handleRefresh}
                disabled={state.loading}
              >
                <RefreshCw className={`h-4 w-4 ${state.loading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Error Alert */}
        {state.error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>خطا</AlertTitle>
            <AlertDescription>{state.error}</AlertDescription>
          </Alert>
        )}

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-3 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">کل کاربران سینک شده</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{state.users.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">کاربران فعال</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {state.users.filter((u) => u.is_active).length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">مدیران سیستم</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">
                {state.users.filter((u) => u.profile_type === "admin").length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Sort */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>جستجو و فیلتر</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="جستجو بر اساس نام کاربری، ایمیل یا نام..."
                  value={state.searchTerm}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, searchTerm: e.target.value }))
                  }
                  className="pr-10"
                />
              </div>

              <div className="flex gap-1">
                {(["name", "email", "created", "role"] as const).map((sort) => (
                  <Button
                    key={sort}
                    variant={state.sortBy === sort ? "default" : "outline"}
                    size="sm"
                    onClick={() => {
                      if (state.sortBy === sort) {
                        setState((prev) => ({
                          ...prev,
                          sortOrder: prev.sortOrder === "asc" ? "desc" : "asc",
                        }));
                      } else {
                        setState((prev) => ({
                          ...prev,
                          sortBy: sort,
                          sortOrder: "desc",
                        }));
                      }
                    }}
                  >
                    {sort === "name" && "نام کاربری"}
                    {sort === "email" && "ایمیل"}
                    {sort === "created" && "تاریخ"}
                    {sort === "role" && "نقش"}
                    {state.sortBy === sort && (
                      <ArrowUpDown className="h-3 w-3 mr-1" />
                    )}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Users Table */}
        <Card>
          <CardHeader>
            <CardTitle>لیست کاربران</CardTitle>
            <CardDescription>{filteredUsers.length} کاربر برای ارائه خدمات</CardDescription>
          </CardHeader>
          <CardContent>
            {state.loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">نام کاربری</TableHead>
                      <TableHead className="text-right">ایمیل</TableHead>
                      <TableHead className="text-center">وضعیت</TableHead>
                      <TableHead className="text-center">نقش پروفایل</TableHead>
                      <TableHead className="text-center">تاریخ عضویت</TableHead>
                      <TableHead className="text-center">دسترسی / API</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.length > 0 ? (
                      filteredUsers.map((user) => (
                        <TableRow key={user.id}>
                          <TableCell className="font-medium">
                            <div>{user.username}</div>
                            <div className="font-mono text-[10px] text-muted-foreground mt-1 select-all">{user.id}</div>
                          </TableCell>
                          <TableCell>{user.email}</TableCell>
                          <TableCell className="text-center">
                            <Badge
                              variant={user.is_active ? "default" : "secondary"}
                              className={
                                user.is_active
                                  ? "bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900 dark:text-green-200"
                                  : "bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900 dark:text-red-200"
                              }
                            >
                              {user.is_active ? "فعال" : "غیرفعال"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge
                              variant={user.profile_type === 'admin' ? "default" : "secondary"}
                              className={
                                user.profile_type === 'admin'
                                  ? "bg-purple-100 text-purple-800 hover:bg-purple-100 dark:bg-purple-900 dark:text-purple-200"
                                  : "bg-gray-100 text-gray-800 hover:bg-gray-100 dark:bg-gray-900 dark:text-gray-200"
                              }
                            >
                              {user.profile_type}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-center" dir="ltr">
                            <span className="text-sm text-muted-foreground">
                              {new Date(user.created_at).toLocaleDateString("fa-IR")}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="h-8 w-8 p-0">
                                  <span className="sr-only">باز کردن منو</span>
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuLabel>عملیات کاربری</DropdownMenuLabel>
                                <DropdownMenuItem onClick={() => handleDetailsClick(user)}>
                                  <UserCog className="ml-2 h-4 w-4" />
                                  مدیریت API Key و آمار
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8">
                          <p className="text-muted-foreground">
                            کاربری یافت نشد
                          </p>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
