import os
import re
import argparse
from datetime import datetime

# Fungsi membaca file SQL
def read_sql_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Mapping tipe SQL ke Laravel migration method (diperluas)
def map_column_type(column_type, column_extra):
    ct = column_type.lower()
    # Tangani ukuran, unsigned, dll
    if 'int' in ct:
        if 'big' in ct:
            base_type = 'bigInteger'
        else:
            base_type = 'integer'
    elif 'varchar' in ct or 'char' in ct:
        base_type = 'string'
    elif 'text' in ct:
        base_type = 'text'
    elif 'date' == ct or ct.startswith('date('):
        base_type = 'date'
    elif 'timestamp' in ct or 'datetime' in ct:
        base_type = 'timestamp'
    elif 'boolean' in ct or ct == 'tinyint(1)':
        base_type = 'boolean'
    elif 'float' in ct or 'double' in ct or 'decimal' in ct:
        base_type = 'float'
    else:
        base_type = 'string'

    # Tangani auto increment
    if 'auto_increment' in column_extra.lower():
        if base_type == 'integer':
            return 'increments'
        elif base_type == 'bigInteger':
            return 'bigIncrements'

    return base_type

# Membuat nama class PascalCase dari nama tabel
def to_pascal_case(name):
    return ''.join(word.capitalize() for word in re.split(r'[_\s]+', name))

# Parsing CREATE TABLE termasuk kolom, tipe, primary key, auto increment
def parse_create_table(sql_content):
    tables = {}

    # Regex capture CREATE TABLE sampai )
    create_table_pattern = re.compile(
        r"CREATE TABLE `(?P<table>\w+)`\s*\((?P<columns>.*?)\)\s*(ENGINE|DEFAULT|CHARSET|;)", 
        re.DOTALL | re.IGNORECASE
    )
    matches = create_table_pattern.finditer(sql_content)

    for m in matches:
        table_name = m.group('table')
        columns_str = m.group('columns')
        columns = []
        primary_keys = []

        # Parsing setiap baris kolom
        lines = [line.strip() for line in columns_str.split(",\n")]

        for line in lines:
            # Cek primary key definisi
            pk_match = re.match(r'PRIMARY KEY\s*\(`(.+?)`\)', line, re.IGNORECASE)
            if pk_match:
                pks = pk_match.group(1).split('`,`')
                primary_keys.extend(pks)
                continue

            # Cek kolom biasa
            col_match = re.match(r'`(\w+)`\s+([^\s]+)(.*)', line)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                col_extra = col_match.group(3).strip()

                col_type_method = map_column_type(col_type, col_extra)
                # Bangun definisi migration Laravel
                if col_type_method in ['increments', 'bigIncrements']:
                    col_line = f"$table->{col_type_method}('{col_name}');"
                else:
                    col_line = f"$table->{col_type_method}('{col_name}')"

                    # Nullable?
                    if 'not null' not in col_extra.lower():
                        col_line += "->nullable()"
                    # Default?
                    default_match = re.search(r'DEFAULT\s+([^\s]+)', col_extra, re.IGNORECASE)
                    if default_match:
                        default_val = default_match.group(1)
                        # Hapus quotes jika ada
                        default_val = default_val.strip("'\"")
                        col_line += f"->default('{default_val}')"
                    col_line += ";"

                columns.append(col_line)

        # Tandai kolom primary key jika tidak auto_increment
        for pk in primary_keys:
            # Jika primary key belum auto_increment maka tambahkan manual
            # Cek apakah kolom pk sudah auto_increment di columns
            found = False
            for i, col_def in enumerate(columns):
                if f"'{pk}'" in col_def and ('increments' in col_def or 'bigIncrements' in col_def):
                    found = True
                    break
            if not found:
                # Tambah index primary key secara manual nanti (di migration Laravel biasanya pakai $table->primary())
                columns.append(f"$table->primary('{pk}');")

        tables[table_name] = columns
    return tables

# Parsing INSERT INTO beserta data untuk seeder
def parse_insert_into(sql_content):
    inserts = {}

    # Regex menangkap INSERT INTO dengan VALUES (bisa multiline)
    insert_pattern = re.compile(
        r"INSERT INTO `(?P<table>\w+)`\s*\((?P<columns>.*?)\)\s*VALUES\s*(?P<values>\(.*?\));",
        re.DOTALL | re.IGNORECASE
    )

    # Untuk menangani multiple insert dalam satu perintah INSERT INTO (misal VALUES (...), (...), ...)
    insert_pattern_multi = re.compile(
        r"INSERT INTO `(?P<table>\w+)`\s*\((?P<columns>.*?)\)\s*VALUES\s*(?P<values>.+?);",
        re.DOTALL | re.IGNORECASE
    )

    # Cari semua INSERT INTO
    for match in insert_pattern_multi.finditer(sql_content):
        table = match.group('table')
        cols_raw = match.group('columns')
        values_raw = match.group('values')

        # Kolom
        columns = [col.strip(' `') for col in cols_raw.split(',')]

        # Split values_raw menjadi beberapa tuple values, bisa ada multiple tuple
        # Contoh values_raw: (1,'a','b'),(2,'c','d'),...
        tuples = []
        buf = ''
        paren_level = 0
        for c in values_raw:
            if c == '(':
                paren_level += 1
            elif c == ')':
                paren_level -= 1
            buf += c
            if paren_level == 0 and buf.strip():
                tuples.append(buf.strip())
                buf = ''

        # Parsing setiap tuple values jadi dict kolom => value
        data_rows = []
        for t in tuples:
            # Hilangkan kurung luar ( )
            inner = t.strip()[1:-1]
            # Pisahkan koma, tapi harus aware dengan quotes
            row_values = parse_sql_values(inner)
            if len(row_values) == len(columns):
                row_dict = dict(zip(columns, row_values))
                data_rows.append(row_dict)

        if table not in inserts:
            inserts[table] = []
        inserts[table].extend(data_rows)

    return inserts

