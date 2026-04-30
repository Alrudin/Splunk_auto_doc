const path = require('path');

module.exports = {
  entry: './src/visualization.js',
  output: {
    filename: 'visualization.js',
    path: path.resolve(__dirname),
    libraryTarget: 'amd'
  },
  externals: [
    'api/SplunkVisualizationBase',
    'api/SplunkVisualizationUtils'
  ]
};
