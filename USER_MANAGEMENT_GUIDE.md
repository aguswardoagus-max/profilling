# User Management CRUD Guide

## 🎯 Overview
User Management system menyediakan operasi CRUD (Create, Read, Update, Delete) lengkap untuk mengelola users di database MySQL.

## 🚀 Akses User Management
```
URL: http://127.0.0.1:5000/user-management
Login: admin / admin123
```

## 📋 Fungsi CRUD yang Tersedia

### 1. CREATE (Add User)
**Fungsi**: Menambahkan user baru ke database

**Cara Menggunakan**:
1. Klik tombol "Add User" (tombol biru dengan icon +)
2. Isi form dengan data:
   - **Username**: Nama pengguna (unique)
   - **Full Name**: Nama lengkap
   - **Email**: Alamat email (unique)
   - **Role**: Pilih role (admin, user, viewer)
   - **Status**: Pilih status (active, inactive, pending)
   - **Password**: Password untuk login
3. Klik "Save User"

**Validasi**:
- Semua field wajib diisi
- Username dan email harus unique
- Password minimal 6 karakter

**API Endpoint**: `POST /api/users`

### 2. READ (View Users)
**Fungsi**: Melihat daftar semua users dari database

**Cara Menggunakan**:
1. Halaman otomatis menampilkan semua users saat dibuka
2. Gunakan search box untuk mencari user
3. Gunakan filter untuk memfilter berdasarkan:
   - Status (All, Active, Inactive, Pending)
   - Role (All, Admin, User, Viewer)

**Fitur**:
- Tabel responsive dengan informasi lengkap
- Avatar dengan initial nama
- Role badges dengan color coding
- Status indicators
- Last login dan created date

**API Endpoint**: `GET /api/users`

### 3. UPDATE (Edit User)
**Fungsi**: Mengedit data user yang sudah ada

**Cara Menggunakan**:
1. Klik tombol edit (icon pensil) pada user yang ingin diedit
2. Form akan terisi dengan data existing
3. Ubah field yang diperlukan:
   - Username, Full Name, Email, Role, Status
   - Password (opsional - kosongkan untuk keep current password)
4. Klik "Save User"

**Validasi**:
- Username dan email harus unique (kecuali untuk user yang sama)
- Password opsional untuk edit

**API Endpoint**: `PUT /api/users/{id}`

### 4. DELETE (Delete User)
**Fungsi**: Menghapus user dari database

**Cara Menggunakan**:
1. Klik tombol delete (icon trash) pada user yang ingin dihapus
2. Konfirmasi di dialog yang muncul
3. User akan dihapus permanen dari database

**Catatan**:
- Delete bersifat hard delete (permanen)
- Semua data terkait (sessions, activities) juga dihapus
- Tidak bisa di-undo

**API Endpoint**: `DELETE /api/users/{id}`

## 🔧 Technical Details

### Database Schema
```sql
users table:
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- username (VARCHAR(50), UNIQUE)
- email (VARCHAR(100), UNIQUE)
- password_hash (VARCHAR(255))
- full_name (VARCHAR(100))
- role (ENUM: admin, user, viewer)
- status (ENUM: active, inactive, pending)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- last_login (TIMESTAMP)
```

### API Request/Response Examples

#### CREATE User
```json
POST /api/users
{
  "username": "new.user",
  "email": "new.user@example.com",
  "password": "password123",
  "full_name": "New User",
  "role": "user",
  "status": "active"
}

Response:
{
  "success": true,
  "message": "User created successfully"
}
```

#### READ Users
```json
GET /api/users

Response:
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "System Administrator",
      "role": "admin",
      "status": "active",
      "created_at": "2025-10-21T15:33:51",
      "last_login": "2025-10-21T15:34:12"
    }
  ]
}
```

#### UPDATE User
```json
PUT /api/users/1
{
  "full_name": "Updated Name",
  "role": "user",
  "status": "inactive"
}

Response:
{
  "success": true,
  "message": "User updated successfully"
}
```

#### DELETE User
```json
DELETE /api/users/1

Response:
{
  "success": true,
  "message": "User deleted successfully"
}
```

## 🎨 UI/UX Features

### Form Validation
- Real-time validation
- Error messages dengan toast notifications
- Required field indicators
- Email format validation

### Responsive Design
- Mobile-friendly table dengan horizontal scroll
- Collapsible sidebar
- Touch-friendly buttons

### User Experience
- Loading indicators
- Success/error notifications
- Confirmation dialogs untuk delete
- Auto-refresh setelah operasi

## 🔐 Security Features

### Authentication
- Session-based authentication
- Bearer token untuk API calls
- Auto-redirect ke login jika tidak authenticated

### Authorization
- Hanya admin yang bisa manage users
- Role-based access control
- Secure password hashing

### Data Protection
- Input sanitization
- SQL injection prevention
- XSS protection

## 📊 Sample Data

Database sudah berisi sample users untuk testing:
- **admin** (admin) - active
- **john.doe** (user) - active
- **jane.smith** (user) - active
- **bob.viewer** (viewer) - active
- **alice.pending** (user) - pending

## 🚨 Troubleshooting

### Common Issues

1. **400 Bad Request saat Create User**
   - Pastikan semua field diisi
   - Username dan email harus unique
   - Password minimal 6 karakter

2. **401 Unauthorized**
   - Pastikan sudah login sebagai admin
   - Session token mungkin expired

3. **User tidak muncul setelah Create**
   - Refresh halaman
   - Cek console untuk error messages

4. **Edit tidak berfungsi**
   - Pastikan form terisi dengan data existing
   - Password bisa dikosongkan untuk keep current

5. **Delete tidak berfungsi**
   - Pastikan konfirmasi dialog di-klik
   - Cek console untuk error messages

### Debug Tips
- Buka Developer Tools (F12)
- Cek Network tab untuk API calls
- Cek Console untuk error messages
- Cek Application tab untuk session data

## 📈 Performance

### Database Optimization
- Indexed columns untuk username dan email
- Efficient queries dengan proper WHERE clauses
- Connection pooling

### Frontend Optimization
- Lazy loading untuk large datasets
- Debounced search
- Efficient DOM updates

## 🔄 Future Enhancements

### Planned Features
- Bulk operations (bulk delete, bulk update)
- User import/export (CSV, Excel)
- Advanced filtering dan sorting
- User activity logs
- Password reset functionality
- User profile pictures

### API Improvements
- Pagination untuk large datasets
- Advanced search dengan multiple criteria
- Audit trail untuk user changes
- Rate limiting untuk API calls

---

**User Management CRUD system sudah siap digunakan dengan semua operasi berfungsi sempurna!** 🎉
