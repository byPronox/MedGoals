import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

const ODOO_URL = (process.env.ODOO_URL || '').replace(/\/+$/, '');
const SESSION_COOKIE = process.env.SESSION_COOKIE_NAME || 'session_id';

export async function odooJsonApi(path: string, payload: any = {}) {
  const cookieStore = await cookies();
  const session = cookieStore.get(SESSION_COOKIE);

  if (!session) {
    redirect('/login');
  }

  const url = `${ODOO_URL}${path}`;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: `${SESSION_COOKIE}=${session.value}`,
      },
      body: JSON.stringify(payload || {}),
      cache: 'no-store',
    });

    if (!res.ok) {
      return { status: 'error', message: `Odoo error ${res.status}` };
    }
    
    const data = await res.json();
    if (data.error && data.error.data && data.error.data.name === 'odoo.http.SessionExpiredException') {
        redirect('/login');
    }

    return data;
  } catch (e) {
    if ((e as any)?.digest?.startsWith('NEXT_REDIRECT')) {
        throw e;
    }
    return { status: 'error', message: 'Network error' };
  }
}

// --- Interfaces ---

interface OdooRelation {
  id: number;
  display_name: string;
}

export interface Area {
  id: number;
  name: string;
  code: string;
}

export interface Specialty {
  id: number;
  name: string;
  code: string;
  area?: { id: number; name: string }; 
}

export interface Employee {
  id: number;
  name: string;
  job_title: string | false;
  work_email: string | false;
  mobile_phone: string | false;
  department_id: OdooRelation | false; 
  avatar_128?: string;
  med_area_id?: OdooRelation | false; 
  med_specialty_id?: OdooRelation | false;
}

export interface EmployeeDetail {
  id: number;
  name: string;
  job_title: string | false;
  work_email: string | false;
  work_phone: string | false;
  mobile_phone: string | false;
  avatar_128?: string;
  department_id: OdooRelation | false;
  parent_id: OdooRelation | false;
  coach_id: OdooRelation | false;
  company_id: OdooRelation | false;
  private_email: string | false;
  private_phone: string | false;
  gender: string | false;
  birthday: string | false;
  marital: string | false;
  address_id: OdooRelation | false;
  resume_line_ids: any[];
  employee_skill_ids: any[];
  goal_assignment_ids: any[];
}

export interface EmployeeRanking {
  id: number;
  name: string;
  job_title: string | false;
  avatar_128?: string;
  med_area_id: { id: number; display_name: string } | false;
  med_specialty_id: { id: number; display_name: string } | false;
  last_score: number;
  rank_area: number;
  rank_specialty: number;
  is_top_performer: boolean;
  employee_score_ids: {
    id: number;
    score_economic: number;
    score_productivity: number;
    cycle_id: { display_name: string };
  }[];
}

export interface CycleInfo {
  id: number;
  name: string;
  state: string;
  date_start: string;
  date_end: string;
}

export interface MyGoalsResponse {
  status: 'ok' | 'error';
  employee_id?: number;
  records?: any[];
}
export interface MedGoalsEmployeeResponse {
    status: 'ok' | 'error';
    employee?: any; 
    score_history?: any[];
}
export interface DashboardResponse {
    status: 'ok' | 'error';
    employee: any;
    last_cycle: any;
    my_score: any;
    top_performers: any[];
}


// --- ENDPOINTS ---

export async function getAreas(): Promise<Area[]> {
  const response = await odooJsonApi('/med_goals/api/areas', {
    jsonrpc: '2.0',
    method: 'call',
    params: {},
  });
  if (response.result && response.result.status === 'ok') {
    return response.result.records as Area[];
  }
  return [];
}

export async function getSpecialties(areaId?: number): Promise<Specialty[]> {
  const params: any = {};
  if (areaId) params.area_id = areaId;

  const response = await odooJsonApi('/med_goals/api/specialties', {
    jsonrpc: '2.0',
    method: 'call',
    params: params,
  });
  if (response.result && response.result.status === 'ok') {
    return response.result.records as Specialty[];
  }
  return [];
}

export async function getEmployees(filters?: { area_id?: number; specialty_id?: number }): Promise<Employee[]> {
  const specification = {
    name: {},
    job_title: {},
    work_email: {},
    mobile_phone: {},
    department_id: { fields: { display_name: {} } },
    avatar_128: {},
    med_area_id: { fields: { display_name: {} } },
    med_specialty_id: { fields: { display_name: {} } },
  };

  const domain: any[] = [];
  if (filters?.area_id) {
    domain.push(['med_area_id', '=', filters.area_id]);
  }
  if (filters?.specialty_id) {
    domain.push(['med_specialty_id', '=', filters.specialty_id]);
  }

  const response = await odooJsonApi('/web/dataset/call_kw/hr.employee/web_search_read', {
    jsonrpc: '2.0',
    method: 'call',
    params: {
      model: 'hr.employee',
      method: 'web_search_read',
      args: [], 
      kwargs: {
        limit: 80,
        offset: 0,
        order: "name asc",
        domain: domain,
        specification: specification,
        context: { lang: "es_ES", bin_size: false } 
      },
    },
  });

  if (response.result && response.result.records) {
    return response.result.records as Employee[];
  }
  return [];
}

