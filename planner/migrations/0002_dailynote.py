import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('planner', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='DailyNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note_date', models.DateField()),
                ('content', models.TextField(blank=True, max_length=1000)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_notes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='dailynote',
            constraint=models.UniqueConstraint(fields=('user', 'note_date'), name='one_note_per_user_per_day'),
        ),
    ]
