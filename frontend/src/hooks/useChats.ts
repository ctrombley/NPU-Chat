import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api';

export function useChats() {
  return useQuery({
    queryKey: ['chats'],
    queryFn: api.listChats,
  });
}

export function useCreateChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (opts?: { name?: string; templateId?: string } | string | void) => {
      if (typeof opts === 'string') return api.createChat(opts);
      if (opts && typeof opts === 'object') return api.createChat(opts.name, opts.templateId);
      return api.createChat();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });
}

export function useDeleteChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (chatId: string) => api.deleteChat(chatId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ chatId, isFavorite }: { chatId: string; isFavorite: boolean }) =>
      api.updateChat(chatId, { is_favorite: isFavorite }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });
}
