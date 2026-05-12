import frappe
from frappe.utils import flt
from collections import OrderedDict, defaultdict


REPORT_LAYOUT = [
	{"label": "Balance", "type": "balance"},

	{"label": "Intercompany Collections", "type": "item", "group": "receipts"},
	{"label": "Local Collections", "type": "item", "group": "receipts"},
	{"label": "Export Collections", "type": "item", "group": "receipts"},
	{"label": "Projects - Receipts", "type": "item", "group": "receipts"},
	{"label": "Other Collections", "type": "item", "group": "receipts"},
	{"label": "Total Operating Receipts", "type": "total_receipts"},

	{"label": "Operating Payments:", "type": "section"},

	{"label": "Salaries", "type": "item", "group": "operating_payments"},
	{"label": "Intercompany Purchases", "type": "item", "group": "operating_payments"},
	{"label": "Purchases Raw & Packing", "type": "item", "group": "operating_payments"},
	{"label": "Import of Raw Materials", "type": "item", "group": "operating_payments"},
	{"label": "Manufacturing Overheads", "type": "item", "group": "operating_payments"},
	{"label": "Selling & Marketing", "type": "item", "group": "operating_payments"},
	{"label": "General & Administration", "type": "item", "group": "operating_payments"},
	{"label": "Tax", "type": "item", "group": "operating_payments"},
	{"label": "Insurances", "type": "item", "group": "operating_payments"},
	{"label": "Total Operating Payments", "type": "total_operating_payments"},

	{"label": "Net Cash Flow From Operations", "type": "net_operations"},

	{"label": "Purchases Assets", "type": "item", "group": "non_operating"},
	{"label": "Pay off Loans", "type": "item", "group": "non_operating"},
	{"label": "Pay off Leasing / Tamweel", "type": "item", "group": "non_operating"},
	{"label": "Interest", "type": "item", "group": "non_operating"},
	{"label": "Projects - Payments", "type": "item", "group": "non_operating"},
	{"label": "Shareholders", "type": "item", "group": "non_operating"},
	{"label": "Related Parties", "type": "item", "group": "non_operating"},
	{"label": "Eco Tec", "type": "item", "group": "non_operating"},
	{"label": "Subtotal - Non-Operating", "type": "total_non_operating"},

	{"label": "Net Cash Flow", "type": "net_total"},
]


# ---------------------------------------------------------------------------
# Column builders
# ---------------------------------------------------------------------------

def get_columns(filters):
	columns = [
		{
			"fieldname": "section",
			"label": "Section",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "cash_budget_item",
			"label": "Cash Budget Item",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Currency",
			"width": 150,
		},
	]

	if filters.get("show_company_breakdown") and filters.report_scope == "Consolidated Group":
		columns.append(
			{
				"fieldname": "company",
				"label": "Company",
				"fieldtype": "Link",
				"options": "Company",
				"width": 180,
			}
		)

	if filters.get("output_format") == "Detail" or filters.get("show_details"):
		columns.extend(
			[
				{
					"fieldname": "posting_date",
					"label": "Posting Date",
					"fieldtype": "Date",
					"width": 100,
				},
				{
					"fieldname": "source_type",
					"label": "Source Type",
					"fieldtype": "Data",
					"width": 120,
				},
				{
					"fieldname": "entry_type",
					"label": "Entry Type",
					"fieldtype": "Data",
					"width": 120,
				},
				{
					"fieldname": "voucher_no",
					"label": "Voucher No",
					"fieldtype": "Dynamic Link",
					"options": "source_type",
					"width": 160,
				},
				{
					"fieldname": "account",
					"label": "Account",
					"fieldtype": "Link",
					"options": "Account",
					"width": 200,
				},
				{
					"fieldname": "cost_center",
					"label": "Cost Center",
					"fieldtype": "Link",
					"options": "Cost Center",
					"width": 160,
				},
				{
					"fieldname": "party_type",
					"label": "Party Type",
					"fieldtype": "Data",
					"width": 100,
				},
				{
					"fieldname": "party",
					"label": "Party",
					"fieldtype": "Dynamic Link",
					"options": "party_type",
					"width": 160,
				},
				{
					"fieldname": "intercompany_counterparty_company",
					"label": "Intercompany Counterparty",
					"fieldtype": "Link",
					"options": "Company",
					"width": 180,
				},
				{
					"fieldname": "mode_of_payment",
					"label": "Mode of Payment",
					"fieldtype": "Link",
					"options": "Mode of Payment",
					"width": 130,
				},
				{
					"fieldname": "debit",
					"label": "Debit",
					"fieldtype": "Currency",
					"width": 120,
				},
				{
					"fieldname": "credit",
					"label": "Credit",
					"fieldtype": "Currency",
					"width": 120,
				},
				{
					"fieldname": "classification_status",
					"label": "Classification Status",
					"fieldtype": "Data",
					"width": 160,
				},
				{
					"fieldname": "exception_reason",
					"label": "Exception Reason",
					"fieldtype": "Data",
					"width": 200,
				},
			]
		)

	return columns


