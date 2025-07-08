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
