import uuid
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
        related_name="%(class)s_created"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_updated"
    )

    # --- Soft Delete ---
    is_active = models.BooleanField(default=True, verbose_name="Active")
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_deleted"
    )

    class Meta:
        abstract = True

    def delete(self, user=None, *args, **kwargs):
        """Soft delete implementation."""
        self.is_active = False
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        """Restore an archived object."""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    def save(self, *args, **kwargs):
        # Protection against modifying archived records
        if self.pk:
            on_db = self.__class__.objects.filter(pk=self.pk).first()
            if on_db and not on_db.is_active:
                # If it's already inactive and we are not trying to restore it
                if not self.is_active == True:
                    raise PermissionError("Modification forbidden on archived objects.")

        super().save(*args, **kwargs)


class Client(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class MoleculeType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Project(BaseModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='projects'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    molecule_type = models.ForeignKey(
        MoleculeType,
        on_delete=models.PROTECT,
        related_name='projects'
    )

    molecule_name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('client', 'name')

    def __str__(self):
        return f"{self.code} - {self.name}"