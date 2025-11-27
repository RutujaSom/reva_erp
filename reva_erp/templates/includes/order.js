// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

window.doc={{ doc.as_json() }};

$(document).ready(function() {
	new po();
});

po = class po {
	al
	constructor(){
		this.po_pdf(); 
	}
	


	po_pdf(){
		$('.download-po').click(function () {
		let purchase_order_name = "{{ doc.name }}";

		frappe.call({
			method: "reva_erp.api.po_pdf.download_po_pdf",
			args: { purchase_order_name },
			callback: function(r) {
				if (r.message) {
					window.location.href = r.message;
				} else {
					frappe.msgprint("Failed to download Purchase Order");
				}
			}
		});
	})};



	navigate_quotations() {
		$('.quotations').click(function(){
			name = $(this).attr('idx')
			window.location.href = "/quotations/" + encodeURIComponent(name);
		})
	}
}

