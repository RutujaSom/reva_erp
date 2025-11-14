// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

window.doc={{ doc.as_json() }};

$(document).ready(function() {
	new rfq();
	doc.supplier = "{{ doc.supplier }}"
	doc.currency = "{{ doc.currency }}"
	doc.number_format = "{{ doc.number_format }}"
	doc.buying_price_list = "{{ doc.buying_price_list }}"
});

rfq = class rfq {
	al
	constructor(){
		this.onfocus_select_all();
		this.change_qty();
		this.change_rate();
		this.terms();
		this.submit_rfq();
		this.navigate_quotations();
		this.supplier_attachments(); 
		this.rfq_pdf(); 
	}
	

	onfocus_select_all(){
		$("input").click(function(){
			$(this).select();
		})
	}

	change_qty(){
		var me = this;
		$('.rfq-items').on("change", ".rfq-qty", function(){
			me.idx = parseFloat($(this).attr('data-idx'));
			me.qty = parseFloat(flt($(this).val())) || 0;
			me.rate = parseFloat(flt($(repl('.rfq-rate[data-idx=%(idx)s]',{'idx': me.idx})).val()));
			me.update_qty_rate();
			$(this).val(format_number(me.qty, doc.number_format, 2));
		})
	}

	change_rate(){
		var me = this;
		$(".rfq-items").on("change", ".rfq-rate", function(){
			me.idx = parseFloat($(this).attr('data-idx'));
			me.rate = parseFloat(flt($(this).val())) || 0;
			me.qty = parseFloat(flt($(repl('.rfq-qty[data-idx=%(idx)s]',{'idx': me.idx})).val()));
			me.update_qty_rate();
			$(this).val(format_number(me.rate, doc.number_format, 2));
		})
	}

	terms(){
		$(".terms").on("change", ".terms-feedback", function(){
			doc.terms = $(this).val();
		})
	}

	update_qty_rate(){
		var me = this;
		doc.grand_total = 0.0;
		$.each(doc.items, function(idx, data){
			if(data.idx == me.idx){
				data.qty = me.qty;
				data.rate = me.rate;
				data.amount = (me.rate * me.qty) || 0.0;
				$(repl('.rfq-amount[data-idx=%(idx)s]',{'idx': me.idx})).text(format_number(data.amount, doc.number_format, 2));
			}

			doc.grand_total += flt(data.amount);
			$('.tax-grand-total').text(format_number(doc.grand_total, doc.number_format, 2));
		})
	}


	supplier_attachments() {
		// Open modal on click
		$(document).on("click", ".add-supplier-attachment", function () {
			$("#attachmentType").val("");
			$("#attachmentFile").val("");
			$("#attachmentRemark").val("");
			$("#attachmentModal").modal("show");
		});

		// Save from modal to table
		$(document).on("click", "#saveAttachment", function () {
			const type = $("#attachmentType").val();
			const file = $("#attachmentFile")[0].files[0];
			const remark = $("#attachmentRemark").val();

			if (!type || !file) {
				frappe.msgprint("Please select Attachment Type and File.");
				return;
			}

			// show section when first attachment added
			$("#supplier-attachments-section").show();

			const row = `
				<tr data-type="${type}" data-remark="${remark}">
					<td>${type}</td>
					<td>
						<input type="file" class="form-control supplier-file" style="display:none">
						<span>${file.name}</span>
					</td>
					<td>${remark || "-"}</td>
					<td><button type="button" class="btn btn-sm btn-danger remove-row">Remove</button></td>
				</tr>`;

			$("#supplier-attachments-body").append(row);

			const lastRow = $("#supplier-attachments-body tr:last");
			const hiddenInput = lastRow.find(".supplier-file")[0];
			const dataTransfer = new DataTransfer();
			dataTransfer.items.add(file);
			hiddenInput.files = dataTransfer.files;

			$("#attachmentModal").modal("hide");
		});

		// Remove attachment row
		$(document).on("click", ".remove-row", function () {
			$(this).closest("tr").remove();

			// hide section if no attachments remain
			if ($("#supplier-attachments-body tr").length === 0) {
				$("#supplier-attachments-section").hide();
			}
		});
	}


	rfq_pdf(){
		$('.download-rfq').click(function () {
		// on("click", ".download-rfq", function() {
		let rfq_name = "{{ doc.name }}";

		frappe.call({
			method: "reva_erp.api.rfq_pdf.download_rfq_pdf",
			args: { rfq_name },
			callback: function(r) {
				if (r.message) {
					window.location.href = r.message;
				} else {
					frappe.msgprint("Failed to download RFQ");
				}
			}
		});
	})};


	submit_rfq() {
		$('.btn-primary').click(function () {  // "Make Quotation" button

			// Collect attachments
			let attachments = [];
			let has_technical_attachment = false;
			let has_commercial_or_unpriced = false;

			$('#supplier-attachments-body tr').each(function () {
				const type = ($(this).data('type') || "").trim().toLowerCase();
				const file_input = $(this).find('.supplier-file')[0];
				const remark = $(this).data('remark') || "";

				if (file_input && file_input.files.length > 0) {
					attachments.push({
						attachment_type: type,
						file: file_input.files[0],
						remark: remark
					});

					if (type === "technical") {
						has_technical_attachment = true;
					}
					if (type === "commercial" || type === "unpriced") {
						has_commercial_or_unpriced = true;
					}
				}
			});

			// ✅ Validation 1: Require at least one Technical attachment
			if (!has_technical_attachment) {
				frappe.msgprint({
					title: "Missing Attachment",
					message: "Please add at least one Technical attachment before submitting the quotation.",
					indicator: "red"
				});
				return;
			}

			// ✅ Validation 2: Require at least one Commercial OR Unpriced attachment
			if (!has_commercial_or_unpriced) {
				frappe.msgprint({
					title: "Missing Attachment",
					message: "Please add at least one Commercial or Unpriced attachment before submitting the quotation.",
					indicator: "red"
				});
				return;
			}

			// Proceed with quotation creation
			frappe.freeze("Creating quotation...");

			frappe.call({
				type: "POST",
				method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.create_supplier_quotation",
				args: { doc: doc },
				btn: this,
				callback: function (r) {
					frappe.unfreeze();

					if (r.message) {
						const quotation_name = r.message;

						// Upload attachments after quotation creation
						if (attachments.length > 0) {
							add_attachments_to_quotation(quotation_name, attachments);
						} else {
							frappe.msgprint("Quotation created successfully.");
							window.location.href = "/supplier-quotations/" + encodeURIComponent(quotation_name);
						}
					} else {
						frappe.msgprint("Failed to create quotation. Please try again.");
					}
				}
			});
		});
	}



	navigate_quotations() {
		$('.quotations').click(function(){
			name = $(this).attr('idx')
			window.location.href = "/quotations/" + encodeURIComponent(name);
		})
	}
}


function add_attachments_to_quotation(quotation_name, attachments){
    let formData = new FormData();
    formData.append("docname", quotation_name);

    attachments.forEach((att, idx) => {
        formData.append(`file_${idx}`, att.file);
        formData.append(`attachment_type_${idx}`, att.attachment_type);
        formData.append(`remark_${idx}`, att.remark);
    });


    $.ajax({
        url: "/api/method/reva_erp.api.supplier_quotaion.add_attachments_to_quotation",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function(r){
            if(r.message){
                window.location.href = "/supplier-quotations/" + encodeURIComponent(quotation_name);
            }
        }
    });
}

