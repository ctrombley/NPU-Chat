import {
  Chat,
  ChatAttributes,
  ChatResponse,
  JsonApiDocument,
  JsonApiResource,
  Message,
  MessageAttributes,
  SearchResultAttributes,
  Template,
  TemplateAttributes,
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
    is_favorite: c.is_favorite || false,
    messages: [],
  }));
}

export async function createChat(name?: string): Promise<Chat> {
  const attrs: Record<string, string> = {};
  if (name) attrs.name = name;
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
    is_favorite: resource.attributes.is_favorite || false,
    messages: [],
  };
}

export async function updateChat(
  chatId: string,
  attrs: Partial<{ name: string; emoji: string; is_favorite: boolean; template_id: string }>
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

// --- Templates ---

export async function listTemplates(): Promise<Template[]> {
  const response = await apiFetch('/api/v1/templates');
  if (!response.ok) throw new Error('Failed to fetch templates');
  const doc: JsonApiDocument<TemplateAttributes> = await response.json();
  return unwrapCollection(doc).map(t => ({
    id: t.id,
    name: t.name,
    prefix: t.prefix,
    postfix: t.postfix,
  }));
}

export async function createTemplate(name: string, prefix: string, postfix: string): Promise<void> {
  const response = await apiFetch('/api/v1/templates', {
    method: 'POST',
    body: JSON.stringify(wrapResource('templates', { name, prefix, postfix })),
  });
  if (!response.ok) throw new Error('Failed to create template');
}

export async function updateTemplate(
  templateId: string,
  attrs: Partial<{ name: string; prefix: string; postfix: string }>
): Promise<void> {
  const response = await apiFetch(`/api/v1/templates/${templateId}`, {
    method: 'PATCH',
    body: JSON.stringify(wrapResource('templates', attrs, templateId)),
  });
  if (!response.ok) throw new Error('Failed to update template');
}

export async function deleteTemplate(templateId: string): Promise<void> {
  const response = await apiFetch(`/api/v1/templates/${templateId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete template');
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
