# Role-Based Menu System Guide

## Overview

Sistem ini telah diimplementasikan dengan fitur role-based menu yang mengatur tampilan menu berdasarkan role user. Menu "User Management" dan "Settings" hanya akan terlihat untuk user dengan role "admin".

## User Roles

### 1. Admin Role
- **Username**: admin
- **Password**: admin123
- **Access**: Semua menu (Dashboard, Profiling, Data Profiling, Cek Plat, User Management, AI Features, Reports, Settings)

### 2. User Role
- **Username**: testuser
- **Password**: test123
- **Access**: Menu terbatas (Dashboard, Profiling, Data Profiling, Cek Plat, AI Features, Reports)
- **Hidden Menus**: User Management, Settings

## Implementation Details

### Frontend Implementation

Setiap halaman HTML memiliki fungsi `setMenuVisibility(userRole)` yang:

1. **Mengambil role user** dari localStorage
2. **Menyembunyikan menu admin-only** untuk user dengan role selain 'admin'
3. **Menu yang disembunyikan**:
   - User Management (`/user-management`)
   - Settings (`/settings`)

### Code Structure

```javascript
setMenuVisibility(userRole) {
    // Hide admin-only menus for non-admin users
    const adminOnlyMenus = ['user-management', 'settings'];
    
    adminOnlyMenus.forEach(menuId => {
        const menuElement = document.querySelector(`a[href="/${menuId}"]`);
        if (menuElement) {
            if (userRole === 'admin') {
                menuElement.style.display = 'flex';
            } else {
                menuElement.style.display = 'none';
            }
        }
    });
}
```

### Files Updated

Semua file HTML telah diupdate dengan sistem role-based menu:

1. ✅ `dashboard.html`
2. ✅ `profiling.html`
3. ✅ `data_profiling.html`
4. ✅ `reports.html`
5. ✅ `settings.html`
6. ✅ `user_management.html`
7. ✅ `ai_features.html`
8. ✅ `cekplat.html`
9. ✅ `data_cari_plat.html`

## Testing

### Test Users

1. **Admin User**:
   - Username: `admin`
   - Password: `admin123`
   - Role: `admin`
   - Expected: Semua menu terlihat

2. **Regular User**:
   - Username: `testuser`
   - Password: `test123`
   - Role: `user`
   - Expected: Menu User Management dan Settings disembunyikan

### How to Test

1. **Login sebagai Admin**:
   - Buka `http://127.0.0.1:5000/login`
   - Login dengan `admin` / `admin123`
   - Navigate ke halaman manapun
   - Verify: Semua menu terlihat termasuk User Management dan Settings

2. **Login sebagai User**:
   - Buka `http://127.0.0.1:5000/login`
   - Login dengan `testuser` / `test123`
   - Navigate ke halaman manapun
   - Verify: Menu User Management dan Settings tidak terlihat

## Security Notes

- **Frontend-only protection**: Sistem ini hanya menyembunyikan menu di frontend
- **Backend protection**: Pastikan endpoint `/user-management` dan `/settings` juga memiliki proteksi role di backend
- **Session validation**: Sistem menggunakan session token untuk validasi user

## Future Enhancements

1. **Backend Role Validation**: Tambahkan middleware untuk validasi role di backend
2. **Dynamic Menu Loading**: Load menu dari backend berdasarkan role user
3. **Granular Permissions**: Implementasi permission yang lebih detail per menu item
4. **Role Management**: Interface untuk mengelola role dan permission

## Troubleshooting

### Menu Tidak Tersembunyi
1. Check localStorage untuk `user_data`
2. Verify role user di database
3. Check browser console untuk error JavaScript

### Login Issues
1. Verify user exists di database
2. Check password hash
3. Verify session token generation

### Database Issues
1. Check MySQL connection
2. Verify users table structure
3. Check role enum values

## Database Schema

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'user', 'viewer') NOT NULL DEFAULT 'user',
    status ENUM('active', 'inactive', 'pending') NOT NULL DEFAULT 'active',
    -- other fields...
);
```

## Support

Jika ada masalah dengan sistem role-based menu, check:
1. Browser console untuk error JavaScript
2. Network tab untuk API calls
3. Database untuk user data dan role
4. Session token validity

