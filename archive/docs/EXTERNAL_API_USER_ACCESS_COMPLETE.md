# ✅ دسترسی کاربران به External APIs - تکمیل شد!

## تاریخ: 2026-04-27

---

## 🎯 هدف

اضافه کردن قابلیت مدیریت دسترسی **فردی کاربران** به External APIs (علاوه بر دسترسی Profile Type)

---

## ✅ کارهای انجام شده

### 1. Database
- ✅ ستون `allowed_external_apis` به جدول `users` اضافه شد
- ✅ نوع: `jsonb NOT NULL DEFAULT '[]'::jsonb`

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_external_apis jsonb NOT NULL DEFAULT '[]'::jsonb;
```

### 2. Backend - Response Network

#### 2.1. User Model
**فایل**: `response-network/api/models/user.py`

**تغییرات**:
```python
from sqlalchemy.dialects.postgresql import JSONB

class User(Base, TimestampMixin):
    # ...
    allowed_external_apis: Mapped[List[str]] = mapped_column(JSONB, nullable=False, server_default='[]')
```

#### 2.2. User Schema
**فایل**: `response-network/api/schemas/user.py`

**تغییرات**:
```python
class UserBase(BaseModel):
    # ...
    allowed_external_apis: list[str] = []

class UserRead(UserBase):
    # ...
    allowed_external_apis: list[str]

class UserUpdate(BaseModel):
    # ...
    allowed_external_apis: list[str] | None = None
