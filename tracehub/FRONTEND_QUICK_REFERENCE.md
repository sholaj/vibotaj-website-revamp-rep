# TraceHub Frontend Quick Reference

**For Developers Implementing UI/UX Features**

---

## Installation Requirements

Ensure consistent local and CI installs by aligning tooling and commands.

- Node: 18.x (required by Vite 5 and jsdom 23)
- npm: 9+ (bundled with Node 18)
- Lockfile: package-lock.json committed
- Version file: .nvmrc with `18` in tracehub/frontend
- Engines: package.json declares `node>=18`, `npm>=9`
- Testing stack versions aligned:
  - vitest ^1.6.1
  - @vitest/ui ^1.6.1
  - @vitest/coverage-v8 ^1.6.1
  - jsdom ^23.0.1
  - @testing-library/* per package.json

Recommended commands:

```bash
cd tracehub/frontend
nvm use 18            # if nvm is installed
npm ci                # reproducible install from lockfile
npm test -- --run     # run tests
npm run test:coverage # run tests with coverage
npm run build         # production build
```

---

## Design Tokens

### Colors

```typescript
// Tailwind CSS classes - use these consistently

// Primary (Blue)
text-primary-600      bg-primary-600      border-primary-600
text-primary-700      bg-primary-700      border-primary-700

// Success (Green)
text-success-600      bg-success-600      border-success-600
text-success-50       bg-success-50       border-success-50

// Warning (Yellow/Orange)
text-warning-600      bg-warning-600      border-warning-600
text-warning-50       bg-warning-50       border-warning-50

// Danger (Red)
text-danger-600       bg-danger-600       border-danger-600
text-danger-50        bg-danger-50        border-danger-50

// Gray Scale
text-gray-900         bg-gray-900         border-gray-900  // Darkest
text-gray-600         bg-gray-600         border-gray-600  // Body text
text-gray-400         bg-gray-400         border-gray-400  // Placeholder
text-gray-200         bg-gray-200         border-gray-200  // Borders
text-gray-50          bg-gray-50          border-gray-50   // Backgrounds
```

### Typography

```css
/* Headings */
.text-2xl font-bold text-gray-900     /* Page title (h1) */
.text-lg font-semibold text-gray-900  /* Card title (h2) */
.text-base font-medium text-gray-900  /* Section title (h3) */

/* Body */
.text-sm text-gray-600                /* Body text */
.text-xs text-gray-500                /* Caption text */
.font-mono                             /* Code/reference numbers */
```

### Spacing

```typescript
// Padding
p-2    // 8px   - Tight
p-4    // 16px  - Standard
p-6    // 24px  - Comfortable

// Margin
m-2, mt-2, mb-2, ml-2, mr-2  // 8px
m-4, mt-4, mb-4, ml-4, mr-4  // 16px
m-6, mt-6, mb-6, ml-6, mr-6  // 24px

// Gap (Flexbox/Grid)
gap-2, gap-4, gap-6

// Space-between
space-x-2, space-y-2  // Horizontal/vertical spacing
```

### Shadows & Borders

```css
.shadow-sm      /* Subtle shadow for cards */
.shadow-md      /* Medium shadow for modals */
.shadow-lg      /* Large shadow for popovers */

.rounded        /* 4px border radius */
.rounded-lg     /* 8px border radius */
.rounded-full   /* Fully rounded (badges) */

.border         /* 1px border */
.border-2       /* 2px border */
```

---

## Component Patterns

### Standard Card

```tsx
<div className="card p-6">
  <h2 className="text-lg font-semibold text-gray-900 mb-4">
    Card Title
  </h2>
  <div className="space-y-3">
    {/* Card content */}
  </div>
</div>
```

### Status Badge

```tsx
const STATUS_STYLES = {
  success: 'badge-success',
  warning: 'badge-warning',
  danger: 'badge-danger',
  info: 'badge-info',
}

<span className={STATUS_STYLES[status]}>
  {label}
</span>
```

### Button

```tsx
// Primary action
<button className="btn-primary">
  <Icon className="h-4 w-4 mr-2" />
  Primary Action
</button>

// Secondary action
<button className="btn-secondary">
  Secondary Action
</button>

// Disabled state
<button className="btn-primary" disabled>
  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
  Loading...
