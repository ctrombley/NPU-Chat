import {
  Chat,
  ChatAttributes,
  ChatResponse,
  JsonApiDocument,
  JsonApiResource,
  Message,
  MessageAttributes,
  SearchResultAttributes,
  Sign,
  SignAttributes,
} from './types';

const JSONAPI_CONTENT_TYPE = 'application/vnd.api+json';

function unwrapResource<T>(resource: JsonApiResource<T>): T & { id: string } {
  return { id: resource.id, ...resource.attributes };
}

function unwrapCollection<T>(doc: JsonApiDocument<T>): (T & { id: string })[] {
  const data = doc.data;
  if (!Array.isArray(data)) return [unwrapResource(data)];
  return data.map(unwrapResource);
}

function wrapResource(type: string, attributes: Record<string, unknown>, id?: string) {
  const data: Record<string, unknown> = { type, attributes };
  if (id) data.id = id;
  return { data };
}

async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': JSONAPI_CONTENT_TYPE,
    ...(options.headers as Record<string, string> || {}),
  };
  return fetch(url, { ...options, headers });
}

// --- Chats ---

export async function listChats(): Promise<Chat[]> {
  const response = await apiFetch('/api/v1/chats');
  if (!response.ok) throw new Error('Failed to fetch chats');
  const doc: JsonApiDocument<ChatAttributes> = await response.json();
  return unwrapCollection(doc).map(c => ({
    id: c.id,
    name: c.name,
    emoji: c.emoji || '',
    sign_id: c.sign_id || 'default',
    is_favorite: c.is_favorite || false,
    metadata: c.metadata || {},
    goal: c.goal || '',
    messages: [],
  }));
}

export async function createChat(name?: string, signId?: string): Promise<Chat> {
  const attrs: Record<string, string> = {};
  if (name) attrs.name = name;
  if (signId) attrs.sign_id = signId;
  const response = await apiFetch('/api/v1/chats', {
    method: 'POST',
    body: JSON.stringify(wrapResource('chats', attrs)),
  });
  if (!response.ok) throw new Error('Failed to create chat');
  const doc: JsonApiDocument<ChatAttributes> = await response.json();
  const resource = Array.isArray(doc.data) ? doc.data[0] : doc.data;
  return {
    id: resource.id,
    name: resource.attributes.name,
    emoji: resource.attributes.emoji || '',
    sign_id: resource.attributes.sign_id || 'default',
    is_favorite: resource.attributes.is_favorite || false,
    metadata: resource.attributes.metadata || {},
    goal: resource.attributes.goal || '',
    messages: [],
  };
}

export async function updateChat(
  chatId: string,
  attrs: Partial<{ name: string; emoji: string; is_favorite: boolean; sign_id: string; metadata: Record<string, unknown>; goal: string }>
): Promise<void> {
  const response = await apiFetch(`/api/v1/chats/${chatId}`, {
    method: 'PATCH',
    body: JSON.stringify(wrapResource('chats', attrs, chatId)),
  });
  if (!response.ok) throw new Error('Failed to update chat');
}

