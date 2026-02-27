export interface Message {
  type: 'sent' | 'received';
  text: string;
  timestamp: number;
}

export interface Chat {
  id: string;
  name?: string;
  emoji?: string;
  is_favorite?: boolean;
  messages: Message[];
}

export interface Template {
  id: string;
  name: string;
  prefix: string;
  postfix: string;
}

export interface ChatResponse {
  content: string;
  session_id?: string;
}

// JSON:API envelope types
export interface JsonApiResource<T = Record<string, unknown>> {
  type: string;
  id: string;
  attributes: T;
}

export interface JsonApiDocument<T = Record<string, unknown>> {
  data: JsonApiResource<T> | JsonApiResource<T>[];
}

export interface JsonApiError {
  status: string;
  title: string;
  detail?: string;
}

export interface JsonApiErrorDocument {
  errors: JsonApiError[];
}
