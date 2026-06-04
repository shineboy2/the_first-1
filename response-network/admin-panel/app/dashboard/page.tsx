"use client";

import { useAuthStore } from "@/lib/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { statsService } from "@/lib/services/admin-api";
import type { SystemStats } from "@/lib/services/admin-api";
import { Loader2, Users, Database, Layers, BarChart3 } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const STATUS_COLORS = {
  completed: "#10b981", // green-500
  failed: "#ef4444",    // red-500
  processing: "#3b82f6",// blue-500
};

const TYPE_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#06b6d4"];

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuthStore();
  const router = useRouter();
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch system stats
        const stats = await statsService.getSystemStats();
        setSystemStats(stats);
        
        // Fetch sync status
        try {
          const sync = await statsService.getSyncStatus();
          setSyncStatus(sync);
        } catch (e) {
          console.error("Could not fetch sync status", e);
        }
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      if (user.role !== 'admin') {
        setLoading(false);
        return;
      }
      fetchData();
    }
  }, [user]);

  if (authLoading || (!user && loading)) return null;

  // Render minimal dashboard for non-admins
  if (user && user.role !== 'admin') {
    return (
      <div className="p-8 space-y-6 max-w-4xl mx-auto mt-12">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">خوش آمدید، {user.username}!</h1>
          <p className="text-xl text-gray-500">پنل کاربری شبکه اینترانت (Response Network)</p>
          <div className="pt-8 flex justify-center gap-4">
            <Button size="lg" onClick={() => router.push('/dashboard/requests')}>مشاهده درخواست‌های من</Button>
          </div>
        </div>
      </div>
    );
  }

  // --- Admin Dashboard Computations --- //

  // Status Pie Chart Data
  const statusData = systemStats ? [
    { name: 'موفق', value: systemStats.requests.completed, color: STATUS_COLORS.completed },
    { name: 'در حال پردازش', value: systemStats.requests.processing, color: STATUS_COLORS.processing },
    { name: 'خطا', value: systemStats.requests.failed, color: STATUS_COLORS.failed },
  ].filter(d => d.value > 0) : [];

  // Active/Inactive Request Types Pie Chart Data (External APIs)
  const typesData = systemStats?.request_types_stats ? [
    { name: 'فعال', value: systemStats.request_types_stats.active, color: '#3b82f6' },
    { name: 'غیرفعال', value: systemStats.request_types_stats.inactive, color: '#94a3b8' },
  ].filter(d => d.value > 0) : [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-12">
      <div className="border-b bg-white dark:bg-gray-800 mb-8 p-8">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              مدیریت آمار شبکه اینترانت (Response)
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              بررسی آماری کلان از درخواست‌های دریافتی، کاربران و پردازش اطلاعات در دیتابیس مرکز.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm border rounded-full px-3 py-1 bg-gray-100 dark:bg-gray-700">
              {user?.username} ({user?.role})
            </span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
        </div>
      ) : systemStats ? (
        <div className="px-8 max-w-7xl mx-auto space-y-8">

          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="border-t-4 border-t-blue-500 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">کل کاربران شبکه</CardTitle>
                <Users className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{systemStats.users.total}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {systemStats.users.active} کاربر فعال
                </p>
              </CardContent>
            </Card>

            <Card className="border-t-4 border-t-indigo-500 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">مجموع درخواست‌های دریافتی</CardTitle>
                <Database className="h-4 w-4 text-indigo-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{systemStats.requests.total}</div>
                <p className="text-xs text-muted-foreground mt-1 text-green-600">
                  {systemStats.requests.completed} پردازش کامل شده
                </p>
              </CardContent>
            </Card>

            <Card className="border-t-4 border-t-pink-500 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">سرویس‌های (انواع) پیکربندی شده</CardTitle>
                <Layers className="h-4 w-4 text-pink-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {(systemStats.request_types_stats?.active || 0) + (systemStats.request_types_stats?.inactive || 0)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {systemStats.request_types_stats?.active || 0} سرویس فعال
                </p>
              </CardContent>
            </Card>

            <Card className="border-t-4 border-t-emerald-500 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">حجم دیتابیس فعلی</CardTitle>
                <Database className="h-4 w-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold" dir="ltr">{systemStats.database.size}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {systemStats.results.total} رکورد پاسخ (Result) ذخیره شده
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Sync Status Section */}
          {syncStatus && (
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold mb-3">وضعیت آخرین همگام‌سازی‌ها (Sync Status)</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {[
                  { key: 'user_export', label: 'کاربران' },
                  { key: 'request_types_export', label: 'انواع درخواست' },
                  { key: 'result_export', label: 'نتایج' },
                  { key: 'request_import', label: 'درخواست‌های جدید' }
                ].map(op => {
                  const data = syncStatus[op.key];
                  if (!data) return (
                    <div key={op.key} className="p-3 bg-gray-50 dark:bg-gray-900 rounded">
                      <div className="text-muted-foreground mb-1">{op.label}</div>
                      <div className="text-xs">هیچوقت</div>
                    </div>
                  );
                  
                  const isSuccess = data.status === 'success' || data.status === 'completed';
                  const isFailed = data.status === 'failed' || data.status === 'error';
                  const isProcessing = data.status === 'in_progress' || data.status === 'processing';
                  
                  return (
                    <div key={op.key} className={`p-3 rounded border-l-4 ${isSuccess ? 'bg-green-50 dark:bg-green-900/20 border-green-500' : isFailed ? 'bg-red-50 dark:bg-red-900/20 border-red-500' : isProcessing ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500' : 'bg-gray-50 dark:bg-gray-900 border-gray-400'}`}>
                      <div className="font-medium mb-1 flex justify-between">
                        <span>{op.label}</span>
                        <span className={isSuccess ? 'text-green-600' : isFailed ? 'text-red-600' : isProcessing ? 'text-blue-600' : 'text-gray-600'}>
                          {isSuccess ? 'موفق' : isFailed ? 'خطا' : isProcessing ? 'در حال انجام' : data.status}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground" dir="ltr">
                        {data.completed_at ? new Date(data.completed_at).toLocaleString('fa-IR') : (data.started_at ? new Date(data.started_at).toLocaleString('fa-IR') : '-')}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

            {/* Requests by Status */}
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>تعداد درخواست‌ها به تفکیک وضعیت (Response Stats)</CardTitle>
                <CardDescription>عملکرد موفقیت‌آمیز، در حال اتصال و خطاهای سیستمی</CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                {statusData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={statusData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {statusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [`${value} درخواست`, 'تعداد']} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">داده‌ای ثبت نشده</div>
                )}
              </CardContent>
            </Card>

            {/* Request Types active/inactive */}
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>تعداد API های (External) فعال/غیرفعال</CardTitle>
                <CardDescription>وضعیت سرویس‌های تنظیم شده در شبکه اینترانت</CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                {typesData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={typesData}
                        cx="50%"
                        cy="50%"
                        innerRadius={70}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {typesData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [`${value} API`, 'تعداد']} />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">داده‌ای ثبت نشده</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Bar Chart Row */}
          <div className="grid grid-cols-1 gap-8">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>نمودار درخواست‌های دریافتی به تفکیک نوع سرویس (کوئری)</CardTitle>
                <CardDescription>حجم ترافیک دریافت شده روی API های متصل به شبکه اینترانت</CardDescription>
              </CardHeader>
              <CardContent className="h-[400px]">
                {systemStats.requests_by_type && systemStats.requests_by_type.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={systemStats.requests_by_type} layout="vertical" margin={{ top: 20, right: 30, left: 100, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" />
                      <YAxis dataKey="type" type="category" width={150} tick={{ fontSize: 12, fill: '#64748b' }} />
                      <Tooltip cursor={{ fill: '#f1f5f9' }} formatter={(value) => [`${value} عدد`, 'تعداد دریافت']} />
                      <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                        {systemStats.requests_by_type.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={TYPE_COLORS[index % TYPE_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">داده‌ای ثبت نشده</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Table Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
            <Card className="col-span-1 lg:col-span-2 shadow-sm">
              <CardHeader>
                <CardTitle>جدول درخواست‌ها به تفکیک کاربر</CardTitle>
                <CardDescription>آمار دریافت و پردازش موفقیت آمیز درخواست‌های کاربران تایید شده</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader className="bg-gray-50 dark:bg-gray-900/50">
                      <TableRow>
                        <TableHead>نام کاربری</TableHead>
                        <TableHead className="text-center">کل درخواست‌های دریافتی</TableHead>
                        <TableHead className="text-center text-green-600">تکمیل شده (موفق)</TableHead>
                        <TableHead className="text-center">درصد موفقیت (Success Rate)</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {systemStats.user_request_stats && systemStats.user_request_stats.length > 0 ? (
                        systemStats.user_request_stats.map((userStat, i) => {
                          const successRate = userStat.total > 0
                            ? Math.round((userStat.completed / userStat.total) * 100)
                            : 0;
                          return (
                            <TableRow key={i}>
                              <TableCell className="font-medium">{userStat.username}</TableCell>
                              <TableCell className="text-center font-bold">{userStat.total}</TableCell>
                              <TableCell className="text-center font-bold text-green-600">{userStat.completed}</TableCell>
                              <TableCell className="text-center">
                                <div className="flex items-center justify-center gap-2">
                                  <span className="w-8 text-right text-xs text-gray-500">{successRate}%</span>
                                  <div className="h-2 w-24 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                      className={`h-full ${successRate > 80 ? 'bg-green-500' : successRate > 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                      style={{ width: `${successRate}%` }}
                                    />
                                  </div>
                                </div>
                              </TableCell>
                            </TableRow>
                          );
                        })
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">داده‌ای ثبت نشده</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </div>

        </div>
      ) : (
        <div className="p-8"><p className="text-red-500 text-center">خطا در بارگذاری اطلاعات داشبورد</p></div>
      )}
    </div>
  );
}
