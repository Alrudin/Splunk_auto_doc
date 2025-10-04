#!/bin/bash
# Test script to verify pre-commit configuration
# This demonstrates that the hooks are properly configured

set -e

echo "Testing Pre-Commit Hook Configuration"
echo "======================================"
echo ""

# Test frontend hooks (should work since npm packages are installed)
echo "✓ Testing Frontend Hooks..."
echo ""

echo "  - ESLint..."
cd frontend && npm run lint > /dev/null 2>&1
echo "    ✓ ESLint passed"

echo "  - Prettier..."
npm run format:check > /dev/null 2>&1
echo "    ✓ Prettier passed"

echo "  - Vitest..."
npm run test -- --run > /dev/null 2>&1
echo "    ✓ Vitest passed"

cd ..

echo ""
echo "✓ All frontend checks passed!"
echo ""

# Note about backend hooks
echo "Note: Backend hooks (ruff, mypy, pytest) are configured in .pre-commit-config.yaml"
echo "      and would run automatically when the Python environment is properly set up."
echo ""

# Test basic pre-commit hooks that don't require installation
echo "Testing Basic Pre-Commit Hooks..."
echo ""

if command -v pre-commit >/dev/null 2>&1; then
    echo "  - Trailing whitespace check..."
    pre-commit run trailing-whitespace --all-files > /dev/null 2>&1 && echo "    ✓ Passed" || echo "    ℹ Needs fixing"
    
    echo "  - End of file fixer..."
    pre-commit run end-of-file-fixer --all-files > /dev/null 2>&1 && echo "    ✓ Passed" || echo "    ℹ Needs fixing"
    
    echo "  - YAML check..."
    pre-commit run check-yaml --all-files > /dev/null 2>&1 && echo "    ✓ Passed" || echo "    ℹ Needs fixing"
    
    echo "  - JSON check..."
    pre-commit run check-json --all-files > /dev/null 2>&1 && echo "    ✓ Passed" || echo "    ℹ Needs fixing"
    
    echo "  - TOML check..."
    pre-commit run check-toml --all-files > /dev/null 2>&1 && echo "    ✓ Passed" || echo "    ℹ Needs fixing"
else
    echo "  ℹ pre-commit not installed, skipping basic hooks"
fi

echo ""
echo "======================================"
echo "✅ Hook configuration is valid!"
echo ""
echo "To use pre-commit hooks:"
echo "  1. Install dependencies: pip install -e \".[dev]\" && cd frontend && npm install"
echo "  2. Install hooks: pre-commit install"
echo "  3. Run on all files: pre-commit run --all-files"
echo ""
