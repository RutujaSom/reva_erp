frappe.ui.form.on('Task Approval', {
    refresh(frm) {
        if (frm.doc.task) {
            fetch_task_details(frm);
        }
        make_form_read_only(frm);
    }
});

function fetch_task_details(frm) {
    if (!frm.doc.task) return;

    frappe.db.get_doc('Task', frm.doc.task)
        .then(task => {
            // Function to set task fields
            const field_map = {
                subject: task.subject,
                project: task.project,
                issue: task.issue,
                type: task.type,
                status: task.status,
                priority: task.priority,
                weight: task.weight,
                parent_task: task.parent_task,
                completed_by: '', // will be filled below
                completed_on: task.completed_on,
                exp_start_date: task.exp_start_date,
                expected_time: task.expected_time,
                start: task.start,
                exp_end_date: task.exp_end_date,
                progress: task.progress,
                duration: task.duration,
                description: task.description,
            };
            // Fetch User full name if completed_by exists
            if (task.completed_by) {
                frappe.db.get_value('User', task.completed_by, 'full_name')
                    .then(r => {
                        const full_name = r.message ? r.message.full_name : task.completed_by;
                        field_map.completed_by = full_name;

                        // Now assign all fields
                        Object.entries(field_map).forEach(([key, value]) => {
                            if (frm.fields_dict[key]) {
                                frm.doc[key] = value || '';
                                frm.refresh_field(key);
                            }
                        });
                        frm.dirty = false;
                    });
            } else {
                // Assign all fields directly if no completed_by
                Object.entries(field_map).forEach(([key, value]) => {
                    if (frm.fields_dict[key]) {
                        frm.doc[key] = value || '';
                        frm.refresh_field(key);
                    }
                });
                frm.dirty = false;
            }
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
}
