import frappe
from frappe.utils import flt


def normalize_row(row):
	row = frappe._dict(row)
	row.amount = abs(flt(row.signed_amount))

	row.is_intercompany = False
	row.intercompany_counterparty_company = None
	row.consolidation_treatment = None
	row.exception_reason = ""

	if row.source_type == "Journal Entry":
		if flt(row.signed_amount) > 0:
			row.direction = "Receipt"
		elif flt(row.signed_amount) < 0:
			row.direction = "Payment"
		else:
			row.direction = "Ignore"

	elif row.source_type == "Payment Entry":
		if row.payment_type == "Receive":
			row.direction = "Receipt"
		elif row.payment_type == "Pay":
			row.direction = "Payment"
		else:
			row.direction = "Transfer"

	else:
		row.direction = "Ignore"

	return row


def get_mapping_rules(settings_name):
	if not settings_name:
		return []

	settings = frappe.get_doc("Cash Budget Settings", settings_name)

	rules = []
	for rule in settings.get("mapping_rules", []):
		if not rule.enabled:
			continue

		rules.append(
			frappe._dict(
				{
					"priority": rule.priority or 0,
					"company": rule.company,
					"source_type": rule.source_type or "Both",
					"journal_entry_type": rule.journal_entry_type,
					"payment_type": rule.payment_type,
					"cost_centers": [v.strip() for v in (rule.cost_centers or "").split(",") if v.strip()],
					"account": rule.account,
					"against_accounts": [v.strip() for v in (rule.against_accounts or "").split(",") if v.strip()],
					"paid_from_account": rule.paid_from_account,
					"paid_to_account": rule.paid_to_account,
					"party_type": rule.party_type,
					"party": rule.party,
					"modes_of_payment": [v.strip() for v in (rule.modes_of_payment or "").split(",") if v.strip()],
					"cash_budget_item": rule.cash_budget_item,
					"direction_override": rule.direction_override or "Auto",
				}
			)
		)

	return sorted(
		rules,
		key=lambda rule: (0 if rule.company else 1, rule.priority or 0),
	)


def find_matching_rule(row, mapping_rules):
	for rule in mapping_rules:
		if rule.company and rule.company != row.company:
			continue

		if rule.source_type not in ("Both", row.source_type):
			continue

		if rule.journal_entry_type and rule.journal_entry_type != "Both" and row.source_type == "Journal Entry":
			if rule.journal_entry_type != row.entry_type:
				continue

		if rule.payment_type and row.source_type == "Payment Entry":
			if rule.payment_type != row.payment_type:
				continue

		if rule.cost_centers and row.cost_center not in rule.cost_centers:
			continue

		if rule.account and rule.account != row.account:
			continue

		if rule.against_accounts:
			row_against = [v.strip() for v in (row.against or "").split(",") if v.strip()]
			if not any(a in row_against for a in rule.against_accounts):
				continue

		if rule.paid_from_account and rule.paid_from_account != row.paid_from:
			continue

		if rule.paid_to_account and rule.paid_to_account != row.paid_to:
			continue

		if rule.party_type and rule.party_type != row.party_type:
			continue

		if rule.party and rule.party != row.party:
			continue

		if rule.modes_of_payment and row.mode_of_payment not in rule.modes_of_payment:
			continue

		return rule

	return None


def classify_row(row, mapping_rules, settings):
	if row.direction in ("Ignore", "Transfer"):
		row.cash_budget_item = (
			"Internal Transfer" if row.direction == "Transfer" else "Ignored"
		)
		row.classification_status = row.direction
		return row

	rule = find_matching_rule(row, mapping_rules)

	if rule:
		row.cash_budget_item = rule.cash_budget_item

		if rule.direction_override and rule.direction_override != "Auto":
			row.direction = rule.direction_override

		row.classification_status = "Mapped"
		return row

	if settings.use_cost_center_as_fallback and row.cost_center:
		row.cash_budget_item = row.cost_center
		row.classification_status = "Cost Center Fallback"
		row.exception_reason = "Needs mapping rule"
		return row

	default_item = (
		settings.default_receipt_item
		if row.direction == "Receipt"
		else settings.default_payment_item
	)

	if default_item and not settings.require_mapping:
		row.cash_budget_item = default_item
		row.classification_status = "Default Item"
		row.exception_reason = "Auto classified by default item"
		return row

	row.cash_budget_item = "Unclassified"
	row.classification_status = "Unclassified"
	row.exception_reason = get_exception_reason(row)
	return row


def get_exception_reason(row):
	reasons = []

	if not row.cost_center:
		reasons.append("Missing Cost Center")

	if not row.party:
		reasons.append("Missing Party")

	if not reasons:
		reasons.append("No matching mapping rule")

	return "; ".join(reasons)