# Parsing values SQL yang aware quotes, escape dan koma dalam string
def parse_sql_values(value_str):
    vals = []
    current = ''
    in_quote = False
    escape = False
    quote_char = ''
    for c in value_str:
        if escape:
            current += c
            escape = False
        elif c == '\\':
            current += c  # Keep backslash for now, can be improved
            escape = True
        elif in_quote:
            current += c
            if c == quote_char:
                in_quote = False
        elif c in ("'", '"'):
            in_quote = True
            quote_char = c
            current += c
        elif c == ',' and not in_quote:
            vals.append(clean_sql_value(current.strip()))
            current = ''
        else:
            current += c
    if current:
        vals.append(clean_sql_value(current.strip()))
    return vals

# Membersihkan value SQL: menghapus tanda kutip jika ada
def clean_sql_value(val):
    if val.lower() == 'null':
        return None
    if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
        return val[1:-1].replace("\\'", "'").replace('\\"', '"')
    return val

# Membaca template eksternal
def read_template(template_path):
    with open(template_path, 'r', encoding='utf-8') as file:
        return file.read()

# Membuat file migration
def create_migration_file(table_name, columns, destination_path, template):
    timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    migration_filename = f"{timestamp}_create_{table_name}_table.php"
    migration_filepath = os.path.join(destination_path, "migrations", migration_filename)

    # Ganti placeholder dengan PascalCase dan snake_case
    class_name = f"Create{to_pascal_case(table_name)}Table"
    columns_str = "\n            ".join(columns)
    migration_content = template.replace("{TABLE_NAME}", table_name)\
                                .replace("{COLUMNS}", columns_str)\
                                .replace("{CLASS_NAME}", class_name)

    os.makedirs(os.path.dirname(migration_filepath), exist_ok=True)
    with open(migration_filepath, 'w', encoding='utf-8') as file:
        file.write(migration_content)

    print(f"[Migration] File created: {migration_filepath}")

# Membuat file seeder
def create_seeder_file(table_name, data_rows, destination_path, template):
    timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    seeder_filename = f"{timestamp}_seed_{table_name}.php"
    seeder_filepath = os.path.join(destination_path, "seeders", seeder_filename)

    class_name = f"{to_pascal_case(table_name)}Seeder"

    # Membuat data seeder berupa array PHP dari data_rows
    seed_data_lines = []
    for row in data_rows:
        pairs = []
        for k, v in row.items():
            if v is None:
                val = 'null'
            elif isinstance(v, str):
                escaped = v.replace("'", "\\'")
                val = f"'{escaped}'"
            else:
                val = str(v)
            pairs.append(f"'{k}' => {val}")
        seed_data_lines.append("                [" + ", ".join(pairs) + "],")
    seed_data_str = "\n".join(seed_data_lines)

    seeder_content = template.replace("{TABLE_NAME}", table_name)\
                             .replace("{CLASS_NAME}", class_name)\
                             .replace("{SEED_DATA}", seed_data_str)

    os.makedirs(os.path.dirname(seeder_filepath), exist_ok=True)
    with open(seeder_filepath, 'w', encoding='utf-8') as file:
        file.write(seeder_content)

    print(f"[Seeder] File created: {seeder_filepath}")

def main():
    parser = argparse.ArgumentParser(description='Generate Laravel Migration and Seeder from SQL file')
    parser.add_argument('sql_file', help='Path to SQL file')
    parser.add_argument('destination', help='Destination folder for generated files')
    args = parser.parse_args()

    # Baca file SQL
    try:
        sql_content = read_sql_file(args.sql_file)
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        return

    # Parse CREATE TABLE
    tables = parse_create_table(sql_content)
    if not tables:
        print("No tables found in SQL file.")
        return

    # Parse INSERT INTO
    inserts = parse_insert_into(sql_content)

    # Baca template migration dan seeder
    try:
        migration_template = read_template('templates/migration_template.php')
        seeder_template = read_template('templates/seeder_template.php')
    except Exception as e:
        print(f"Error reading template files: {e}")
        return

    print("\nTables found:")
    for i, tbl in enumerate(tables.keys(), start=1):
        print(f"{i}. {tbl}")

    # Pilih tabel untuk migrasi
    chosen_tables = input("\nEnter comma separated table numbers to generate migration/seeder for (or 'all'): ").strip()
    if chosen_tables.lower() == 'all':
        selected_tables = list(tables.keys())
    else:
        indices = [int(i) for i in chosen_tables.split(',') if i.strip().isdigit()]
        selected_tables = []
        for i in indices:
            if i >= 1 and i <= len(tables):
                selected_tables.append(list(tables.keys())[i-1])

    # Pilih generate migration, seeder, atau keduanya
    choice = input("Generate migration, seeder, or both? (migration/seeder/both): ").strip().lower()
    if choice not in ['migration', 'seeder', 'both']:
        print("Invalid choice.")
        return

    for table in selected_tables:
        if choice in ['migration', 'both']:
            create_migration_file(table, tables[table], args.destination, migration_template)
        if choice in ['seeder', 'both']:
            data_rows = inserts.get(table, [])
            if data_rows:
                create_seeder_file(table, data_rows, args.destination, seeder_template)
            else:
                print(f"[Seeder] No insert data found for table '{table}', seeder skipped.")

if __name__ == "__main__":
    main()