def get_matrix_columns(report_companies, filters):
	columns = [
		{
			"fieldname": "description",
			"label": "DES.",
			"fieldtype": "Data",
			"width": 280,
		}
	]

	include_plan = filters.get("include_plan")

	for company in report_companies:
		key = frappe.scrub(company)

		if include_plan:
			columns.append({
				"fieldname": f"{key}_plan",
				"label": f"{company} O.Plan",
				"fieldtype": "Currency",
				"width": 120,
			})

		columns.append({
			"fieldname": f"{key}_actual",
			"label": f"{company} Actu.",
			"fieldtype": "Currency",
			"width": 120,
		})

	if include_plan:
		columns.append({
			"fieldname": "consolidated_plan",
			"label": "Consolidated O.Plan",
			"fieldtype": "Currency",
			"width": 150,
		})

	columns.append({
		"fieldname": "consolidated_actual",
		"label": "Consolidated Actu.",
		"fieldtype": "Currency",
		"width": 150,
	})

	return columns


# ---------------------------------------------------------------------------
# Data builder — dispatcher
# ---------------------------------------------------------------------------

def build_data(rows, filters, settings, report_companies=None):
	if filters.get("output_format") == "Matrix":
		return build_matrix_data(rows, filters, settings, report_companies or [])

	if filters.get("output_format") == "Detail" or filters.get("show_details"):
		return build_detail_data(rows, filters)

	return build_summary_data(rows, filters)


# ---------------------------------------------------------------------------
# Matrix output
# ---------------------------------------------------------------------------

def build_matrix_data(rows, filters, settings, report_companies):
	actual = defaultdict(float)
	intercompany_rows = []
	unclassified_rows = []
	transfer_rows = []

	for row in rows:
		if row.direction in ("Ignore", "Eliminated"):
			continue

		if row.direction == "Transfer":
			transfer_rows.append(row)
			continue

		if row.direction == "Intercompany":
			intercompany_rows.append(row)
			continue

		if row.classification_status == "Unclassified":
			unclassified_rows.append(row)
			continue

		if row.direction not in ("Receipt", "Payment"):
			continue

		if not row.cash_budget_item:
			continue

		actual[(row.cash_budget_item, row.company)] += flt(row.amount)

	data = []
	totals = {
		"receipts": defaultdict(float),
		"operating_payments": defaultdict(float),
		"non_operating": defaultdict(float),
	}

	for line in REPORT_LAYOUT:
		label = line["label"]
		line_type = line["type"]

		if line_type == "section":
			data.append(_matrix_section_row(label, report_companies))
			continue

		if line_type == "balance":
			data.append(_matrix_balance_row(label, report_companies))
			continue

		if line_type == "item":
			row_dict = _matrix_item_row(label, report_companies, actual)

			group = line.get("group")
			if group in totals:
				for company in report_companies:
					totals[group][company] += actual[(label, company)]

			data.append(row_dict)
			continue

		if line_type == "total_receipts":
			data.append(_matrix_total_row(label, report_companies, totals["receipts"]))
			continue

		if line_type == "total_operating_payments":
			data.append(_matrix_total_row(label, report_companies, totals["operating_payments"]))
			continue

		if line_type == "net_operations":
			net = defaultdict(float)
			for company in report_companies:
				net[company] = totals["receipts"][company] - totals["operating_payments"][company]
			data.append(_matrix_total_row(label, report_companies, net, row_type="net"))
			continue

		if line_type == "total_non_operating":
			data.append(_matrix_total_row(label, report_companies, totals["non_operating"]))
			continue

		if line_type == "net_total":
			net = defaultdict(float)
			for company in report_companies:
				net[company] = (
					totals["receipts"][company]
					- totals["operating_payments"][company]
					- totals["non_operating"][company]
				)
			data.append(_matrix_total_row(label, report_companies, net, row_type="net"))
			continue

	# Intercompany section
	if filters.get("show_intercompany") and intercompany_rows:
		data.extend(_matrix_intercompany_section(intercompany_rows, report_companies))

	# Unclassified section
	if filters.get("show_unclassified") and unclassified_rows:
		data.extend(_matrix_unclassified_section(unclassified_rows, report_companies))

	# Internal Transfers section
	if filters.get("show_internal_transfers") and transfer_rows:
		data.extend(_matrix_transfer_section(transfer_rows, report_companies))

	return data


