#!/usr/bin/env python3
"""
Script untuk menambahkan data sample profiling ke database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from datetime import datetime

def add_sample_profiling_data():
    """Add sample profiling data to database"""
    
    # Sample data berdasarkan contoh yang diberikan
    sample_data = [
        {
            'nama': 'BUDIMAN SUTRISNO',
            'nik': '1501011234567890',
            'ttl': 'Tanjab Timur, 15 Januari 1975',
            'jk': 'L',
            'alamat': 'Jl. Sawit Indah No. 45, Desa Sawit Makmur, Kec. Muara Sabak, Kab. Tanjab Timur',
            'kel': 'Sawit Makmur',
            'kec': 'Muara Sabak',
            'kab_kota': 'Tanjung Jabung Timur',
            'prov': 'Jambi',
            'hp': '081234567890',
            'nama_ayah': 'Sutrisno',
            'nama_ibu': 'Siti Aminah',
            'nama_istri': 'Rahayu',
            'anak': '1) Ahmad (15 tahun); 2) Sari (12 tahun)',
            'pekerjaan': 'Manager Perkebunan',
            'jabatan': 'Manager Operasional PT. Mitra Prima Gitabadi',
            'foto_url': '/static/clean_photos/1501011234567890.jpg',
            'kategori': 'Perkebunan',
            'subkategori': 'Sawit Ilegal',
            'hasil_pendalaman': 'Berdasarkan hasil penyelidikan mendalam, ditemukan berbagai indikasi keterlibatan dalam operasi perkebunan sawit ilegal.',
            'target_prioritas': 'Berdasarkan hasil penyelidikan, Budiman Sutrisno merupakan salah satu aktor kunci dalam operasi perkebunan sawit ilegal PT. Mitra Prima Gitabadi. Memiliki peran penting dalam koordinasi operasi harian dan pengelolaan tenaga kerja.',
            'simpul_pengolahan': 'Bekerja sama dengan beberapa pihak terkait dalam proses pengolahan hasil perkebunan sawit ilegal, termasuk koordinasi dengan supplier dan distributor hasil panen.',
            'aktor_pendukung': 'Memiliki jaringan dengan beberapa pemilik lahan lokal dan tenaga kerja yang terlibat dalam operasi perkebunan. Juga berkoordinasi dengan pihak-pihak terkait transportasi hasil panen.',
            'jaringan_lokal': 'Memiliki hubungan erat dengan masyarakat lokal di sekitar lokasi perkebunan, termasuk beberapa tokoh masyarakat yang mendukung operasi tersebut.',
            'koordinasi': 'Melakukan koordinasi rutin dengan manajemen PT. Mitra Prima Gitabadi dan pihak-pihak terkait dalam operasi perkebunan sawit ilegal.',
            'status_verifikasi': 'verified'
        },
        {
            'nama': 'SITI RAHAYU',
            'nik': '1501011234567891',
            'ttl': 'Tanjab Timur, 20 Maret 1980',
            'jk': 'P',
            'alamat': 'Jl. Sawit Indah No. 45, Desa Sawit Makmur, Kec. Muara Sabak, Kab. Tanjab Timur',
            'kel': 'Sawit Makmur',
            'kec': 'Muara Sabak',
            'kab_kota': 'Tanjung Jabung Timur',
            'prov': 'Jambi',
            'hp': '081234567891',
            'nama_ayah': 'Ahmad',
            'nama_ibu': 'Fatimah',
            'nama_istri': None,
            'anak': '1) Ahmad (15 tahun); 2) Sari (12 tahun)',
            'pekerjaan': 'Ibu Rumah Tangga',
            'jabatan': None,
            'foto_url': '/static/clean_photos/1501011234567891.jpg',
            'kategori': 'Perkebunan',
            'subkategori': 'Keluarga Aktor',
            'hasil_pendalaman': 'Istri dari Budiman Sutrisno yang terlibat dalam operasi perkebunan sawit ilegal.',
            'target_prioritas': 'Sebagai istri dari aktor kunci, Siti Rahayu memiliki pengetahuan tentang operasi perkebunan sawit ilegal yang dilakukan suaminya.',
            'simpul_pengolahan': 'Membantu dalam pengelolaan keuangan dan administrasi operasi perkebunan.',
            'aktor_pendukung': 'Memiliki akses ke informasi operasional dan jaringan keluarga yang terlibat.',
            'jaringan_lokal': 'Aktif dalam kegiatan masyarakat dan memiliki hubungan dengan tokoh-tokoh lokal.',
            'koordinasi': 'Berkoordinasi dengan suami dalam berbagai aspek operasi perkebunan.',
            'status_verifikasi': 'draft'
        },
        {
            'nama': 'AHMAD SUTRISNO',
            'nik': '1501011234567892',
            'ttl': 'Tanjab Timur, 10 Juni 2008',
            'jk': 'L',
            'alamat': 'Jl. Sawit Indah No. 45, Desa Sawit Makmur, Kec. Muara Sabak, Kab. Tanjab Timur',
            'kel': 'Sawit Makmur',
            'kec': 'Muara Sabak',
            'kab_kota': 'Tanjung Jabung Timur',
            'prov': 'Jambi',
            'hp': '081234567892',
            'nama_ayah': 'Budiman Sutrisno',
            'nama_ibu': 'Siti Rahayu',
            'nama_istri': None,
            'anak': None,
            'pekerjaan': 'Pelajar',
            'jabatan': None,
            'foto_url': '/static/clean_photos/1501011234567892.jpg',
            'kategori': 'Perkebunan',
            'subkategori': 'Keluarga Aktor',
            'hasil_pendalaman': 'Anak dari Budiman Sutrisno yang tinggal di lokasi operasi perkebunan sawit ilegal.',
            'target_prioritas': 'Sebagai anak dari aktor kunci, Ahmad memiliki potensi untuk terlibat dalam operasi perkebunan di masa depan.',
            'simpul_pengolahan': 'Belum terlibat langsung dalam operasi, namun memiliki akses ke informasi keluarga.',
            'aktor_pendukung': 'Memiliki hubungan dengan jaringan keluarga yang terlibat dalam operasi.',
            'jaringan_lokal': 'Aktif dalam kegiatan sekolah dan memiliki teman-teman di lingkungan perkebunan.',
            'koordinasi': 'Berkoordinasi dengan orang tua dalam kegiatan sehari-hari.',
            'status_verifikasi': 'draft'
        },
        {
            'nama': 'HARTO WIJAYA',
            'nik': '1501011234567893',
            'ttl': 'Tanjab Timur, 5 September 1970',
            'jk': 'L',
            'alamat': 'Jl. Perkebunan No. 12, Desa Sawit Makmur, Kec. Muara Sabak, Kab. Tanjab Timur',
            'kel': 'Sawit Makmur',
            'kec': 'Muara Sabak',
            'kab_kota': 'Tanjung Jabung Timur',
            'prov': 'Jambi',
            'hp': '081234567893',
            'nama_ayah': 'Wijaya',
            'nama_ibu': 'Sari',
            'nama_istri': 'Dewi',
            'anak': '1) Rudi (20 tahun); 2) Lisa (18 tahun)',
            'pekerjaan': 'Pemilik Lahan',
            'jabatan': 'Pemilik Lahan Sawit',
            'foto_url': '/static/clean_photos/1501011234567893.jpg',
            'kategori': 'Perkebunan',
            'subkategori': 'Pemilik Lahan',
            'hasil_pendalaman': 'Pemilik lahan yang menyewakan tanahnya untuk operasi perkebunan sawit ilegal.',
            'target_prioritas': 'Hartono Wijaya merupakan pemilik lahan yang menyewakan tanahnya kepada PT. Mitra Prima Gitabadi untuk operasi perkebunan sawit ilegal.',
            'simpul_pengolahan': 'Menyediakan lahan untuk operasi perkebunan dan menerima pembayaran sewa dari perusahaan.',
            'aktor_pendukung': 'Memiliki jaringan dengan pemilik lahan lain dan tenaga kerja lokal.',
            'jaringan_lokal': 'Tokoh masyarakat yang memiliki pengaruh di desa Sawit Makmur.',
            'koordinasi': 'Berkoordinasi dengan manajemen PT. Mitra Prima Gitabadi dalam hal sewa lahan.',
            'status_verifikasi': 'verified'
        },
        {
            'nama': 'BAMBANG SUTRISNO',
            'nik': '1501011234567894',
            'ttl': 'Tanjab Timur, 12 Desember 1972',
            'jk': 'L',
            'alamat': 'Jl. Sawit Indah No. 45, Desa Sawit Makmur, Kec. Muara Sabak, Kab. Tanjab Timur',
            'kel': 'Sawit Makmur',
            'kec': 'Muara Sabak',
            'kab_kota': 'Tanjung Jabung Timur',
            'prov': 'Jambi',
            'hp': '081234567894',
            'nama_ayah': 'Sutrisno',
            'nama_ibu': 'Siti Aminah',
            'nama_istri': 'Rina',
            'anak': '1) Dedi (16 tahun); 2) Maya (14 tahun)',
            'pekerjaan': 'Tenaga Kerja',
            'jabatan': 'Mandor Perkebunan',
            'foto_url': '/static/clean_photos/1501011234567894.jpg',
            'kategori': 'Perkebunan',
            'subkategori': 'Tenaga Kerja',
            'hasil_pendalaman': 'Saudara kandung Budiman Sutrisno yang bekerja sebagai mandor di perkebunan sawit ilegal.',
            'target_prioritas': 'Bambang Sutrisno merupakan saudara kandung dari Budiman Sutrisno dan bekerja sebagai mandor di perkebunan sawit ilegal PT. Mitra Prima Gitabadi.',
            'simpul_pengolahan': 'Mengawasi tenaga kerja dan memastikan operasi perkebunan berjalan lancar.',
            'aktor_pendukung': 'Memiliki akses ke informasi operasional dan jaringan tenaga kerja.',
            'jaringan_lokal': 'Memiliki hubungan dengan tenaga kerja lokal dan masyarakat sekitar.',
            'koordinasi': 'Berkoordinasi dengan Budiman Sutrisno dalam operasi perkebunan.',
            'status_verifikasi': 'verified'
        }
    ]
    
    # Get admin user ID (assuming admin user exists)
    admin_user = db.get_user_by_username('admin')
    if not admin_user:
        print("Admin user not found. Please create admin user first.")
        return False
    
    user_id = admin_user['id']
    
    print(f"Adding {len(sample_data)} sample profiling records...")
    
    success_count = 0
    for data in sample_data:
        try:
            success = db.save_profiling_report(
                user_id=user_id,
                nama=data['nama'],
                nik=data['nik'],
                ttl=data['ttl'],
                jk=data['jk'],
                alamat=data['alamat'],
                kel=data['kel'],
                kec=data['kec'],
                kab_kota=data['kab_kota'],
                prov=data['prov'],
                hp=data['hp'],
                nama_ayah=data['nama_ayah'],
                nama_ibu=data['nama_ibu'],
                nama_istri=data['nama_istri'],
                anak=data['anak'],
                pekerjaan=data['pekerjaan'],
                jabatan=data['jabatan'],
                foto_url=data['foto_url'],
                kategori=data['kategori'],
                subkategori=data['subkategori'],
                hasil_pendalaman=data['hasil_pendalaman'],
                target_prioritas=data['target_prioritas'],
                simpul_pengolahan=data['simpul_pengolahan'],
                aktor_pendukung=data['aktor_pendukung'],
                jaringan_lokal=data['jaringan_lokal'],
                koordinasi=data['koordinasi'],
                status_verifikasi=data['status_verifikasi']
            )
            
            if success:
                success_count += 1
                print(f"[OK] Added: {data['nama']}")
            else:
                print(f"[FAIL] Failed to add: {data['nama']}")
                
        except Exception as e:
            print(f"[ERROR] Error adding {data['nama']}: {e}")
    
    print(f"\nCompleted! Successfully added {success_count}/{len(sample_data)} records.")
    return success_count > 0

if __name__ == "__main__":
    add_sample_profiling_data()
