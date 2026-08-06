from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("production", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="analysis",
            old_name="lower_normal_operating_range",
            new_name="lower_specification",
        ),
        migrations.RenameField(
            model_name="analysis",
            old_name="upper_normal_operating_range",
            new_name="upper_specification",
        ),
    ]