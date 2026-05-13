frappe.ui.form.on("Cash Budget Mapping Rule", {
	add_cost_center(_frm, cdt, cdn) {
		const dialog = new frappe.ui.Dialog({
			title: __("Add Cost Center"),
			fields: [
				{
					fieldname: "cost_center",
					fieldtype: "Link",
					label: __("Cost Center"),
					options: "Cost Center",
					reqd: 1,
				},
			],
			primary_action_label: __("Add"),
			primary_action(values) {
				const row = locals[cdt][cdn];
				const existing = (row.cost_centers || "")
					.split(",")
					.map((v) => v.trim())
					.filter((v) => v);

				if (!existing.includes(values.cost_center)) {
					existing.push(values.cost_center);
					frappe.model.set_value(cdt, cdn, "cost_centers", existing.join(", "));
				}
				dialog.hide();
			},
		});
		dialog.show();
	},

	add_mode_of_payment(_frm, cdt, cdn) {
		const dialog = new frappe.ui.Dialog({
			title: __("Add Mode of Payment"),
			fields: [
				{
					fieldname: "mode_of_payment",
					fieldtype: "Link",
					label: __("Mode of Payment"),
					options: "Mode of Payment",
					reqd: 1,
				},
			],
			primary_action_label: __("Add"),
			primary_action(values) {
				const row = locals[cdt][cdn];
				const existing = (row.modes_of_payment || "")
					.split(",")
					.map((v) => v.trim())
					.filter((v) => v);

				if (!existing.includes(values.mode_of_payment)) {
					existing.push(values.mode_of_payment);
					frappe.model.set_value(cdt, cdn, "modes_of_payment", existing.join(", "));
				}
				dialog.hide();
			},
		});
		dialog.show();
	},
});
