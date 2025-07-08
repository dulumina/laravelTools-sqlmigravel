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
