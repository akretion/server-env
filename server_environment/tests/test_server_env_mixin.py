# Copyright 2026 Akretion (https://www.akretion.com).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from . import common


class TestServerEnvMixinFieldDescriptor(common.ServerEnvironmentCase):
    """Regression tests on the descriptor of env-managed fields (issue #301).

    The mixin replaces env-managed fields by new computed field
    descriptors. It used to mutate the original descriptor in place,
    but such descriptors are shared between all the registries of the
    process for fields defined once in Python (e.g. ``res.partner.city``):
    the ``_compute_server_env`` compute then leaked on the other
    registries not applying the mixin, and any access to the field
    raised on them ``AttributeError: 'res.partner' object has no
    attribute '_compute_server_env'`` (see issue #301).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Avoid import errors by other repos depending on server env test classes
        from odoo_test_helper import FakeModelLoader

        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls._origin_fields = {}
        for model in ("res.partner", "res.users"):
            cls._origin_fields[model] = set(dir(cls.env[model].__class__))

    @classmethod
    def remove_mixin_fields(cls):
        """Clean up what FakeModelLoader.restore_registry() leaves behind.

        restore_registry() skips "x_"-prefixed fields (e.g.
        x_city_env_default) and never touches non-field attributes
        (e.g. _inverse_server_env_city).
        """
        for model in ("res.partner", "res.users"):
            extra = set(cls.env[model].__class__.__dict__) - cls._origin_fields[model]
            for attr in extra:
                delattr(cls.env[model].__class__, attr)

    def setUp(self):
        super().setUp()
        from .fake_models import FakePartner

        # Backup the registry for each test (and not only once in
        # setUpClass): restore_registry() assigns the backup copy as the
        # live "_fields" of the models, which is then cleared and
        # repopulated in place by _setup_base() on the next
        # update_registry() call. A single backup would therefore be
        # destroyed after the first update/restore cycle.
        self.loader.backup_registry()
        self.loader.update_registry((FakePartner,))
        self.addCleanup(self.loader.restore_registry)
        self.addCleanup(self.remove_mixin_fields)

    def test_field_descriptor_not_mutated_in_place(self):
        """The mixin must install a new descriptor on the model."""
        # The descriptor of "city" is defined once in Python on the base
        # "res.partner" class: the very same object is shared between all
        # the registries of the process.
        from odoo.addons.base.models import res_partner

        shared_field = res_partner.Partner.city
        env_field = self.env["res.partner"]._fields["city"]
        self.assertIsNot(env_field, shared_field)
        self.assertEqual(env_field.compute, "_compute_server_env")
        self.assertFalse(env_field.store)
        # the original descriptor must be left untouched, as it is shared
        # with the other registries of the process
        self.assertFalse(shared_field.compute)
        self.assertTrue(shared_field.store)
        self.assertTrue(shared_field.copy)

    def test_res_users_create_with_mixin(self):
        """Creating a res.users must work when the mixin is applied.

        The creation of a user also creates its partner, on which address
        fields (including the env-managed "city") are read.
        """
        user = self.env["res.users"].create({"name": "Bob", "login": "bob@example.com"})
        self.assertEqual(user.partner_id.city, False)

    def test_res_partner_usable_after_mixin_unload(self):
        """res.partner must keep working once the mixin is unloaded.

        This reproduces issue #301: with the former in-place mutation, the
        "city" descriptor shared with the other registries kept
        ``compute="_compute_server_env"`` while the model class no longer
        had the method, making any access on plain ``res.partner`` records
        fail with ``AttributeError: 'res.partner' object has no attribute
        '_compute_server_env'``.
        """
        # while the mixin is applied, the field reads and writes the env
        # configuration
        partner = self.env["res.partner"].create({"name": "Contact"})
        partner.write({"city": "Env City"})
        self.assertEqual(partner.city, "Env City")
        # flush pending writes while the mixin fields are still in place,
        # then unload the mixin, as done for any other registry not using it
        self.env.flush_all()
        self.loader.restore_registry()
        # the field is a plain stored field again
        city_field = self.env["res.partner"]._fields["city"]
        self.assertTrue(city_field.store)
        self.assertFalse(city_field.compute)
        # and the companion fields of the mixin are gone as well
        self.assertNotIn("x_city_env_default", self.env["res.partner"]._fields)
        # ... and records can be created and read without any error
        partner = self.env["res.partner"].create({"name": "Other Contact"})
        self.assertEqual(partner.city, False)
        # creating a res.users also creates a partner whose address fields
        # (including the env-managed "city") are read upon creation
        self.env["res.users"].create({"name": "Bob", "login": "bob@example.com"})
