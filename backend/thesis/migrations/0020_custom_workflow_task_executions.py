import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("thesis", "0019_configurable_workflows_and_prompts")]

    operations = [
        migrations.AddField(
            model_name="chapterrevision",
            name="prompt_version_used",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Versión del prompt utilizada"),
        ),
        migrations.CreateModel(
            name="WorkflowTaskExecution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("revision_no", models.PositiveIntegerField()),
                ("idempotency_key", models.UUIDField()),
                ("input_json", models.JSONField(default=dict)),
                ("output_json", models.JSONField(default=dict)),
                ("prompt_text_used", models.TextField(blank=True, default="")),
                ("prompt_version_used", models.PositiveIntegerField(blank=True, null=True)),
                ("output_sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="executions", to="thesis.workflowtask")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="task_executions", to="thesis.projectworkflow")),
            ],
            options={"db_table": "thesis_workflow_task_execution", "ordering": ["task", "revision_no"]},
        ),
        migrations.AddConstraint(
            model_name="workflowtaskexecution",
            constraint=models.UniqueConstraint(fields=("task", "revision_no"), name="unique_workflow_task_revision"),
        ),
        migrations.AddConstraint(
            model_name="workflowtaskexecution",
            constraint=models.UniqueConstraint(fields=("task", "idempotency_key"), name="unique_workflow_task_idempotency"),
        ),
        migrations.AddConstraint(
            model_name="workflowtaskexecution",
            constraint=models.CheckConstraint(condition=models.Q(revision_no__gt=0), name="workflow_task_revision_positive"),
        ),
    ]
