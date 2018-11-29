from frappe import _


def get_data():
	return {
		'fieldname': 'purchase_invoice',
		'non_standard_fieldnames': {
			'Journal Entry': 'reference_name',
			'Payment Entry': 'reference_name',
			# 'Payment Request': 'reference_name',
			'Landed Cost Voucher': 'receipt_document',
			# 'Purchase Invoice': 'return_against',
			'Auto Repeat': 'reference_document'
		},
		'transactions': [
			{
				'label': _('Payment'),
				'items': ['Payment Entry', 'Journal Entry']
			},
			{
				'label': _('Subscription'),
				'items': ['Auto Repeat']
			},
			{
				'label': _('Costing'),
				'items': ['Landed Cost Voucher']
			},
		]
	}
