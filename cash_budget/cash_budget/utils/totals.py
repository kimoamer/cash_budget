import frappe
from frappe.utils import flt
from collections import OrderedDict


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

	if filters.get("show_details"):
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


def build_data(rows, filters, settings):
	if filters.get("show_details"):
		return build_detail_data(rows, filters)

	return build_summary_data(rows, filters)


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
				sub_key = (key, row.company)
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
