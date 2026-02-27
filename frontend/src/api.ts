import { Chat, Message, Template, ChatResponse } from './types';

const JSONAPI_CONTENT_TYPE = 'application/vnd.api+json';

interface JsonApiResource<T = Record<string, unknown>> {
  type: string;
  id: string;
  attributes: T;
}

interface JsonApiDocument<T = Record<string, unknown>> {
  data: JsonApiResource<T> | JsonApiResource<T>[];
}

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
  const response = await apiFetch('/api/chats');
  if (!response.ok) throw new Error('Failed to fetch chats');
  const doc: JsonApiDocument = await response.json();
  return unwrapCollection(doc).map(c => ({
    id: c.id,
    name: c.name as string,
    emoji: (c.emoji as string) || '',
    is_favorite: (c.is_favorite as boolean) || false,
    messages: [],
  }));
}

export async function createChat(name: string): Promise<Chat> {
  const response = await apiFetch('/api/chats', {
    method: 'POST',
    body: JSON.stringify(wrapResource('chats', { name })),
  });
  if (!response.ok) throw new Error('Failed to create chat');
  const doc: JsonApiDocument = await response.json();
  const resource = Array.isArray(doc.data) ? doc.data[0] : doc.data;
  return {
    id: resource.id,
    name: resource.attributes.name as string,
    emoji: (resource.attributes.emoji as string) || '',
    is_favorite: (resource.attributes.is_favorite as boolean) || false,
    messages: [],
  };
}

export async function updateChat(
  chatId: string,
  attrs: Partial<{ name: string; emoji: string; is_favorite: boolean; template_id: string }>
): Promise<void> {
  const response = await apiFetch(`/api/chats/${chatId}`, {
    method: 'PATCH',
    body: JSON.stringify(wrapResource('chats', attrs, chatId)),
  });
  if (!response.ok) throw new Error('Failed to update chat');
}

export async function deleteChat(chatId: string): Promise<void> {
  const response = await apiFetch(`/api/chats/${chatId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete chat');
}

export async function getChatMessages(chatId: string): Promise<Message[]> {
  const response = await apiFetch(`/api/chats/${chatId}/messages`);
  if (!response.ok) throw new Error('Failed to fetch messages');
  const doc: JsonApiDocument = await response.json();
  return unwrapCollection(doc).map(m => ({
    type: (m.role as string) === 'user' ? 'sent' as const : 'received' as const,
    text: m.content as string,
    timestamp: Date.now(),
  }));
}

// --- Templates ---

export async function listTemplates(): Promise<Template[]> {
  const response = await apiFetch('/api/templates');
  if (!response.ok) throw new Error('Failed to fetch templates');
  const doc: JsonApiDocument = await response.json();
  return unwrapCollection(doc).map(t => ({
    id: t.id,
    name: t.name as string,
    prefix: t.prefix as string,
    postfix: t.postfix as string,
  }));
}

export async function createTemplate(name: string, prefix: string, postfix: string): Promise<void> {
  const response = await apiFetch('/api/templates', {
    method: 'POST',
    body: JSON.stringify(wrapResource('templates', { name, prefix, postfix })),
  });
  if (!response.ok) throw new Error('Failed to create template');
}

export async function updateTemplate(
  templateId: string,
  attrs: Partial<{ name: string; prefix: string; postfix: string }>
): Promise<void> {
  const response = await apiFetch(`/api/templates/${templateId}`, {
    method: 'PATCH',
    body: JSON.stringify(wrapResource('templates', attrs, templateId)),
  });
  if (!response.ok) throw new Error('Failed to update template');
}

export async function deleteTemplate(templateId: string): Promise<void> {
  const response = await apiFetch(`/api/templates/${templateId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete template');
}

// --- Search ---

export async function sendMessage(inputText: string, sessionId?: string): Promise<ChatResponse> {
  const attrs: Record<string, string> = { input_text: inputText };
  if (sessionId) attrs.session_id = sessionId;

  const response = await apiFetch('/api/search', {
    method: 'POST',
    body: JSON.stringify(wrapResource('search-requests', attrs)),
  });
  if (!response.ok) throw new Error('Failed to send message');
  const doc: JsonApiDocument = await response.json();
  const resource = Array.isArray(doc.data) ? doc.data[0] : doc.data;
  return {
    content: resource.attributes.content as string,
    session_id: resource.attributes.session_id as string,
  };
}