```

#### 2.3. External APIs Router
**فایل**: `response-network/api/routers/external_apis.py`

**Endpoints جدید**:

1. **Grant User Access**
```python
@router.post("/{api_id}/user-access")
async def grant_user_access(
    api_id: UUID,
    data: GrantUserAccessRequest,  # user_ids: List[UUID]
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Grant access to multiple users for this external API."""
```

2. **List User Access**
```python
@router.get("/{api_id}/user-access")
async def list_user_access(
    api_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all users that have access to this external API."""
```

3. **Revoke User Access**
```python
@router.delete("/{api_id}/user-access/{user_id}")
async def revoke_user_access(
    api_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Revoke a user's access to this external API."""
```

### 3. Frontend - Admin Panel

#### 3.1. ManageAccessDialog Component
**فایل**: `response-network/admin-panel/components/external-apis/manage-access-dialog.tsx`

**تغییرات**:
- ✅ اضافه شدن Tabs با دو Tab:
  - Tab 1: دسترسی پروفایل‌ها
  - Tab 2: دسترسی کاربران (جدید)
- ✅ فرم اضافه کردن کاربر
- ✅ لیست کاربران با دسترسی
- ✅ دکمه حذف دسترسی کاربر

**ساختار**:
```tsx
<Tabs defaultValue="profile">
  <TabsList>
    <TabsTrigger value="profile">دسترسی پروفایل‌ها</TabsTrigger>
    <TabsTrigger value="user">دسترسی کاربران</TabsTrigger>
  </TabsList>
  
  <TabsContent value="profile">
    {/* مدیریت دسترسی Profile Types */}
  </TabsContent>
  
  <TabsContent value="user">
    {/* مدیریت دسترسی کاربران */}
  </TabsContent>
</Tabs>
```

#### 3.2. API Service
**فایل**: `response-network/admin-panel/lib/services/admin-api.ts`

**متدهای جدید**:
```typescript
// در externalApiService
async grantUserAccess(apiId: string, userIds: string[]): Promise<void>
async getUserAccess(apiId: string): Promise<any[]>
async revokeUserAccess(apiId: string, userId: string): Promise<void>
```

---

## 🔄 فرایند کامل

### مدیریت دسترسی:
1. Admin به صفحه External APIs می‌رود
2. روی منوی عملیات یک API کلیک می‌کند
3. "مدیریت دسترسی" را انتخاب می‌کند
4. Dialog با دو Tab باز می‌شود:
   - **Tab پروفایل‌ها**: مدیریت دسترسی Profile Types
   - **Tab کاربران**: مدیریت دسترسی فردی کاربران
5. می‌تواند کاربر اضافه یا حذف کند
6. تغییرات بلافاصله اعمال می‌شوند

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

---

## 📊 مقایسه قبل و بعد

### قبل:
```
External API Access:
└── Profile Type Access (گروهی)
    ├── admin → ocr_space ✓
    └── user → ✗
```

### بعد:
```
External API Access:
├── Profile Type Access (گروهی)
│   ├── admin → ocr_space ✓
│   └── user → ✗
└── User Access (فردی)
    ├── user_123 → ocr_space ✓
    └── user_456 → ocr_space ✓
```

---

## 🚀 Deploy

### فایل‌های تغییر یافته:

**Backend**:
1. `response-network/api/models/user.py`
2. `response-network/api/schemas/user.py`
3. `response-network/api/routers/external_apis.py`

**Frontend**:
1. `response-network/admin-panel/components/external-apis/manage-access-dialog.tsx`
2. `response-network/admin-panel/lib/services/admin-api.ts`

### دستورات Deploy:
```bash
# Database
ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_external_apis jsonb NOT NULL DEFAULT '[]'::jsonb;

# Backend
docker compose up --build -d api

# Frontend
docker compose up --build -d admin-panel
```

**وضعیت**: ✅ همه سرویس‌ها rebuild و در حال اجرا هستند

---

## 📝 تست

### مراحل تست:
1. ✅ ورود به `/dashboard/external-apis`
2. ✅ کلیک روی "مدیریت دسترسی" برای یک API
3. ✅ رفتن به Tab "دسترسی کاربران"
4. ✅ اضافه کردن یک کاربر
5. ✅ بررسی لیست کاربران با دسترسی
6. ✅ حذف دسترسی یک کاربر
7. ✅ Export/Import و بررسی sync

### URL تست:
```
http://192.168.214.141:3000/dashboard/external-apis
```

Login: `admin` / `admin123456`

---

## ✅ نتیجه نهایی

### کامل شده:
- ✅ Database: ستون `allowed_external_apis` اضافه شد
- ✅ Backend: User Model, Schema, و Endpoints
- ✅ Frontend: Dialog با Tab کاربران
- ✅ API Service: متدهای مدیریت دسترسی کاربران
- ✅ Deploy: همه تغییرات اعمال شدند

### قابلیت‌های جدید:
1. ✅ مدیریت دسترسی فردی کاربران
2. ✅ Override کردن دسترسی Profile Type
3. ✅ UI یکپارچه با Request Types
4. ✅ Export/Import دسترسی‌ها

---

## 🎯 مزایا

### 1. کنترل دقیق‌تر
- دسترسی فردی به کاربران خاص
- Override کردن محدودیت‌های Profile Type

### 2. انعطاف‌پذیری
- می‌توان به یک کاربر خاص دسترسی داد بدون تغییر Profile Type

### 3. سازگاری
- دقیقاً مثل Request Types کار می‌کند
- UI و UX یکسان

### 4. Sync خودکار
- Export/Import دسترسی‌ها به Request Network
- Access Control در Request Network

---

## 📚 مستندات مرتبط

- `EXTERNAL_API_TODO_CRITICAL.md` - TODO های قبلی
- `EXTERNAL_API_ACCESS_REFACTOR.md` - بازطراحی مدیریت دسترسی
- `EXTERNAL_API_USER_ACCESS_TODO.md` - TODO دسترسی کاربران
- `response-network/admin-panel/components/request-types/manage-access-dialog.tsx` - الگوی مرجع

---

## 🎉 پایان

سیستم External API حالا کامل است:
- ✅ مدیریت API ها
- ✅ دسترسی Profile Type
- ✅ دسترسی کاربران
- ✅ Export/Import
- ✅ Access Control
- ✅ UI یکپارچه

همه چیز آماده استفاده است!
