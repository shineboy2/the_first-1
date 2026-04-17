"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import type { z } from "zod";

import api from "../api";
import { loginFormSchema } from "../types";
import { useAuthStore } from "@/lib/stores/auth-store";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Loader2, Lock, Mail } from "lucide-react";
import { useTheme } from "next-themes";

// Form validation schema
type FormSchema = z.infer<typeof loginFormSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { setUser, setToken } = useAuthStore();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const form = useForm<FormSchema>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  async function onSubmit(values: FormSchema) {
    setIsLoading(true);
    setError(null);

    try {
      // Create URLSearchParams for x-www-form-urlencoded format
      const formData = new URLSearchParams();
      formData.append("username", values.username);
      formData.append("password", values.password);

      console.log("Sending login request with:", {
        url: `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`,
        data: formData.toString(),
      });

      const response = await api.post("/api/v1/auth/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      // Extract token from response
      const token = response.data.access_token;

      // Set token first so subsequent API calls are authenticated
      setToken(token);

      // Set auth token in cookie for middleware
      document.cookie = `auth-token=${token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;

      // Fetch complete user data from /api/v1/users/me
      try {
        const userResponse = await api.get("/api/v1/users/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        // Map profile_type to role for consistency
        const userData = userResponse.data;
        const user = {
          id: userData.id || values.username,
          username: userData.username || values.username,
          email: userData.email || "",
          role: userData.role || (userData.profile_type === "admin" ? "admin" : "user"),
          profile_type: userData.profile_type,
        };

        setUser(user);
      } catch (userError) {
        console.error("Failed to fetch user data:", userError);
        // Fallback to basic user data from login response
        const user = {
          id: response.data.user_id || values.username,
          username: values.username,
          email: response.data.email || "",
          role: response.data.role || "user",
        };
        setUser(user);
      }

      // Wait a bit for zustand persist to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      // Redirect to dashboard with hard reload to ensure middleware runs
      window.location.href = "/dashboard";
    } catch (error: unknown) {
      console.error("Login error:", error);

      // Type guard for AxiosError
      const isAxiosError = (err: unknown): err is import("axios").AxiosError<{ detail?: string }> => {
        return typeof err === "object" && err !== null && "isAxiosError" in err;
      };

      if (isAxiosError(error)) {
        if (error.response) {
          const status = error.response.status;
          const detail = error.response.data?.detail;

          if (status === 401) {
            setError(detail || "نام کاربری یا رمز عبور اشتباه است");
          } else {
            setError(detail || "خطای سرور: لطفا دوباره تلاش کنید");
          }
        } else if (error.request) {
          setError("خطا در ارتباط با سرور");
        } else {
          setError("خطای پیکربندی درخواست");
        }
      } else {
        setError("خطای غیر منتظره");
      }
    } finally {
      setIsLoading(false);
    }
  }

  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
      </div>

      {/* Login Card */}
      <div className="w-full max-w-md relative z-10">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 rounded-lg mb-4">
            <Lock className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Response Admin</h1>
          <p className="text-gray-400">پنل مدیریت شبکه پاسخ‌دهی</p>
        </div>

        {/* Form Card */}
        <div className="bg-gray-800 dark:bg-gray-900 rounded-lg shadow-xl p-8 border border-gray-700">
          {error && (
            <Alert variant="destructive" className="mb-6 bg-red-900/20 border-red-800">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>خطا</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              {/* Username Field */}
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-gray-200">نام کاربری</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input
                          placeholder="نام کاربری یا ایمیل"
                          {...field}
                          disabled={isLoading}
                          className="pl-10 bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 focus:border-blue-500"
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Password Field */}
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-gray-200">رمز عبور</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input
                          type="password"
                          placeholder="رمز عبور"
                          {...field}
                          disabled={isLoading}
                          className="pl-10 bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 focus:border-blue-500"
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Submit Button */}
              <Button
                className="w-full bg-blue-600 hover:bg-blue-700 text-white mt-6"
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    در حال ورود...
                  </>
                ) : (
                  "ورود"
                )}
              </Button>
            </form>
          </Form>

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-gray-700 text-center text-sm text-gray-400">
            <p>برای دسترسی به پنل مدیریت، اطلاعات خود را وارد کنید</p>
          </div>
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-blue-900/20 border border-blue-800 rounded-lg p-4">
          <p className="text-sm text-blue-200">
            💡 <strong>نکته:</strong> برای تست، از اطلاعات ادمین پیش‌فرض استفاده کنید
          </p>
        </div>
      </div>
    </div>
  );
}