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
- **Run Detail** (`/runs/:id`) - View details for a specific run and trigger parsing

## Features

### Parse Button

The Run Detail page includes a "Parse" button that allows users to trigger parsing of uploaded configuration files.

**Button Behavior:**
- **Enabled** when run status is `stored` - Ready to be parsed
- **Disabled** for other statuses:
  - `parsing` - Parse job already in progress
  - `normalized` or `complete` - Already parsed successfully
  - `failed` or `pending` - Not in a valid state for parsing

**Usage:**
1. Navigate to the Runs page (`/runs`)
2. Click on a run ID to view its details
3. If the run has `stored` status, click the "Parse" button
4. The button will show a loading state while the parse job is enqueued
5. On success, you'll see a confirmation message
6. On error, an error message will be displayed

**API Endpoint:**
The Parse button sends a POST request to `/v1/runs/{id}/parse` which enqueues a Celery background task to parse the configuration files.

## API Integration

The frontend connects to the backend API through a proxy configured in `vite.config.ts`. All requests to `/api/*` are forwarded to the backend.
