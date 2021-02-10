# -*- coding: utf-8 -*-
{
    'name': "amgenevent",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Neftalí Michelet",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'event', 'event_sale', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/config_settings_views.xml',
        'views/partner_views.xml',
        'views/event_templates.xml',
        'views/event_views.xml',
        'views/purchase_views.xml',
        'report/event_event_templates.xml',
        'report/event_event_reports.xml',
        'data/initial_data.xml',
        'data/email_template_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
