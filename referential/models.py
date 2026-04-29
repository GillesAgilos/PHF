import uuid

from django.core.exceptions import PermissionDenied
from django.db import models
from django.conf import settings
from django.utils import timezone

class BaseModel(models.Model):
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Audit Trail ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_created",
        verbose_name="Created By"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_updated",
        verbose_name="Last Updated By"
    )

    # --- Soft Delete & Status ---
    is_active = models.BooleanField(default=True, verbose_name="Active")
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_deleted",
        verbose_name="Deleted By"
    )

    class Meta:
        abstract = True

    def delete(self, user=None, *args, **kwargs):
        self.is_active = False
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    def save(self, *args, **kwargs):
        if self.pk:
            on_db = self.__class__.objects.filter(pk=self.pk).first()
            if on_db and not on_db.is_active and self.is_active == on_db.is_active:
                raise PermissionError("Modification forbidden on archived objects.")

        super().save(*args, **kwargs)

class Client(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived clients.")
        return obj


class Project(BaseModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='projects'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived projects.")
        return obj