"""
Class Record Web Application - Instance-Based Grading
Modern web-based class record system with Flask
Supports multiple instances per grading component (Assignment 1, Assignment 2, etc.)

To run: python app_instance.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import sqlite3
import pandas as pd
import openpyxl
from openpyxl.styles import Font
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

DATABASE = 'class_record_instance.db'


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize database with instance-based grading schema"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Drop all tables
        cursor.execute('DROP TABLE IF EXISTS grade_summary')
        cursor.execute('DROP TABLE IF EXISTS scores')
        cursor.execute('DROP TABLE IF EXISTS component_instances')
        cursor.execute('DROP TABLE IF EXISTS grading_components')
        cursor.execute('DROP TABLE IF EXISTS course_students')
        cursor.execute('DROP TABLE IF EXISTS students')
        cursor.execute('DROP TABLE IF EXISTS courses')
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                course_title TEXT NOT NULL,
                offering_number TEXT DEFAULT '1',
                description TEXT,
                schedule TEXT,
                room TEXT,
                days TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                id_number TEXT NOT NULL UNIQUE,
                email TEXT,
                status TEXT DEFAULT 'Active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grading_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'class_standing',
                prelim_mid_weight REAL DEFAULT 0.0,
                semis_final_weight REAL DEFAULT 0.0,
                max_score REAL DEFAULT 100.0,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS component_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER,
                course_id INTEGER,
                instance_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                max_score REAL DEFAULT 100.0,
                weight_fraction REAL DEFAULT 1.0,
                period TEXT NOT NULL,
                FOREIGN KEY (component_id) REFERENCES grading_components(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                student_id INTEGER,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(course_id, student_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                student_id INTEGER,
                instance_id INTEGER,
                score REAL DEFAULT 0.0,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (instance_id) REFERENCES component_instances(id),
                UNIQUE(course_id, student_id, instance_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grade_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                student_id INTEGER,
                prelim_mid_total REAL DEFAULT 0.0,
                semis_final_total REAL DEFAULT 0.0,
                final_grade REAL DEFAULT 0.0,
                letter_grade TEXT DEFAULT 'F',
                remarks TEXT DEFAULT 'Failed',
                extra_credit REAL DEFAULT 0.0,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(course_id, student_id)
            )
        ''')
        
        db.commit()
        
        # Insert dummy data if empty
        cursor.execute('SELECT COUNT(*) FROM courses')
        if cursor.fetchone()[0] == 0:
            insert_dummy_data(db)


def insert_dummy_data(db):
    """Insert comprehensive dummy data for verification"""
    cursor = db.cursor()
    
    print("Inserting dummy data...")
    
    # Course
    cursor.execute('''
        INSERT INTO courses (course_code, course_title, offering_number, description, schedule, room, days)
        VALUES ('Math 201E (2018)', 'Differential Equations', '1', 
                'Advanced differential equations for engineering students', 
                '8:00-9:00 AM', 'CH504', 'MWF')
    ''')
    course_id = cursor.lastrowid
    
    # Students
    students_data = [
        ('CELESTIAL', 'Gerry Luz', '59844380', 'gerry.celestial@email.com'),
        ('DELA CRUZ', 'Rojemie', '59842976', 'rojemie.delacruz@email.com'),
        ('JAMERO', 'Van Vincent', '59845710', 'van.jamero@email.com'),
    ]
    
    student_ids = []
    for last, first, id_num, email in students_data:
        cursor.execute('INSERT INTO students (last_name, first_name, id_number, email) VALUES (?, ?, ?, ?)',
                     (last, first, id_num, email))
        student_ids.append(cursor.lastrowid)
    
    # Link students to course
    for student_id in student_ids:
        cursor.execute('INSERT INTO course_students (course_id, student_id) VALUES (?, ?)',
                     (course_id, student_id))
    
    # Grading components
    components = [
        ('Assignments', 'class_standing', 10.0, 10.0, 100.0),
        ('Oral Recitation', 'class_standing', 5.0, 5.0, 100.0),
        ('Seatwork', 'class_standing', 5.0, 5.0, 50.0),
        ('Quizzes', 'class_standing', 30.0, 30.0, 100.0),
        ('Pre / Semi exam', 'major_exam', 25.0, 0.0, 100.0),
        ('Mid / Fin exam', 'major_exam', 0.0, 25.0, 100.0),
    ]
    
    comp_ids = {}
    for name, category, prelim, semis, max_score in components:
        cursor.execute('''
            INSERT INTO grading_components (course_id, name, category, prelim_mid_weight, semis_final_weight, max_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (course_id, name, category, prelim, semis, max_score))
        comp_ids[name] = cursor.lastrowid
    
    # Component instances - Prelim-Mid
    prelim_instances = [
        ('Assignments', 1, 'Assignment 1', 100.0, 0.2),
        ('Assignments', 2, 'Assignment 2', 100.0, 0.2),
        ('Assignments', 3, 'Assignment 3', 100.0, 0.2),
        ('Assignments', 4, 'Assignment 4', 100.0, 0.2),
        ('Assignments', 5, 'Assignment 5', 100.0, 0.2),
        ('Oral Recitation', 1, 'Recitation 1', 100.0, 0.2),
        ('Oral Recitation', 2, 'Recitation 2', 100.0, 0.2),
        ('Oral Recitation', 3, 'Recitation 3', 100.0, 0.2),
        ('Oral Recitation', 4, 'Recitation 4', 100.0, 0.2),
        ('Oral Recitation', 5, 'Recitation 5', 100.0, 0.2),
        ('Seatwork', 1, 'Seatwork 1', 50.0, 0.2),
        ('Seatwork', 2, 'Seatwork 2', 50.0, 0.2),
        ('Seatwork', 3, 'Seatwork 3', 50.0, 0.2),
        ('Seatwork', 4, 'Seatwork 4', 50.0, 0.2),
        ('Seatwork', 5, 'Seatwork 5', 50.0, 0.2),
        ('Quizzes', 1, 'Quiz 1', 100.0, 1/3),
        ('Quizzes', 2, 'Quiz 2', 100.0, 1/3),
        ('Quizzes', 3, 'Quiz 3', 100.0, 1/3),
        ('Pre / Semi exam', 1, 'Prelim Exam', 100.0, 1.0),
    ]
    
    for comp_name, inst_num, title, max_score, weight_fraction in prelim_instances:
        comp_id = comp_ids[comp_name]
        cursor.execute('''
            INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (comp_id, course_id, inst_num, title, max_score, weight_fraction, 'prelim_mid'))
    
    # Component instances - Semis-Final
    semis_instances = [
        ('Assignments', 1, 'Assignment 6', 100.0, 0.2),
        ('Assignments', 2, 'Assignment 7', 100.0, 0.2),
        ('Assignments', 3, 'Assignment 8', 100.0, 0.2),
        ('Assignments', 4, 'Assignment 9', 100.0, 0.2),
        ('Assignments', 5, 'Assignment 10', 100.0, 0.2),
        ('Oral Recitation', 1, 'Recitation 6', 100.0, 0.2),
        ('Oral Recitation', 2, 'Recitation 7', 100.0, 0.2),
        ('Oral Recitation', 3, 'Recitation 8', 100.0, 0.2),
        ('Oral Recitation', 4, 'Recitation 9', 100.0, 0.2),
        ('Oral Recitation', 5, 'Recitation 10', 100.0, 0.2),
        ('Seatwork', 1, 'Seatwork 6', 50.0, 0.2),
        ('Seatwork', 2, 'Seatwork 7', 50.0, 0.2),
        ('Seatwork', 3, 'Seatwork 8', 50.0, 0.2),
        ('Seatwork', 4, 'Seatwork 9', 50.0, 0.2),
        ('Seatwork', 5, 'Seatwork 10', 50.0, 0.2),
        ('Quizzes', 1, 'Quiz 4', 100.0, 1/3),
        ('Quizzes', 2, 'Quiz 5', 100.0, 1/3),
        ('Quizzes', 3, 'Quiz 6', 100.0, 1/3),
        ('Mid / Fin exam', 1, 'Midterm Exam', 100.0, 1.0),
    ]
    
    for comp_name, inst_num, title, max_score, weight_fraction in semis_instances:
        comp_id = comp_ids[comp_name]
        cursor.execute('''
            INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (comp_id, course_id, inst_num, title, max_score, weight_fraction, 'semis_final'))
    
    db.commit()
    
    # Sample scores from user data
    prelim_scores = {
        'Assignment 1': 85.0, 'Assignment 2': 90.0, 'Assignment 3': 88.0,
        'Assignment 4': 75.0, 'Assignment 5': 82.0,
        'Recitation 1': 90.0, 'Recitation 2': 85.0, 'Recitation 3': 92.0,
        'Recitation 4': 88.0, 'Recitation 5': 90.0,
        'Seatwork 1': 45.0, 'Seatwork 2': 48.0, 'Seatwork 3': 44.0,
        'Seatwork 4': 40.0, 'Seatwork 5': 46.0,
        'Quiz 1': 75.0, 'Quiz 2': 80.0, 'Quiz 3': 65.0,
        'Prelim Exam': 65.0,
    }
    
    semis_scores = {
        'Assignment 6': 90.0, 'Assignment 7': 85.0, 'Assignment 8': 92.0,
        'Assignment 9': 80.0, 'Assignment 10': 88.0,
        'Recitation 6': 85.0, 'Recitation 7': 90.0, 'Recitation 8': 88.0,
        'Recitation 9': 85.0, 'Recitation 10': 92.0,
        'Seatwork 6': 48.0, 'Seatwork 7': 45.0, 'Seatwork 8': 50.0,
        'Seatwork 9': 42.0, 'Seatwork 10': 47.0,
        'Quiz 4': 80.0, 'Quiz 5': 85.0, 'Quiz 6': 70.0,
        'Midterm Exam': 70.0,
    }
    
    # Insert scores for all students
    cursor.execute('SELECT id, title FROM component_instances WHERE course_id = ?', (course_id,))
    instances = cursor.fetchall()
    
    for student_idx, student_id in enumerate(student_ids):
        for instance_id, title in instances:
            if title in prelim_scores:
                base = prelim_scores[title]
            elif title in semis_scores:
                base = semis_scores[title]
            else:
                base = 80.0
            
            # Add variation per student for testing
            variation = (student_idx * 2) - 2  # Small variation
            score = max(0, min(100, base + variation))
            
            cursor.execute('''
                INSERT INTO scores (course_id, student_id, instance_id, score)
                VALUES (?, ?, ?, ?)
            ''', (course_id, student_id, instance_id, score))
    
    db.commit()
    
    # Calculate grades
    for student_id in student_ids:
        calculate_student_grade(course_id, student_id)
    
    db.commit()
    print("Dummy data inserted successfully!")


def calculate_student_grade(course_id, student_id):
    """Calculate grade using instance-based computation"""
    db = get_db()
    cursor = db.cursor()
    
    # Get all instances for this course
    cursor.execute('''
        SELECT ci.id, ci.title, ci.max_score, ci.weight_fraction, ci.period,
               gc.prelim_mid_weight, gc.semis_final_weight
        FROM component_instances ci
        JOIN grading_components gc ON ci.component_id = gc.id
        WHERE ci.course_id = ?
        ORDER BY ci.period, gc.name, ci.instance_number
    ''', (course_id,))
    instances = cursor.fetchall()
    
    # Get all scores for this student
    cursor.execute('''
        SELECT instance_id, score FROM scores
        WHERE course_id = ? AND student_id = ?
    ''', (course_id, student_id))
    scores = {row['instance_id']: row['score'] for row in cursor.fetchall()}
    
    # Get extra credit
    cursor.execute('''
        SELECT extra_credit FROM grade_summary
        WHERE course_id = ? AND student_id = ?
    ''', (course_id, student_id))
    row = cursor.fetchone()
    extra_credit = row['extra_credit'] if row else 0.0
    
    # Calculate Prelim-Mid total
    prelim_total = 0.0
    for inst in instances:
        if inst['period'] != 'prelim_mid':
            continue
        instance_id = inst['id']
        score = scores.get(instance_id, 0.0)
        max_score = inst['max_score']
        weight_fraction = inst['weight_fraction']
        component_weight = inst['prelim_mid_weight']
        contribution = (score / max_score) * weight_fraction * component_weight
        prelim_total += contribution
    
    # Calculate Semis-Final total
    semis_total = 0.0
    for inst in instances:
        if inst['period'] != 'semis_final':
            continue
        instance_id = inst['id']
        score = scores.get(instance_id, 0.0)
        max_score = inst['max_score']
        weight_fraction = inst['weight_fraction']
        component_weight = inst['semis_final_weight']
        contribution = (score / max_score) * weight_fraction * component_weight
        semis_total += contribution
    
    # Apply extra credit (split equally)
    prelim_total = min(50, prelim_total + extra_credit / 2)
    semis_total = min(50, semis_total + extra_credit / 2)
    final_grade = prelim_total + semis_total
    
    # Determine letter grade
    if final_grade >= 95:
        letter_grade, remarks = 'A', 'Passed'
    elif final_grade >= 90:
        letter_grade, remarks = 'B', 'Passed'
    elif final_grade >= 85:
        letter_grade, remarks = 'C', 'Passed'
    elif final_grade >= 80:
        letter_grade, remarks = 'D', 'Passed'
    elif final_grade >= 75:
        letter_grade, remarks = 'E', 'Passed'
    else:
        letter_grade, remarks = 'F', 'Failed'
    
    cursor.execute('''
        INSERT OR REPLACE INTO grade_summary
        (course_id, student_id, prelim_mid_total, semis_final_total, final_grade, letter_grade, remarks, extra_credit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (course_id, student_id, prelim_total, semis_total, final_grade, letter_grade, remarks, extra_credit))
    
    db.commit()


def recalculate_all_grades(course_id):
    """Recalculate grades for all students in a course"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT student_id FROM course_students WHERE course_id = ?', (course_id,))
    student_ids = [row['student_id'] for row in cursor.fetchall()]
    for student_id in student_ids:
        calculate_student_grade(course_id, student_id)
    db.commit()


