import calendar

import frappe
from frappe import _

from cash_budget.cash_budget.utils.companies import (
	get_report_companies,
	validate_same_currency,
)
from cash_budget.cash_budget.utils.queries import (
	get_cash_account_names,
	get_journal_entry_rows,
	get_payment_entry_rows,
)
from cash_budget.cash_budget.utils.classification import (
	normalize_row,
	get_mapping_rules,
	classify_row,
)
from cash_budget.cash_budget.utils.intercompany import (
	get_intercompany_party_map,
	apply_intercompany_mapping,
	apply_consolidation_treatment,
)
from cash_budget.cash_budget.utils.totals import (
	get_columns,
	get_matrix_columns,
	build_data,
)


MONTH_MAP = {
	"January": 1,
	"February": 2,
	"March": 3,
	"April": 4,
	"May": 5,
	"June": 6,
	"July": 7,
	"August": 8,
	"September": 9,
	"October": 10,
	"November": 11,
	"December": 12,
}


def execute(filters=None):
	filters = frappe._dict(filters or {})

	apply_month_filters(filters)
	validate_filters(filters)

	report_companies = get_report_companies(
		company=filters.company,
		report_scope=filters.report_scope,
		include_parent_company_entries=filters.get("include_parent_company_entries"),
	)

	validate_same_currency(report_companies)

	settings = get_settings(filters.company, filters.report_scope)

	if filters.get("output_format") == "Matrix":
		columns = get_matrix_columns(report_companies, filters)
	else:
		columns = get_columns(filters)

	raw_rows = []
	cash_accounts = get_cash_account_names(settings, report_companies)

	if filters.source_type in (None, "", "All", "Journal Entry") and settings.include_journal_entry:
		raw_rows.extend(get_journal_entry_rows(filters, report_companies, cash_accounts))

	if filters.source_type in (None, "", "All", "Payment Entry") and settings.include_payment_entry:
		raw_rows.extend(get_payment_entry_rows(filters, report_companies))

	mapping_rules = get_mapping_rules(settings.name)
	intercompany_parties = get_intercompany_party_map(settings.name)

	rows = []

	for row in raw_rows:
		row = normalize_row(row)
		row = classify_row(row, mapping_rules, settings)
		row = apply_intercompany_mapping(row, intercompany_parties)
		row = apply_consolidation_treatment(row, filters)
		rows.append(row)

	if filters.get("cash_budget_item"):
		rows = [
			row
			for row in rows
			if row.get("cash_budget_item") == filters.get("cash_budget_item")
		]

	data = build_data(rows, filters, settings, report_companies)

	return columns, data


def apply_month_filters(filters):
	if not filters.get("month") or not filters.get("year"):
		return

	month_no = MONTH_MAP.get(filters.month)
	if not month_no:
		return

	year = int(filters.year)
	last_day = calendar.monthrange(year, month_no)[1]

	filters.from_date = f"{year}-{month_no:02d}-01"
	filters.to_date = f"{year}-{month_no:02d}-{last_day:02d}"


def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Company is required"))

	if not filters.get("from_date"):
		frappe.throw(_("From Date is required"))

	if not filters.get("to_date"):
		frappe.throw(_("To Date is required"))

	if not filters.get("report_scope"):
		filters.report_scope = "Single Company"

	if not filters.get("output_format"):
		filters.output_format = "Matrix"


def get_settings(company, report_scope):
	settings_name = None

	if report_scope == "Consolidated Group":
		settings_name = frappe.db.get_value(
			"Cash Budget Settings",
			{"company": company, "is_group_settings": 1},
			"name",
		)

	if not settings_name:
		settings_name = frappe.db.get_value(
			"Cash Budget Settings",
			{"company": company},
			"name",
		)

	if not settings_name:
		return frappe._dict(
			{
				"name": None,
				"company": company,
				"include_journal_entry": 1,
				"include_payment_entry": 1,
				"use_cost_center_as_fallback": 1,
				"require_mapping": 0,
				"default_receipt_item": None,
				"default_payment_item": None,
				"detect_intercompany": 1,
				"show_internal_transfers": 0,
				"ignore_cancelled_gl_entries": 1,
			}
		)

	return frappe.get_doc("Cash Budget Settings", settings_name)
