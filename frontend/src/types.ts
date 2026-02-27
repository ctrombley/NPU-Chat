export interface Message {
  type: 'sent' | 'received';
  text: string;
  timestamp: number;
}

export interface Chat {
  id: string;
  name?: string;
  emoji?: string;
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

