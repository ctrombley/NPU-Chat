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
  sign_id?: string;
  is_favorite?: boolean;
  metadata?: Record<string, unknown>;
  goal?: string;
  messages: Message[];
}

export interface AspectSchema {
  description: string;
  initial: number;
  min: number;
  max: number;
}

export interface Sign {
  id: string;
  name: string;
  prefix: string;
  postfix: string;
  values?: unknown;
  interests?: unknown;
  default_goal?: string;
  aspects?: Record<string, AspectSchema> | null;
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
  sign_id: string;
  is_favorite: boolean;
  message_count: number;
  created_at: number | null;
  metadata?: Record<string, unknown>;
  goal?: string;
}

export interface MessageAttributes {
  role: string;
  content: string;
}

export interface SignAttributes {
  name: string;
  prefix: string;
  postfix: string;
  values?: unknown;
  interests?: unknown;
  default_goal?: string;
  aspects?: Record<string, AspectSchema> | null;
}

export interface SearchResultAttributes {
  content: string;
  session_id: string;
}