</button>
```

### Loading Skeleton

```tsx
function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-6 w-48 bg-gray-200 rounded"></div>
      <div className="h-16 bg-gray-200 rounded"></div>
      <div className="h-16 bg-gray-200 rounded"></div>
    </div>
  )
}
```

### Error Display

```tsx
function ErrorDisplay({ message, onRetry }: Props) {
  return (
    <div className="bg-danger-50 border border-danger-200 rounded-lg p-6 text-center">
      <AlertCircle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-danger-800 mb-2">
        Error Title
      </h3>
      <p className="text-danger-600 mb-4">{message}</p>
      <button onClick={onRetry} className="btn-primary">
        Try Again
      </button>
    </div>
  )
}
```

### Empty State

```tsx
function EmptyState() {
  return (
    <div className="text-center py-12">
      <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        No items found
      </h3>
      <p className="text-gray-600">
        Items will appear here once available.
      </p>
    </div>
  )
}
```

### Modal

```tsx
function Modal({ isOpen, onClose, title, children }: Props) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">{title}</h2>
            <button onClick={onClose}>
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6">{children}</div>
        </div>
      </div>
    </div>
  )
}
```

---

## Responsive Patterns

### Grid Layouts

```tsx
// Dashboard cards - 1 col mobile, 2 col tablet, 3 col desktop
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <ItemCard key={item.id} {...item} />)}
</div>

// Shipment detail - stacked mobile, 2+1 columns desktop
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
  <div className="lg:col-span-2">
    {/* Main content */}
  </div>
  <div>
    {/* Sidebar */}
  </div>
</div>
```

### Hide/Show by Breakpoint

```tsx
// Hide on mobile, show on desktop
<div className="hidden lg:block">Desktop only</div>

// Show on mobile, hide on desktop
<div className="lg:hidden">Mobile only</div>

// Show different content
<div className="lg:hidden">Mobile version</div>
<div className="hidden lg:block">Desktop version</div>
```

### Text Truncation

```tsx
// Single line truncate
<p className="truncate">Long text that will be truncated with ellipsis</p>

// Multi-line clamp (requires Tailwind plugin or custom CSS)
<p className="line-clamp-2">
  Text that will be clamped to 2 lines with ellipsis
</p>
```

### Touch Targets (Mobile)

```tsx
// Minimum 44x44px touch target
<button className="p-3 min-h-[44px] min-w-[44px]">
  <Icon className="h-5 w-5" />
</button>

// Increase tap area with negative margin
<button className="p-2 -m-2">
  Small visual, large tap area
</button>
```

---

## API Integration Patterns

### Basic Fetch on Mount

```tsx
function MyComponent() {
  const [data, setData] = useState<Data | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const result = await api.getData()
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, []) // Empty deps = run once on mount

  if (isLoading) return <LoadingSkeleton />
  if (error) return <ErrorDisplay message={error} onRetry={fetchData} />
  if (!data) return <EmptyState />

  return <div>{/* Render data */}</div>
}
```

### Fetch with Dependencies

```tsx
// Re-fetch when shipmentId changes
useEffect(() => {
  fetchShipmentData(shipmentId)
}, [shipmentId])

// Re-fetch when multiple dependencies change
useEffect(() => {
  fetchFilteredData(filters, sortBy, page)
}, [filters, sortBy, page])
```

### Manual Refresh

```tsx
const [isRefreshing, setIsRefreshing] = useState(false)

const handleRefresh = async () => {
  setIsRefreshing(true)
  try {
    // Invalidate cache first
    api.invalidateCache('/shipments')
    const data = await api.getShipments()
    setShipments(data)
  } catch (error) {
    console.error('Refresh failed:', error)
  } finally {
    setIsRefreshing(false)
  }
}

return (
  <button onClick={handleRefresh} disabled={isRefreshing}>
    <RefreshCw className={isRefreshing ? 'animate-spin' : ''} />
    Refresh
  </button>
)
```

### Polling

```tsx
useEffect(() => {
  // Initial fetch
  fetchData()

  // Set up polling
  const interval = setInterval(fetchData, 30000) // 30 seconds

  // Cleanup
  return () => clearInterval(interval)
}, [])
```

### Optimistic Updates

```tsx
const handleToggle = async (id: string) => {
  // Optimistically update UI
  setItems(prev => prev.map(item =>
    item.id === id ? { ...item, enabled: !item.enabled } : item
  ))

  try {
    await api.updateItem(id)
  } catch (error) {
    // Revert on error
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, enabled: !item.enabled } : item
    ))
    showToast('Update failed', 'error')
  }
}
```

---

## Custom Hooks

### usePolling

```tsx
function usePolling<T>(
  fetchFn: () => Promise<T>,
  interval: number = 30000
): { data: T | null; isLoading: boolean; error: string | null } {
  const [data, setData] = useState<T | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const result = await fetchFn()
        setData(result)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Fetch failed')
      } finally {
        setIsLoading(false)
      }
    }

    fetch()
    const id = setInterval(fetch, interval)
    return () => clearInterval(id)
  }, [fetchFn, interval])

  return { data, isLoading, error }
}

