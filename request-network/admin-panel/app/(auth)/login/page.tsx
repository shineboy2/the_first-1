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
import { AlertCircle, Loader2, Lock, Mail, Eye, EyeOff } from "lucide-react";
import { useTheme } from "next-themes";
import Image from "next/image";

// Form validation schema
type FormSchema = z.infer<typeof loginFormSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { setUser, setToken } = useAuthStore();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [captchaId, setCaptchaId] = useState("");
  const [captchaImage, setCaptchaImage] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const fetchCaptcha = async () => {
    try {
      const res = await api.get("/api/v1/captcha/");
      setCaptchaId(res.data.captcha_id);
      setCaptchaImage(res.data.image_base64);
    } catch (err) {
      console.error("Failed to load captcha", err);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchCaptcha();
  }, []);

  const form = useForm<FormSchema>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: {
      username: "",
      password: "",
      captcha_solution: "",
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
      formData.append("captcha_id", captchaId);
      formData.append("captcha_solution", values.captcha_solution);

      console.log("Sending login request with:", {
        url: `${api.defaults.baseURL || 'http://localhost:8001'}/api/v1/auth/login`,
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

      // Redirect to dashboard
      router.push("/dashboard");
      router.refresh();
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
      // Refresh captcha on error
      fetchCaptcha();
      form.setValue("captcha_solution", "");
    } finally {
      setIsLoading(false);
    }
  }

  if (!mounted) {
    return null;
  }

  return (
    <div className="w-full max-w-md relative z-10 p-4">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">سامانه صیاد</h1>
          <p className="text-gray-400">پنل مدیریت شبکه درخواست</p>
        </div>

        {/* Form Card */}
        <div className="bg-gray-900/60 backdrop-blur-md rounded-lg shadow-2xl p-8 border border-gray-700/50">
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
                        <Mail className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ right: '0.75rem' }} />
                        <Input
                          placeholder="نام کاربری یا ایمیل"
                          {...field}
                          disabled={isLoading}
                          className="pr-10 pl-3 bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 focus:border-blue-500"
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
                        <Lock className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ right: '0.75rem' }} />
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="رمز عبور"
                          {...field}
                          disabled={isLoading}
                          className="pr-10 pl-10 bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 focus:border-blue-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 focus:outline-none"
                          style={{ left: '0.75rem' }}
                        >
                          {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Captcha Field */}
              <FormField
                control={form.control}
                name="captcha_solution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-gray-200">کد امنیتی</FormLabel>
                    <div className="flex gap-2">
                      <FormControl>
                        <Input
                          placeholder="کد تصویر را وارد کنید"
                          {...field}
                          disabled={isLoading}
                          className="bg-gray-700 border-gray-600 text-white placeholder:text-gray-400 focus:border-blue-500"
                          dir="ltr"
                        />
                      </FormControl>
                      <div className="flex items-center gap-2 bg-gray-700 rounded-md p-1 border border-gray-600">
                        {captchaImage ? (
                          <img
                            src={captchaImage}
                            alt="captcha"
                            className="h-10 w-[140px] rounded object-cover cursor-pointer"
                            onClick={fetchCaptcha}
                          />
                        ) : (
                          <div className="h-10 w-[140px] bg-gray-800 flex items-center justify-center animate-pulse rounded">
                            ...
                          </div>
                        )}
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={fetchCaptcha}
                          disabled={isLoading}
                          className="h-10 w-10 text-gray-400 hover:text-white"
                        >
                          <Loader2 className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                        </Button>
                      </div>
                    </div>
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
    </div>
  );
}