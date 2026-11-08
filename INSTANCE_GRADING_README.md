# Instance-Based Grading System

This document describes the new instance-based grading system for the Class Record application.

## Overview

The system now supports **multiple instances per grading component**. For example:
- Assignment 1, Assignment 2, Assignment 3, etc.
- Quiz 1, Quiz 2, Quiz 3, etc.
- Recitation 1, Recitation 2, etc.

Each instance has its own:
- Title (e.g., "Assignment 1")
- Max score (e.g., 100)
- Weight fraction (e.g., 0.2 for 1 of 5 assignments)

## Database Schema

### New Tables

1. **`component_instances`** - Stores individual instances of grading components
   - `id` - Primary key
   - `component_id` - Foreign key to grading_components
   - `course_id` - Foreign key to courses
   - `instance_number` - Instance number (1, 2, 3, ...)
   - `title` - Instance title (e.g., "Assignment 1")
   - `max_score` - Maximum score for this instance
   - `weight_fraction` - Fraction of component weight (e.g., 0.2 for 1 of 5)
   - `period` - Either "prelim_mid" or "semis_final"

2. **`scores`** - Stores scores per student per instance
   - `id` - Primary key
   - `course_id` - Foreign key to courses
   - `student_id` - Foreign key to students
   - `instance_id` - Foreign key to component_instances
   - `score` - Score for this instance

3. **`grade_summary`** - Stores computed totals per student per course
   - All the same fields as before
   - Computed using instance-based formula

## Grade Computation Formula

The system uses the following formula to compute grades:

```
For each instance:
  contribution = (score / max_score) * weight_fraction * component_weight

Prelim-Mid Total = Sum of all Prelim-Mid instance contributions
Semis-Final Total = Sum of all Semis-Final instance contributions

Final Grade = min(50, Prelim-Mid Total) + min(50, Semis-Final Total)
```

### Example

For **Assignment 1** with:
- Score: 85/100
- Weight fraction: 0.2 (1 of 5 assignments)
- Component weight: 10% (of Prelim-Mid)

Contribution = (85/100) * 0.2 * 10% = 0.85 * 0.2 * 10 = **1.70%**

For **Prelim Exam** with:
- Score: 65/100
- Weight fraction: 1.0 (only one exam)
- Component weight: 25% (of Prelim-Mid)

Contribution = (65/100) * 1.0 * 25% = 0.65 * 25 = **16.25%**

## Default Structure

The system comes with a default grading structure:

### Prelim-Mid Period (50% total)
- **Assignments**: 10% (5 instances, each with weight_fraction = 0.2)
- **Oral Recitation**: 5% (5 instances, each with weight_fraction = 0.2)
- **Seatwork**: 5% (5 instances, each with weight_fraction = 0.2)
- **Quizzes**: 30% (3 instances, each with weight_fraction = 1/3)
- **Prelim Exam**: 25% (1 instance, weight_fraction = 1.0)

### Semis-Final Period (50% total)
- **Assignments**: 10% (5 instances, each with weight_fraction = 0.2)
- **Oral Recitation**: 5% (5 instances, each with weight_fraction = 0.2)
- **Seatwork**: 5% (5 instances, each with weight_fraction = 0.2)
- **Quizzes**: 30% (3 instances, each with weight_fraction = 1/3)
- **Midterm Exam**: 25% (1 instance, weight_fraction = 1.0)

## Dummy Data

The system includes comprehensive dummy data for verification:

- **1 Course**: Math 201E (2018) - Differential Equations
- **3 Students**:
  - CELESTIAL, Gerry Luz (ID: 59844380)
  - DELA CRUZ, Rojemie (ID: 59842976)
  - JAMERO, Van Vincent (ID: 59845710)
- **38 Instances**: 5 assignments, 5 recitations, 5 seatworks, 3 quizzes, 1 exam per period

### Sample Scores (Student 1)

**Prelim-Mid:**
- Assignments: 83, 88, 86, 73, 80 (out of 100 each)
- Recitations: 88, 83, 90, 86, 88 (out of 100 each)
- Seatworks: 43, 46, 42, 38, 44 (out of 50 each)
- Quizzes: 73, 78, 63 (out of 100 each)
- Prelim Exam: 63 (out of 100)

**Semis-Final:**
- Assignments: 88, 83, 90, 78, 86 (out of 100 each)
- Recitations: 83, 88, 86, 83, 90 (out of 100 each)
- Seatworks: 46, 43, 48, 40, 45 (out of 50 each)
- Quizzes: 78, 83, 68 (out of 100 each)
- Midterm Exam: 68 (out of 100)

### Expected Results (Student 1)