// Usage
const { data: unreadCount } = usePolling(
  () => api.getUnreadNotificationCount(),
  30000
)
```

### useCountdown

```tsx
function useCountdown(targetDate: string): {
  days: number
  hours: number
  minutes: number
  seconds: number
  isExpired: boolean
} {
  const [timeLeft, setTimeLeft] = useState(calculateTimeLeft(targetDate))

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft(calculateTimeLeft(targetDate))
    }, 1000)

    return () => clearInterval(interval)
  }, [targetDate])

  return {
    ...timeLeft,
    isExpired: timeLeft.total <= 0
  }
}

function calculateTimeLeft(targetDate: string) {
  const total = new Date(targetDate).getTime() - Date.now()
  return {
    total,
    days: Math.floor(total / (1000 * 60 * 60 * 24)),
    hours: Math.floor((total / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((total / (1000 * 60)) % 60),
    seconds: Math.floor((total / 1000) % 60),
  }
}

// Usage
const { days, hours, minutes, isExpired } = useCountdown(shipment.eta)
```

### useClickOutside

```tsx
function useClickOutside<T extends HTMLElement>(
  callback: () => void
): React.RefObject<T> {
  const ref = useRef<T>(null)

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback()
      }
    }

    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [callback])

  return ref
}

// Usage
const dropdownRef = useClickOutside<HTMLDivElement>(() => setIsOpen(false))

return <div ref={dropdownRef}>{/* Dropdown content */}</div>
```

---

## Accessibility Checklist

### Semantic HTML

```tsx
// ✅ Good - semantic HTML
<nav>
  <ul>
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

// ❌ Bad - div soup
<div>
  <div onClick={() => navigate('/dashboard')}>Dashboard</div>
</div>
```

### ARIA Attributes

```tsx
// Button
<button
  aria-label="Close modal"
  aria-pressed={isActive}
  aria-disabled={isDisabled}
>
  <X />
</button>

// Toggle
<button
  role="switch"
  aria-checked={isEnabled}
  onClick={handleToggle}
>
  {isEnabled ? 'On' : 'Off'}
</button>

// Modal
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <h2 id="modal-title">Modal Title</h2>
  <p id="modal-description">Modal description</p>
</div>

// Live region (for dynamic updates)
<div aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>
```

### Keyboard Navigation

```tsx
// Handle keyboard events
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    handleClick()
  }
  if (e.key === 'Escape') {
    handleClose()
  }
}

// Make non-interactive elements keyboard accessible
<div
  role="button"
  tabIndex={0}
  onKeyDown={handleKeyDown}
  onClick={handleClick}
>
  Click me
</div>
```

### Focus Management

```tsx
// Focus trap in modal
useEffect(() => {
  if (isOpen) {
    const previouslyFocused = document.activeElement
    modalRef.current?.focus()

    return () => {
      (previouslyFocused as HTMLElement)?.focus()
    }
  }
}, [isOpen])

// Visible focus indicator
<button className="focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
  Click me
</button>
```

---

## Performance Tips

### Memoization

```tsx
// Memoize expensive calculations
const sortedItems = useMemo(() => {
  return items.sort((a, b) => a.date.localeCompare(b.date))
}, [items])

// Memoize components
const MemoizedCard = React.memo(ShipmentCard)

// Memoize callbacks
const handleClick = useCallback((id: string) => {
  console.log('Clicked:', id)
}, [])
```

### Lazy Loading

```tsx
// Lazy load pages
const Analytics = lazy(() => import('./pages/Analytics'))
const Users = lazy(() => import('./pages/Users'))

// Use with Suspense
<Suspense fallback={<LoadingSkeleton />}>
  <Routes>
    <Route path="/analytics" element={<Analytics />} />
    <Route path="/users" element={<Users />} />
  </Routes>
