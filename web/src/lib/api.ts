const API_BASE = '/api';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const isForm = typeof FormData !== 'undefined' && init.body instanceof FormData;
  if (!isForm && init.body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers, credentials: 'include' });
  if (res.status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/register')) {
    window.dispatchEvent(new Event('ragged:unauthorized'));
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(res.status, typeof body.detail === 'string' ? body.detail : 'Request failed');
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

const get = <T>(p: string) => request<T>(p);
const post = <T>(p: string, body?: unknown) =>
  request<T>(p, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });
const del = <T>(p: string) => request<T>(p, { method: 'DELETE' });

function postForm<T>(p: string, files: File[]): Promise<T> {
  const fd = new FormData();
  files.forEach((f) => fd.append('files', f));
  return request<T>(p, { method: 'POST', body: fd });
}

export type Source = {
  chunk_id: string;
  document_id: string;
  file_name: string;
  content: string;
  similarity: number;
};
export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources: Source[];
};
export type CreateMessageResponse = { user_message: Message; assistant_message: Message };

export const api = {
  auth: {
    register: (email: string, password: string) => post('/auth/register', { email, password }),
    login: (email: string, password: string) => post('/auth/login', { email, password }),
    logout: () => post('/auth/logout'),
    me: () => get('/auth/me'),
  },
  threads: {
    list: (includeArchived = false) =>
      get(`/threads${includeArchived ? '?include_archived=true' : ''}`),
    create: (title: string) => post('/threads', { title }),
    archive: (id: string) => post(`/threads/${id}/archive`),
    restore: (id: string) => post(`/threads/${id}/restore`),
    delete: (id: string) => del(`/threads/${id}`),
  },
  documents: {
    list: (threadId: string) => get(`/threads/${threadId}/documents`),
    get: (threadId: string, docId: string) => get(`/threads/${threadId}/documents/${docId}`),
    upload: (threadId: string, files: File[]) => postForm(`/threads/${threadId}/documents`, files),
  },
  messages: {
    list: (threadId: string) => get<Message[]>(`/threads/${threadId}/messages`),
    create: (threadId: string, content: string) =>
      post<CreateMessageResponse>(`/threads/${threadId}/messages`, { content }),
  },
};
