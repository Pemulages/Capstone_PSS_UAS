# UAS Capstone Project - Pemrograman Sisi Server

**Nama:** ABDURRAZZAQ ILHAM AZIZ  
**NIM:** A11.2022.14301  
**Kelas:** A11.4601  
**Mata Kuliah:** Pemrograman Sisi Server

---

## Langkah Menjalankan Project

### 1. Clone Repository

Clone repository ke komputer Anda:
```bash
git clone https://github.com/Pemulages/Capstone_PSS_UAS.git
cd CAPSTONE_PSS_UAS
```

### 2. Build dan Jalankan Docker

Jalankan perintah berikut untuk membangun dan menjalankan semua service:
```bash
docker compose up --build
```

### 3. Masuk ke Container Django

Buka terminal di container Django.  
Cara 1: Klik kanan pada container bernama `prepare_lms` di Docker extension, lalu pilih **Attach Shell**  
Cara 2: Jalankan perintah berikut:
```bash
docker exec -it prepare_lms bash
```

### 4. Migrasi Database

Di dalam container, jalankan:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Buat Superuser

Masih di dalam container, buat akun admin:
```bash
python manage.py createsuperuser
```
Isi username, email, dan password sesuai keinginan.

### 6. Import Data Awal

Masih di dalam container, jalankan:
```bash
python importer2.py
```

---

## Cara Mengakses Aplikasi

- Buka browser dan akses:  
  [http://localhost:8001](http://localhost:8001)
- Untuk halaman admin:  
  [http://localhost:8001/admin](http://localhost:8001/admin)

---

## Catatan

- Pastikan Docker sudah terinstall dan berjalan.
- File `importer2.py` digunakan untuk mengisi data awal ke database.