</Suspense>
```

### Debounce

```tsx
// Debounce search input
const [searchTerm, setSearchTerm] = useState('')
const debouncedSearch = useDebounce(searchTerm, 500)

useEffect(() => {
  if (debouncedSearch) {
    fetchSearchResults(debouncedSearch)
  }
}, [debouncedSearch])

// Debounce utility
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}
```

---

## Common Gotchas

### 1. Stale Closures in useEffect

```tsx
// ❌ Bad - fetchData is recreated on every render
useEffect(() => {
  const fetchData = async () => {
    const data = await api.getData(filter)
    setData(data)
  }
  fetchData()
}, [filter]) // filter changes, but fetchData reference changes too!

// ✅ Good - use useCallback
const fetchData = useCallback(async () => {
  const data = await api.getData(filter)
  setData(data)
}, [filter])

useEffect(() => {
  fetchData()
}, [fetchData])
```

### 2. Missing Cleanup

```tsx
// ❌ Bad - interval not cleaned up
useEffect(() => {
  setInterval(() => setCount(c => c + 1), 1000)
}, [])

// ✅ Good - cleanup function
useEffect(() => {
  const interval = setInterval(() => setCount(c => c + 1), 1000)
  return () => clearInterval(interval)
}, [])
```

### 3. Async in useEffect

```tsx
// ❌ Bad - async useEffect directly
useEffect(async () => {
  const data = await fetchData()
  setData(data)
}, [])

// ✅ Good - IIFE or separate async function
useEffect(() => {
  const fetchData = async () => {
    const data = await api.getData()
    setData(data)
  }
  fetchData()
}, [])
```

### 4. Keys in Lists

```tsx
// ❌ Bad - using index as key
{items.map((item, index) => (
  <div key={index}>{item.name}</div>
))}

// ✅ Good - using unique ID
{items.map(item => (
  <div key={item.id}>{item.name}</div>
))}
```

### 5. Object/Array Dependencies

```tsx
// ❌ Bad - object created on every render
useEffect(() => {
  fetchData({ page, limit })
}, [{ page, limit }]) // New object every time!

// ✅ Good - primitive dependencies
useEffect(() => {
  fetchData({ page, limit })
}, [page, limit])
```

---

## Testing Snippets

### Basic Component Test

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ShipmentCard from './ShipmentCard'

test('renders shipment reference', () => {
  const shipment = { id: '1', reference: 'VIBO-2026-001' }
  render(<ShipmentCard shipment={shipment} />)

  expect(screen.getByText('VIBO-2026-001')).toBeInTheDocument()
})

test('calls onClick when clicked', async () => {
  const handleClick = jest.fn()
  render(<ShipmentCard shipment={shipment} onClick={handleClick} />)

  await userEvent.click(screen.getByRole('button'))

  expect(handleClick).toHaveBeenCalledWith(shipment.id)
})
```

### API Mock

```tsx
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.get('/api/shipments', (req, res, ctx) => {
    return res(ctx.json([
      { id: '1', reference: 'VIBO-2026-001' }
    ]))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

---

## Git Commit Messages

```bash
# Format: <type>(<scope>): <subject>

# Types:
feat:     # New feature
fix:      # Bug fix
refactor: # Code refactoring
style:    # Formatting, no code change
test:     # Adding tests
docs:     # Documentation
chore:    # Maintenance

# Examples:
feat(tracking): add container map visualization
fix(mobile): resolve navigation menu overflow on small screens
refactor(api): consolidate error handling logic
style(dashboard): improve card spacing and alignment
test(shipment): add tests for document upload flow
docs(readme): update setup instructions
chore(deps): upgrade react-router to v6.22
```

---

## Useful Resources

### Tailwind CSS
- Docs: https://tailwindcss.com/docs
- Cheatsheet: https://nerdcave.com/tailwind-cheat-sheet

### React
- Hooks: https://react.dev/reference/react
- TypeScript: https://react-typescript-cheatsheet.netlify.app/

### Icons
- Lucide: https://lucide.dev/
- Search: https://lucide.dev/icons

### Accessibility
- WAI-ARIA: https://www.w3.org/WAI/ARIA/apg/
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

### Date Formatting
- date-fns: https://date-fns.org/docs/format

---

**Quick Reference Card**
**Version:** 1.0
**Last Updated:** 2026-01-03
