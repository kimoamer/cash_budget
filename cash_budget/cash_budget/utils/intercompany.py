import frappe


def get_intercompany_party_map(settings_name):
	if not settings_name:
		return {}

	settings = frappe.get_doc("Cash Budget Settings", settings_name)

	result = {}

	for row in settings.get("intercompany_parties", []):
		if not row.enabled:
			continue

		key = (row.company, row.party_type, row.party)

		result[key] = frappe._dict(
			{
				"represents_company": row.represents_company,
				"treatment": row.treatment or "Show Separately",
				"alias_name": row.alias_name,
			}
		)

	return result


def apply_intercompany_mapping(row, intercompany_parties):
	if not row.party_type or not row.party:
		return row

	key = (row.company, row.party_type, row.party)
	mapping = intercompany_parties.get(key)

	if not mapping:
		return row

	row.is_intercompany = True
	row.intercompany_counterparty_company = mapping.represents_company
	row.consolidation_treatment = mapping.treatment or "Show Separately"
	row.classification_status = "Intercompany"

	return row


def apply_consolidation_treatment(row, filters):
	if filters.report_scope != "Consolidated Group":
		return row

	if not row.is_intercompany:
		return row

	treatment = row.consolidation_treatment or "Show Separately"

	if treatment == "Exclude":
		row.direction = "Eliminated"
		row.classification_status = "Eliminated Intercompany"
		return row

	if treatment == "Show Separately":
		row.direction = "Intercompany"
		row.classification_status = "Intercompany - Shown Separately"
		return row

	if treatment == "Include":
		row.classification_status = "Intercompany - Included"
		return row

	return row
