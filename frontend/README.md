# NPU-Chat Frontend

React 18 + TypeScript + Vite + Tailwind CSS frontend for NPU-Chat.

## Quick Start

```bash
npm install
npm run dev     # Vite dev server on http://localhost:5173
```

The dev server proxies `/api/*` requests to `http://localhost:5000` (Flask). Start the backend separately with `make run` from the project root.

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Type-check with `tsc`, then build to `../static/dist/` |
| `npm test` | Run Jest tests |
| `npm run lint` | Run ESLint |
| `npm run build-and-run` | Build frontend, then start Flask |

## Architecture

```
src/
├── main.tsx              # Entry point: StrictMode → ErrorBoundary → QueryClientProvider → App
├── App.tsx               # Root component, manages local UI state
├── api.ts                # JSON:API client (fetch wrappers)
├── types.ts              # TypeScript interfaces
├── index.css             # Tailwind directives, CSS custom properties, animations
├── hooks/
│   ├── useChats.ts       # Chat list query + create/delete/favorite mutations
│   ├── useMessages.ts    # Messages query (per chat)
│   └── useSearch.ts      # Send message mutation
├── components/
│   ├── ErrorBoundary.tsx  # Class component, catches render errors
│   ├── ChatList.tsx       # Sidebar chat list with inline creation
│   ├── ChatListItem.tsx   # Individual chat entry (favorite, delete)
│   ├── ChatMessages.tsx   # Scrollable message container, auto-scroll
│   ├── Message.tsx        # Message bubble with copy button
│   ├── MessageInput.tsx   # Auto-expanding textarea, Enter to send
│   ├── Templates.tsx      # Template CRUD sidebar
│   ├── TemplateListItem.tsx # Template entry with edit/delete
│   └── ui/               # Reusable primitives (CVA variants)
│       ├── Button.tsx     # Button + IconButton with variants
│       ├── Sidebar.tsx    # Fixed-width sidebar container
│       ├── ListItem.tsx   # Selectable list row with active state
│       └── MessageBubble.tsx # Sent/received message styling
├── lib/
│   └── utils.ts          # cn() — clsx + tailwind-merge helper
├── __tests__/            # Jest test files
├── test-utils.tsx        # Custom render with QueryClientProvider, mock factories
└── setupTests.ts         # Jest setup: DOM matchers, browser API mocks
```

## Data Flow

### Server State (TanStack Query)

All server data is managed through TanStack Query hooks. Components never call `fetch` directly.

```
useChats()          → GET  /api/v1/chats           → Chat[]
useMessages(id)     → GET  /api/v1/chats/:id/messages → Message[]
useCreateChat()     → POST /api/v1/chats           → invalidates ['chats']
useDeleteChat()     → DELETE /api/v1/chats/:id      → invalidates ['chats']
useToggleFavorite() → PATCH /api/v1/chats/:id       → invalidates ['chats']
useSendMessage()    → POST /api/v1/search           → invalidates ['chats', 'messages']
```

Query keys:
- `['chats']` — the chat list
- `['messages', chatId]` — messages for a specific chat

### Local State (App.tsx)

UI-only state stays in `useState`:
- `currentChatId` — which chat is selected
- `showTemplates` — templates view toggle
- `isCreatingChat` / `newChatName` — inline chat creation form
- `optimisticMessages` — user messages shown before server confirms

### API Client (api.ts)

All functions handle JSON:API envelope wrapping/unwrapping:

```typescript
// Unwrap: { data: { type, id, attributes } } → { id, ...attributes }
unwrapResource<T>(resource)
unwrapCollection<T>(doc)

// Wrap: { name: "foo" } → { data: { type: "chats", attributes: { name: "foo" } } }
wrapResource(type, attributes, id?)

// Fetch with JSON:API content type header
apiFetch(url, options?)
```

## Component API

### ChatList

```tsx
<ChatList
  chats={Chat[]}
  currentChatId={string | null}
  onNewChat={() => void}
  onSwitchChat={(chatId: string) => void}
  onDeleteChat={(chatId: string) => void}
  onToggleFavorite={(chatId: string, isFavorite: boolean) => void}
  onShowTemplates={() => void}
  isCreatingChat={boolean}           // show inline name input
  newChatName={string}
  onNewChatNameChange={(name: string) => void}
  onCreateChatSubmit={() => void}    // Enter or OK button
  onCreateChatCancel={() => void}    // Escape key
/>
```

### ChatMessages

```tsx
<ChatMessages messages={Message[]} />
```

Auto-scrolls to the bottom when `messages` changes via `useRef` + `useEffect`.

### MessageInput

```tsx
<MessageInput
  currentChatId={string | null}    // null disables the input
  onMessageSent={(text: string) => void}
  isLoading={boolean}              // shows spinner, disables input
/>
```

- Enter sends, Shift+Enter inserts a newline
- Textarea auto-expands up to `15vh`
- Placeholder changes based on whether a chat is selected

### Templates

