

frappe.pages['supplier-quotation-a'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Custom Supplier Quotation Comparison'),
        single_column: true
    });

    // --- Add CSS ---
    let style = `
    <style>
    .toggle-switch {
        position: relative;
        width: 100px;
        height: 34px;
        background-color: #e9ecef;
        border-radius: 30px;
        overflow: hidden;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
    .toggle-slider {
        position: absolute;
        top: 2px;
        left: 2px;
        width: 46px;
        height: 30px;
        background-color: white;
        border-radius: 25px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 2;
    }
    .toggle-label {
        position: absolute;
        top: 0;
        width: 50%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        z-index: 1;
    }
    .approve-label { left: 0; color: #008000; }
    .reject-label { right: 0; color: #FF0000; }
    .toggle-switch.approve { background-color: #008000; }
    .toggle-switch.reject { background-color: #FF0000; }
    .toggle-switch.approve .toggle-slider { left: 52px; }
    .toggle-switch.approve .approve-label { color: white; }
    .toggle-switch.reject .reject-label { color: white; }

    /* Scrollable wrapper */
    .table-scroll-wrapper {
        overflow-x: auto;
        position: relative;
        width: 100%;
    }

    /* Sticky Decision column (header + cells) */
    .table-scroll-wrapper table th.sticky-col,
    .table-scroll-wrapper table td.sticky-col {
        position: sticky;
        right: 0;
        background-color: #f8f9fa;
        z-index: 12; /* higher than body cells */
        min-width: 120px;
        max-width: 150px;
    }

    /* Sticky header row */
    .table-scroll-wrapper table thead th {
        position: sticky;
        top: 0;
        background-color: #f8f9fa;
        z-index: 15; /* higher than sticky-col to overlap cells */
    }

    /* Optional: Increase z-index for sticky last column header */
    .table-scroll-wrapper table thead th.sticky-col {
        z-index: 20; /* ensures top-right cell overlaps both header and body */
    }

    /* Set column widths */
    .table-scroll-wrapper table th, .table-scroll-wrapper table td {
        min-width: 150px;
        max-width: 250px;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }

    </style>
    `;
    $('head').append(style);

    // --- Filter area ---
    let $filter_area = $('<div class="report-filter-area d-flex flex-wrap gap-3 mb-4" style="row-gap: 15px;"></div>');
    $(page.main).append($filter_area);

    const filters_def = [
        { fieldtype: "Link", label: __("Company"), options: "Company", fieldname: "company", default: frappe.defaults.get_user_default("Company"), reqd: 1 },
        { fieldname: "from_date", label: __("From Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -1) },
        { fieldname: "to_date", label: __("To Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
        { fieldtype: "Link", label: __("Item"), fieldname: "item_code", options: "Item" },
        { fieldname: "supplier", label: __("Supplier"), fieldtype: "MultiSelectList", options: "Supplier", get_data: txt => frappe.db.get_link_options("Supplier", txt) },
        { fieldtype: "MultiSelectList", label: __("Supplier Quotation"), fieldname: "supplier_quotation", options: "Supplier Quotation", get_data: txt => frappe.db.get_link_options("Supplier Quotation", txt, { docstatus: ["<", 2] }) },
        { fieldtype: "Link", label: __("Request for Quotation"), options: "Request for Quotation", fieldname: "request_for_quotation", get_query: () => ({ filters: { docstatus: ["<", 2] } }) },
        { fieldname: "categorize_by", label: __("Categorize by"), fieldtype: "Select", options: [ { label: __("Categorize by Supplier"), value: "Categorize by Supplier" }, { label: __("Categorize by Item"), value: "Categorize by Item" } ], default: "Categorize by Supplier" },
        { fieldtype: "Check", label: __("Include Expired"), fieldname: "include_expired", default: 0 },
    ];

    // store filters here
    let filters = {};

    // Example: loop over your filters_def
    filters_def.forEach(f => {
        let field = page.add_field({
            label: f.label,
            fieldname: f.fieldname,
            fieldtype: f.fieldtype,
            options: f.options,
            default: f.default,
            reqd: f.reqd,
            get_data: f.get_data,        // for MultiSelectList
            get_query: f.get_query,      // for Link filters
            change() {                   // triggers automatically for Link, MultiSelectList, Select, Date, Check
                load_data();
            },
            dropdown_parent: 'body' // <-- ensures dropdown is appended to body
        });

        filters[f.fieldname] = field;

        // optional: apply custom CSS to wrapper
        $(field.wrapper).css({
            'min-width': '220px',
            'max-width': '280px',
            'flex': '1 1 250px',
            'margin-right': '15px',
        });
    });


    // --- Data wrapper ---
    let $data_wrapper = $('<div class="mt-4"></div>');
    $(page.main).append($data_wrapper);

    // --- Submit button ---
    let $button_container = $('<div class="d-flex justify-content-end mt-3"><button class="btn btn-primary">'+__("Submit")+'</button></div>');
    $(page.main).append($button_container);
    let $submit_btn = $button_container.find("button");
    $submit_btn.on('click', function() {
        frappe.confirm(__('Are you sure you want to submit?'), process_records);
    });

    // --- Load data ---
    function load_data() {
        let args = {};
        Object.keys(filters).forEach(key => args[key] = filters[key].get_value());
        args["workflow_state"] = "Pending";


        frappe.call({
            method: "frappe.desk.query_report.run",
            // method: "reva_erp.api.supplier_quotation_com.get_supplier_quotation_comparison",
            args: { report_name: "Supplier Quotation Comparison", filters: args },
            freeze: true,
            freeze_message: __("Loading data..."),
            callback: function(r) {
                if (r.message && r.message.result && r.message.result.length > 0) {
                    render_table(r.message.result);
                } else {
                    $data_wrapper.html('<div class="text-muted mt-3">'+__("No data found")+'</div>');
                }

                // if (r.message && r.message && r.message.length > 0) {
                //     render_table(r.message);
                // } else {
                //     $data_wrapper.html('<div class="text-muted mt-3">'+__("No data found")+'</div>');
                // }
            }
        });
    }

    // --- Render table ---
    function render_table(data) {
        $data_wrapper.empty();
        let scroll_wrapper = $('<div class="table-scroll-wrapper"></div>');
        let table = $('<table class="table table-bordered table-hover"><thead class="table-light"></thead><tbody></tbody></table>');

        let columns = Object.keys(data[0]);
        let thead = table.find('thead');
        let tr_head = $('<tr></tr>');
        columns.forEach(c => tr_head.append('<th>'+frappe.utils.to_title_case(c.replace(/_/g,' '))+'</th>'));
        tr_head.append('<th class="sticky-col">Decision</th>');
        thead.append(tr_head);

        let tbody = table.find('tbody');
        data.forEach(row => {
            let tr = $('<tr></tr>');
            columns.forEach(c => tr.append('<td>'+ (row[c] ?? "") +'</td>'));

            let toggle = $(`
                <div class="toggle-switch reject" data-name="${row.quotation}">
                    <div class="toggle-slider"></div>
                    <div class="toggle-label approve-label">Approve</div>
                    <div class="toggle-label reject-label">Reject</div>
                </div>
            `);
            toggle.on('click', function() { $(this).toggleClass('approve reject'); });
            tr.append($('<td class="sticky-col"></td>').append(toggle));

            tbody.append(tr);
        });

        scroll_wrapper.append(table);
        $data_wrapper.append(scroll_wrapper);
    }

    function process_records() {
        let approve_list = [], reject_list = [];
        $data_wrapper.find('.toggle-switch').each(function() {
            let name = $(this).data('name');
            if ($(this).hasClass('approve')) approve_list.push(name);
            else reject_list.push(name);
        });

        frappe.call({
            method: "reva_erp.api.supplier_quotation_com.process_supplier_quotations",
            args: { approve: approve_list, reject: reject_list },
            freeze: true,
            freeze_message: __("Processing..."),
            callback: function(r) {
                frappe.show_alert({ message: __("Approval/Rejection process completed"), indicator: "green" });
                load_data();
            },
            error: function(err) {
                frappe.msgprint(__("Error processing quotations"));
                console.error(err);
            }
        });
    }

    setTimeout(load_data, 200);
};