export async function getEmployeeDetail(id: number): Promise<EmployeeDetail | null> {
    const specification = {
        active: {},
        user_id: { fields: { display_name: {} } },
        image_128: {},
        company_id: { fields: { display_name: {} } },
        work_contact_id: { fields: {} },
        avatar_128: {},
        name: {},
        job_title: {},
        category_ids: { fields: { display_name: {}, color: {} } },
        mobile_phone: {},
        work_phone: {},
        work_email: {},
        department_id: { fields: { display_name: {} } },
        job_id: { fields: { display_name: {} } },
        parent_id: { fields: { display_name: {} } },
        coach_id: { fields: { display_name: {} } },
        resume_line_ids: {fields: {line_type_id: { fields: { display_name: {} } },name: {},description: {},date_start: {},date_end: {},display_type: {}},limit: 40,order: ""},
        employee_skill_ids: {fields: {skill_id: { fields: { display_name: {} } },skill_level_id: { fields: { display_name: {} } },level_progress: {},skill_type_id: { fields: { display_name: {} } }},limit: 40,order: ""},
        address_id: { fields: { display_name: {} } },
        work_location_id: { fields: { display_name: {} } },
        private_email: {},
        private_phone: {},
        marital: {},
        gender: {},
        birthday: {},
        goal_assignment_ids: {fields: {goal_id: { fields: { display_name: {} } },target_value: {},actual_value: {},completion_rate: {},state: {}},limit: 40}
      };
    
      const response = await odooJsonApi('/web/dataset/call_kw/hr.employee/web_read', {
        jsonrpc: '2.0',
        method: 'call',
        params: {
          model: 'hr.employee',
          method: 'web_read',
          args: [[id]], 
          kwargs: {
            specification: specification,
            context: { lang: "es_ES", bin_size: false } 
          },
        },
      });
    
      if (response.result && response.result.length > 0) {
        return response.result[0] as EmployeeDetail;
      }
      return null;
}

export async function getRankings(areaId?: number): Promise<EmployeeRanking[]> {
  const specification = {
    name: {},
    job_title: {},
    avatar_128: {},
    med_area_id: { fields: { display_name: {} } },
    med_specialty_id: { fields: { display_name: {} } },
    last_score: {},
    rank_area: {},
    rank_specialty: {},
    is_top_performer: {},
    employee_score_ids: {
      fields: {
        score_economic: {},
        score_productivity: {},
        cycle_id: { fields: { display_name: {} } }
      },
      limit: 1, 
      order: "create_date desc"
    }
  };

  const domain: any[] = [];
  if (areaId) {
    domain.push(['med_area_id', '=', areaId]);
  }

  const response = await odooJsonApi('/web/dataset/call_kw/hr.employee/web_search_read', {
    jsonrpc: '2.0',
    method: 'call',
    params: {
      model: 'hr.employee',
      method: 'web_search_read',
      args: [], 
      kwargs: {
        domain: domain, 
        limit: 100, 
        order: "last_score desc",
        specification: specification,
        context: { lang: "es_ES", bin_size: false } 
      },
    },
  });

  if (response.result && response.result.records) {
    return response.result.records as EmployeeRanking[];
  }
  
  return [];
}

export async function getRankingCycleInfo(): Promise<CycleInfo | null> {
    const response = await odooJsonApi('/med_goals/api/top_performers', {jsonrpc: '2.0',method: 'call',params: {limit: 1},});
    if (response.result && response.result.status === 'ok') {return response.result.cycle as CycleInfo;}
    return null;
}
export async function getMyGoals(filters?: { cycle_id?: number; state?: string }): Promise<MyGoalsResponse> {
    const response = await odooJsonApi('/med_goals/api/my-goals', {jsonrpc: '2.0',method: 'call',params: {...(filters || {})},});
    if (response.result) {return response.result as MyGoalsResponse;}
    return { status: 'error', message: 'Failed to fetch goals' };
}
export async function getMedGoalsEmployeeDetail(id: number): Promise<MedGoalsEmployeeResponse> {
    const response = await odooJsonApi(`/med_goals/api/employees/${id}`, {jsonrpc: '2.0',method: 'call',params: {}, });
    if (response.result) {return response.result as MedGoalsEmployeeResponse;}
    return { status: 'error', message: 'Failed to fetch extended details' };
}
export async function getCurrentUserProfile() {
    const goalsData = await getMyGoals();
    if (goalsData.status === 'ok' && goalsData.employee_id) {
      const fullProfile = await getEmployeeDetail(goalsData.employee_id);
      return fullProfile;
    }
    return null;
}
export async function getDashboardData(): Promise<DashboardResponse | null> {
    const response = await odooJsonApi('/med_goals/api/dashboard', {jsonrpc: '2.0',method: 'call',params: {},});
    if (response.result && response.result.status === 'ok') {return response.result as DashboardResponse;}
    return null;
}
export interface PerformanceLog {id: number;name: string;date: string;metric_value: number;notes: string;employee: { id: number; name: string } | null;assignment: { id: number; name: string } | null;}
export async function getPerformanceLogs(filters?: { employee_id?: number; assignment_id?: number }): Promise<PerformanceLog[]> {
    const response = await odooJsonApi('/med_goals/api/performance_logs', {jsonrpc: '2.0',method: 'call',params: {...(filters || {})},});
    if (response.result && response.result.status === 'ok') {return response.result.records as PerformanceLog[];}
    return [];
}