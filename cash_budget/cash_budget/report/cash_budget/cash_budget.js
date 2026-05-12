frappe.query_reports["Cash Budget"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "report_scope",
			label: __("Report Scope"),
			fieldtype: "Select",
			options: "Single Company\nConsolidated Group",
			default: "Single Company",
			reqd: 1,
		},
		{
			fieldname: "output_format",
			label: __("Output Format"),
			fieldtype: "Select",
			options: "Matrix\nSummary\nDetail",
			default: "Matrix",
			reqd: 1,
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Int",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "include_parent_company_entries",
			label: __("Include Parent Company Entries"),
			fieldtype: "Check",
			default: 0,
			depends_on: "eval:doc.report_scope == 'Consolidated Group'",
		},
		{
			fieldname: "show_company_breakdown",
			label: __("Show Company Breakdown"),
			fieldtype: "Check",
			default: 1,
			depends_on:
				"eval:doc.report_scope == 'Consolidated Group' && doc.output_format == 'Summary'",
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "cash_budget_item",
			label: __("Cash Budget Item"),
			fieldtype: "Link",
			options: "Cash Budget Item",
		},
		{
			fieldname: "source_type",
			label: __("Source Type"),
			fieldtype: "Select",
			options: "\nAll\nJournal Entry\nPayment Entry",
			default: "All",
		},
		{
			fieldname: "show_unclassified",
			label: __("Show Unclassified"),
			fieldtype: "Check",
			default: 1,
		},
		{
			fieldname: "show_intercompany",
			label: __("Show Intercompany Movements"),
			fieldtype: "Check",
			default: 1,
			depends_on: "eval:doc.report_scope == 'Consolidated Group'",
		},
		{
			fieldname: "show_internal_transfers",
			label: __("Show Internal Transfers"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "include_plan",
			label: __("Include O.Plan"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) {
			return value;
		}

		if (data.row_type === "section") {
			return `<span style="font-weight:bold; background-color:#00d9d9; display:block; padding:2px;">${value}</span>`;
		}

		if (data.row_type === "total") {
			return `<span style="font-weight:bold; color:white; background-color:#0000cc; display:block; padding:2px;">${value}</span>`;
		}

		if (data.row_type === "net") {
			return `<span style="font-weight:bold; background-color:#00d9d9; display:block; padding:2px;">${value}</span>`;
		}

		if (data.row_type === "warning") {
			return `<span style="font-weight:bold; background-color:#fce4d6; display:block; padding:2px;">${value}</span>`;
		}

		return value;
	},
};
