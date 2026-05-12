import frappe
from frappe import _


def get_report_companies(company, report_scope, include_parent_company_entries=False):
	if report_scope == "Single Company":
		return [company]

	if report_scope != "Consolidated Group":
		frappe.throw(_("Invalid Report Scope"))

	if not is_group_company(company):
		frappe.throw(_("Consolidated Group scope requires a group company"))

	companies = get_child_companies(company)

	if include_parent_company_entries:
		companies.append(company)

	if not companies:
		frappe.throw(_("No child companies found under selected group company"))

	return companies


def is_group_company(company):
	return bool(frappe.db.get_value("Company", company, "is_group"))


def get_child_companies(parent_company):
	parent = frappe.get_doc("Company", parent_company)

	return frappe.get_all(
		"Company",
		filters={
			"lft": [">", parent.lft],
			"rgt": ["<", parent.rgt],
			"is_group": 0,
		},
		pluck="name",
		order_by="lft asc",
	)


def validate_same_currency(companies):
	company_rows = frappe.get_all(
		"Company",
		filters={"name": ["in", companies]},
		fields=["name", "default_currency"],
	)

	currencies = set(row.default_currency for row in company_rows)

	if len(currencies) > 1:
		frappe.throw(
			_(
				"Multiple company currencies found: {0}. Currency conversion is not enabled in Phase 1."
			).format(", ".join(sorted(currencies)))
		)

	return list(currencies)[0] if currencies else None
