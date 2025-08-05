# React Hooks Documentation

This document describes the custom React hooks used in SafeAppealNavigator's frontend.

## Table of Contents
- [Core Hooks](#core-hooks)
- [Legal Research Hooks](#legal-research-hooks)
- [Document Management Hooks](#document-management-hooks)
- [UI/UX Hooks](#uiux-hooks)
- [WebSocket Hooks](#websocket-hooks)

## Core Hooks

### `useAGUI`
Manages WebSocket connection to the AG-UI backend.

```typescript
import { useAGUI } from '@/hooks/useAGUI';

function MyComponent() {
  const {
    connected,
    sendMessage,
    lastMessage,
    threadId
  } = useAGUI();

  const handleSendMessage = () => {
    sendMessage({
      type: 'chat',
      content: 'Hello from frontend'
    });
  };

  return (
    <div>
      Status: {connected ? 'Connected' : 'Disconnected'}
    </div>
  );
}
```

**Returns:**
- `connected`: boolean - WebSocket connection status
- `sendMessage`: (message: AGUIMessage) => void - Send message to backend
- `lastMessage`: AGUIMessage | null - Most recent received message
- `threadId`: string - Current thread identifier

### `useAuth`
Manages user authentication state.

```typescript
import { useAuth } from '@/hooks/useAuth';

function ProtectedComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();

  if (!isAuthenticated) {
    return <LoginForm onLogin={login} />;
  }

  return <div>Welcome, {user.name}!</div>;
}
```

## Legal Research Hooks

### `useWCATSearch`
Handles WCAT case searches and results.

```typescript
import { useWCATSearch } from '@/hooks/useWCATSearch';

function CaseSearch() {
  const {
    search,
    results,
    loading,
    error,
    filters,
    setFilters
  } = useWCATSearch();

  const handleSearch = async (query: string) => {
    await search({
      query,
      dateRange: filters.dateRange,
      maxResults: 20
    });
  };

  return (
    <div>
      {loading && <Spinner />}
      {results.map(case => (
        <CaseCard key={case.id} case={case} />
      ))}
    </div>
  );
}
```

**Parameters:**
- `query`: string - Search terms
- `dateRange`: { start: Date, end: Date } - Date filter
- `maxResults`: number - Maximum results to return

### `useCaseAnalysis`
Analyzes case strength and provides recommendations.

```typescript
import { useCaseAnalysis } from '@/hooks/useCaseAnalysis';

function CaseAnalyzer({ caseData }) {
  const {
    analyze,
    analysis,
    strengths,
    weaknesses,
    recommendations
  } = useCaseAnalysis();

  useEffect(() => {
    analyze(caseData);
  }, [caseData]);

  return (
    <div>
      <h3>Case Strength: {analysis?.score}/100</h3>
      <Recommendations items={recommendations} />
    </div>
  );
}
```

## Document Management Hooks

### `useDocumentUpload`
Handles document uploads with progress tracking.

```typescript
import { useDocumentUpload } from '@/hooks/useDocumentUpload';

function DocumentUploader() {
  const {
    upload,
    progress,
    uploadedFiles,
    error
  } = useDocumentUpload();

  const handleFileSelect = async (files: File[]) => {
    await upload(files, {
      category: 'medical',
      caseId: currentCase.id
    });
  };

  return (
    <DropZone
      onFilesSelected={handleFileSelect}
      progress={progress}
    />
  );
}
```

### `useDocumentOrganizer`
Automatically categorizes and tags documents.

```typescript
import { useDocumentOrganizer } from '@/hooks/useDocumentOrganizer';

function DocumentList({ documents }) {
  const {
    organize,
    categories,
    tags,
    getDocumentsByCategory
  } = useDocumentOrganizer(documents);

  useEffect(() => {
    organize();
  }, [documents]);

  return (
    <div>
      {categories.map(category => (
        <CategorySection
          key={category}
          documents={getDocumentsByCategory(category)}
        />
      ))}
    </div>
  );
}
```

## UI/UX Hooks

### `useCaseTimeline`
Manages case timeline visualization.

```typescript
import { useCaseTimeline } from '@/hooks/useCaseTimeline';

function CaseTimeline({ caseId }) {
  const {
    events,
    addEvent,
    updateEvent,
    milestones,
    deadlines
  } = useCaseTimeline(caseId);

  return (
    <Timeline>
      {events.map(event => (
        <TimelineEvent
          key={event.id}
          event={event}
          isDeadline={deadlines.includes(event.id)}
        />
      ))}
    </Timeline>
  );
}
```

### `useNotifications`
Manages user notifications and alerts.

```typescript
import { useNotifications } from '@/hooks/useNotifications';

function NotificationCenter() {
  const {
    notifications,
    addNotification,
    dismissNotification,
    clearAll
  } = useNotifications();

  return (
    <div>
      {notifications.map(notification => (
        <Notification
          key={notification.id}
          {...notification}
          onDismiss={() => dismissNotification(notification.id)}
        />
      ))}
    </div>
  );
}
```

## WebSocket Hooks

### `useRealtimeUpdates`
Subscribes to real-time case updates.

```typescript
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';

function CaseMonitor({ caseId }) {
  const { updates, subscribe, unsubscribe } = useRealtimeUpdates();

  useEffect(() => {
    subscribe(`case.${caseId}`);
    return () => unsubscribe(`case.${caseId}`);
  }, [caseId]);

  return (
    <div>
      {updates.map(update => (
        <UpdateNotification key={update.id} update={update} />
      ))}
    </div>
  );
}
```

### `useAgentStatus`
Monitors backend agent status and availability.

```typescript
import { useAgentStatus } from '@/hooks/useAgentStatus';

function AgentStatusPanel() {
  const { agents, isProcessing, queueLength } = useAgentStatus();

  return (
    <div>
      {agents.map(agent => (
        <AgentCard
          key={agent.id}
          agent={agent}
          status={agent.status}
        />
      ))}
      <div>Queue: {queueLength} tasks pending</div>
    </div>
  );
}
```

## Best Practices

### 1. Error Handling
Always handle errors gracefully in hooks:

```typescript
const useMyHook = () => {
  const [error, setError] = useState<Error | null>(null);

  const doSomething = async () => {
    try {
      // ... operation
    } catch (err) {
      setError(err);
      // Optionally notify user
    }
  };

  return { doSomething, error };
};
```

### 2. Cleanup
Always clean up subscriptions and side effects:

```typescript
useEffect(() => {
  const subscription = subscribe();

  return () => {
    subscription.unsubscribe();
  };
}, [dependencies]);
```

### 3. TypeScript
Always provide proper TypeScript types:

```typescript
interface UseMyHookReturn {
  data: MyDataType | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export const useMyHook = (params: MyParams): UseMyHookReturn => {
  // Implementation
};
```

### 4. Memoization
Use `useMemo` and `useCallback` for expensive operations:

```typescript
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

const stableCallback = useCallback(() => {
  doSomething(value);
}, [value]);
```

## Testing Hooks

Example of testing a custom hook:

```typescript
import { renderHook, act } from '@testing-library/react-hooks';
import { useWCATSearch } from './useWCATSearch';

describe('useWCATSearch', () => {
  it('should search and return results', async () => {
    const { result } = renderHook(() => useWCATSearch());

    await act(async () => {
      await result.current.search({
        query: 'back injury',
        maxResults: 10
      });
    });

    expect(result.current.results).toHaveLength(10);
    expect(result.current.loading).toBe(false);
  });
});
```