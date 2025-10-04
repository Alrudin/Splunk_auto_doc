import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Splunk Auto Doc
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          A web application that parses and analyzes Splunk configuration files to generate
          comprehensive documentation and visualizations.
        </p>
        <div className="flex gap-4">
          <Link
            to="/upload"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Upload Configuration
          </Link>
          <Link
            to="/runs"
            className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            View Runs
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <FeatureCard
          title="Configuration Parsing"
          description="Extract and normalize Splunk configuration files (inputs.conf, props.conf, transforms.conf, etc.)"
          icon="📄"
        />
        <FeatureCard
          title="Serverclass Resolution"
          description="Resolve deployment server configurations to determine host memberships and app assignments"
          icon="🖥️"
        />
        <FeatureCard
          title="Data Flow Analysis"
          description="Trace data routing from inputs through transforms to final destinations"
          icon="🔄"
        />
        <FeatureCard
          title="Interactive Visualization"
          description="Explore configuration relationships and data paths through web-based visualizations"
          icon="📊"
        />
        <FeatureCard
          title="Version Tracking"
          description="Maintain historical snapshots of configuration changes through ingestion runs"
          icon="📜"
        />
        <FeatureCard
          title="API Integration"
          description="RESTful API for programmatic access to configuration data and analysis results"
          icon="🔌"
        />
      </div>

      {/* Getting Started */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Getting Started</h2>
        <ol className="list-decimal list-inside space-y-2 text-gray-700">
          <li>
            <strong>Upload your Splunk configuration:</strong> Use the upload page to submit
            tar/zip archives or individual conf files
          </li>
          <li>
            <strong>Select upload type:</strong> Choose from full etc/ directory, app bundles,
            or single conf files
          </li>
          <li>
            <strong>View ingestion runs:</strong> Track the status and results of your uploads
            in the runs page
          </li>
          <li>
            <strong>Explore results:</strong> (Coming soon) Browse hosts, apps, data paths, and
            configuration relationships
          </li>
        </ol>
      </div>
    </div>
  );
}

interface FeatureCardProps {
  title: string;
  description: string;
  icon: string;
}

function FeatureCard({ title, description, icon }: FeatureCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  );
}
