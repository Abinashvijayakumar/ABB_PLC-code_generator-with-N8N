# Enable GitHub Pages with GitHub Actions
# This file helps ensure the repository is properly configured for GitHub Pages

# Repository Settings Required:
# 1. Go to Settings > Pages
# 2. Source: Deploy from a branch OR GitHub Actions (recommended)
# 3. Branch: gh-pages (if using branch) OR GitHub Actions

# The workflow in .github/workflows/pages.yml will handle the deployment
# automatically when changes are pushed to the main branch.

# For the domain https://Abinashvijayakumar.github.io/ABB_PLC-code_generator-with-N8N
# to work, ensure:
# - Repository is public or has GitHub Pages enabled for private repos
# - The workflow has proper permissions (included in pages.yml)
# - No conflicts with existing GitHub Pages configuration