export async function deleteChat(chatId: string): Promise<void> {
  const response = await apiFetch(`/api/v1/chats/${chatId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete chat');
}

export async function getChatMessages(chatId: string): Promise<Message[]> {
  const response = await apiFetch(`/api/v1/chats/${chatId}/messages`);
  if (!response.ok) throw new Error('Failed to fetch messages');
  const doc: JsonApiDocument<MessageAttributes> = await response.json();
  return unwrapCollection(doc).map(m => ({
    id: m.id,
    type: m.role === 'user' ? 'sent' as const : 'received' as const,
    text: m.content,
    timestamp: Date.now(),
  }));
}

export async function reviewChatMetadata(chatId: string, userMessage?: string): Promise<ChatUpdate | null> {
  const body = userMessage !== undefined ? JSON.stringify({ user_message: userMessage }) : undefined;
  const response = await apiFetch(`/api/v1/chats/${chatId}/review-metadata`, { method: 'POST', body });
  if (!response.ok) return null;
  const doc: JsonApiDocument<ChatAttributes> = await response.json();
  const resource = Array.isArray(doc.data) ? doc.data[0] : doc.data;
  return {
    name: resource.attributes.name,
    emoji: resource.attributes.emoji || '',
    metadata: resource.attributes.metadata || {},
    goal: resource.attributes.goal || '',
  };
}

// --- Signs ---

export async function listSigns(): Promise<Sign[]> {
  const response = await apiFetch('/api/v1/signs');
  if (!response.ok) throw new Error('Failed to fetch signs');
  const doc: JsonApiDocument<SignAttributes> = await response.json();
  return unwrapCollection(doc).map(s => ({
    id: s.id,
    name: s.name,
    prefix: s.prefix,
    postfix: s.postfix,
    values: s.values,
    interests: s.interests,
    default_goal: s.default_goal || '',
    aspects: s.aspects,
  }));
}

export async function createSign(
  name: string, prefix: string, postfix: string,
  opts?: { values?: string; interests?: string; default_goal?: string; aspects?: string }
): Promise<void> {
  const attrs: Record<string, string> = { name, prefix, postfix };
  if (opts?.values) attrs.values = opts.values;
  if (opts?.interests) attrs.interests = opts.interests;
  if (opts?.default_goal) attrs.default_goal = opts.default_goal;
  if (opts?.aspects) attrs.aspects = opts.aspects;
  const response = await apiFetch('/api/v1/signs', {
    method: 'POST',
    body: JSON.stringify(wrapResource('signs', attrs)),
  });
  if (!response.ok) throw new Error('Failed to create sign');
}

export async function updateSign(
  signId: string,
  attrs: Partial<{ name: string; prefix: string; postfix: string; values: string; interests: string; default_goal: string; aspects: string }>
): Promise<void> {
  const response = await apiFetch(`/api/v1/signs/${signId}`, {
    method: 'PATCH',
    body: JSON.stringify(wrapResource('signs', attrs, signId)),
  });
  if (!response.ok) throw new Error('Failed to update sign');
}

export async function cloneSign(signId: string): Promise<Sign> {
  const response = await apiFetch(`/api/v1/signs/${signId}/clone`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
  if (!response.ok) throw new Error('Failed to clone sign');
  const doc: JsonApiDocument<SignAttributes> = await response.json();
  const resource = Array.isArray(doc.data) ? doc.data[0] : doc.data;
  return {
    id: resource.id,
    name: resource.attributes.name,
    prefix: resource.attributes.prefix,
    postfix: resource.attributes.postfix,
    values: resource.attributes.values,
    interests: resource.attributes.interests,
    default_goal: resource.attributes.default_goal || '',
    aspects: resource.attributes.aspects,
  };
}

export async function deleteSign(signId: string): Promise<void> {
  const response = await apiFetch(`/api/v1/signs/${signId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete sign');
}

// --- Search ---

export async function sendMessage(inputText: string, sessionId?: string): Promise<ChatResponse> {
  const attrs: Record<string, string> = { input_text: inputText };
  if (sessionId) attrs.session_id = sessionId;

  const response = await apiFetch('/api/v1/search', {
    method: 'POST',
    body: JSON.stringify(wrapResource('search-requests', attrs)),
  });
  if (!response.ok) throw new Error('Failed to send message');
  const doc: JsonApiDocument<SearchResultAttributes> = await response.json();
  const resource = Array.isArray(doc.data) ? doc.data[0] : doc.data;
  return {
    content: resource.attributes.content,
    session_id: resource.attributes.session_id,
  };
}

export interface ChatUpdate {
  name: string;
  emoji: string;
  metadata?: Record<string, unknown>;
  goal?: string;
}

export async function sendMessageStream(
  inputText: string,
  sessionId: string,
  onChunk: (chunk: string) => void,
  onDone: (sessionId: string) => void,
): Promise<void> {
  const attrs: Record<string, string> = { input_text: inputText, session_id: sessionId };

  const response = await apiFetch('/api/v1/search/stream', {
    method: 'POST',
    body: JSON.stringify(wrapResource('search-requests', attrs)),
  });

  if (!response.ok) throw new Error('Failed to send message');
  if (!response.body) throw new Error('No response body for streaming');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE lines from buffer
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const jsonStr = line.slice(6);
      try {
        const event = JSON.parse(jsonStr);
        if (event.done) {
          onDone(event.session_id);
          return;
        }
        if (event.chunk) {
          onChunk(event.chunk);
        }
      } catch {
        // Skip malformed events
      }
    }
  }
}