# ---------------------------------------------------------------------------
# Matrix helper rows
# ---------------------------------------------------------------------------

def _matrix_item_row(label, report_companies, actual):
	row = {
		"description": label,
		"row_type": "item",
	}

	consolidated = 0

	for company in report_companies:
		key = frappe.scrub(company)
		value = actual[(label, company)]
		row[f"{key}_actual"] = value
		consolidated += value

	row["consolidated_actual"] = consolidated
	return row


def _matrix_total_row(label, report_companies, totals_by_company, row_type="total"):
	row = {
		"description": label,
		"row_type": row_type,
		"is_total_row": 1,
	}

	consolidated = 0

	for company in report_companies:
		key = frappe.scrub(company)
		value = totals_by_company[company]
		row[f"{key}_actual"] = value
		consolidated += value

	row["consolidated_actual"] = consolidated
	return row


def _matrix_section_row(label, report_companies):
	row = {
		"description": label,
		"row_type": "section",
		"is_section_row": 1,
	}

	for company in report_companies:
		row[f"{frappe.scrub(company)}_actual"] = None

	row["consolidated_actual"] = None
	return row


def _matrix_balance_row(label, report_companies):
	row = {
		"description": label,
		"row_type": "balance",
	}

	for company in report_companies:
		row[f"{frappe.scrub(company)}_actual"] = None

	row["consolidated_actual"] = None
	return row


# ---------------------------------------------------------------------------
# Matrix extra sections
# ---------------------------------------------------------------------------

def _matrix_intercompany_section(rows, report_companies):
	data = [_matrix_section_row("Intercompany Movements", report_companies)]

	summary = defaultdict(lambda: defaultdict(float))

	for row in rows:
		label = "{0} -> {1}".format(
			row.company, row.intercompany_counterparty_company or "Unknown"
		)
		summary[label][row.company] += flt(row.amount)

	for label, company_amounts in summary.items():
		row_dict = {"description": label, "row_type": "intercompany"}
		consolidated = 0

		for company in report_companies:
			key = frappe.scrub(company)
			value = company_amounts.get(company, 0)
			row_dict[f"{key}_actual"] = value
			consolidated += value

		row_dict["consolidated_actual"] = consolidated
		data.append(row_dict)

	return data


def _matrix_unclassified_section(rows, report_companies):
	data = [_matrix_section_row("Unclassified / Needs Review", report_companies)]

	summary = defaultdict(lambda: defaultdict(float))

	for row in rows:
		reason = row.exception_reason or "Unknown"
		summary[reason][row.company] += flt(row.amount)

	for reason, company_amounts in summary.items():
		row_dict = {"description": reason, "row_type": "warning"}
		consolidated = 0

		for company in report_companies:
			key = frappe.scrub(company)
			value = company_amounts.get(company, 0)
			row_dict[f"{key}_actual"] = value
			consolidated += value

		row_dict["consolidated_actual"] = consolidated
		data.append(row_dict)

	return data