# Initialize database
init_db()


# ============================================================================
# Flask Routes
# ============================================================================

@app.route('/')
def dashboard():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    
    course_list = []
    total_passed = 0
    total_failed = 0
    total_students = 0
    
    for course in courses:
        cursor.execute('SELECT COUNT(*) FROM course_students WHERE course_id = ?', (course['id'],))
        student_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM grade_summary WHERE course_id = ? AND remarks = \'Passed\'', (course['id'],))
        passed = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM grade_summary WHERE course_id = ? AND remarks = \'Failed\'', (course['id'],))
        failed = cursor.fetchone()[0]
        
        pass_rate = (passed / student_count * 100) if student_count > 0 else 0
        
        course_list.append({
            'id': course['id'],
            'full_name': f"{course['course_title']} ({course['course_code']})",
            'course_code': course['course_code'],
            'schedule': f"{course['schedule']} {course['days']}",
            'room': course['room'],
            'student_count': student_count,
            'pass_rate': round(pass_rate, 1)
        })
        
        total_passed += passed
        total_failed += failed
        total_students += student_count
    
    overall_pass_rate = (total_passed / total_students * 100) if total_students > 0 else 0
    
    return render_template('dashboard.html', 
                         courses=course_list,
                         total_courses=len(courses),
                         total_students=total_students,
                         overall_pass_rate=round(overall_pass_rate, 1))