- **Prelim-Mid Total**: ~53.96% (capped at 50%)
- **Semis-Final Total**: ~57.14% (capped at 50%)
- **Final Grade**: 100.00%
- **Letter Grade**: A
- **Remarks**: Passed

## How to Use

### Running the Application

1. **Initialize the database** (first time only):
   ```bash
   python3 app_instance.py
   ```
   This will create the database and insert dummy data.

2. **Run the Flask application**:
   ```bash
   export FLASK_APP=app_instance.py
   flask run
   ```
   Or:
   ```bash
   python3 app_instance.py
   ```

3. **Access the application**:
   Open your browser to: http://localhost:5000

### Managing Grading Criteria

1. Go to **Dashboard** → Select a course → **Grading Criteria**
2. View current components and their weights
3. Add new components or update existing ones
4. Add/Edit/Delete instances for each component

### Entering Grades

1. Go to **Dashboard** → Select a course → **Grade Entry**
2. Select a student from the list
3. Enter scores for each instance
4. Click **Save Grades**
5. View the computed totals and final grade

### Exporting Data

- **Per-course XLSX**: Export a single course's grading sheet
- **Per-course PDF**: Export a single course's grading sheet as PDF
- **All courses XLSX**: Export all courses in one file

## Verification

To verify the computations match your Class Record:

1. Use the dummy data provided
2. Check the computation for each instance using the formula above
3. Verify the Prelim-Mid and Semis-Final totals
4. Verify the final grade is the sum of the two period totals (each capped at 50%)

### Example Verification

For **Student 1** (CELESTIAL, Gerry Luz):

**Prelim-Mid Assignments:**
- Assignment 1: (83/100) * 0.2 * 10% = 1.66%
- Assignment 2: (88/100) * 0.2 * 10% = 1.76%
- Assignment 3: (86/100) * 0.2 * 10% = 1.72%
- Assignment 4: (73/100) * 0.2 * 10% = 1.46%
- Assignment 5: (80/100) * 0.2 * 10% = 1.60%
- **Total**: 8.20%

**Prelim-Mid Recitations:**
- Recitation 1: (88/100) * 0.2 * 5% = 0.88%
- Recitation 2: (83/100) * 0.2 * 5% = 0.83%
- Recitation 3: (90/100) * 0.2 * 5% = 0.90%
- Recitation 4: (86/100) * 0.2 * 5% = 0.86%
- Recitation 5: (88/100) * 0.2 * 5% = 0.88%
- **Total**: 4.35%

**Prelim-Mid Seatworks:**
- Seatwork 1: (43/50) * 0.2 * 5% = 0.86%
- Seatwork 2: (46/50) * 0.2 * 5% = 0.92%
- Seatwork 3: (42/50) * 0.2 * 5% = 0.84%
- Seatwork 4: (38/50) * 0.2 * 5% = 0.76%
- Seatwork 5: (44/50) * 0.2 * 5% = 0.88%
- **Total**: 4.26%

**Prelim-Mid Quizzes:**
- Quiz 1: (73/100) * (1/3) * 30% = 7.30%
- Quiz 2: (78/100) * (1/3) * 30% = 7.80%
- Quiz 3: (63/100) * (1/3) * 30% = 6.30%
- **Total**: 21.40%

**Prelim Exam:**
- Prelim Exam: (63/100) * 1.0 * 25% = 15.75%

**Prelim-Mid Total**: 8.20 + 4.35 + 4.26 + 21.40 + 15.75 = **53.96%**
**Prelim-Mid (capped)**: min(50, 53.96) = **50.00%**

Similarly for Semis-Final, the total is **57.14%**, capped at **50.00%**.

**Final Grade**: 50.00 + 50.00 = **100.00%**

## Customization

You can customize the grading structure by:

1. **Adding new components**: Use the "Add New Component" button
2. **Adding instances**: Click "Add Instance" for any component
3. **Adjusting weights**: Edit the weight fraction for each instance
4. **Changing max scores**: Edit the max score for each instance

### Important Rules

1. **Major exams** must maintain 25% each (Pre/Semi and Mid/Fin)
2. **Class standing** components must sum to 50% per period
3. **Weight fractions** for instances in a component must sum to 1.0
4. **Extra credit** is split equally between both periods

## Technical Details

### Database File

The application uses SQLite database file: `class_record_instance.db`

### Key Functions

- `calculate_student_grade(course_id, student_id)`: Computes grade for a student
- `recalculate_all_grades(course_id)`: Recomputes grades for all students in a course
- `insert_dummy_data(db)`: Inserts test data for verification

### Templates

- `grade_entry_instance.html`: Grade entry with instance-level scoring
- `grading_criteria_instance.html`: Manage components and instances

## Support

For questions or issues, please refer to the main README.md or contact the developer.
