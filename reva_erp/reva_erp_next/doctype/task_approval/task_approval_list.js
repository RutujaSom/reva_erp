frappe.listview_settings["Task Approval"] = {
    onload(listview) {
        setup_workflow_state_filter(listview);
    },
    refresh(listview) {
        patch_workflow_state_filters(listview);
    },
};

const allowed_workflow_states = ["Draft", "Pending", "Approved", "Rejected"];

function setup_workflow_state_filter(listview) {
    patch_workflow_state_filters(listview);
    patch_filter_group(listview);
}

function patch_filter_group(listview) {
    const filter_list = listview.filter_area && listview.filter_area.filter_list;
    if (!filter_list || filter_list._reva_workflow_state_patch_added) {
        return;
    }

    filter_list._reva_workflow_state_patch_added = true;

    const original_add_filter = filter_list.add_filter.bind(filter_list);
    filter_list.add_filter = function (...args) {
        const result = original_add_filter(...args);
        Promise.resolve(result).then(() => patch_workflow_state_filters(listview));
        setTimeout(() => patch_workflow_state_filters(listview), 100);
        return result;
    };

    if (filter_list._push_new_filter) {
        const original_push_new_filter = filter_list._push_new_filter.bind(filter_list);
        filter_list._push_new_filter = function (...args) {
            const row = original_push_new_filter(...args);
            patch_filter_row(row);
            return row;
        };
    }
}

function patch_workflow_state_filters(listview) {
    patch_standard_filter(listview);

    const filter_list = listview.filter_area && listview.filter_area.filter_list;
    const rows = (filter_list && (filter_list.filters || filter_list.filter_rows)) || [];
    rows.forEach(patch_filter_row);
}

function patch_standard_filter(listview) {
    const field = listview.page && listview.page.fields_dict.workflow_state;
    if (field) {
        apply_allowed_workflow_query(field);
    }
}

function patch_filter_row(row) {
    if (!row) {
        return;
    }

    if (!row._reva_workflow_state_filter_patched && row.set_field) {
        row._reva_workflow_state_filter_patched = true;

        const original_set_field = row.set_field.bind(row);
        row.set_field = function (...args) {
            const result = original_set_field(...args);
            patch_filter_row(row);
            return result;
        };
    }

    const fieldname = row.field && row.field.df && row.field.df.fieldname;
    if (fieldname === "workflow_state") {
        apply_allowed_workflow_query(row.field);
    }
}

function apply_allowed_workflow_query(field) {
    const get_query = () => ({
        filters: {
            name: ["in", allowed_workflow_states],
        },
    });

    field.get_query = get_query;
    field.df.get_query = get_query;
    field.df.only_select = 1;

    if (field.$input && field.$input.cache) {
        field.$input.cache = {};
    }

    if (field.awesomplete) {
        field.awesomplete.list = allowed_workflow_states.map((state) => ({
            label: __(state),
            value: state,
        }));
    }
}
