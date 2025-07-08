# SQL to Laravel Migration & Seeder Generator

Aplikasi Python yang mengkonversi file SQL (CREATE TABLE dan INSERT INTO) menjadi file Migration dan Seeder Laravel secara otomatis.

## 🚀 Fitur

- **Parsing CREATE TABLE**: Mengkonversi struktur tabel SQL menjadi Laravel migration
- **Parsing INSERT INTO**: Mengkonversi data SQL menjadi Laravel seeder
- **Mapping Tipe Data**: Otomatis memetakan tipe data SQL ke method Laravel migration
- **Template Customizable**: Menggunakan template PHP yang dapat disesuaikan
- **Selective Generation**: Pilih tabel mana yang ingin digenerate
- **Flexible Output**: Generate migration saja, seeder saja, atau keduanya

## 📋 Instalasi

1. Clone atau download repository ini
2. Pastikan Python 3.x sudah terinstall
3. Siapkan file SQL yang ingin dikonversi
4. Pastikan folder `templates/` berisi file template yang diperlukan

## 📁 Struktur File

```
├── app.py                      # Main application
├── templates/
│   ├── migration_template.php  # Template untuk migration
│   └── seeder_template.php     # Template untuk seeder
└── README.md
```

## 🛠️ Penggunaan

### Sintaks Dasar

```bash
python app.py <path_to_sql_file> <destination_folder>
```

### Contoh Penggunaan

```bash
python app.py database.sql ./output
```

### Proses Interaktif

Setelah menjalankan perintah, aplikasi akan:

1. Menampilkan daftar tabel yang ditemukan
2. Meminta input nomor tabel yang ingin digenerate (atau 'all' untuk semua)
3. Meminta pilihan generate migration, seeder, atau keduanya

### Contoh Interaksi

```
Tables found:
1. users
2. products
3. orders

Enter comma separated table numbers to generate migration/seeder for (or 'all'): 1,2
Generate migration, seeder, or both? (migration/seeder/both): both
```

## 🔄 Mapping Tipe Data

Aplikasi otomatis memetakan tipe data SQL ke method Laravel migration:

| SQL Type | Laravel Method |
|----------|----------------|
| INT (dengan AUTO_INCREMENT) | `increments()` |
| BIGINT (dengan AUTO_INCREMENT) | `bigIncrements()` |
| INT/INTEGER | `integer()` |
| BIGINT | `bigInteger()` |
| VARCHAR/CHAR | `string()` |
| TEXT | `text()` |
| DATE | `date()` |
| TIMESTAMP/DATETIME | `timestamp()` |
| BOOLEAN/TINYINT(1) | `boolean()` |
| FLOAT/DOUBLE/DECIMAL | `float()` |

## ⚡ Fitur Tambahan

- **Nullable Fields**: Otomatis mendeteksi kolom yang bisa NULL
- **Default Values**: Mengkonversi nilai default dari SQL
- **Primary Key**: Mendeteksi dan menghandle primary key
- **Auto Increment**: Mengkonversi AUTO_INCREMENT ke increments()
- **Timestamps**: Menggunakan timestamp dengan format Laravel

## 📄 Output

### Migration Files
```
output/migrations/2024_01_15_120000_create_users_table.php
```

### Seeder Files
```
output/seeders/2024_01_15_120000_seed_users.php
```

## 🎨 Template Customization

Anda dapat memodifikasi template di folder `templates/`:

### Migration Template (`migration_template.php`)
```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class {CLASS_NAME} extends Migration
{
    public function up()
    {
        Schema::create('{TABLE_NAME}', function (Blueprint $table) {
            {COLUMNS}
        });
    }

    public function down()
    {
        Schema::dropIfExists('{TABLE_NAME}');
    }
}
```

### Seeder Template (`seeder_template.php`)
```php
<?php

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class {CLASS_NAME} extends Seeder
{
    public function run()
    {
        DB::table('{TABLE_NAME}')->insert([
{SEED_DATA}
        ]);
    }
}
```

## 🏷️ Placeholder Template

Template menggunakan placeholder berikut:

- `{CLASS_NAME}`: Nama class dalam PascalCase
- `{TABLE_NAME}`: Nama tabel
- `{COLUMNS}`: Definisi kolom untuk migration
- `{SEED_DATA}`: Data array untuk seeder

## 📝 Contoh Input SQL

```sql
CREATE TABLE `users` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `name` varchar(255) NOT NULL,
    `email` varchar(255) NOT NULL,
    `email_verified_at` timestamp NULL DEFAULT NULL,
    `password` varchar(255) NOT NULL,
    `created_at` timestamp NULL DEFAULT NULL,
    `updated_at` timestamp NULL DEFAULT NULL,
    PRIMARY KEY (`id`)
);

INSERT INTO `users` (`id`, `name`, `email`, `password`) VALUES
(1, 'John Doe', 'john@example.com', '$2y$10$...'),
(2, 'Jane Smith', 'jane@example.com', '$2y$10$...');
```

## 📤 Contoh Output

### Migration
```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateUsersTable extends Migration
{
    public function up()
    {
        Schema::create('users', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->string('name');
            $table->string('email');
            $table->timestamp('email_verified_at')->nullable();
            $table->string('password');
            $table->timestamp('created_at')->nullable();
            $table->timestamp('updated_at')->nullable();
        });
    }

    public function down()
    {
        Schema::dropIfExists('users');
    }
}
```

### Seeder
```php
<?php

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class UsersSeeder extends Seeder
{
    public function run()
    {
        DB::table('users')->insert([
            ['id' => 1, 'name' => 'John Doe', 'email' => 'john@example.com', 'password' => '$2y$10$...'],
            ['id' => 2, 'name' => 'Jane Smith', 'email' => 'jane@example.com', 'password' => '$2y$10$...'],
        ]);
    }
}
```

## 📋 Persyaratan

- Python 3.x
- File SQL dengan format CREATE TABLE dan INSERT INTO standar
- Template file di folder `templates/`

## 📌 Catatan

- Aplikasi ini mendukung encoding UTF-8
- Pastikan file SQL memiliki sintaks yang valid
- Seeder hanya akan dibuat jika ada data INSERT INTO untuk tabel tersebut
- Nama file output menggunakan timestamp untuk menghindari konflik

## 🤝 Kontribusi

Silakan buat pull request atau laporkan bug melalui issues. Kontribusi dalam bentuk:

- Perbaikan bug
- Penambahan fitur
- Peningkatan dokumentasi
- Optimasi kode

## 📜 Lisensi

Aplikasi ini bebas digunakan dan dimodifikasi sesuai kebutuhan.