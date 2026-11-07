from django.db import migrations, models


class Migration(migrations.Migration):
    """Alinea la BD con items/models.py: campos en español + nuevo campo grosor_lana."""

    dependencies = [
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(model_name='item', old_name='title', new_name='titulo'),
        migrations.RenameField(model_name='item', old_name='description', new_name='descripcion'),
        migrations.RenameField(model_name='item', old_name='created_by', new_name='creado_por'),
        migrations.RenameField(model_name='item', old_name='created_at', new_name='creado_a'),
        migrations.AlterModelOptions(
            name='item',
            options={'ordering': ['-creado_a']},
        ),
        migrations.AddField(
            model_name='item',
            name='grosor_lana',
            field=models.TextField(blank=True),
        ),
    ]
