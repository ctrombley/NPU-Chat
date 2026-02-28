import { useQuery } from '@tanstack/react-query';
import * as api from '../api';

export function useMessages(chatId: string | null) {
  return useQuery({
    queryKey: ['messages', chatId],
    queryFn: () => api.getChatMessages(chatId!),
    enabled: !!chatId,
  });
}
