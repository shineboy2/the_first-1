# TODO: اضافه کردن دسترسی کاربران به External APIs

## تاریخ: 2026-04-27

---

## ✅ انجام شده

### 1. Database
- ✅ ستون `allowed_external_apis` به جدول `users` اضافه شد
- ✅ نوع: `jsonb NOT NULL DEFAULT '[]'::jsonb`

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_external_apis jsonb NOT NULL DEFAULT '[]'::jsonb;
```

---

## ❌ باقی مانده

### 2. Backend - Response Network

#### 2.1. User Model
**فایل**: `response-network/api/models/user.py`

**تغییرات**:
```python
from sqlalchemy.dialects.postgresql import JSONB

class User(Base, TimestampMixin):
    # ... existing fields
    
    # اضافه کردن
    allowed_external_apis: Mapped[List[str]] = mapped_column(JSONB, nullable=False, server_default='[]')
```

#### 2.2. User Schema
**فایل**: `response-network/api/schemas/user.py`

**تغییرات**:
```python
class UserRead(BaseModel):
    # ... existing fields
    allowed_external_apis: List[str] = []

class UserUpdate(BaseModel):
    # ... existing fields
    allowed_external_apis: Optional[List[str]] = None
```

#### 2.3. External APIs Router
**فایل**: `response-network/api/routers/external_apis.py`

**Endpoints جدید**:
```python
# Grant user access
@router.post("/{api_id}/user-access")
async def grant_user_access(
    api_id: UUID,
    data: GrantUserAccessRequest,  # user_ids: List[UUID]
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Grant access to multiple users for this external API."""
    pass

# List user access
@router.get("/{api_id}/user-access")
async def list_user_access(
    api_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all users that have access to this external API."""
    pass

# Revoke user access
@router.delete("/{api_id}/user-access/{user_id}")
async def revoke_user_access(
    api_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Revoke a user's access to this external API."""
    pass
```

#### 2.4. Export Users
**فایل**: `response-network/api/workers/tasks/users_exporter.py`

**تغییرات**:
- ✅ از قبل `allowed_external_apis` را export می‌کند (چک کنید)

#### 2.5. Import Users  
**فایل**: `request-network/api/workers/tasks/users_importer.py`

**تغییرات**:
- ✅ از قبل `allowed_external_apis` را import می‌کند (چک کنید)

---

### 3. Frontend - Admin Panel

#### 3.1. ManageAccessDialog Component
**فایل**: `response-network/admin-panel/components/external-apis/manage-access-dialog.tsx`

**تغییرات**:
- اضافه کردن Tab "دسترسی کاربران" (مثل Request Types)
- فرم اضافه کردن کاربر
- لیست کاربران با دسترسی
- دکمه حذف دسترسی

**ساختار**:
```tsx
<Tabs defaultValue="profile">
  <TabsList>
    <TabsTrigger value="profile">دسترسی پروفایل‌ها</TabsTrigger>
    <TabsTrigger value="user">دسترسی کاربران</TabsTrigger>
  </TabsList>
  
  <TabsContent value="profile">
    {/* کد فعلی */}
  </TabsContent>
  
  <TabsContent value="user">
    {/* فرم اضافه کردن کاربر */}
    {/* لیست کاربران */}
  </TabsContent>
</Tabs>
```

#### 3.2. API Service
**فایل**: `response-network/admin-panel/lib/services/admin-api.ts`

**متدهای جدید**:
```typescript
// در externalApiService
async grantUserAccess(apiId: string, userIds: string[]): Promise<void> {
  await api.post(`/api/v1/external-apis/${apiId}/user-access`, {
    user_ids: userIds
  });
}

async getUserAccess(apiId: string): Promise<UserAccess[]> {
  const response = await api.get(`/api/v1/external-apis/${apiId}/user-access`);
  return response.data;
}

async revokeUserAccess(apiId: string, userId: string): Promise<void> {
  await api.delete(`/api/v1/external-apis/${apiId}/user-access/${userId}`);
}
```

---

## 📋 مراحل پیاده‌سازی

### مرحله 1: Backend (Response Network)
1. ✅ Database: ستون اضافه شد
2. ⏳ User Model: اضافه کردن فیلد
3. ⏳ User Schema: اضافه کردن فیلد
4. ⏳ External APIs Router: اضافه کردن endpoints
5. ⏳ Export/Import: بررسی و تست

### مرحله 2: Frontend (Admin Panel)
1. ⏳ ManageAccessDialog: اضافه کردن Tab کاربران
2. ⏳ API Service: اضافه کردن متدها
3. ⏳ تست کامل

### مرحله 3: تست End-to-End
1. ⏳ اضافه کردن دسترسی کاربر در Response Network
2. ⏳ Export/Import
3. ⏳ تست ارسال درخواست از Request Network
4. ⏳ بررسی access control

---

## 🎯 هدف نهایی

کاربران بتوانند:
1. از طریق Profile Type دسترسی داشته باشند (✅ موجود)
2. به صورت فردی دسترسی بگیرند (❌ نیاز به پیاده‌سازی)
3. دسترسی فردی override کند دسترسی Profile Type را

---

## 📝 نکات مهم

### منطق دسترسی:
```python
def has_external_api_access(user: User, api_name: str) -> bool:
    # 1. چک کردن دسترسی فردی
    if api_name in user.allowed_external_apis:
        return True
    
    # 2. چک کردن دسترسی Profile Type
    profile = get_profile_type(user.profile_type)
    if api_name in profile.permissions.get("allowed_external_apis", []):
        return True
    
    return False
```

### Export/Import:
- `allowed_external_apis` باید در export users باشد
- Import باید آن را به Request Network sync کند
- Request Network از آن برای access control استفاده می‌کند

---

## ⏱️ زمان تخمینی

- Backend: 2-3 ساعت
- Frontend: 2-3 ساعت
- تست: 1 ساعت

**جمع**: 5-7 ساعت

---

## 🚨 اولویت

**متوسط** - سیستم فعلاً با دسترسی Profile Type کار می‌کند، اما برای کنترل دقیق‌تر نیاز به دسترسی فردی است.

