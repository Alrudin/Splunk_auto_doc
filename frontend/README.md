# Splunk Auto Doc - Frontend

React-based frontend application for Splunk Auto Doc, built with Vite, TypeScript, TailwindCSS, and React Query.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and development server
- **TailwindCSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Query (@tanstack/react-query)** - Server state management and data fetching
- **ESLint** - Code linting

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000` (or configure via `.env`)

### Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env to configure API URL if needed
   ```

### Development

1. **Start the development server**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

2. **Build for production**
   ```bash
   npm run build
   ```

   Production files will be generated in the `dist/` directory

3. **Preview production build**
   ```bash
   npm run preview
   ```

4. **Lint code**
   ```bash
   npm run lint
   ```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and service functions
│   ├── components/       # Reusable React components
│   ├── layouts/          # Page layouts
│   ├── pages/            # Page components
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Root application component
│   ├── main.tsx          # Application entry point
│   └── index.css         # Global styles with Tailwind directives
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # TailwindCSS configuration
└── package.json          # Dependencies and scripts
```

## Pages

- **Home** (`/`) - Landing page with feature overview
- **Upload** (`/upload`) - Drag-and-drop file upload interface
- **Runs** (`/runs`) - Table listing all ingestion runs
- **Run Detail** (`/runs/:runId`) - Detailed view of a specific ingestion run with live status updates

## API Integration

The frontend connects to the backend API through a proxy configured in `vite.config.ts`. All requests to `/api/*` are forwarded to the backend.

## Live Status Polling

The Run Detail page implements automatic polling for parse status updates to provide real-time feedback on parsing progress.

### Polling Behavior

- **Polling Endpoint**: `GET /v1/runs/{id}/parse-status`
- **Poll Interval**: Every 2 seconds while the run is in `parsing` or `normalized` state
- **Terminal States**: Polling stops automatically when status transitions to `complete` or `failed`

### Status Lifecycle

```
pending → stored → parsing → normalized → complete
                      ↓
                   failed
```

### Implementation Details

The polling is implemented using React Query's `refetchInterval` option, which provides:

- **Automatic retry**: Built-in retry logic with exponential backoff on errors
- **Smart refetching**: Automatically pauses when the browser tab is in the background
- **Cleanup**: Polling stops when component unmounts or status reaches a terminal state
- **Optimistic updates**: Uses React Query's caching to provide instant UI updates

### Status Badge Colors

- **Green** (`complete`): Parsing completed successfully
- **Red** (`failed`): Parsing encountered an error
- **Blue with spinner** (`parsing`, `normalized`): Actively parsing or normalizing
- **Yellow** (`stored`, `pending`): Waiting to start parsing
- **Gray**: Unknown or other states

### Error Handling

- **Network errors**: React Query automatically retries failed requests (default: 1 retry)
- **Parse errors**: Error messages from the backend are displayed in a red error box
- **Invalid run ID**: Shows validation error if run ID is not a positive integer
- **Run not found**: Displays user-friendly message if run doesn't exist

### Example Usage

```typescript
// Polling is automatic when viewing a run detail page
// Navigate to /runs/123 to see live updates

// The status will update in real-time:
// 1. Initially: "stored" (yellow badge)
// 2. After triggering parse: "parsing" (blue badge with spinner)
// 3. After parsing: "normalized" (blue badge with spinner)
// 4. Finally: "complete" (green badge) or "failed" (red badge)
```
