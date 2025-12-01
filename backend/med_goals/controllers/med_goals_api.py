# med_goals/controllers/med_goals_api.py

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError


def _ensure_group(group_xmlid):
    """Pequeño helper para restringir endpoints."""
    if not request.env.user.has_group(group_xmlid):
        # Lanzar error estándar de permisos
        raise AccessError(_("You do not have access to this resource."))


class MedGoalsApi(http.Controller):

    def _get_current_employee(self):
        """Devuelve el hr.employee vinculado al usuario actual."""
        Employee = request.env["hr.employee"].sudo()
        employee = Employee.search(
            [
                ("user_id", "=", request.env.user.id),
                ("company_id", "in", request.env.user.company_ids.ids),
            ],
            limit=1,
        )
        return employee
    

    # =========================================================
    # 2) DETALLE DE EMPLEADO + HISTORIAL DE SCORES
    # =========================================================
    @http.route(
        "/med_goals/api/employees/<int:employee_id>",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_employee_detail(self, employee_id, **payload):
        """
        Detalle de un empleado:
        - Información básica (sin datos sensibles privados)
        - Último score
        - Historial de scores por ciclo
        """
        _ensure_group("med_goals.group_med_goals_user")

        Employee = request.env["hr.employee"].sudo()
        Score = request.env["med.employee.score"].sudo()

        employee = Employee.browse(employee_id)
        if not employee.exists():
            return {"status": "error", "message": "Employee not found"}

        # ACL y record rules se respetan automáticamente por Odoo
        employee_info = employee.read(
            [
                "name",
                "job_title",
                "work_email",
                "work_phone",
                "med_area_id",
                "med_specialty_id",
                "last_score",
                "last_evaluation_date",
                "is_top_performer",
                "rank_area",
                "rank_specialty",
            ]
        )[0]

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        employee_info["med_area"] = m2o(employee_info.pop("med_area_id"))
        employee_info["med_specialty"] = m2o(employee_info.pop("med_specialty_id"))

        scores = Score.search_read(
            [("employee_id", "=", employee.id)],
            fields=[
                "id",
                "cycle_id",
                "score_total",
                "score_goals",
                "score_productivity",
                "score_quality",
                "score_economic",
                "rank_global",
                "rank_area",
                "rank_specialty",
                "is_top_performer",
                "create_date",
            ],
            order="create_date desc",
        )

        for s in scores:
            s["cycle"] = m2o(s.pop("cycle_id"))

        return {
            "status": "ok",
            "employee": employee_info,
            "score_history": scores,
        }

    # =========================================================
    # 3) LISTA DE CICLOS Y SCOREBOARD DE UN CICLO
    # =========================================================
    @http.route(
        "/med_goals/api/evaluation_cycles",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_evaluation_cycles(self, **payload):
        """
        Devuelve ciclos de evaluación (para filtros en el panel).
        Body:
        {
          "state": "closed" | "open" | "draft" | null
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        state = payload.get("state")
        domain = [("company_id", "in", request.env.user.company_ids.ids)]
        if state:
            domain.append(("state", "=", state))

        cycles = request.env["med.evaluation.cycle"].sudo().search_read(
            domain,
            fields=[
                "id",
                "name",
                "date_start",
                "date_end",
                "state",
            ],
            order="date_start desc",
        )

        return {
            "status": "ok",
            "records": cycles,
        }

    @http.route(
        "/med_goals/api/evaluation_cycles/<int:cycle_id>/scores",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_cycle_scores(self, cycle_id, **payload):
        """
        Scoreboard de un ciclo:
        - Por defecto ordena por score_total desc.
        Body opcional:
        {
          "area_id": 1,
          "specialty_id": 2,
          "limit": 100,
          "offset": 0
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        area_id = payload.get("area_id")
        specialty_id = payload.get("specialty_id")
        limit = payload.get("limit", 100)
        offset = payload.get("offset", 0)

        Score = request.env["med.employee.score"].sudo()

        domain = [("cycle_id", "=", cycle_id)]
        if area_id:
            domain.append(("employee_id.med_area_id", "=", area_id))
        if specialty_id:
            domain.append(("employee_id.med_specialty_id", "=", specialty_id))

        fields = [
            "employee_id",
            "score_total",
            "score_goals",
            "score_productivity",
            "score_quality",
            "score_economic",
            "rank_global",
            "rank_area",
            "rank_specialty",
            "is_top_performer",
        ]

        scores = Score.search_read(
            domain,
            fields=fields,
            limit=limit,
            offset=offset,
            order="score_total desc",
        )

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        for rec in scores:
            rec["employee"] = m2o(rec.pop("employee_id"))

        total = Score.search_count(domain)

        return {
            "status": "ok",
            "count": total,
            "records": scores,
        }


    # =========================================================
    # 4) TOP PERFORMERS / DREAM TEAMS
    # =========================================================
    @http.route(
        "/med_goals/api/top_performers",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_top_performers(self, **payload):
        """
        Devuelve Top Performers del último ciclo cerrado
        o del cycle_id indicado.

        Body opcional:
        {
          "cycle_id": 3,
          "limit": 10
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        limit = payload.get("limit", 10)
        cycle_id = payload.get("cycle_id")

        Cycle = request.env["med.evaluation.cycle"].sudo()
        Score = request.env["med.employee.score"].sudo()

        if cycle_id:
            cycle = Cycle.browse(cycle_id)
        else:
            cycle = Cycle.search(
                [("state", "=", "closed"), ("company_id", "in", request.env.user.company_ids.ids)],
                limit=1,
                order="date_end desc",
            )

        if not cycle:
            return {
                "status": "ok",
                "cycle": None,
                "records": [],
                "message": "No closed evaluation cycle found.",
            }

        scores = Score.search_read(
            [("cycle_id", "=", cycle.id)],
            fields=[
                "employee_id",
                "score_total",
                "rank_global",
                "rank_area",
                "rank_specialty",
                "is_top_performer",
            ],
            limit=limit,
            order="score_total desc",
        )

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        for rec in scores:
            rec["employee"] = m2o(rec.pop("employee_id"))

        cycle_info = cycle.read(["id", "name", "date_start", "date_end", "state"])[0]

        return {
            "status": "ok",
            "cycle": cycle_info,
            "records": scores,
        }

    # =========================================================
    # 5) ÁREAS Y ESPECIALIDADES
    # =========================================================
    @http.route(
        "/med_goals/api/areas",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_areas(self, **payload):
        """
        Lista de áreas (para filtros).
        """
        _ensure_group("med_goals.group_med_goals_user")

        Area = request.env["med.area"].sudo()
        areas = Area.search_read(
            [("company_id", "in", request.env.user.company_ids.ids)],
            fields=["id", "name", "code", "description"],
            order="name asc",
        )
        return {"status": "ok", "records": areas}

    @http.route(
        "/med_goals/api/specialties",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_specialties(self, **payload):
        """
        Lista de especialidades, opcionalmente filtradas por área.
        Body opcional:
        {
          "area_id": 1
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        area_id = payload.get("area_id")
        domain = [("company_id", "in", request.env.user.company_ids.ids)]
        if area_id:
            domain.append(("area_id", "=", area_id))

        Special = request.env["med.specialty"].sudo()
        specs = Special.search_read(
            domain,
            fields=["id", "name", "code", "area_id", "description"],
            order="area_id, name",
        )

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        for s in specs:
            s["area"] = m2o(s.pop("area_id"))

        return {"status": "ok", "records": specs}

    # =========================================================
    # 6) PERFORMANCE LOGS (CRUD SIMPLE PARA USUARIOS)
    # =========================================================
    @http.route(
        "/med_goals/api/performance_logs",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def list_performance_logs(self, **payload):
        """
        Lista logs de performance, normalmente para detalle de asignación.
        Body:
        {
          "employee_id": 6,        // opcional
          "assignment_id": 10      // opcional
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        domain = [("company_id", "in", request.env.user.company_ids.ids)]

        employee_id = payload.get("employee_id")
        assignment_id = payload.get("assignment_id")

        if employee_id:
            domain.append(("employee_id", "=", employee_id))
        if assignment_id:
            domain.append(("assignment_id", "=", assignment_id))

        logs = request.env["med.performance.log"].sudo().search_read(
            domain,
            fields=[
                "id",
                "name",
                "date",
                "employee_id",
                "assignment_id",
                "metric_value",
                "notes",
            ],
            order="date desc, id desc",
        )

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        for l in logs:
            l["employee"] = m2o(l.pop("employee_id"))
            l["assignment"] = m2o(l.pop("assignment_id"))

        return {"status": "ok", "records": logs}

    @http.route("/med_goals/api/performance_logs/create",type="json",auth="user",methods=["POST"],csrf=False,)
    def create_performance_log(self, **payload):
        """
        Crear un nuevo log de performance.
        ACL: med.performance.log.user tiene create y write.

        Body:
        {
          "employee_id": 6,
          "assignment_id": 10,
          "name": "Weekly update",
          "metric_value": 25,
          "notes": "Some explanation"
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        required = ["employee_id", "name"]
        for field in required:
            if not payload.get(field):
                return {"status": "error", "message": f"Missing field: {field}"}

        vals = {
            "name": payload["name"],
            "employee_id": payload["employee_id"],
            "assignment_id": payload.get("assignment_id"),
            "metric_value": payload.get("metric_value"),
            "notes": payload.get("notes"),
        }

        log = request.env["med.performance.log"].sudo().create(vals)

        return {"status": "ok", "id": log.id}

    # =========================================================
    # 7) GOAL ASSIGNMENTS (LECTURA / OPCIONAL CREATE)
    # =========================================================
    @http.route(
        "/med_goals/api/goal_assignments",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def list_goal_assignments(self, **payload):
        """
        Lista asignaciones de metas.

        Body:
        {
          "employee_id": 6,          // opcional
          "cycle_id": 3,            // opcional
          "state": "in_progress"    // opcional
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        domain = [("company_id", "in", request.env.user.company_ids.ids)]

        employee_id = payload.get("employee_id")
        cycle_id = payload.get("cycle_id")
        state = payload.get("state")

        if employee_id:
            domain.append(("employee_id", "=", employee_id))
        if cycle_id:
            domain.append(("evaluation_cycle_id", "=", cycle_id))
        if state:
            domain.append(("state", "=", state))

        Assign = request.env["med.goal.assignment"].sudo()

        assignments = Assign.search_read(
            domain,
            fields=[
                "id",
                "name",
                "employee_id",
                "goal_id",
                "evaluation_cycle_id",
                "target_value",
                "actual_value",
                "completion_rate",
                "state",
            ],
            order="evaluation_cycle_id desc, employee_id, name",
        )

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        for a in assignments:
            a["employee"] = m2o(a.pop("employee_id"))
            a["goal"] = m2o(a.pop("goal_id"))
            a["cycle"] = m2o(a.pop("evaluation_cycle_id"))

        return {"status": "ok", "records": assignments}
    
 
     # =========================================================
    # 8) MIS METAS (PORTAL / MY-GOALS)
    # =========================================================
    @http.route(
        "/med_goals/api/my-goals",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_my_goals(self, **payload):
        """
        Devuelve las metas asignadas al empleado vinculado al usuario actual.
        Body opcional:
        {
          "cycle_id": 1,
          "state": "in_progress" | "done" | "draft"
        }
        """
        _ensure_group("med_goals.group_med_goals_user")

        employee = self._get_current_employee()
        if not employee:
            return {
                "status": "error",
                "message": "No employee is linked to the current user.",
            }

        cycle_id = payload.get("cycle_id")
        state = payload.get("state")

        domain = [
            ("company_id", "in", request.env.user.company_ids.ids),
            ("employee_id", "=", employee.id),
        ]
        if cycle_id:
            domain.append(("evaluation_cycle_id", "=", cycle_id))
        if state:
            domain.append(("state", "=", state))

        Assign = request.env["med.goal.assignment"].sudo()
        assignments = Assign.search_read(
            domain,
            fields=[
                "id",
                "name",
                "goal_id",
                "evaluation_cycle_id",
                "target_value",
                "actual_value",
                "completion_rate",
                "state",
            ],
            order="evaluation_cycle_id desc, name",
        )

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        for a in assignments:
            a["goal"] = m2o(a.pop("goal_id"))
            a["cycle"] = m2o(a.pop("evaluation_cycle_id"))

        return {
            "status": "ok",
            "employee_id": employee.id,
            "employee_name": employee.name,
            "records": assignments,
        }

    # =========================================================
    # 9) DASHBOARD RESUMEN (PORTAL)
    # =========================================================
    @http.route(
        "/med_goals/api/dashboard",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_dashboard(self, **payload):
        """
        Resumen para el panel del usuario:
        - info de empleado
        - último score
        - ciclo actual/último cerrado
        - top performers global (solo resumen)
        """
        _ensure_group("med_goals.group_med_goals_user")

        employee = self._get_current_employee()
        if not employee:
            return {
                "status": "error",
                "message": "No employee is linked to the current user.",
            }

        # Info básica del empleado
        emp_vals = employee.read(
            [
                "name",
                "job_title",
                "work_email",
                "work_phone",
                "med_area_id",
                "med_specialty_id",
                "last_score",
                "last_evaluation_date",
                "is_top_performer",
                "rank_area",
                "rank_specialty",
            ]
        )[0]

        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None

        emp_vals["med_area"] = m2o(emp_vals.pop("med_area_id"))
        emp_vals["med_specialty"] = m2o(emp_vals.pop("med_specialty_id"))

        Cycle = request.env["med.evaluation.cycle"].sudo()
        Score = request.env["med.employee.score"].sudo()

        # Último ciclo cerrado
        last_cycle = Cycle.search(
            [
                ("state", "=", "closed"),
                ("company_id", "in", request.env.user.company_ids.ids),
            ],
            limit=1,
            order="date_end desc",
        )

        cycle_info = None
        my_score = None
        if last_cycle:
            cycle_info = last_cycle.read(
                ["id", "name", "date_start", "date_end", "state"]
            )[0]

            my_score_rec = Score.search(
                [("employee_id", "=", employee.id), ("cycle_id", "=", last_cycle.id)],
                limit=1,
            )
            if my_score_rec:
                my_score = my_score_rec.read(
                    [
                        "score_total",
                        "score_goals",
                        "score_productivity",
                        "score_quality",
                        "score_economic",
                        "rank_global",
                        "rank_area",
                        "rank_specialty",
                        "is_top_performer",
                    ]
                )[0]

        # Top performers globales del ciclo
        top_records = []
        if last_cycle:
            top_scores = Score.search_read(
                [("cycle_id", "=", last_cycle.id)],
                fields=[
                    "employee_id",
                    "score_total",
                    "rank_global",
                    "is_top_performer",
                ],
                order="score_total desc",
                limit=5,
            )
            for rec in top_scores:
                rec["employee"] = m2o(rec.pop("employee_id"))
                top_records.append(rec)

        return {
            "status": "ok",
            "employee": emp_vals,
            "last_cycle": cycle_info,
            "my_score": my_score,
            "top_performers": top_records,
        }