```tsx
<Templates onBack={() => void} />
```

Self-contained component that fetches and manages templates via `api.ts`. Supports inline editing, two-click delete confirmation, and new template creation.

### ErrorBoundary

```tsx
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

Class component using `getDerivedStateFromError`. Renders a "Something went wrong" fallback with a "Try Again" button that resets the error state.

## UI Components (CVA Variants)

Reusable primitives in `components/ui/` use [CVA](https://cva.style/docs) for type-safe variant styling.

### Button

```tsx
<Button variant="primary" size="sidebar">New Chat</Button>
<Button variant="secondary" size="sidebar">Manage Templates</Button>
<Button variant="send" size="icon">⊛</Button>
```

| Variant | Style |
|---|---|
| `primary` | Purple accent background |
| `secondary` | Gray background |
| `send` | Circular, purple border, green glow on hover |

| Size | Style |
|---|---|
| `sidebar` | Full width, standard padding |
| `compact` | Small padding, `text-xs` |
| `icon` | No padding |

### IconButton

```tsx
<IconButton variant="danger" aria-label="Delete chat">×</IconButton>
<IconButton variant="favorite" aria-label="Add to favorites">☆</IconButton>
```

| Variant | Hover Color |
|---|---|
| `danger` | Red |
| `favorite` | Yellow |

### ListItem

```tsx
<ListItem active={isSelected} onClick={handleClick}>
  Chat Name
</ListItem>
```

Active items get a purple left border accent (`border-l-4 border-accent`).

### MessageBubble

```tsx
<MessageBubble variant="sent">User message</MessageBubble>
<MessageBubble variant="received">Bot response</MessageBubble>
```

| Variant | Alignment | Background | Rounding |
|---|---|---|---|
| `sent` | Right-aligned | `rgb(56,56,56)` | Left corners |
| `received` | Left-aligned | `rgb(17,17,17)` | Right corners |

## Styling

### Theme

Colors are defined as CSS custom properties in `index.css` and referenced via Tailwind classes configured in `tailwind.config.js`:

| Tailwind Class | CSS Variable | Value |
|---|---|---|
| `bg-chat-bg` | `--color-chat-bg` | `rgb(35, 35, 35)` |
| `bg-sidebar-bg` | `--color-sidebar-bg` | `rgb(26, 26, 26)` |
| `bg-message-sent` | `--color-message-sent` | `rgb(56, 56, 56)` |
| `bg-message-received` | `--color-message-received` | `rgb(17, 17, 17)` |
| `bg-accent` | `--color-accent` | `rgb(152, 5, 181)` |
| `bg-accent-hover` | `--color-accent-hover` | `rgb(176, 37, 209)` |

The custom font `font-bauhaus` is set on the root layout.

### Class Merging

Use `cn()` from `lib/utils.ts` to compose Tailwind classes safely:

```typescript
import { cn } from '@/lib/utils';

cn('px-2 py-1', isActive && 'bg-accent', className)
// Handles conflicts: cn('px-2', 'px-4') → 'px-4'
```

### Custom Animations

| Class | Effect | Used By |
|---|---|---|
| `.animate` | Purple glow pulse (1s) | Copy button feedback |
| `.loader` | Spinning conic-gradient ring | Send button loading state |
| `.pupil` | Growing/shrinking dot (2s loop) | Inside the loader ring |

## Testing

```bash
npm test           # Run all tests
npm test -- --watch  # Watch mode
npm test -- --coverage  # Coverage report
```

### Test Utilities (`test-utils.tsx`)

Custom `render` wraps components in `QueryClientProvider` with `retry: false`:

```typescript
import { render, screen } from '../test-utils';

render(<MyComponent />);
expect(screen.getByText('hello')).toBeInTheDocument();
```

Mock data factories:

```typescript
import { createMockChat, createMockMessage, createMockTemplate } from '../test-utils';

const chat = createMockChat({ name: 'Custom Name' });
const message = createMockMessage({ type: 'received', text: 'Bot reply' });
const template = createMockTemplate({ prefix: 'You are a pirate.' });
```

### Browser API Mocks (`setupTests.ts`)

These are mocked globally for all tests:
- `window.matchMedia` — media queries always return `false`
- `Element.prototype.scrollIntoView` — no-op (for auto-scroll)
- `navigator.clipboard.writeText` — resolves immediately (for copy button)

### Mocking Fetch

Tests mock `global.fetch` to simulate API responses:

```typescript
global.fetch = jest.fn();

(global.fetch as jest.Mock).mockImplementation((url: string) => {
  if (url === '/api/v1/chats') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        data: [{ type: 'chats', id: '1', attributes: { name: 'Test' } }]
      }),
    });
  }
  return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
});
```

## Build

```bash
npm run build
```

1. `tsc` — type-checks the entire project (strict mode, no unused locals/params)
2. `vite build` — bundles to `../static/dist/` (served by Flask in production)

The `@` path alias maps to `src/` for cleaner imports (`@/components/ChatList`).
