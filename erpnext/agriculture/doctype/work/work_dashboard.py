from frappe import _


def get_data():
	return {
		'fieldname': 'work_no',
		'non_standard_fieldnames': {},
		'internal_links': {},
		'transactions': [
			{
				'label': _('Stock'),
				'items': ['Stock Entry']
			}
		]
	}
