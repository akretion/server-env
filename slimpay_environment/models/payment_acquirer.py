# Copyright 2020 Akretion, Mourad EL HADJ MIMOUNE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class PaymentAcquirer(models.Model):
    _name = "payment.acquirer"
    _inherit = ["payment.acquirer", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        payment_fields = super()._server_env_fields
        payment_fields.update({
            "slimpay_api_url": {},
            "slimpay_creditor": {},
            "slimpay_app_id": {},
            "slimpay_app_secret": {},
        })
        return payment_fields

    @api.model
    def _server_env_global_section_name(self):
        """Name of the global section in the configuration files

        Can be customized in your model
        used only if we don't use encryption_data module
        """
        return 'slimpay_payment_acquirer'
