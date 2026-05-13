import frappe


def get_cash_account_names(settings, report_companies):
	# Track which companies have explicit account configuration
	configured_companies = set()
	cash_accounts = []

	if settings and getattr(settings, "name", None):
		for row in settings.get("cash_accounts", []):
			if not row.enabled:
				continue

			if row.company:
				if row.company not in report_companies:
					continue
				configured_companies.add(row.company)

			cash_accounts.append(row.account)

	# For companies with no explicit configuration, fall back to account_type = Cash or Bank
	unconfigured = [c for c in report_companies if c not in configured_companies]

	if unconfigured:
		fallback = frappe.get_all(
			"Account",
			filters={
				"company": ["in", unconfigured],
				"account_type": ["in", ["Cash", "Bank"]],
				"is_group": 0,
				"disabled": 0,
			},
			pluck="name",
		)
		cash_accounts.extend(fallback)

	return list(set(cash_accounts))


def get_journal_entry_rows(filters, report_companies, cash_accounts=None):
	values = {
		"companies": report_companies,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"cost_center": filters.get("cost_center"),
	}

	conditions = ""

	if filters.get("cost_center"):
		conditions += " AND gle.cost_center = %(cost_center)s"

	if cash_accounts:
		values["cash_accounts"] = cash_accounts
		conditions += " AND gle.account NOT IN %(cash_accounts)s"

	return frappe.db.sql(
		f"""
		SELECT
			gle.company,
			gle.posting_date,
			'Journal Entry' AS source_type,
			gle.voucher_no,
			je.voucher_type AS entry_type,
			gle.account,
			gle.cost_center,
			gle.debit,
			gle.credit,
			(gle.credit - gle.debit) AS signed_amount,
			gle.remarks,
			gle.against,
			NULL AS payment_type,
			NULL AS paid_from,
			NULL AS paid_to,
			gle.party_type,
			gle.party,
			NULL AS mode_of_payment
		FROM `tabGL Entry` gle
		INNER JOIN `tabJournal Entry` je
			ON je.name = gle.voucher_no
		WHERE
			gle.company IN %(companies)s
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gle.is_cancelled = 0
			AND gle.voucher_type = 'Journal Entry'
			AND je.docstatus = 1
			AND je.voucher_type IN ('Cash Entry', 'Bank Entry')
			AND (gle.debit != 0 OR gle.credit != 0)
			{conditions}
		""",
		values,
		as_dict=True,
	)


def get_payment_entry_rows(filters, report_companies):
	values = {
		"companies": report_companies,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"cost_center": filters.get("cost_center"),
	}

	conditions = ""

	if filters.get("cost_center"):
		conditions += " AND gle.cost_center = %(cost_center)s"

	return frappe.db.sql(
		f"""
		SELECT
			gle.company,
			gle.posting_date,
			'Payment Entry' AS source_type,
			gle.voucher_no,
			pe.payment_type AS entry_type,
			gle.account,
			gle.cost_center,
			gle.debit,
			gle.credit,
			(gle.debit - gle.credit) AS signed_amount,
			gle.remarks,
			gle.against,
			pe.payment_type,
			pe.paid_from,
			pe.paid_to,
			pe.party_type,
			pe.party,
			pe.mode_of_payment
		FROM `tabGL Entry` gle
		INNER JOIN `tabPayment Entry` pe
			ON pe.name = gle.voucher_no
		WHERE
			gle.company IN %(companies)s
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gle.is_cancelled = 0
			AND gle.voucher_type = 'Payment Entry'
			AND pe.docstatus = 1
			AND pe.payment_type IN ('Receive', 'Pay')
			AND (
				(pe.payment_type = 'Receive' AND gle.account = pe.paid_to)
				OR
				(pe.payment_type = 'Pay' AND gle.account = pe.paid_from)
			)
			AND (gle.debit != 0 OR gle.credit != 0)
			{conditions}
		""",
		values,
		as_dict=True,
	)