@app.route('/course/<int:course_id>')
def course_detail(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    cursor.execute('''
        SELECT s.* FROM students s
        JOIN course_students cs ON s.id = cs.student_id
        WHERE cs.course_id = ?
        ORDER BY s.last_name, s.first_name
    ''', (course_id,))
    students = cursor.fetchall()
    
    roster = []
    for student in students:
        cursor.execute('SELECT * FROM grade_summary WHERE course_id = ? AND student_id = ?', 
                     (course_id, student['id']))
        grade = cursor.fetchone()
        roster.append({'student': student, 'grade': grade})
    
    cursor.execute('SELECT * FROM grading_components WHERE course_id = ? ORDER BY name', (course_id,))
    components = cursor.fetchall()
    
    cursor.execute('''
        SELECT ci.*, gc.name as component_name
        FROM component_instances ci
        JOIN grading_components gc ON ci.component_id = gc.id
        WHERE ci.course_id = ?
        ORDER BY ci.period, gc.name, ci.instance_number
    ''', (course_id,))
    instances = cursor.fetchall()
    
    total = len(students)
    passed = sum(1 for r in roster if r['grade'] and r['grade']['remarks'] == 'Passed')
    failed = sum(1 for r in roster if r['grade'] and r['grade']['remarks'] == 'Failed')
    pass_rate = (passed / total * 100) if total > 0 else 0
    fail_rate = (failed / total * 100) if total > 0 else 0
    avg = sum(r['grade']['final_grade'] for r in roster if r['grade']) / total if total > 0 else 0
    
    dist = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
    for r in roster:
        if r['grade'] and r['grade']['letter_grade'] in dist:
            dist[r['grade']['letter_grade']] += 1
    
    instances_by_period = {'prelim_mid': [], 'semis_final': []}
    for inst in instances:
        instances_by_period[inst['period']].append(inst)
    
    return render_template('course_detail.html',
                         course=course,
                         roster=roster,
                         components=components,
                         instances=instances,
                         instances_by_period=instances_by_period,
                         total=total,
                         passed=passed,
                         failed=failed,
                         pass_rate=round(pass_rate, 1),
                         fail_rate=round(fail_rate, 1),
                         avg=round(avg, 2),
                         dist=dist)


@app.route('/course/<int:course_id>/grades', methods=['GET', 'POST'])
def grade_entry(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    cursor.execute('''
        SELECT ci.id, ci.title, ci.max_score, ci.weight_fraction, ci.period,
               gc.name as component_name, gc.prelim_mid_weight, gc.semis_final_weight
        FROM component_instances ci
        JOIN grading_components gc ON ci.component_id = gc.id
        WHERE ci.course_id = ?
        ORDER BY ci.period, gc.name, ci.instance_number
    ''', (course_id,))
    instances = cursor.fetchall()
    
    cursor.execute('''
        SELECT s.* FROM students s
        JOIN course_students cs ON s.id = cs.student_id
        WHERE cs.course_id = ?
        ORDER BY s.last_name, s.first_name
    ''', (course_id,))
    students = cursor.fetchall()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        
        for inst in instances:
            instance_id = inst['id']
            score_field = f'score_{instance_id}'
            score = request.form.get(score_field, '')
            
            if score:
                try:
                    score = float(score)
                    score = max(0, min(inst['max_score'], score))
                except:
                    score = 0
            else:
                score = 0
            
            cursor.execute('''
                INSERT OR REPLACE INTO scores (course_id, student_id, instance_id, score)
                VALUES (?, ?, ?, ?)
            ''', (course_id, student_id, instance_id, score))
        
        db.commit()
        calculate_student_grade(course_id, student_id)
        
        flash('Grades saved successfully!', 'success')
        return redirect(url_for('grade_entry', course_id=course_id, student_id=student_id))
    
    current_student_id = request.args.get('student_id', students[0]['id'] if students else None)
    
    scores = {}
    if current_student_id:
        cursor.execute('SELECT instance_id, score FROM scores WHERE course_id = ? AND student_id = ?',
                     (course_id, current_student_id))
        scores = {row['instance_id']: row['score'] for row in cursor.fetchall()}
    
    grade_summary = None
    if current_student_id:
        cursor.execute('SELECT * FROM grade_summary WHERE course_id = ? AND student_id = ?',
                     (course_id, current_student_id))
        grade_summary = cursor.fetchone()
    
    instances_by_component = {}
    for inst in instances:
        comp_name = inst['component_name']
        if comp_name not in instances_by_component:
            instances_by_component[comp_name] = []
        instances_by_component[comp_name].append(inst)
    
    prelim_total = 0.0
    semis_total = 0.0
    for inst in instances:
        instance_id = inst['id']
        score = scores.get(instance_id, 0.0)
        max_score = inst['max_score']
        weight_fraction = inst['weight_fraction']
        
        if inst['period'] == 'prelim_mid':
            component_weight = inst['prelim_mid_weight']
            contribution = (score / max_score) * weight_fraction * component_weight
            prelim_total += contribution
        else:
            component_weight = inst['semis_final_weight']
            contribution = (score / max_score) * weight_fraction * component_weight
            semis_total += contribution
    
    return render_template('grade_entry_instance.html',
                         course=course,
                         instances=instances,
                         instances_by_component=instances_by_component,
                         students=students,
                         current_student_id=current_student_id,
                         scores=scores,
                         grade_summary=grade_summary,
                         prelim_total=prelim_total,
                         semis_total=semis_total)


@app.route('/course/<int:course_id>/grading-criteria', methods=['GET', 'POST'])
def grading_criteria(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    cursor.execute('SELECT * FROM grading_components WHERE course_id = ? ORDER BY name', (course_id,))
    components = cursor.fetchall()
    
    cursor.execute('''
        SELECT ci.*, gc.name as component_name
        FROM component_instances ci
        JOIN grading_components gc ON ci.component_id = gc.id
        WHERE ci.course_id = ?
        ORDER BY ci.period, gc.name, ci.instance_number
    ''', (course_id,))
    instances = cursor.fetchall()
    
    instances_by_component = {}
    for inst in instances:
        comp_name = inst['component_name']
        if comp_name not in instances_by_component:
            instances_by_component[comp_name] = []
        instances_by_component[comp_name].append(inst)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_component':
            name = request.form.get('name')
            category = request.form.get('category')
            prelim_weight = float(request.form.get('prelim_weight', 0))
            semis_weight = float(request.form.get('semis_weight', 0))
            max_score = float(request.form.get('max_score', 100))
            
            cursor.execute('''
                INSERT INTO grading_components (course_id, name, category, prelim_mid_weight, semis_final_weight, max_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (course_id, name, category, prelim_weight, semis_weight, max_score))
            db.commit()
            flash('Component added!', 'success')
            return redirect(url_for('grading_criteria', course_id=course_id))
        
        elif action == 'update_component':
            comp_id = request.form.get('component_id')
            prelim_weight = float(request.form.get(f'prelim_{comp_id}', 0))
            semis_weight = float(request.form.get(f'semis_{comp_id}', 0))
            
            cursor.execute('''
                UPDATE grading_components SET prelim_mid_weight = ?, semis_final_weight = ?
                WHERE id = ?
            ''', (prelim_weight, semis_weight, comp_id))
            db.commit()
            recalculate_all_grades(course_id)
            flash('Component weights updated!', 'success')
            return redirect(url_for('grading_criteria', course_id=course_id))
        
        elif action == 'add_instance':
            comp_id = request.form.get('component_id')
            instance_number = int(request.form.get('instance_number'))
            title = request.form.get('title')
            max_score = float(request.form.get('max_score', 100))
            weight_fraction = float(request.form.get('weight_fraction', 1.0))
            period = request.form.get('period')
            
            cursor.execute('''
                INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (comp_id, course_id, instance_number, title, max_score, weight_fraction, period))
            db.commit()
            flash('Instance added!', 'success')
            return redirect(url_for('grading_criteria', course_id=course_id))
        
        elif action == 'update_instance':
            instance_id = request.form.get('instance_id')
            title = request.form.get(f'title_{instance_id}')
            max_score = float(request.form.get(f'max_score_{instance_id}', 100))
            weight_fraction = float(request.form.get(f'weight_fraction_{instance_id}', 1.0))
            
            cursor.execute('''
                UPDATE component_instances SET title = ?, max_score = ?, weight_fraction = ?
                WHERE id = ?
            ''', (title, max_score, weight_fraction, instance_id))
            db.commit()
            recalculate_all_grades(course_id)
            flash('Instance updated!', 'success')
            return redirect(url_for('grading_criteria', course_id=course_id))
        
        elif action == 'delete_instance':
            instance_id = request.form.get('instance_id')
            cursor.execute('DELETE FROM component_instances WHERE id = ?', (instance_id,))
            cursor.execute('DELETE FROM scores WHERE instance_id = ?', (instance_id,))
            db.commit()
            recalculate_all_grades(course_id)
            flash('Instance deleted!', 'success')
            return redirect(url_for('grading_criteria', course_id=course_id))
    
    return render_template('grading_criteria_instance.html',
                         course=course,
                         components=components,
                         instances=instances,
                         instances_by_component=instances_by_component)


@app.route('/import-students', methods=['GET', 'POST'])
def import_students():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        if course_id:
            return redirect(url_for('add_students_to_course', course_id=course_id))
    
    return render_template('import_students.html', courses=courses)


@app.route('/course/<int:course_id>/add-students', methods=['GET', 'POST'])
def add_students_to_course(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    cursor.execute('SELECT * FROM courses')
    all_courses = cursor.fetchall()
    
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            try:
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.filename.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(file)
                else:
                    flash('Unsupported file format', 'error')
                    return redirect(url_for('add_students_to_course', course_id=course_id))
                
                imported = 0
                for _, row in df.iterrows():
                    last_name = str(row.get('Last Name', row.get('last_name', ''))).strip()
                    first_name = str(row.get('First Name', row.get('first_name', ''))).strip()
                    id_number = str(row.get('ID Number', row.get('id_number', ''))).strip()
                    email = str(row.get('Email Address', row.get('email', ''))).strip()
                    
                    if not last_name or not first_name:
                        continue
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO students (last_name, first_name, id_number, email)
                        VALUES (?, ?, ?, ?)
                    ''', (last_name, first_name, id_number, email))
                    
                    if cursor.rowcount == 0:
                        cursor.execute('''
                            UPDATE students SET last_name = ?, first_name = ?, id_number = ?, email = ?
                            WHERE id_number = ?
                        ''', (last_name, first_name, id_number, email, id_number))
                    
                    student_id = cursor.lastrowid
                    if student_id == 0:
                        cursor.execute('SELECT id FROM students WHERE id_number = ?', (id_number,))
                        student_id = cursor.fetchone()['id']
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO course_students (course_id, student_id)
                        VALUES (?, ?)
                    ''', (course_id, student_id))
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO grade_summary (course_id, student_id)
                        VALUES (?, ?)
                    ''', (course_id, student_id))
                    
                    imported += 1
                
                db.commit()
                flash(f'Successfully imported {imported} students!', 'success')
                return redirect(url_for('course_detail', course_id=course_id))
            
            except Exception as e:
                db.rollback()
                flash(f'Error importing file: {str(e)}', 'error')
                return redirect(url_for('add_students_to_course', course_id=course_id))
    
    return render_template('import_students.html', courses=all_courses, selected_course_id=course_id)


@app.route('/course/add', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        course_title = request.form.get('course_title')
        offering_number = request.form.get('offering_number', '1')
        description = request.form.get('description', '')
        schedule = request.form.get('schedule', '')
        room = request.form.get('room', '')
        days = request.form.get('days', '')
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO courses (course_code, course_title, offering_number, description, schedule, room, days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (course_code, course_title, offering_number, description, schedule, room, days))
        
        course_id = cursor.lastrowid
        db.commit()
        
        # Add default grading components
        components = [
            ('Assignments', 'class_standing', 10.0, 10.0, 100.0),
            ('Oral Recitation', 'class_standing', 5.0, 5.0, 100.0),
            ('Seatwork', 'class_standing', 5.0, 5.0, 50.0),
            ('Quizzes', 'class_standing', 30.0, 30.0, 100.0),
            ('Pre / Semi exam', 'major_exam', 25.0, 0.0, 100.0),
            ('Mid / Fin exam', 'major_exam', 0.0, 25.0, 100.0),
        ]
        
        for name, category, prelim, semis, max_score in components:
            cursor.execute('''
                INSERT INTO grading_components (course_id, name, category, prelim_mid_weight, semis_final_weight, max_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (course_id, name, category, prelim, semis, max_score))
            comp_id = cursor.lastrowid
            
            if name == 'Assignments':
                for i in range(1, 6):
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Assignment {i}', 100.0, 0.2, 'prelim_mid'))
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Assignment {i+5}', 100.0, 0.2, 'semis_final'))
            
            elif name == 'Oral Recitation':
                for i in range(1, 6):
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Recitation {i}', 100.0, 0.2, 'prelim_mid'))
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Recitation {i+5}', 100.0, 0.2, 'semis_final'))
            
            elif name == 'Seatwork':
                for i in range(1, 6):
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Seatwork {i}', 50.0, 0.2, 'prelim_mid'))
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Seatwork {i+5}', 50.0, 0.2, 'semis_final'))
            
            elif name == 'Quizzes':
                for i in range(1, 4):
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Quiz {i}', 100.0, 1/3, 'prelim_mid'))
                    cursor.execute('''
                        INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (comp_id, course_id, i, f'Quiz {i+3}', 100.0, 1/3, 'semis_final'))
            
            elif name == 'Pre / Semi exam':
                cursor.execute('''
                    INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (comp_id, course_id, 1, 'Prelim Exam', 100.0, 1.0, 'prelim_mid'))
            
            elif name == 'Mid / Fin exam':
                cursor.execute('''
                    INSERT INTO component_instances (component_id, course_id, instance_number, title, max_score, weight_fraction, period)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (comp_id, course_id, 1, 'Midterm Exam', 100.0, 1.0, 'semis_final'))
        
        db.commit()
        flash('Course added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_course.html')


@app.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        course_title = request.form.get('course_title')
        offering_number = request.form.get('offering_number')
        description = request.form.get('description')
        schedule = request.form.get('schedule')
        room = request.form.get('room')
        days = request.form.get('days')
        
        cursor.execute('''
            UPDATE courses SET course_code = ?, course_title = ?, offering_number = ?, 
            description = ?, schedule = ?, room = ?, days = ?
            WHERE id = ?
        ''', (course_code, course_title, offering_number, description, schedule, room, days, course_id))
        
        db.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course_id))
    
    return render_template('edit_course.html', course=course)


@app.route('/master-list')
def master_list():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM students ORDER BY last_name, first_name')
    students = cursor.fetchall()
    
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    
    master_data = []
    for student in students:
        grades = []
        for course in courses:
            cursor.execute('''
                SELECT g.* FROM grade_summary g
                WHERE g.student_id = ? AND g.course_id = ?
            ''', (student['id'], course['id']))
            grade = cursor.fetchone()
            if grade:
                grades.append(f"{course['course_code']}: {grade['final_grade']:.2f}")
            else:
                grades.append(f"{course['course_code']}: N/A")
        
        master_data.append({'student': student, 'grades': ', '.join(grades)})
    
    course_stats = []
    for course in courses:
        cursor.execute('SELECT COUNT(*) FROM course_students WHERE course_id = ?', (course['id'],))
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM grade_summary WHERE course_id = ? AND remarks = \'Passed\'', (course['id'],))
        passed = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM grade_summary WHERE course_id = ? AND remarks = \'Failed\'', (course['id'],))
        failed = cursor.fetchone()[0]
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        course_stats.append({
            'course': course,
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(pass_rate, 1)
        })
    
    return render_template('master_list.html',
                         students=master_data,
                         course_stats=course_stats)


@app.route('/export/course/<int:course_id>/xlsx')
def export_course_xlsx(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    cursor.execute('''
        SELECT s.* FROM students s
        JOIN course_students cs ON s.id = cs.student_id
        WHERE cs.course_id = ?
        ORDER BY s.last_name, s.first_name
    ''', (course_id,))
    students = cursor.fetchall()
    
    cursor.execute('SELECT * FROM grading_components WHERE course_id = ? ORDER BY name', (course_id,))
    components = cursor.fetchall()
    
    cursor.execute('''
        SELECT ci.*, gc.name as component_name
        FROM component_instances ci
        JOIN grading_components gc ON ci.component_id = gc.id
        WHERE ci.course_id = ?
        ORDER BY ci.period, gc.name, ci.instance_number
    ''', (course_id,))
    instances = cursor.fetchall()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = course['course_code'][:31]
    
    ws.append([f"{course['course_title']} ({course['course_code']})"])
    ws.append([f"Schedule: {course['schedule']} {course['days']} | Room: {course['room']}"])
    ws.append([])
    ws.append(["Course Information"])
    ws.append(["Course Code", course['course_code']])
    ws.append(["Course Title", course['course_title']])
    ws.append(["Offering Number", course['offering_number']])
    ws.append(["Description", course['description']])
    ws.append([])
    
    ws.append(["GRADING CRITERIA"])
    ws.append(["Component", "Prelim-Mid %", "Semis-Final %", "Total %"])
    for comp in components:
        ws.append([comp['name'], comp['prelim_mid_weight'], comp['semis_final_weight'], 
                   comp['prelim_mid_weight'] + comp['semis_final_weight']])
    
    total_prelim = sum(comp['prelim_mid_weight'] for comp in components)
    total_semis = sum(comp['semis_final_weight'] for comp in components)
    ws.append(["TOTALS", total_prelim, total_semis, total_prelim + total_semis])
    ws.append([])
    
    passed = 0
    for s in students:
        cursor.execute('SELECT remarks FROM grade_summary WHERE course_id = ? AND student_id = ?',
                     (course_id, s['id']))
        g = cursor.fetchone()
        if g and g[0] == 'Passed':
            passed += 1
    
    avg_grade = 0
    total_grades = 0
    for s in students:
        cursor.execute('SELECT final_grade FROM grade_summary WHERE course_id = ? AND student_id = ?',
                     (course_id, s['id']))
        g = cursor.fetchone()
        if g:
            avg_grade += g[0]
            total_grades += 1
    avg_grade = avg_grade / total_grades if total_grades > 0 else 0
    
    ws.append(["CLASS STATISTICS"])
    ws.append(["Total Students", len(students)])
    ws.append(["Passed", passed])
    ws.append(["Failed", len(students) - passed])
    ws.append(["Class Average", round(avg_grade, 2)])
    ws.append([])
    
    ws.append(["STUDENT ROSTER"])
    
    headers = ["No", "Last Name", "First Name", "ID Number"]
    prelim_instances = [i for i in instances if i['period'] == 'prelim_mid']
    for inst in prelim_instances:
        headers.append(f"{inst['title']}")
    headers.append("PM Total")
    
    semis_instances = [i for i in instances if i['period'] == 'semis_final']
    for inst in semis_instances:
        headers.append(f"{inst['title']}")
    headers.append("SF Total")
    headers.extend(["Final", "Letter", "Remarks"])
    
    ws.append(headers)
    
    for idx, student in enumerate(students, 1):
        cursor.execute('SELECT * FROM grade_summary WHERE course_id = ? AND student_id = ?',
                     (course_id, student['id']))
        grade = cursor.fetchone()
        
        row = [idx, student['last_name'], student['first_name'], student['id_number']]
        
        cursor.execute('SELECT instance_id, score FROM scores WHERE course_id = ? AND student_id = ?',
                     (course_id, student['id']))
        scores = {row['instance_id']: row['score'] for row in cursor.fetchall()}
        
        for inst in prelim_instances:
            score = scores.get(inst['id'], '')
            row.append(score if score != 0 else '')
        
        if grade:
            row.append(round(grade['prelim_mid_total'], 2))
        else:
            row.append('')
        
        for inst in semis_instances:
            score = scores.get(inst['id'], '')
            row.append(score if score != 0 else '')
        
        if grade:
            row.append(round(grade['semis_final_total'], 2))
        else:
            row.append('')
        
        if grade:
            row.extend([round(grade['final_grade'], 2), grade['letter_grade'], grade['remarks']])
        else:
            row.extend(['', '', ''])
        
        ws.append(row)
    
    bold_font = Font(bold=True)
    for col in range(1, len(headers) + 1):
        ws.cell(row=1, column=col).font = bold_font
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=f"{course['course_code'].replace(' ', '_')}_ClassRecord.xlsx")


@app.route('/export/all/xlsx')
def export_all_xlsx():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    
    wb = openpyxl.Workbook()
    del wb['Sheet']
    
    for course in courses:
        cursor.execute('''
            SELECT s.* FROM students s
            JOIN course_students cs ON s.id = cs.student_id
            WHERE cs.course_id = ?
            ORDER BY s.last_name, s.first_name
        ''', (course['id'],))
        students = cursor.fetchall()
        
        cursor.execute('SELECT * FROM grading_components WHERE course_id = ? ORDER BY name', (course['id'],))
        components = cursor.fetchall()
        
        cursor.execute('''
            SELECT ci.*, gc.name as component_name
            FROM component_instances ci
            JOIN grading_components gc ON ci.component_id = gc.id
            WHERE ci.course_id = ?
            ORDER BY ci.period, gc.name, ci.instance_number
        ''', (course['id'],))
        instances = cursor.fetchall()
        
        sheet_name = course['course_code'][:31]
        ws = wb.create_sheet(title=sheet_name)
        
        ws.append([f"{course['course_title']} ({course['course_code']})"])
        ws.append([f"Schedule: {course['schedule']} {course['days']} | Room: {course['room']}"])
        ws.append([])
        ws.append(["Course Information"])
        ws.append(["Course Code", course['course_code']])
        ws.append(["Course Title", course['course_title']])
        ws.append(["Offering Number", course['offering_number']])
        ws.append(["Description", course['description']])
        ws.append([])
        
        ws.append(["GRADING CRITERIA"])
        ws.append(["Component", "Prelim-Mid %", "Semis-Final %", "Total %"])
        for comp in components:
            ws.append([comp['name'], comp['prelim_mid_weight'], comp['semis_final_weight'], 
                       comp['prelim_mid_weight'] + comp['semis_final_weight']])
        
        total_prelim = sum(comp['prelim_mid_weight'] for comp in components)
        total_semis = sum(comp['semis_final_weight'] for comp in components)
        ws.append(["TOTALS", total_prelim, total_semis, total_prelim + total_semis])
        ws.append([])
        
        passed = 0
        for s in students:
            cursor.execute('SELECT remarks FROM grade_summary WHERE course_id = ? AND student_id = ?',
                         (course['id'], s['id']))
            g = cursor.fetchone()
            if g and g[0] == 'Passed':
                passed += 1
        
        avg_grade = 0
        total_grades = 0
        for s in students:
            cursor.execute('SELECT final_grade FROM grade_summary WHERE course_id = ? AND student_id = ?',
                         (course['id'], s['id']))
            g = cursor.fetchone()
            if g:
                avg_grade += g[0]
                total_grades += 1
        avg_grade = avg_grade / total_grades if total_grades > 0 else 0
        
        ws.append(["CLASS STATISTICS"])
        ws.append(["Total Students", len(students)])
        ws.append(["Passed", passed])
        ws.append(["Failed", len(students) - passed])
        ws.append(["Class Average", round(avg_grade, 2)])
        ws.append([])
        
        ws.append(["STUDENT ROSTER"])
        
        headers = ["No", "Last Name", "First Name", "ID Number"]
        prelim_instances = [i for i in instances if i['period'] == 'prelim_mid']
        for inst in prelim_instances:
            headers.append(f"{inst['title']}")
        headers.append("PM Total")
        
        semis_instances = [i for i in instances if i['period'] == 'semis_final']
        for inst in semis_instances:
            headers.append(f"{inst['title']}")
        headers.append("SF Total")
        headers.extend(["Final", "Letter", "Remarks"])
        
        ws.append(headers)
        
        for idx, student in enumerate(students, 1):
            cursor.execute('SELECT * FROM grade_summary WHERE course_id = ? AND student_id = ?',
                         (course['id'], student['id']))
            grade = cursor.fetchone()
            
            row = [idx, student['last_name'], student['first_name'], student['id_number']]
            
            cursor.execute('SELECT instance_id, score FROM scores WHERE course_id = ? AND student_id = ?',
                         (course['id'], student['id']))
            scores = {row['instance_id']: row['score'] for row in cursor.fetchall()}
            
            for inst in prelim_instances:
                score = scores.get(inst['id'], '')
                row.append(score if score != 0 else '')
            
            if grade:
                row.append(round(grade['prelim_mid_total'], 2))
            else:
                row.append('')
            
            for inst in semis_instances:
                score = scores.get(inst['id'], '')
                row.append(score if score != 0 else '')
            
            if grade:
                row.append(round(grade['semis_final_total'], 2))
            else:
                row.append('')
            
            if grade:
                row.extend([round(grade['final_grade'], 2), grade['letter_grade'], grade['remarks']])
            else:
                row.extend(['', '', ''])
            
            ws.append(row)
        
        bold_font = Font(bold=True)
        for col in range(1, len(headers) + 1):
            ws.cell(row=1, column=col).font = bold_font
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name='ClassRecords_All.xlsx')


@app.route('/export/course/<int:course_id>/pdf')
def export_course_pdf(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    cursor.execute('''
        SELECT s.* FROM students s
        JOIN course_students cs ON s.id = cs.student_id
        WHERE cs.course_id = ?
        ORDER BY s.last_name, s.first_name
    ''', (course_id,))
    students = cursor.fetchall()
    
    cursor.execute('SELECT * FROM grading_components WHERE course_id = ? ORDER BY name', (course_id,))
    components = cursor.fetchall()
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0078d4'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        name='Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0078d4'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    elements.append(Paragraph(f"{course['course_title']} ({course['course_code']})", title_style))
    elements.append(Paragraph(f"Schedule: {course['schedule']} {course['days']} | Room: {course['room']}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Course Information", heading_style))
    info_data = [
        ["Course Code:", course['course_code']],
        ["Course Title:", course['course_title']],
        ["Offering Number:", course['offering_number']],
        ["Description:", course['description']],
    ]
    info_table = Table(info_data, colWidths=[120, 300])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Grading Criteria", heading_style))
    criteria_data = [["Component", "Prelim-Mid %", "Semis-Final %", "Total %"]]
    for comp in components:
        criteria_data.append([comp['name'], f"{comp['prelim_mid_weight']}%", 
                             f"{comp['semis_final_weight']}%", 
                             f"{comp['prelim_mid_weight'] + comp['semis_final_weight']}%"])
    
    total_prelim = sum(comp['prelim_mid_weight'] for comp in components)
    total_semis = sum(comp['semis_final_weight'] for comp in components)
    criteria_data.append(["TOTALS", f"{total_prelim}%", f"{total_semis}%", f"{total_prelim + total_semis}%"])
    
    criteria_table = Table(criteria_data)
    criteria_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(criteria_table)
    elements.append(Spacer(1, 12))
    
    passed = 0
    for s in students:
        cursor.execute('SELECT remarks FROM grade_summary WHERE course_id = ? AND student_id = ?',
                     (course_id, s['id']))
        g = cursor.fetchone()
        if g and g[0] == 'Passed':
            passed += 1
    
    avg_grade = 0
    total_grades = 0
    for s in students:
        cursor.execute('SELECT final_grade FROM grade_summary WHERE course_id = ? AND student_id = ?',
                     (course_id, s['id']))
        g = cursor.fetchone()
        if g:
            avg_grade += g[0]
            total_grades += 1
    avg_grade = avg_grade / total_grades if total_grades > 0 else 0
    
    elements.append(Paragraph("Class Statistics", heading_style))
    stats_data = [
        ["Total Students", str(len(students))],
        ["Passed", f"{passed} ({passed/len(students)*100:.1f}%)" if students else "0"],
        ["Failed", f"{len(students)-passed} ({100-(passed/len(students)*100):.1f}%)" if students else "0"],
        ["Class Average", f"{avg_grade:.2f}"],
    ]
    stats_table = Table(stats_data, colWidths=[150, 200])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Student Roster", heading_style))
    headers = ["No", "Last Name", "First Name", "ID", "PM Total", "SF Total", "Final", "Letter", "Remarks"]
    roster_data = [headers]
    
    for idx, student in enumerate(students, 1):
        cursor.execute('SELECT * FROM grade_summary WHERE course_id = ? AND student_id = ?',
                     (course_id, student['id']))
        grade = cursor.fetchone()
        
        if grade:
            roster_data.append([
                str(idx), student['last_name'], student['first_name'], student['id_number'],
                f"{grade['prelim_mid_total']:.2f}",
                f"{grade['semis_final_total']:.2f}",
                f"{grade['final_grade']:.2f}",
                grade['letter_grade'],
                grade['remarks']
            ])
        else:
            roster_data.append([str(idx), student['last_name'], student['first_name'], student['id_number'], '', '', '', '', ''])
    
    roster_table = Table(roster_data)
    roster_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(roster_table)
    
    doc.build(elements)
    output.seek(0)
    
    return send_file(output,
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f"{course['course_code'].replace(' ', '_')}_ClassRecord.pdf")


if __name__ == '__main__':
    # Clean up old database
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    
    # Initialize and run
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

