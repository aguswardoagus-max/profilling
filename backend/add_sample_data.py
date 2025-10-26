#!/usr/bin/env python3
"""
Script untuk menambahkan data sample ke database untuk testing dashboard
"""

import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime, timedelta
import random

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'clearance_facesearch')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def add_sample_profiling_data():
    """Add sample profiling data"""
    try:
        connection = get_db_connection()
        if not connection:
            print("Failed to connect to database")
            return False
        
        cursor = connection.cursor()
        
        # Get user IDs
        cursor.execute("SELECT id FROM users LIMIT 3")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            print("No users found in database")
            return False
        
        # Add sample profiling data
        search_types = ['identity', 'phone', 'face']
        sample_data = []
        
        # Generate data for last 7 days
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            for j in range(random.randint(5, 20)):  # 5-20 searches per day
                sample_data.append((
                    random.choice(user_ids),
                    random.choice(search_types),
                    f'{{"param": "sample_{j}"}}',
                    f'{{"result": "sample_result_{j}"}}',
                    f'{{"person": "sample_person_{j}"}}',
                    f'{{"family": "sample_family_{j}"}}',
                    f'{{"phone": "sample_phone_{j}"}}',
                    f'{{"face": "sample_face_{j}"}}',
                    date,
                    '127.0.0.1',
                    'Sample User Agent'
                ))
        
        # Insert sample data
        insert_query = '''
            INSERT INTO profiling_data 
            (user_id, search_type, search_params, search_results, person_data, 
             family_data, phone_data, face_data, search_timestamp, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        cursor.executemany(insert_query, sample_data)
        connection.commit()
        
        print(f"Added {len(sample_data)} profiling data records")
        return True
        
    except Error as e:
        print(f"Error adding sample profiling data: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def add_sample_cek_plat_data():
    """Add sample cek plat data"""
    try:
        connection = get_db_connection()
        if not connection:
            print("Failed to connect to database")
            return False
        
        cursor = connection.cursor()
        
        # Get user IDs
        cursor.execute("SELECT id FROM users LIMIT 3")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            print("No users found in database")
            return False
        
        # Add sample cek plat data
        regions = ['BH', 'BB', 'BG', 'BL', 'BM', 'BN', 'BP']
        sample_data = []
        
        for i in range(50):  # 50 sample records
            region = random.choice(regions)
            no_polisi = f"{region} {random.randint(1000, 9999)} {chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"
            
            sample_data.append((
                random.choice(user_ids),
                no_polisi,
                f'Sample Owner {i}',
                f'Sample Address {i}',
                random.choice(['Toyota', 'Honda', 'Suzuki', 'Daihatsu', 'Mitsubishi']),
                random.choice(['Sedan', 'Hatchback', 'SUV', 'MPV', 'Pickup']),
                f'Model {i}',
                random.randint(2010, 2023),
                random.choice(['Hitam', 'Putih', 'Merah', 'Biru', 'Silver']),
                f'RANGKA{i:06d}',
                f'MESIN{i:06d}',
                f'{random.randint(1000, 2000)}cc',
                random.choice(['Bensin', 'Solar']),
                datetime.now() + timedelta(days=random.randint(30, 365)),
                datetime.now() + timedelta(days=random.randint(30, 365)),
                'Aktif',
                round(random.uniform(-6.2, -6.1), 6),
                round(random.uniform(106.8, 106.9), 6),
                round(random.uniform(80, 100), 2),
                f'{{"accuracy": "high"}}',
                f'Sample Location {i}',
                datetime.now() - timedelta(days=random.randint(0, 30)),
                '127.0.0.1',
                'Sample User Agent'
            ))
        
        # Insert sample data
        insert_query = '''
            INSERT INTO cek_plat_data 
            (user_id, no_polisi, nama_pemilik, alamat, merk_kendaraan, type_kendaraan,
             model_kendaraan, tahun_pembuatan, warna_kendaraan, no_rangka, no_mesin,
             silinder, bahan_bakar, masa_berlaku_stnk, masa_berlaku_pajak, status_kendaraan,
             coordinates_lat, coordinates_lon, accuracy_score, accuracy_details, display_name,
             search_timestamp, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        cursor.executemany(insert_query, sample_data)
        connection.commit()
        
        print(f"Added {len(sample_data)} cek plat data records")
        return True
        
    except Error as e:
        print(f"Error adding sample cek plat data: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def add_sample_user_activities():
    """Add sample user activities"""
    try:
        connection = get_db_connection()
        if not connection:
            print("Failed to connect to database")
            return False
        
        cursor = connection.cursor()
        
        # Get user IDs
        cursor.execute("SELECT id FROM users LIMIT 3")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            print("No users found in database")
            return False
        
        # Add sample user activities
        activities = [
            ('login', 'User logged in successfully'),
            ('search', 'Face search completed for NIK 1505041107830002'),
            ('search', 'Identity search completed'),
            ('search', 'Phone number search completed'),
            ('logout', 'User logged out'),
            ('error', 'Search failed - invalid parameters'),
            ('search', 'License plate search completed'),
            ('login', 'New user session started')
        ]
        
        sample_data = []
        for i in range(20):  # 20 sample activities
            activity = random.choice(activities)
            sample_data.append((
                random.choice(user_ids),
                activity[0],
                activity[1],
                '127.0.0.1',
                'Sample User Agent',
                datetime.now() - timedelta(hours=random.randint(0, 72))
            ))
        
        # Insert sample data
        insert_query = '''
            INSERT INTO user_activities 
            (user_id, activity_type, description, ip_address, user_agent, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        
        cursor.executemany(insert_query, sample_data)
        connection.commit()
        
        print(f"Added {len(sample_data)} user activity records")
        return True
        
    except Error as e:
        print(f"Error adding sample user activities: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def main():
    """Main function"""
    print("Adding sample data to database...")
    
    print("\n=== Adding Sample Profiling Data ===")
    add_sample_profiling_data()
    
    print("\n=== Adding Sample Cek Plat Data ===")
    add_sample_cek_plat_data()
    
    print("\n=== Adding Sample User Activities ===")
    add_sample_user_activities()
    
    print("\n=== Sample data added successfully! ===")
    print("You can now test the dashboard with real data.")

if __name__ == "__main__":
    main()
