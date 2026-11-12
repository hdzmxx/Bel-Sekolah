# Bel Sekolah Otomatis

Aplikasi desktop untuk membunyikan bel sekolah secara otomatis sesuai jadwal.
Ditulis dengan Python + Tkinter, tanpa perlu memasang paket tambahan di Windows.

**By HDZMXX**

## Fitur

- Jadwal bel per hari: Senin–Minggu, atau gabungan **Senin–Kamis**, **Senin–Jumat**, **Senin–Sabtu**.
- Beberapa kategori jadwal (mis. *Reguler*, *Ujian*) yang bisa dipindah dengan satu klik.
- Halaman Jadwal otomatis menampilkan **hari yang sedang berjalan** (bisa diganti lewat filter).
- Nada bawaan (Ding-dong, Bel panjang) atau file **mp3/wav** sendiri.
- Tambah jadwal beruntun dengan opsi *Buat lagi setelah simpan* dan *Pertahankan data yang diisi*.
- Beranda berisi jam besar, hitung mundur bel berikutnya, dan daftar jadwal hari ini.
- Pengaturan nama sekolah, alamat, volume, dan jalan otomatis saat Windows menyala.
- **Ekspor / Impor** jadwal beserta file nada dalam satu berkas `.zip` (mode *Ganti* atau *Gabung*),
  sehingga mudah dipindah ke komputer lain.
- Mode portabel: data disimpan di folder `data/` dan `nada/` di sebelah aplikasi.

## Menjalankan

Butuh Python 3.8 atau lebih baru (Tkinter sudah termasuk di Python untuk Windows).

```
python bel_sekolah.py
```

Di Linux/macOS pasang dulu `pygame` untuk suara dan Tkinter bila belum ada:

```
pip install -r requirements.txt
```

## Membuat .exe (Windows)

Jalankan `build.bat`, atau manual:

```
pip install pyinstaller==5.13.2
pyinstaller --noconsole --onefile --name BelSekolah bel_sekolah.py
```

Hasilnya ada di `dist/BelSekolah.exe`. Simpan di folder tetap (mis. `C:\BelSekolah`);
folder `data` dan `nada` akan dibuat di sebelahnya.

### Windows 7

Python 3.9 ke atas tidak mendukung Windows 7, jadi buat .exe dengan **Python 3.8.10**
(pilih 32-bit agar jalan di Windows 7 32-bit maupun 64-bit). Jika .exe gagal dibuka di Windows 7:

| Pesan error | Penyebab / solusi |
|---|---|
| `api-ms-win-crt-runtime-l1-1-0.dll is missing` | Pasang Service Pack 1, lalu update **KB4474419** dan **KB2999226** (Universal C Runtime). |
| `Error loading Python DLL ... python38.dll` | Runtime Windows belum lengkap (lihat di atas) atau bit-ness tidak cocok (exe 64-bit di Windows 32-bit). |
| `DLL load failed while importing _tkinter` | Pasang update **KB2533623**. |

Visual C++ Redistributable terbaru tidak bisa dipasang di Windows 7; gunakan update di atas.

## Data dan pencadangan

| Lokasi | Isi |
|---|---|
| `data/config.json` | Jadwal, kategori, nama sekolah, volume |
| `nada/` | File nada yang dipakai jadwal |

Gunakan menu **Berkas → Ekspor database dan nada…** secara berkala untuk membuat cadangan,
dan **Impor** untuk memulihkannya di komputer yang sama atau berbeda.

## Catatan

- Aplikasi harus tetap terbuka (boleh diminimalkan) agar bel berbunyi.
- Saat bel aktif, aplikasi mencegah komputer masuk mode tidur.

## Lisensi

[MIT](LICENSE) © 2026 HDZMXX
