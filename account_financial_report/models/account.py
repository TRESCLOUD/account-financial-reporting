# © 2011 Guewen Baconnier (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    centralized = fields.Boolean(
        help="If flagged, no details will be displayed in "
        "the General Ledger report (the webkit one only), "
        "only centralized amounts per period.",
    )
    # Odoo 20 eliminó `account.group`: la jerarquía vive en la propia cuenta vía
    # `parent_id`, así que los campos que el informe pedía al grupo se calculan aquí.
    complete_name = fields.Char(
        "Full Name", compute="_compute_complete_name", recursive=True
    )
    complete_code = fields.Char(
        "Full Code", compute="_compute_complete_code", recursive=True
    )
    level = fields.Integer(compute="_compute_level", recursive=True)
    compute_account_ids = fields.Many2many(
        "account.account",
        compute="_compute_account_ids",
        string="Compute accounts",
        store=False,
    )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        """Encadena el nombre de la cuenta con el de sus ascendientes."""
        for account in self:
            if account.parent_id.complete_name:
                account.complete_name = (
                    f"{account.parent_id.complete_name}/{account.name}"
                )
            else:
                account.complete_name = account.name

    @api.depends("code", "parent_id.complete_code")
    def _compute_complete_code(self):
        """Encadena el código de la cuenta con el de sus ascendientes."""
        for account in self:
            if account.parent_id.complete_code:
                account.complete_code = (
                    f"{account.parent_id.complete_code}/{account.code}"
                )
            else:
                account.complete_code = account.code

    @api.depends("parent_id", "parent_id.level")
    def _compute_level(self):
        """Profundidad de la cuenta en el árbol, con la raíz en cero."""
        for account in self:
            account.level = account.parent_id.level + 1 if account.parent_id else 0

    @api.depends("parent_path")
    def _compute_account_ids(self):
        """Subárbol de la cuenta, ella incluida.

        En v20 una cuenta-nodo también puede tener apuntes propios, así que entra
        en su propio subtotal. Las cuentas-nodo del plan ecuatoriano vienen
        archivadas, de ahí el `active_test`.
        """
        Account = self.env["account.account"].with_context(active_test=False)
        for account in self:
            account.compute_account_ids = Account.search(
                [("id", "child_of", account.id)]
            )
