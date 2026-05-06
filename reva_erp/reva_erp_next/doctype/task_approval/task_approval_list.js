// frappe.listview_settings['Task Approval'] = {
//     onload: function(listview) {
        
//         // Add custom select filter field in the toolbar
//         let status_filter = listview.page.add_field({
//             fieldname: 'workflow_state',
//             label: 'Status',
//             fieldtype: 'Select',
//             options: [
//                 { value: '', label: 'All' },
//                 { value: 'Pending', label: 'Pending' },
//                 { value: 'Approved', label: 'Approved' },
//                 { value: 'Rejected', label: 'Rejected' },
//                 // 👆 add only the states you want
//             ],
//             change: function() {
//                 let selected_value = status_filter.get_value();
//                 alert(selected_value);
                
//                 // Remove existing workflow_state filter
//                 listview.filter_area.filter_list.filter_rows
//                     .filter(row => row.fieldname === 'workflow_state')
//                     .forEach(row => row.remove());

//                 if (selected_value) {
//                     alert('Applying filter: ' + selected_value);
//                     // Apply new filter
//                     listview.filter_area.filter_list.add_filter(
//                         'Task Approval',
//                         'workflow_state',
//                         '=',
//                         selected_value
//                     ).then(() => listview.refresh());
//                 } else {
//                     // No filter, reload all
//                     listview.refresh();
//                 }
//             }
//         });
//     }
// };


// frappe.listview_settings['Task Approval'] = {
//     onload: function(listview) {

//         // Add to the left filter area (below "Filter By" section)
//         let $filter_area = listview.filter_area.$filter_list_wrapper;

//         let $wrapper = $(`
//             <select class="form-control input-xs custom-status-filter" 
//                     style="height: 28px; font-size: 12px;">
//                     <option value="">All</option>
//                     <option value="Pending">Pending</option>
//                     <option value="Approved">Approved</option>
//                     <option value="Rejected">Rejected</option>
//                 </select>
            
//         `).prependTo($filter_area);

//         // Handle change event
//         $wrapper.find('.custom-status-filter').on('change', function() {
//             let selected_value = $(this).val();

//             // Remove existing workflow_state filter rows
//             listview.filter_area.filter_list.filter_rows
//                 .filter(row => row.fieldname === 'workflow_state')
//                 .forEach(row => row.remove());

//             if (selected_value) {
//                 listview.filter_area.filter_list.add_filter(
//                     'Task Approval',
//                     'workflow_state',
//                     '=',
//                     selected_value
//                 ).then(() => listview.refresh());
//             } else {
//                 listview.refresh();
//             }
//         });
//     }
// };





frappe.listview_settings['Task Approval'] = {
    onload: function(listview) {
        setup_workflow_filter_patch(listview);
        patch_workflow_filter(listview);
    },
    refresh: function(listview) {
        patch_workflow_filter(listview);
    }
};

const allowed_workflow_states = ['Pending', 'Approved', 'Rejected'];

function setup_workflow_filter_patch(listview) {
    const filter_list = listview.filter_area && listview.filter_area.filter_list;
    if (!filter_list || filter_list._workflow_state_patch_added) {
        return;
    }

    filter_list._workflow_state_patch_added = true;

    const original_add_filter = filter_list.add_filter.bind(filter_list);
    filter_list.add_filter = function(...args) {
        const result = original_add_filter(...args);
        Promise.resolve(result).then(() => patch_workflow_filter(listview));
        setTimeout(() => patch_workflow_filter(listview), 100);
        return result;
    };

    const original_push_new_filter = filter_list._push_new_filter.bind(filter_list);
    filter_list._push_new_filter = function(...args) {
        const row = original_push_new_filter(...args);
        patch_filter_row(row);
        return row;
    };
}

function patch_workflow_filter(listview) {
    const filter_list = listview.filter_area && listview.filter_area.filter_list;
    const rows = (filter_list && (filter_list.filters || filter_list.filter_rows)) || [];
    rows.forEach(patch_filter_row);
}

function patch_filter_row(row) {
    if (!row || row._workflow_state_filter_patched) {
        patch_filter_value(row);
        return;
    }

    row._workflow_state_filter_patched = true;

    const original_set_field = row.set_field.bind(row);
    row.set_field = function(...args) {
        const result = original_set_field(...args);
        patch_filter_value(row);
        return result;
    };

    patch_filter_value(row);
}

function patch_filter_value(row) {
    const fieldname = row.field && row.field.df && row.field.df.fieldname;
    if (fieldname !== 'workflow_state') {
        return;
    }

    const get_query = function() {
        return {
            filters: {
                name: ['in', allowed_workflow_states]
            }
        };
    };

    row.field.get_query = get_query;
    row.field.df.get_query = get_query;

    if (row.field.$input && row.field.$input.cache) {
        row.field.$input.cache = {};
    }
}