def _matrix_transfer_section(rows, report_companies):
	data = [_matrix_section_row("Internal Transfers", report_companies)]

	by_company = defaultdict(float)
	for row in rows:
		by_company[row.company] += flt(row.amount)

	row_dict = {"description": "Total Internal Transfers", "row_type": "item"}
	consolidated = 0

	for company in report_companies:
		key = frappe.scrub(company)
		value = by_company.get(company, 0)
		row_dict[f"{key}_actual"] = value
		consolidated += value

	row_dict["consolidated_actual"] = consolidated
	data.append(row_dict)

	return data


# ---------------------------------------------------------------------------
# Summary output (existing)
# ---------------------------------------------------------------------------

def build_summary_data(rows, filters):
	data = []

	receipt_items = OrderedDict()
	payment_items = OrderedDict()
	intercompany_rows = []
	unclassified_rows = []
	transfer_rows = []

	for row in rows:
		if row.direction == "Receipt":
			key = row.cash_budget_item or "Other Receipts"
			if filters.get("show_company_breakdown") and filters.report_scope == "Consolidated Group":
				receipt_items.setdefault(key, OrderedDict())
				receipt_items[key].setdefault(row.company, 0)
				receipt_items[key][row.company] += flt(row.amount)
			else:
				receipt_items.setdefault(key, 0)
				receipt_items[key] += flt(row.amount)

		elif row.direction == "Payment":
			key = row.cash_budget_item or "Other Payments"
			if filters.get("show_company_breakdown") and filters.report_scope == "Consolidated Group":
				payment_items.setdefault(key, OrderedDict())
				payment_items[key].setdefault(row.company, 0)
				payment_items[key][row.company] += flt(row.amount)
			else:
				payment_items.setdefault(key, 0)
				payment_items[key] += flt(row.amount)

		elif row.direction == "Intercompany":
			intercompany_rows.append(row)

		elif row.direction == "Transfer":
			transfer_rows.append(row)

		elif row.classification_status == "Unclassified":
			unclassified_rows.append(row)

	# Receipts section
	total_receipts = 0
	data.append({"section": "Receipts", "cash_budget_item": "", "amount": None, "indent": 0, "bold": 1})

	if filters.get("show_company_breakdown") and filters.report_scope == "Consolidated Group":
		for item_name, company_amounts in receipt_items.items():
			item_total = sum(company_amounts.values())
			total_receipts += item_total
			data.append({"section": "", "cash_budget_item": item_name, "amount": item_total, "indent": 1})
			for company, amount in company_amounts.items():
				data.append(
					{
						"section": "",
						"cash_budget_item": item_name,
						"amount": amount,
						"company": company,
						"indent": 2,
					}
				)
	else:
		for item_name, amount in receipt_items.items():
			total_receipts += amount
			data.append({"section": "", "cash_budget_item": item_name, "amount": amount, "indent": 1})

	data.append(
		{
			"section": "",
			"cash_budget_item": "Total Receipts",
			"amount": total_receipts,
			"indent": 0,
			"bold": 1,
		}
	)
	data.append({})

	# Payments section
	total_payments = 0
	data.append({"section": "Payments", "cash_budget_item": "", "amount": None, "indent": 0, "bold": 1})

	if filters.get("show_company_breakdown") and filters.report_scope == "Consolidated Group":
		for item_name, company_amounts in payment_items.items():
			item_total = sum(company_amounts.values())
			total_payments += item_total
			data.append({"section": "", "cash_budget_item": item_name, "amount": item_total, "indent": 1})
			for company, amount in company_amounts.items():
				data.append(
					{
						"section": "",
						"cash_budget_item": item_name,
						"amount": amount,
						"company": company,
						"indent": 2,
					}
				)
	else:
		for item_name, amount in payment_items.items():
			total_payments += amount
			data.append({"section": "", "cash_budget_item": item_name, "amount": amount, "indent": 1})

	data.append(
		{
			"section": "",
			"cash_budget_item": "Total Payments",
			"amount": total_payments,
			"indent": 0,
			"bold": 1,
		}
	)
	data.append({})

	# Net Cash Movement
	net_cash = total_receipts - total_payments
	data.append(
		{
			"section": "Net",
			"cash_budget_item": "Net Cash Movement",
			"amount": net_cash,
			"indent": 0,
			"bold": 1,
		}
	)
	data.append({})

	# Intercompany section
	if filters.get("show_intercompany") and intercompany_rows:
		data.append(
			{
				"section": "Intercompany",
				"cash_budget_item": "Intercompany Movements",
				"amount": None,
				"indent": 0,
				"bold": 1,
			}
		)
		ic_summary = OrderedDict()
		for row in intercompany_rows:
			key = "{0} -> {1}".format(
				row.company, row.intercompany_counterparty_company
			)
			ic_summary.setdefault(key, {"receipt": 0, "payment": 0})
			if flt(row.signed_amount) > 0:
				ic_summary[key]["receipt"] += flt(row.amount)
			else:
				ic_summary[key]["payment"] += flt(row.amount)

		for key, amounts in ic_summary.items():
			net = amounts["receipt"] - amounts["payment"]
			data.append(
				{
					"section": "",
					"cash_budget_item": key,
					"amount": net,
					"indent": 1,
				}
			)
		data.append({})

	# Internal Transfers
	if filters.get("show_internal_transfers") and transfer_rows:
		data.append(
			{
				"section": "Transfers",
				"cash_budget_item": "Internal Transfers",
				"amount": None,
				"indent": 0,
				"bold": 1,
			}
		)
		total_transfers = sum(flt(r.amount) for r in transfer_rows)
		data.append(
			{
				"section": "",
				"cash_budget_item": "Total Internal Transfers",
				"amount": total_transfers,
				"indent": 1,
			}
		)
		data.append({})

	# Unclassified section
	if filters.get("show_unclassified") and unclassified_rows:
		data.append(
			{
				"section": "Unclassified",
				"cash_budget_item": "Unclassified / Needs Review",
				"amount": None,
				"indent": 0,
				"bold": 1,
			}
		)
		reason_totals = OrderedDict()
		for row in unclassified_rows:
			reason = row.exception_reason or "Unknown"
			reason_totals.setdefault(reason, 0)
			reason_totals[reason] += flt(row.amount)

		for reason, amount in reason_totals.items():
			data.append(
				{
					"section": "",
					"cash_budget_item": reason,
					"amount": amount,
					"indent": 1,
				}
			)

	return data


