from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('planner', '0002_dailynote')]
    operations = [
        migrations.RemoveConstraint(
            model_name='dailynote',
            name='one_note_per_user_per_day',
        ),
        migrations.AlterModelOptions(
            name='dailynote',
            options={'ordering': ['-note_date', '-updated_at']},
        ),
    ]
