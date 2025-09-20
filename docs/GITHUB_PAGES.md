# GitHub Pages Setup for PLC Co-pilot

This document explains how to deploy the PLC Co-pilot frontend to GitHub Pages.

## Automatic Deployment

The repository includes a GitHub Actions workflow (`.github/workflows/pages.yml`) that automatically deploys the frontend to GitHub Pages when code is pushed to the `main` branch.

## GitHub Pages Configuration

To enable GitHub Pages for this repository:

1. Go to your repository settings
2. Navigate to "Pages" in the left sidebar
3. Under "Source", select "GitHub Actions"
4. The workflow will automatically deploy the frontend files to `https://yourusername.github.io/repository-name`

## Demo Mode

When the application is served from GitHub Pages, it automatically switches to demo mode:

- **Demo Detection**: Automatically detects the GitHub Pages hostname
- **Sample Responses**: Provides realistic PLC code examples without requiring backend services
- **Full UI**: All interface features remain functional for demonstration
- **Educational Value**: Shows the complete workflow from prompt to generated code

## Local Development vs GitHub Pages

| Feature | Local Development | GitHub Pages |
|---------|------------------|--------------|
| Backend API | Full FastAPI backend required | Demo mode with samples |
| AI Generation | Real AI-powered responses | Pre-defined sample responses |
| Code Quality | Production-grade output | Educational examples |
| Use Case | Full development environment | Portfolio/demo showcase |

## Customization

To customize the demo responses, edit the `generateDemoResponse()` function in `frontend/script.js`.

## Repository Structure for Pages

```
├── .github/workflows/pages.yml    # GitHub Pages deployment workflow
├── frontend/                      # Source files
│   ├── index.html                # Main HTML file
│   ├── script.js                 # JavaScript with demo mode support
│   └── styles.css                # CSS with demo banner styles
└── docs/                         # Additional documentation
```

The workflow automatically copies frontend files to the repository root for GitHub Pages deployment.