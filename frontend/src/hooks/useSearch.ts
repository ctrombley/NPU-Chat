import { useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api';

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ inputText, sessionId }: { inputText: string; sessionId?: string }) =>
      api.sendMessage(inputText, sessionId),
    onSuccess: (_data, variables) => {
      if (variables.sessionId) {
        queryClient.invalidateQueries({ queryKey: ['messages', variables.sessionId] });
      }
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });
}
