# utils_tests.py
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

# =========================================================================
# 1. POUR LES ENTITÉS PRINCIPALES (BaseModel) - Devient un Mixin Python pur
# =========================================================================
class BaseEntityTestMixin:
    model = None
    form_class = None
    app_namespace = 'referential'

    def setUp(self):
        super().setUp() # Appelle le setUp de TestCase qui sera hérité plus tard
        self.user = User.objects.create_user(username="user", password="123")
        self.admin_user = User.objects.create_superuser(username="admin", password="123")
        # On force la connexion du client pour éviter les redirections 302
        self.client.force_login(self.user)

    def get_valid_factory_data(self) -> dict:
        raise NotImplementedError

    def create_instance(self, **kwargs):
        data = self.get_valid_factory_data()
        data.update(kwargs)
        return self.model.objects.create(**data)

    def test_base_lifecycle(self):
        """Teste le workflow DRAFT -> VALIDATED -> SOFT_DELETE -> RESTORE"""
        instance = self.create_instance()
        self.assertEqual(instance.status, 'DRAFT')

        # Validation
        instance.validate_entity(user=self.admin_user)
        self.assertEqual(instance.status, 'VALIDATED')

        # Soft Delete
        instance.delete(user=self.user)
        self.assertFalse(instance.is_active)
        self.assertEqual(instance.deleted_by, self.user)

        # Restore
        instance.restore()
        self.assertTrue(instance.is_active)
        self.assertEqual(instance.status, 'DRAFT')


# =========================================================================
# 2. POUR LES COMPOSANTS DÉPENDANTS (BaseComponentEntity)
# =========================================================================
class BaseComponentEntityTestMixin:
    model = None

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="user", password="123")
        self.client.force_login(self.user)

    def get_valid_factory_data(self) -> dict:
        raise NotImplementedError

    def create_instance(self, **kwargs):
        data = self.get_valid_factory_data()
        data.update(kwargs)
        return self.model.objects.create(**data)

    def test_parent_lock_prevents_modification(self):
        """Vérifie le clean() : Impossible de modifier/créer si le parent est VALIDATED"""
        instance = self.create_instance()
        parent = instance.get_parent_entity()

        parent.status = 'VALIDATED'
        parent.save()

        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_save_resets_parent_status_to_draft(self):
        """Vérifie le save() : Sauvegarder un enfant repasse le parent REJECTED en DRAFT"""
        instance = self.create_instance()
        parent = instance.get_parent_entity()

        parent.status = 'REJECTED'
        parent.save()

        instance.is_active = True
        instance.save()

        parent.refresh_from_db()
        self.assertEqual(parent.status, 'DRAFT')