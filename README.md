# Class Record App

A Python application for managing class records with a modern UI. Built with PySimpleGUI for a professional, user-friendly interface.

## Features

### Course Management
- Create and manage multiple courses/classes
- Add course details: schedule, room, course code, offering number, title, and description
- View, edit, and delete courses

### Student Roster
- Import students from CSV or Excel (.xlsx) files
- Required fields: Last Name, First Name, ID Number, Email Address
- Master student list tracking all students across courses

### Grading System
- **Bigrade grading scheme**: Prelim-Mid and Semis-Final periods
- **Customizable grade percentages** for all components
- **Fixed major exam weights**: 25% for Pre/Semi exam and 25% for Mid/Fin exam
- **Class standing coursework**: Assignments, Oral Recitation, Seatwork, Quizzes, Projects with varying percentages
- **Total validation**: All percentages must total 100%
- **Extra credits**: Added for both bigrades and automatically split equally

### Reports & Statistics
- Per-course statistics: pass/fail rates, class average, grade distribution
- Master student list with grades across all courses
- Course reports with summary statistics

### Export Functionality
- Export per-course grading sheets to XLSX or PDF
- Export all courses to XLSX or PDF
- Professional formatting matching standard class record formats

## Requirements

- Python 3.7+
- Required packages:
  ```
  PySimpleGUI
  pandas
  openpyxl
  reportlab
  ```

## Installation

```bash
# Clone the repository
git clone https://github.com/laseraph/class-record-app-CET.git
cd class-record-app-CET

# Install dependencies
pip install PySimpleGUI pandas openpyxl reportlab

# Run the application
python class_record_app.py
```

## Usage

### Quick Start
1. Run `python class_record_app.py`
2. The application loads with sample data (2 courses, 3 students)
3. Explore the dashboard to see all features

### Importing Students
1. Click "Import Students" from the dashboard
2. Select a course
3. Choose CSV or Excel file
4. File must contain: Last Name, First Name, ID Number, Email Address

### Managing Grading Criteria
1. Select a course
2. Click "Grading Criteria"
3. Add, edit, or delete grading components
4. Adjust percentages for Prelim-Mid and Semis-Final
5. Ensure total weights sum to 100%

### Entering Grades
1. Select a course
2. Click "Enter Grades"
3. Choose bigrade period (Prelim-Mid or Semis-Final)
4. Select student and enter scores for each component
5. Save grades and move to next student

### Exporting Data
1. From course detail view: Export single course to XLSX or PDF
2. From master list: Export all courses to XLSX or PDF

## Sample Data

The application includes sample data:
- **Courses**: Differential Equations, Engineering Economy
- **Students**: 3 sample students
- **Grading Components**: Pre-configured with standard weights

## Grading Scale

- A: 95-100% (Passed)
- B: 90-94.99% (Passed)
- C: 85-89.99% (Passed)
- D: 80-84.99% (Passed)
- E: 75-79.99% (Passed)
- F: Below 75% (Failed)

## File Structure

```
class-record-app-CET/
├── class_record_app.py    # Main application
├── sample_students.csv    # Sample student data for testing
└── README.md              # This file
```

## Notes

- Requires Tkinter to be installed on your system for PySimpleGUI
- On Linux: `sudo apt-get install python3-tk`
- On Windows: Tkinter is usually included with Python
- On macOS: `brew install python-tk`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
