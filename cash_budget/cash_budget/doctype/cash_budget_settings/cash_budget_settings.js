frappe.ui.form.on("Cash Budget Mapping Rule", {
	cost_center_selector(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.cost_center_selector) return;

		const existing = (row.cost_centers || "")
			.split(",")
			.map((v) => v.trim())
			.filter((v) => v);

		if (!existing.includes(row.cost_center_selector)) {
			existing.push(row.cost_center_selector);
			frappe.model.set_value(cdt, cdn, "cost_centers", existing.join(", "));
		}

		frappe.model.set_value(cdt, cdn, "cost_center_selector", "");
	},

	mode_of_payment_selector(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.mode_of_payment_selector) return;

		const existing = (row.modes_of_payment || "")
			.split(",")
			.map((v) => v.trim())
			.filter((v) => v);

		if (!existing.includes(row.mode_of_payment_selector)) {
			existing.push(row.mode_of_payment_selector);
			frappe.model.set_value(cdt, cdn, "modes_of_payment", existing.join(", "));
		}

		frappe.model.set_value(cdt, cdn, "mode_of_payment_selector", "");
	},
});
