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

	// supplier_attachments() {
	// 	const me = this;

	// 	// Open modal on click
	// 	$(document).on("click", ".add-supplier-attachment", function () {
	// 		// Reset modal fields
	// 		$("#attachmentType").val("");
	// 		$("#attachmentFile").val("");
	// 		$("#attachmentRemark").val("");
	// 		$("#attachmentModal").modal("show");
	// 	});

	// 	// Save from modal to table
	// 	$(document).on("click", "#saveAttachment", function () {
	// 		const type = $("#attachmentType").val();
	// 		const file = $("#attachmentFile")[0].files[0];
	// 		const remark = $("#attachmentRemark").val();

	// 		if (!type || !file) {
	// 			frappe.msgprint("Please select Attachment Type and File.");
	// 			return;
	// 		}

	// 		const row = `
	// 			<tr data-type="${type}" data-remark="${remark}">
	// 				<td>${type}</td>
	// 				<td>
	// 					<input type="file" class="form-control supplier-file" style="display:none">
	// 					<span>${file.name}</span>
	// 				</td>
	// 				<td>${remark || "-"}</td>
	// 				<td><button type="button" class="btn btn-sm btn-danger remove-row">Remove</button></td>
	// 			</tr>`;


	// 		// Append to table
	// 		$("#supplier-attachments-body").append(row);

	// 		// Add hidden file input (clone) to preserve file object
	// 		const lastRow = $("#supplier-attachments-body tr:last");
	// 		const hiddenInput = lastRow.find(".supplier-file")[0];
	// 		const dataTransfer = new DataTransfer();
	// 		dataTransfer.items.add(file);
	// 		hiddenInput.files = dataTransfer.files;

	// 		$("#attachmentModal").modal("hide");
	// 	});

	// 	// Remove attachment row
	// 	$(document).on("click", ".remove-row", function () {
	// 		$(this).closest("tr").remove();
	// 	});
	// }


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



	// submit_rfq(){
	// 	$('.btn-sm').click(function(){
	// 		frappe.freeze();
	// 		frappe.call({
	// 			type: "POST",
	// 			method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.create_supplier_quotation",
	// 			args: {
	// 				doc: doc
	// 			},
	// 			btn: this,
	// 			callback: function(r){
	// 				frappe.unfreeze();
	// 				if(r.message){
	// 					$('.btn-sm').hide()
	// 					window.location.href = "/supplier-quotations/" + encodeURIComponent(r.message);
	// 				}
	// 			}
	// 		})
	// 	})
	// }

	submit_rfq(){
		$('.btn-primary').click(function(){  // "Make Quotation" button
			frappe.freeze();

			// Step 1: Create quotation
			frappe.call({
				type: "POST",
				method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.create_supplier_quotation",
				args: { doc: doc },
				btn: this,
				callback: function(r){
					frappe.unfreeze();
					if(r.message){
						const quotation_name = r.message;

						// Step 2: Add attachments after quotation is created
						let attachments = [];
						
						$('#supplier-attachments-body tr').each(function(){
							const type = $(this).data('type') || "";
							const file_input = $(this).find('.supplier-file')[0];
							const remark = $(this).data('remark') || "";

							if(file_input && file_input.files.length > 0){
								attachments.push({
									attachment_type: type,
									file: file_input.files[0],
									remark: remark
								});
							}
						});


						if(attachments.length > 0){
							add_attachments_to_quotation(quotation_name, attachments);
						} else {
							// No attachments, just redirect
							window.location.href = "/supplier-quotations/" + encodeURIComponent(quotation_name);
						}
					}
				}
			})
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

