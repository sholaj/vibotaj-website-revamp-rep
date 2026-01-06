# TraceHub Frontend Documentation

This directory contains all frontend-related documentation including UI/UX specifications, component hierarchies, and implementation guides.

## Quick Navigation

### For Developers
- **[FRONTEND_QUICK_REFERENCE.md](FRONTEND_QUICK_REFERENCE.md)** - Quick reference guide
  - Design tokens (colors, spacing, typography)
  - Common component patterns
  - Tailwind CSS classes
  - Icon usage
  - API integration patterns

- **[COMPONENT_HIERARCHY.md](COMPONENT_HIERARCHY.md)** - Component structure
  - React component tree
  - Component relationships
  - State management
  - Props flow

### For Planning & Design
- **[FRONTEND_UI_UX_SPEC.md](FRONTEND_UI_UX_SPEC.md)** - Comprehensive UI/UX specification (1400+ lines)
  - Current state assessment
  - 6 detailed feature specifications:
    1. Container Tracking Dashboard
    2. Audit Pack Download UI
    3. Mobile Responsiveness
    4. Email Notification Preferences
    5. Role-Based Dashboards
    6. Advanced Search & Filters
  - Wireframes and mockups
  - Component breakdowns
  - API dependencies
  - Complexity estimates

- **[FRONTEND_IMPLEMENTATION_SUMMARY.md](FRONTEND_IMPLEMENTATION_SUMMARY.md)** - Executive summary
  - UI/UX planning overview
  - Sprint allocation (4 sprints, ~110 hours)
  - Priority features
  - Documents delivered

## Tech Stack

- **Framework:** React 18
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** React Context / Redux (TBD)
- **Build Tool:** Vite
- **Testing:** Jest + React Testing Library

## Design System

### Color Palette
- **Primary:** Blue (vibotaj brand color)
- **Success:** Green
- **Warning:** Yellow/Orange
- **Danger:** Red
- **Gray Scale:** Neutral tones

### Typography
- **Headings:** Inter font family
- **Body:** System fonts for performance
- **Monospace:** For code/data display

For complete design tokens, see [FRONTEND_QUICK_REFERENCE.md](FRONTEND_QUICK_REFERENCE.md).

## Key Features

### Current Implementation
- User authentication and role-based access
- Shipment management
- Document upload and management
- Basic tracking display

### Planned Features (See FRONTEND_UI_UX_SPEC.md)
1. **Container Tracking Dashboard** - Real-time tracking with map integration
2. **Mobile Responsiveness** - Full mobile optimization
3. **Audit Pack Download** - Streamlined document download UX
4. **Email Preferences** - User notification settings
5. **Role-Based Dashboards** - Customized views per role
6. **Advanced Search** - Powerful filtering and search

## Development Workflow

### Start Development Server
```bash
cd tracehub/frontend
npm install
npm run dev
```

### Run Tests
```bash
npm test              # Run tests
npm run test:watch    # Watch mode
npm run test:coverage # With coverage
```

### Build for Production
```bash
npm run build         # Build optimized bundle
npm run preview       # Preview production build
```

## Related Documentation

- [Backend API](../api/) - API specifications
- [Architecture](../architecture/) - System architecture
- [Deployment](../deployment/) - Deployment guides
