from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError


def _ensure_group(group_xmlid):
    """Pequeño helper para restringir endpoints."""
    if not request.env.user.has_group(group_xmlid):
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
        _ensure_group("med_goals.group_med_goals_user")

        Employee = request.env["hr.employee"].sudo()
        Score = request.env["med.employee.score"].sudo()

        employee = Employee.browse(employee_id)
        if not employee.exists():
            return {"status": "error", "message": "Employee not found"}

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
    # 3) LISTA DE CICLOS Y SCOREBOARD
    # =========================================================
    @http.route(
        "/med_goals/api/evaluation_cycles",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_evaluation_cycles(self, **payload):
        _ensure_group("med_goals.group_med_goals_user")

        state = payload.get("state")
        domain = [("company_id", "in", request.env.user.company_ids.ids)]
        if state:
            domain.append(("state", "=", state))

        cycles = request.env["med.evaluation.cycle"].sudo().search_read(
            domain,
            fields=["id", "name", "date_start", "date_end", "state"],
            order="date_start desc",
        )

        return {"status": "ok", "records": cycles}

    @http.route(
        "/med_goals/api/evaluation_cycles/<int:cycle_id>/scores",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_cycle_scores(self, cycle_id, **payload):
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

        scores = Score.search_read(
            domain,
            fields=[
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
            ],
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

        return {"status": "ok", "count": total, "records": scores}


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
        Devuelve Top Performers del CICLO ABIERTO ACTUAL (Prioridad)
        o del último ciclo cerrado si no hay abierto.
        """
        _ensure_group("med_goals.group_med_goals_user")

        limit = payload.get("limit", 10)
        cycle_id = payload.get("cycle_id")

        Cycle = request.env["med.evaluation.cycle"].sudo()
        Score = request.env["med.employee.score"].sudo()

        if cycle_id:
            cycle = Cycle.browse(cycle_id)
        else:
            # CAMBIO PRINCIPAL: Priorizar 'open', si no hay 'open', buscar 'closed'
            cycle = Cycle.search(
                [("state", "=", "open"), ("company_id", "in", request.env.user.company_ids.ids)],
                limit=1,
                order="date_start desc",
            )
            # Fallback opcional: si no hay abierto, traer el último cerrado
            if not cycle:
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
                "message": "No active or closed evaluation cycle found.",
            }

        # NOTA: Para ciclos abiertos, los scores pueden estar vacíos si no se ha ejecutado
        # el cálculo. Asegúrate de tener un Cron o calcularlos dinámicamente si es necesario.
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
    @http.route("/med_goals/api/areas", type="json", auth="user", methods=["POST"], csrf=False)
    def get_areas(self, **payload):
        _ensure_group("med_goals.group_med_goals_user")
        Area = request.env["med.area"].sudo()
        areas = Area.search_read(
            [("company_id", "in", request.env.user.company_ids.ids)],
            fields=["id", "name", "code", "description"],
            order="name asc",
        )
        return {"status": "ok", "records": areas}

    @http.route("/med_goals/api/specialties", type="json", auth="user", methods=["POST"], csrf=False)
    def get_specialties(self, **payload):
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
    # 6) PERFORMANCE LOGS
    # =========================================================
    @http.route("/med_goals/api/performance_logs", type="json", auth="user", methods=["POST"], csrf=False)
    def list_performance_logs(self, **payload):
        """
        Modificado: Devuelve el historial de Scores (med.employee.score) 
        para poblar la tabla de 'Activity Logs' con evaluaciones en lugar de logs técnicos.
        """
        _ensure_group("med_goals.group_med_goals_user")
        domain = [("company_id", "in", request.env.user.company_ids.ids)]
        
        if payload.get("employee_id"):
            domain.append(("employee_id", "=", payload.get("employee_id")))
        
        # Nota: assignment_id no aplica a scores globales, se ignora si viene en payload
        
        scores = request.env["med.employee.score"].sudo().search_read(
            domain,
            fields=[
                "id", 
                "employee_id", 
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
                "create_date"
            ],
            order="create_date desc, id desc",
        )
        
        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None
            
        for s in scores:
            s["employee"] = m2o(s.pop("employee_id"))
            s["cycle"] = m2o(s.pop("cycle_id"))
            # FIX: Mapear campos para compatibilidad con Frontend (Charts.tsx)
            s["date"] = s["create_date"] 
            # Generar un nombre para que no salga vacío en la tabla
            cycle_name = s["cycle"]["name"] if s["cycle"] else "General"
            s["name"] = f"Evaluación: {cycle_name}"
            
        return {"status": "ok", "records": scores}

    @http.route("/med_goals/api/performance_logs/create", type="json", auth="user", methods=["POST"], csrf=False)
    def create_performance_log(self, **payload):
        _ensure_group("med_goals.group_med_goals_user")
        if not payload.get("employee_id") or not payload.get("name"):
            return {"status": "error", "message": "Missing required fields"}
        
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
    # 7) GOAL ASSIGNMENTS
    # =========================================================
    @http.route("/med_goals/api/goal_assignments", type="json", auth="user", methods=["POST"], csrf=False)
    def list_goal_assignments(self, **payload):
        _ensure_group("med_goals.group_med_goals_user")
        domain = [("company_id", "in", request.env.user.company_ids.ids)]
        if payload.get("employee_id"): domain.append(("employee_id", "=", payload.get("employee_id")))
        if payload.get("cycle_id"): domain.append(("evaluation_cycle_id", "=", payload.get("cycle_id")))
        if payload.get("state"): domain.append(("state", "=", payload.get("state")))

        assignments = request.env["med.goal.assignment"].sudo().search_read(
            domain,
            fields=["id", "name", "employee_id", "goal_id", "evaluation_cycle_id", "target_value", "actual_value", "completion_rate", "state"],
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
    # 8) MIS METAS
    # =========================================================
    @http.route("/med_goals/api/my-goals", type="json", auth="user", methods=["POST"], csrf=False)
    def get_my_goals(self, **payload):
        _ensure_group("med_goals.group_med_goals_user")
        employee = self._get_current_employee()
        if not employee: return {"status": "error", "message": "No employee found"}

        domain = [("company_id", "in", request.env.user.company_ids.ids), ("employee_id", "=", employee.id)]
        if payload.get("cycle_id"): domain.append(("evaluation_cycle_id", "=", payload.get("cycle_id")))
        if payload.get("state"): domain.append(("state", "=", payload.get("state")))

        assignments = request.env["med.goal.assignment"].sudo().search_read(
            domain,
            fields=["id", "name", "goal_id", "evaluation_cycle_id", "target_value", "actual_value", "completion_rate", "state"],
            order="evaluation_cycle_id desc, name",
        )
        def m2o(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return {"id": val[0], "name": val[1]}
            return None
        for a in assignments:
            a["goal"] = m2o(a.pop("goal_id"))
            a["cycle"] = m2o(a.pop("evaluation_cycle_id"))
        return {"status": "ok", "employee_id": employee.id, "employee_name": employee.name, "records": assignments}

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
        Resumen para el panel:
        - info de empleado
        - CICLO ACTUAL (ABIERTO) como prioridad
        - top performers del ciclo actual
        """
        _ensure_group("med_goals.group_med_goals_user")

        employee = self._get_current_employee()
        if not employee:
            return {"status": "error", "message": "No employee found"}

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

        # CAMBIO PRINCIPAL: Buscar 'open' en lugar de 'closed'
        last_cycle = Cycle.search(
            [
                ("state", "=", "open"), 
                ("company_id", "in", request.env.user.company_ids.ids),
            ],
            limit=1,
            order="date_start desc",
        )
        
        # Fallback si no hay abierto (opcional, si quieres que siempre muestre algo)
        if not last_cycle:
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
        top_records = []

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

            # Top performers del ciclo seleccionado (sea abierto o cerrado)
            top_scores = Score.search_read(
                [("cycle_id", "=", last_cycle.id)],
                fields=["employee_id", "score_total", "rank_global", "is_top_performer"],
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