import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("thesis", "0035_remove_chaptercitationoccurrence_chapter_cit_revision_order_uq_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AIGenerationBatch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("workflow_version_no", models.PositiveIntegerField()),
                ("state_version_at_request", models.PositiveIntegerField()),
                ("idempotency_key", models.UUIDField()),
                ("request_data", models.JSONField()),
                ("request_sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ai_generation_batches", to="thesis.project")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="requested_ai_batches", to=settings.AUTH_USER_MODEL)),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ai_batches", to="thesis.projectworkflow")),
            ],
            options={"db_table": "thesis_ai_generation_batch", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AIGenerationBatchItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("task_id", models.CharField(max_length=50)),
                ("item_order", models.PositiveSmallIntegerField()),
                ("input_sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="items", to="thesis.aigenerationbatch")),
                ("job", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="batch_item", to="thesis.aigenerationjob")),
            ],
            options={"db_table": "thesis_ai_generation_batch_item", "ordering": ["item_order"]},
        ),
        migrations.AddConstraint(
            model_name="aigenerationbatch",
            constraint=models.UniqueConstraint(fields=("project", "idempotency_key"), name="unique_ai_batch_project_idempotency"),
        ),
        migrations.AddIndex(
            model_name="aigenerationbatch",
            index=models.Index(fields=["project", "created_at"], name="ai_batch_proj_created_idx"),
        ),
        migrations.AddConstraint(
            model_name="aigenerationbatchitem",
            constraint=models.UniqueConstraint(fields=("batch", "task_id"), name="unique_ai_batch_task"),
        ),
        migrations.AddConstraint(
            model_name="aigenerationbatchitem",
            constraint=models.UniqueConstraint(fields=("batch", "item_order"), name="unique_ai_batch_order"),
        ),
        migrations.AddConstraint(
            model_name="aigenerationbatchitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("item_order__gte", 1), ("item_order__lte", 8)),
                name="ai_batch_order_range_ck",
            ),
        ),
        migrations.RunSQL(
            sql="""
                CREATE TRIGGER ai_generation_batch_append_only
                BEFORE UPDATE OR DELETE ON thesis_ai_generation_batch
                FOR EACH ROW EXECUTE FUNCTION tesismcp_reject_history_change();
                CREATE TRIGGER ai_generation_batch_item_append_only
                BEFORE UPDATE OR DELETE ON thesis_ai_generation_batch_item
                FOR EACH ROW EXECUTE FUNCTION tesismcp_reject_history_change();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS ai_generation_batch_item_append_only ON thesis_ai_generation_batch_item;
                DROP TRIGGER IF EXISTS ai_generation_batch_append_only ON thesis_ai_generation_batch;
            """,
        ),
    ]
