# Clinical Tool Hub

A comprehensive web-based application built with Python and NiceGUI, designed to provide various clinical tools and utilities for healthcare professionals.

[![nicegui](https://img.shields.io/badge/nicegui-1.4.5-blue)](https://nicegui.io/)
[![requests](https://img.shields.io/badge/requests-2.31.0-blue)](https://requests.readthedocs.io/)
[![pandas](https://img.shields.io/badge/pandas-2.2.0-blue)](https://pandas.pydata.org/)
[![plotly](https://img.shields.io/badge/plotly-5.24.1-blue)](https://plotly.com/python/)
[![ollama](https://img.shields.io/badge/ollama-0.4.0-blue)](https://ollama.com/blog/python-javascript-libraries)
[![PyPDF2](https://img.shields.io/badge/PyPDF2-3.0.1-blue)](https://pypdf2.readthedocs.io/en/3.x/)

## Features

- **ICD-10 Lookup**: Quick search and lookup of ICD-10 codes and descriptions
- **Insulin & Glucose Tracking**: Monitor and visualize insulin and glucose patterns
- **Wound Tracking**: Track and visualize wound measurements over time
- **Cost Estimator**: Calculate treatment costs based on insurance and CPT codes
- **NPI Lookup**: Search and verify National Provider Identifier information
- **Doctor/Rep Information**: Manage and lookup healthcare provider and representative contact information
- **MME Calculator**: Calculate Morphine Milligram Equivalents for pain medications
- **HPI Reword**: AI-powered tool to enhance and restructure History of Present Illness notes
- **HPI Info**: Generate structured History of Present Illness notes from form inputs
- **Office Forms**: Fill out PDF office forms and download copy for printing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/BattlemasterLoL/medical_office_tool_app.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Dependencies

- nicegui
- requests
- pandas
- plotly
- ollama
- PyPDF2

## Usage

Run the application:
```bash
python main.py
```

The application will be available at `http://localhost:8080` by default.

## Data Files Required

The following CSV files are required in the root directory:
- `fee_schedule.csv`: Contains CPT codes and fee schedules
- `doctor_info.csv`: Contains healthcare provider information
- `rep_info.csv`: Contains representative contact information

## Features in Detail

### ICD-10 Lookup
- Search ICD-10 codes and descriptions
- Interactive table display of results

### Insulin & Glucose Tracking
- Input and track insulin and glucose measurements
- Visualize patterns with interactive charts

### Wound Tracking
- Track wound measurements over time
- Generate visualization plots
- Support for different measurement units

### Cost Estimator
- Calculate treatment costs based on CPT codes
- Insurance coverage calculation
- Deductible and out-of-pocket considerations

### NPI Lookup
- Search providers by NPI number
- View detailed provider information
- Filter and sort results

### Doctor/Rep Information
- Manage healthcare provider contact information
- Store and retrieve representative information
- Quick access to contact details

### MME Calculator
- Calculate total Morphine Milligram Equivalents
- Support for multiple opioid medications
- Visual indicators for high MME values

### HPI Reword
- AI-powered note enhancement
- Maintain medical accuracy while improving clarity
- Detailed change tracking

### HPI Info
- Structured input form for patient information
- Automatic HPI generation
- Standardized format output

### Office Forms
- Fill out office forms
- All in one place forms
- Referral, Letterhead, Excuse note, Physical Therapy order, and Lab order

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

## Acknowledgments

- Built with [NiceGUI](https://nicegui.io/)
- Uses [Plotly](https://plotly.com/) for visualizations
- Powered by [Ollama](https://ollama.ai/) for AI features
