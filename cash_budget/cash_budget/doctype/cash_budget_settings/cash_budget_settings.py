import frappe
from frappe import _
from frappe.model.document import Document


class CashBudgetSettings(Document):
	def validate(self):
		self.validate_unique_company()
		self.validate_group_settings()
		self.validate_mapping_rules()
		self.validate_intercompany_parties()

	def validate_unique_company(self):
		existing = frappe.db.get_value(
			"Cash Budget Settings",
			{
				"company": self.company,
				"name": ["!=", self.name],
			},
			"name",
		)

		if existing:
			frappe.throw(
				_("Cash Budget Settings already exists for company {0}").format(self.company)
			)

	def validate_group_settings(self):
		if not self.is_group_settings:
			return

		is_group = frappe.db.get_value("Company", self.company, "is_group")

		if not is_group:
			frappe.throw(_("Group settings require a group company"))

	def validate_mapping_rules(self):
		for rule in self.get("mapping_rules", []):
			if not rule.cash_budget_item:
				frappe.throw(_("Cash Budget Item is required in mapping rules"))

			if rule.priority is None:
				frappe.throw(_("Priority is required in mapping rules"))

			if rule.source_type == "Journal Entry" and rule.payment_type:
				frappe.throw(
					_("Payment Type should not be set for Journal Entry mapping rules")
				)

			if rule.source_type == "Payment Entry" and rule.journal_entry_type:
				frappe.throw(
					_("Journal Entry Type should not be set for Payment Entry mapping rules")
				)

	def validate_intercompany_parties(self):
		seen = set()

		for row in self.get("intercompany_parties", []):
			key = (row.company, row.party_type, row.party)

			if key in seen:
				frappe.throw(
					_("Duplicate Intercompany Party mapping for {0} / {1} / {2}").format(
						row.company, row.party_type, row.party
					)
				)

			seen.add(key)

			if row.company == row.represents_company:
				frappe.throw(
					_(
						"Transaction Company cannot represent itself in Intercompany Party mapping"
					)
				)
