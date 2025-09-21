# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a comprehensive e-commerce automation system that combines:
- **Web Automation**: Browser-based data collection using PyAutoGUI and image recognition
- **AI Cold Email Generation**: Leveraging Vertex AI (Gemini) for personalized email creation
- **File Organization**: Automated processing of downloaded data and files
- **Client Discovery**: Multi-module system (M1-M6) for finding potential clients

## Commands

### Main Execution
```bash
# Start the complete integrated system (recommended)
start_complete_system.bat

# Alternative launch methods
python ultimate_automation_system.py
```

### Testing and Development
```bash
# Run basic automation tests
python test_complete_automation.py

# Verify assets are available
python verify_assets.py

# Create missing image assets
python create_missing_assets.py

# Individual module testing
python run_client_discovery.py
python run_data_crawler.py
```

### Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Set environment variables
set VERTEX_PROJECT_ID=jadong-471919
```

## Architecture

### Core Components
- **`ultimate_automation_system.py`**: Main integrated GUI application that merges all functionality
- **`config/config.yaml`**: Central configuration file for all system parameters
- **`core/config.py`**: Configuration loader with environment variable support
- **`core/safety_monitor.py`**: System safety and error monitoring

### AI/LLM Pipeline
- **`llm/gemini_client.py`**: Vertex AI integration for Gemini models
- **`llm/two_stage_processor.py`**: Two-stage email generation (extraction → composition)
- **`compose/composer.py`**: Final email composition and formatting

### Web Automation
- **Browser automation**: Uses PyAutoGUI with image template matching
- **Image assets**: `assets/img/` contains templates for UI element recognition
- **Fallback coordinates**: Absolute coordinates stored when image recognition fails
- **File processing**: Automated organization of downloaded Excel/CSV files

### Client Discovery System (M1-M6 Modules)
- **M1 UI Navigator**: Browser navigation and initial setup
- **M2 List Scanner**: Scans store cards from listing pages using OCR
- **M3 Detail Reader**: Extracts detailed information from store pages
- **M4 Filter**: Applies business logic filters to discovered data
- **M5 Storage**: Manages data persistence and Excel integration
- **M6 Monitor**: System monitoring and health checks

### Data Flow
1. **Web Collection**: Automated browser interaction → Download files
2. **File Processing**: Organize downloads → Extract data
3. **AI Analysis**: OCR text extraction → Gemini processing → Email generation
4. **Client Discovery**: Parallel scanning system → Filtered results

## Configuration

### Environment Variables
- `VERTEX_PROJECT_ID`: Required for Vertex AI (default: "jadong-471919")

### Key Configuration Sections
- **Paths**: Input/output directories, asset locations
- **OCR**: Tesseract settings and language configuration
- **LLM**: Model parameters, temperature, token limits
- **GUI**: Window settings, confidence thresholds
- **Runtime**: Concurrency, rate limiting, retry logic

## File Conventions
- Korean comments and UI text are standard in this codebase
- Windows-specific paths (E:/, C:/) are hardcoded in many places
- Image assets use .png format with specific naming conventions
- Excel files follow specific column naming patterns for data exchange

## Safety Considerations
- System includes cost monitoring (max $0.05 per job)
- Rate limiting for API calls (60 RPM, 120K TPM)
- Error recovery mechanisms with exponential backoff
- Automated pause/resume functionality for long-running operations

## Notes
- This is a Windows-specific system designed for Korean e-commerce platforms
- Requires Tesseract OCR installation at `E:/Tesseract/tesseract.exe`
- Uses specific screen coordinates optimized for 1800x1200 resolution
- Privacy backup system creates bundles under `privacy_backup/` directory