frappe.ui.form.on('Task Approval', {
    refresh(frm) {
        if (frm.doc.task) {
            frm._auto_filling = true;
            fetch_task_details(frm);
        }
        make_form_read_only(frm);
        frm.disable_save(); // 🔒 disable save initially
    },

    remark(frm) {
        // ✅ User interaction → allow save
        frm.enable_save();
        console.log("Remark changed:", frm.doc.remark);
    }
});

// List View Configuration
frappe.listview_settings['Task Approval'] = {
    // Set default filter to show only Pending workflow state
    default_filters: [
        ['workflow_state', '=', 'Pending']
    ],
    
    // Customize filter options - only show Discard, Reject, Approved, and Open
    add_fields: [
        "workflow_state",
        "approval_level",
        "task",
        "approver_name",
        "emp_name"
    ],
    
    onload(listview) {
        // Override the filter options for workflow_state
        listview.page.fields.workflow_state.df.options = [
            '',
            'Open',
            'Pending',
            'Approved',
            'Rejected',
            'Discard'
        ];
        
        // Refresh the field to apply changes
        listview.page.fields.workflow_state.refresh();
        
        // Set default value to Pending
        listview.page.fields.workflow_state.set_input('Pending');
        
        // Apply the filter
        listview.filter_area.clear().then(() => {
            listview.filter_area.add('Task Approval', 'workflow_state', '=', 'Pending');
        });
    },
    
    form_render(listview, doc) {
        // Customize indicator color based on workflow state
        if (doc.workflow_state === 'Pending') {
            doc._indicator_color = 'orange';
        } else if (doc.workflow_state === 'Approved') {
            doc._indicator_color = 'green';
        } else if (doc.workflow_state === 'Rejected') {
            doc._indicator_color = 'red';
        } else if (doc.workflow_state === 'Discard') {
            doc._indicator_color = 'gray';
        } else {
            doc._indicator_color = 'blue';
        }
    }
};


function fetch_task_details(frm) {
    if (!frm.doc.task) return;

    frappe.db.get_doc('Task', frm.doc.task).then(task => {
        const field_map = {
            subject: task.subject,
            project: task.project,
            issue: task.issue,
            type: task.type,
            status: task.status,
            priority: task.priority,
            weight: task.weight,
            parent_task: task.parent_task,
            completed_on: task.completed_on,
            exp_start_date: task.exp_start_date,
            expected_time: task.expected_time,
            start: task.start,
            exp_end_date: task.exp_end_date,
            progress: task.progress,
            duration: task.duration,
            description: task.description,
        };

        Object.entries(field_map).forEach(([key, value]) => {
            if (frm.fields_dict[key]) {
                // ✅ does NOT mark form dirty
                frappe.model.set_value(
                    frm.doctype,
                    frm.docname,
                    key,
                    value || '',
                    null,
                    true   // skip_dirty = true
                );
            }
        });

        // completed_by handling
        if (task.completed_by) {
            frappe.db.get_value('User', task.completed_by, 'full_name').then(r => {
                frappe.model.set_value(
                    frm.doctype,
                    frm.docname,
                    'completed_by',
                    r.message?.full_name || task.completed_by,
                    null,
                    true
                );
            });
        }

        frm._auto_filling = false;
    });
}

function make_form_read_only(frm) {
    const task_fields = [
        'subject', 'project', 'issue', 'type', 'status', 'priority', 'weight',
        'parent_task', 'completed_by', 'completed_on', 'exp_start_date',
        'expected_time', 'start', 'exp_end_date', 'progress', 'duration', 'description'
    ];

    task_fields.forEach(f => {
        if (frm.fields_dict[f]) {
            frm.set_df_property(f, 'read_only', 1);
        }
    });

    if (frm.doc.workflow_state === "Approved" || frm.doc.workflow_state === "Discard") {
        frm.set_df_property('remark', 'read_only', 1);
    }
}
