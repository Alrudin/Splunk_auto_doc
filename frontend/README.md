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
- **Run Detail** (`/runs/:id`) - Detailed view of a specific run with parsed entity counts

### Run Detail Page

The Run Detail page displays comprehensive information about a specific ingestion run, including:

- **Run Information**: ID, status, upload type, label, and timestamps
- **Parsed Entity Counts**: After parsing completes, displays counts for:
  - Stanzas
  - Inputs
  - Props
  - Transforms
  - Indexes
  - Outputs
  - Serverclasses

#### Features

- **Loading States**: Shows loading indicators while fetching run details and summary data
- **Error Handling**: Displays user-friendly error messages if the run is not found or if the summary fetch fails
- **Navigation**: Includes a back link to return to the runs list
- **Status Badges**: Color-coded badges showing the current status of the run (complete, parsing, failed, etc.)

#### Usage

1. Navigate to the Runs page (`/runs`)
2. Click on any run ID in the table to view its details
3. The detail page will show run information and, if parsing is complete, entity counts

#### Error States

- **Invalid Run ID**: If the URL contains an invalid run ID, an error message is displayed
- **Run Not Found**: If the run ID doesn't exist in the database (404 error)
- **Summary Fetch Failed**: If the summary endpoint returns an error

## API Integration

The frontend connects to the backend API through a proxy configured in `vite.config.ts`. All requests to `/api/*` are forwarded to the backend.