# ---------------------------------------------------------------------------
# Detail output (existing)
# ---------------------------------------------------------------------------

def build_detail_data(rows, filters):
	data = []

	for row in rows:
		if row.direction in ("Ignore", "Eliminated"):
			continue

		if row.direction == "Transfer" and not filters.get("show_internal_transfers"):
			continue

		if row.direction == "Intercompany" and not filters.get("show_intercompany"):
			continue

		if row.classification_status == "Unclassified" and not filters.get("show_unclassified"):
			continue

		section = row.direction
		if row.direction in ("Receipt", "Payment"):
			section = row.direction + "s"

		data.append(
			{
				"section": section,
				"cash_budget_item": row.cash_budget_item,
				"amount": flt(row.amount),
				"company": row.company,
				"posting_date": row.posting_date,
				"source_type": row.source_type,
				"entry_type": row.entry_type,
				"voucher_no": row.voucher_no,
				"account": row.account,
				"cost_center": row.cost_center,
				"party_type": row.party_type,
				"party": row.party,
				"intercompany_counterparty_company": row.intercompany_counterparty_company,
				"mode_of_payment": row.mode_of_payment,
				"debit": flt(row.debit),
				"credit": flt(row.credit),
				"classification_status": row.classification_status,
				"exception_reason": row.exception_reason,
			}
		)

	return data
