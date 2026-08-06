from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("production", "0002_rename_analysis_nor_to_specification"),
    ]

    operations = [
        migrations.RenameField(
            model_name="historicalanalysis",
            old_name="lower_normal_operating_range",
            new_name="lower_specification",
        ),
        migrations.RenameField(
            model_name="historicalanalysis",
            old_name="upper_normal_operating_range",
            new_name="upper_specification",
        ),
    ]
