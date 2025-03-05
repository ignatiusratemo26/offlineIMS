# Generated by Django 5.1.6 on 2025-03-05 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EquipmentBooking",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("CANCELLED", "Cancelled"),
                            ("COMPLETED", "Completed"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("purpose", models.TextField()),
                (
                    "project_name",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Workspace",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
                ("capacity", models.PositiveIntegerField(default=1)),
                (
                    "lab",
                    models.CharField(
                        choices=[
                            ("IVE", "IvE Design Studio"),
                            ("CEZERI", "Cezeri Lab"),
                            ("MEDTECH", "MedTech Lab"),
                        ],
                        max_length=20,
                    ),
                ),
                ("location", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="workspaces/"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WorkspaceBooking",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("CANCELLED", "Cancelled"),
                            ("COMPLETED", "Completed"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("purpose", models.TextField()),
                (
                    "project_name",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("participants_count", models.PositiveIntegerField(default=1)),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="BookingSlot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
            ],
            options={
                "unique_together": {("date", "start_time", "end_time")},
            },
        ),
    ]
