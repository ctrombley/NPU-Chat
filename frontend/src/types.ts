export interface Message {
  id?: string;
  type: 'sent' | 'received';
  text: string;
  timestamp: number;
  isTyping?: boolean;
}

export interface Chat {
  id: string;
  name?: string;
  emoji?: string;
  template_id?: string;
  is_favorite?: boolean;
  metadata?: Record<string, unknown>;
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

// Typed API attribute interfaces
export interface ChatAttributes {
  name: string;
  emoji: string;
  template_id: string;
  is_favorite: boolean;
  message_count: number;
  created_at: number | null;
  metadata?: Record<string, unknown>;
}

export interface MessageAttributes {
  role: string;
  content: string;
}

export interface TemplateAttributes {
  name: string;
  prefix: string;
  postfix: string;
}

export interface SearchResultAttributes {
  content: string;
  session_id: string;
}
