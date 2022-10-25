# Generated by Django 3.2.4 on 2022-10-11 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tag", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="VisibleRange",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("created_by", models.CharField(default="", max_length=32, verbose_name="创建者")),
                ("updated_time", models.DateTimeField(auto_now=True, null=True, verbose_name="更新时间")),
                ("updated_by", models.CharField(blank=True, default="", max_length=32, verbose_name="修改者")),
                ("name", models.CharField(max_length=128, verbose_name="构件名称")),
                ("version", models.CharField(max_length=128, verbose_name="构件版本")),
                (
                    "target_type",
                    models.CharField(
                        choices=[("PLUGIN", "插件"), ("AGENT", "Agent")], max_length=20, verbose_name="目标类型"
                    ),
                ),
                ("is_public", models.BooleanField(default=False, verbose_name="是否全部可见")),
                ("bk_biz_id", models.IntegerField(default=None, null=True, verbose_name="业务ID")),
                ("bk_obj_id", models.CharField(max_length=32, null=True, verbose_name="CMDB对象ID")),
                ("bk_inst_scope", models.JSONField(default=list, verbose_name="CMDB实例ID范围")),
            ],
            options={
                "verbose_name": "版本可见范围",
                "verbose_name_plural": "版本可见范围",
            },
        ),
    ]