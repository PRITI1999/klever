# Generated by Django 2.2.5 on 2019-12-10 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_auto_20191210_1339'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedjobarchive',
            name='name',
            field=models.CharField(default='default', max_length=128),
            preserve_default=False,
        ),
    ]
