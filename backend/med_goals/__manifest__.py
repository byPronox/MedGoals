{
    "name": "MED-GOALS",
    "summary": "Employee performance evaluation, goals, cycles and leaderboards.",
    "description": """
Performance Evaluation System (MED-GOALS)

Core module for performance evaluation integrated with Odoo HR.
It defines goals, assignments, performance logs, evaluation cycles,
scoring configuration and computed rankings / top performers per employee.
    """,
    "version": "17.0.1.0.0",
    "author": "Stefan Jativa & Justin Gomezcoello",
    "website": "https://example.com",
    "category": "Human Resources",
    "license": "LGPL-3",
    "depends": ["base", "hr", "hr_contract"],
    "data": [
        "security/med_goals_security.xml",
        "security/ir.model.access.csv",
        "views/med_menus.xml",
        "views/area_views.xml",
        "views/specialty_views.xml",
        "views/goal_definition_views.xml",
        "views/goal_assignment_views.xml",
        "views/performance_log_views.xml",
        "views/evaluation_cycle_views.xml",
        "views/employee_score_views.xml",
        "views/scoring_config_views.xml",
        "views/hr_employee_inherit_views.xml",
    ],
    "installable": True,
    "application": True,
}
