frappe.listview_settings["Task Approval"] = {
	add_fields: ["workflow_state", "approver_name", "emp_name", "task"],
	filters: [["workflow_state", "=", "Pending"]],
	hide_name_filter: true,

	onload(listview) {
		// Add workflow state filter
		if (!listview.page.fields_dict.workflow_state) {
			listview.page.add_field({
				fieldname: "workflow_state",
				label: __("Workflow State"),
				fieldtype: "Select",
				onchange: () => {
					const value = listview.page.fields_dict.workflow_state.get_value();
					frappe.route_options = { workflow_state: value };
					listview.refresh();
				},
			});
		}

		// Allowed workflow states
		const allowed_states = ["Pending", "Approved", "Rejected", "Discarded"];

		// Delay needed because options are injected async by Frappe
		setTimeout(() => {
			const field = listview.page.fields_dict.workflow_state;
			if (!field || !field.$input) return;

			// Remove unwanted options
			field.$input.find("option").each(function () {
				const val = $(this).val();
				if (val && !allowed_states.includes(val)) {
					$(this).remove();
				}
			});

			// Default value
			if (!field.get_value()) {
				field.set_value("Pending");
			}
		}, 300);
	},
};