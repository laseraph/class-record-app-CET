# Class Record App

A comprehensive class record management system with **two versions available**:
- **Web Application** (Flask) - Modern browser-based interface
- **Desktop Application** (PySimpleGUI) - Traditional desktop interface

## 🚀 Quick Start

### Option 1: Web Application (Recommended)

The modern web-based version with a professional UI.

```bash
# Clone the repository
git clone https://github.com/laseraph/class-record-app-CET.git
cd class-record-app-CET

# Install dependencies
pip install -r requirements.txt

# Run the web application
python app.py

# Open in browser
# Go to http://localhost:5000
```

### Option 2: Desktop Application

The traditional desktop version using PySimpleGUI.

```bash
# Install dependencies
pip install PySimpleGUI pandas openpyxl reportlab

# Run the desktop application
python class_record_app.py
```

---

## ✨ Features

### Course Management
- ✅ Create, view, edit, and delete courses
- ✅ Add course details: schedule, room, course code, offering number, title, and description
- ✅ Organize multiple courses in one system

### Student Roster
- ✅ Import students from CSV or Excel (.xlsx) files
- ✅ Flexible column name detection (Last Name, First Name, ID Number, Email)
- ✅ Master student list tracking all students across courses
- ✅ Link students to specific courses

### Grading System
- ✅ **Bigrade grading scheme**: Prelim-Mid and Semis-Final periods
- ✅ **Customizable grade percentages** for all components
- ✅ **Fixed major exam weights**: 25% for Pre/Semi exam and 25% for Mid/Fin exam
- ✅ **Class standing coursework**: Assignments, Oral Recitation, Seatwork, Quizzes, Projects
- ✅ **Total validation**: All percentages must total 100%
- ✅ **Extra credits**: Added for both bigrades and automatically split equally

### Grade Entry
- ✅ Enter grades for each student per component
- ✅ Automatic grade calculation with weighted scores
- ✅ Final grades, letter grades, and remarks automatically computed
- ✅ Save and move to next student for efficient data entry

### Reports & Statistics
- ✅ Per-course statistics: pass/fail rates, class average, grade distribution
- ✅ Master student list with grades across all courses
- ✅ Course reports with summary statistics
- ✅ Visual grade distribution (A, B, C, D, E, F)

### Export Functionality
- ✅ Export per-course grading sheets to XLSX format
- ✅ Export per-course grading sheets to PDF format
- ✅ Export all courses to XLSX format
- ✅ Export all courses to PDF format
- ✅ Professional formatting with headers, colors, and proper layout

---

## 📁 Project Structure

```
class-record-app-CET/
├── app.py                          # Flask web application
├── class_record_app.py             # Desktop application (PySimpleGUI)
├── requirements.txt                # Python dependencies
├── sample_students.csv             # Sample student data
├── static/
│   ├── css/
│   │   └── style.css               # Custom CSS styles
│   └── js/
│       └── main.js                 # Custom JavaScript
└── templates/
    ├── base.html                    # Base template
    ├── add_course.html              # Add course form
    ├── course_detail.html           # Course detail view
    ├── dashboard.html               # Main dashboard
    ├── edit_course.html             # Edit course form
    ├── grade_entry.html             # Grade entry form
    ├── grading_criteria.html         # Grading criteria management
    ├── import_students.html         # Student import form
    └── master_list.html             # Master student list
```

---

## 🌐 Web Application Details

### Features
- **Modern UI**: Bootstrap 5 with custom styling
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Navigation**: Easy-to-use menu and breadcrumbs
- **Real-time Updates**: Instant feedback and validation
- **Professional Look**: Clean, modern interface

### Pages
1. **Dashboard**: Overview of all courses with statistics
2. **Course Detail**: Detailed view of a specific course with roster and statistics
3. **Grade Entry**: Form for entering student grades
4. **Grading Criteria**: Manage grading components and weights
5. **Add/Edit Course**: Course management forms
6. **Import Students**: Upload student data from files
7. **Master List**: View all students across all courses

---

## 💻 Desktop Application Details

### Features
- **PySimpleGUI**: Modern desktop UI framework
- **DarkTeal9 Theme**: Professional dark theme
- **Modal Dialogs**: Clean form interactions
- **Table Views**: Styled tables with sorting and filtering
- **Color Coding**: Green for passed, red for failed

### Requirements
- Python 3.7+
- Tkinter (usually included with Python)
- On Linux: `sudo apt-get install python3-tk`
- On macOS: `brew install python-tk`

---

## 📊 Grading Scale

| Grade | Range | Remarks |
|-------|-------|---------|
| A | 95-100% | Passed |
| B | 90-94.99% | Passed |
| C | 85-89.99% | Passed |
| D | 80-84.99% | Passed |
| E | 75-79.99% | Passed |
| F | Below 75% | Failed |

---

## 📝 Sample Data

Both applications include sample data:
- **2 Courses**: Differential Equations, Engineering Economy
- **3 Students**: Sample student records
- **6 Grading Components**: Pre-configured with standard weights

---

## 🎨 UI Comparison

### Web Application (Flask)
- ✅ Browser-based - Access from any device
- ✅ Modern, professional interface
- ✅ Responsive design
- ✅ Better for teams and remote access
- ✅ Built-in navigation and breadcrumbs

### Desktop Application (PySimpleGUI)
- ✅ Traditional desktop experience
- ✅ Faster for local use
- ✅ No browser required
- ✅ Good for single-user scenarios

---

## 🔧 Configuration

### Web Application
- Edit `app.py` to change database location
- Modify `static/css/style.css` for custom styling
- Update `templates/` for custom HTML layouts

### Desktop Application
- Edit `class_record_app.py` for customization
- Modify theme in the `__init__` method

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with Flask and Bootstrap for the web version
- Built with PySimpleGUI for the desktop version
- Uses pandas, openpyxl, and reportlab for data processing and export
