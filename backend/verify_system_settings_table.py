#!/usr/bin/env python3
"""
Script untuk memverifikasi apakah tabel system_settings sudah ada di database
"""

import sys
import os
from database import db

def verify_table():
    """Verifikasi apakah tabel system_settings ada dan bisa digunakan"""
    print("=" * 60)
    print("VERIFYING system_settings TABLE")
    print("=" * 60)
    
    try:
        # Test connection
        conn = db.get_connection()
        if not conn:
            print("❌ Cannot connect to database")
            return False
        
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'system_settings'
        """)
        
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            print("✅ Table 'system_settings' exists")
            
            # Check table structure
            cursor.execute("DESCRIBE system_settings")
            columns = cursor.fetchall()
            print(f"\n📋 Table structure ({len(columns)} columns):")
            for col in columns:
                print(f"   - {col[0]} ({col[1]})")
            
            # Test read/write
            print("\n🧪 Testing read/write operations...")
            
            # Test write
            test_key = "test_verification_key"
            test_value = "test_value_123"
            success = db.update_setting(test_key, test_value, "Test setting for verification")
            
            if success:
                print("✅ Write operation: SUCCESS")
            else:
                print("❌ Write operation: FAILED")
                return False
            
            # Test read
            retrieved_value = db.get_setting(test_key)
            if retrieved_value == test_value:
                print("✅ Read operation: SUCCESS")
            else:
                print(f"❌ Read operation: FAILED (expected '{test_value}', got '{retrieved_value}')")
                return False
            
            # Cleanup test data
            cursor.execute("DELETE FROM system_settings WHERE setting_key = %s", (test_key,))
            conn.commit()
            print("✅ Cleanup: Test data removed")
            
            # Check if GOOGLE_CSE_API_KEY exists
            api_key = db.get_setting('GOOGLE_CSE_API_KEY')
            if api_key:
                masked = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
                print(f"\n🔑 GOOGLE_CSE_API_KEY found: {masked}")
            else:
                print("\n⚠️  GOOGLE_CSE_API_KEY not found in database")
                print("   You can add it via the Settings page in the web interface")
            
            print("\n" + "=" * 60)
            print("✅ VERIFICATION COMPLETE - Table is working correctly!")
            print("=" * 60)
            return True
        else:
            print("❌ Table 'system_settings' does NOT exist")
            print("\n💡 Solution:")
            print("   1. Run the application once (it will create the table automatically)")
            print("   2. Or run: python setup_database.py")
            print("   3. Or run: python setup_db_simple.py")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    success = verify_table()
    sys.exit(0 if success else 1)

