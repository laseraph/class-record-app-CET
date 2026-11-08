"""
Class Record Web Application
Modern web-based class record system with Flask
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import sqlite3
import pandas as pd
import openpyxl
from openpyxl.styles import Font
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import csv

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Database setup
DATABASE = 'class_record.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
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
                prelim_mid_weight REAL DEFAULT 0.0,
                semis_final_weight REAL DEFAULT 0.0,
                max_score REAL DEFAULT 100.0,
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
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                student_id INTEGER,
                prelim_mid_scores TEXT DEFAULT '{}',
                semis_final_scores TEXT DEFAULT '{}',
                prelim_mid_total REAL DEFAULT 0.0,
                semis_final_total REAL DEFAULT 0.0,
                final_grade REAL DEFAULT 0.0,
                letter_grade TEXT DEFAULT 'F',
                remarks TEXT DEFAULT '',
                extra_credit REAL DEFAULT 0.0,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(course_id, student_id)
            )
        ''')
        
        db.commit()
        
        # Insert sample data if empty
        cursor.execute('SELECT COUNT(*) FROM courses')
        if cursor.fetchone()[0] == 0:
            # Sample courses
            cursor.execute('''
                INSERT INTO courses (course_code, course_title, offering_number, description, schedule, room, days)
                VALUES ('Math 201E (2018)', 'Differential Equations', '1', 'Advanced differential equations', '8:00-9:00 AM', 'CH504', 'MWF')
            ''')
            cursor.execute('''
                INSERT INTO courses (course_code, course_title, offering_number, description, schedule, room, days)
                VALUES ('ES 201 (2018)', 'Engineering Economy', '1', 'Economic analysis', '10:00-11:00 AM', 'CH505', 'TTh')
            ''')
            db.commit()
            
            # Get course IDs
            cursor.execute('SELECT id FROM courses')
            course_ids = [row[0] for row in cursor.fetchall()]
            
            # Sample students
            students = [
                ('CELESTIAL', 'Gerry Luz', '59844380', 'gerry@email.com'),
                ('DELA CRUZ', 'Rojemie', '59842976', 'rojemie@email.com'),
                ('JAMERO', 'Van Vincent', '59845710', 'van@email.com'),
            ]
            for last, first, id_num, email in students:
                cursor.execute('INSERT INTO students (last_name, first_name, id_number, email) VALUES (?, ?, ?, ?)',
                             (last, first, id_num, email))
            db.commit()
            
            # Link students to courses
            for course_id in course_ids:
                for last, first, id_num, email in students:
                    cursor.execute('SELECT id FROM students WHERE id_number = ?', (id_num,))
                    student_id = cursor.fetchone()[0]
                    cursor.execute('INSERT INTO course_students (course_id, student_id) VALUES (?, ?)',
                                 (course_id, student_id))
            db.commit()
            
            # Grading components
            components = [
                ('Assignments', 10.0, 10.0),
                ('Oral Recitation', 5.0, 5.0),
                ('Seatwork', 5.0, 5.0),
                ('Quizzes', 30.0, 30.0),
                ('Pre / Semi exam', 25.0, 25.0),
                ('Mid / Fin exam', 25.0, 25.0),
            ]
            for course_id in course_ids:
                for name, prelim, semis in components:
                    cursor.execute('''
                        INSERT INTO grading_components (course_id, name, prelim_mid_weight, semis_final_weight)
                        VALUES (?, ?, ?, ?)
                    ''', (course_id, name, prelim, semis))
            db.commit()
            
            # Sample grades for first course
            cursor.execute('SELECT id FROM courses LIMIT 1')
            course_id = cursor.fetchone()[0]
            for last, first, id_num, email in students:
                cursor.execute('SELECT id FROM students WHERE id_number = ?', (id_num,))
                student_id = cursor.fetchone()[0]
                cursor.execute('''
                    INSERT INTO grades (course_id, student_id, prelim_mid_scores, semis_final_scores, 
                                       prelim_mid_total, semis_final_total, final_grade, letter_grade, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (course_id, student_id, 
                      '{"Assignments": 85, "Oral Recitation": 90, "Seatwork": 88, "Quizzes": 75, "Pre / Semi exam": 65}',
                      '{"Assignments": 90, "Oral Recitation": 85, "Seatwork": 92, "Quizzes": 80, "Mid / Fin exam": 70}',
                      76.25, 78.75, 77.5, 'C', 'Passed'))
            db.commit()

# Initialize database on startup
init_db()


@app.route('/')
def dashboard():
    db = get_db()
    
    # Get all courses with stats
    cursor = db.cursor()
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    
    course_list = []
    total_passed = 0
    total_failed = 0
    total_students = 0
    
    for course in courses:
        cursor.execute('''
            SELECT COUNT(*) FROM course_students WHERE course_id = ?
        ''', (course['id'],))
        student_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM grades WHERE course_id = ? AND remarks = 'Passed'
        ''', (course['id'],))
        passed = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM grades WHERE course_id = ? AND remarks = 'Failed'
        ''', (course['id'],))
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
    
    # Get course info
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Get students in this course
    cursor.execute('''
        SELECT s.* FROM students s
        JOIN course_students cs ON s.id = cs.student_id
        WHERE cs.course_id = ?
    ''', (course_id,))
    students = cursor.fetchall()
    
    # Get grades for these students
    roster = []
    for student in students:
        cursor.execute('''
            SELECT * FROM grades WHERE course_id = ? AND student_id = ?
        ''', (course_id, student['id']))
        grade = cursor.fetchone()
        roster.append({
            'student': student,
            'grade': grade
        })
    
    # Get grading components
    cursor.execute('''
        SELECT * FROM grading_components WHERE course_id = ?
    ''', (course_id,))
    components = cursor.fetchall()
    
    # Calculate statistics
    total = len(students)
    passed = sum(1 for r in roster if r['grade'] and r['grade']['remarks'] == 'Passed')
    failed = sum(1 for r in roster if r['grade'] and r['grade']['remarks'] == 'Failed')
    pass_rate = (passed / total * 100) if total > 0 else 0
    fail_rate = (failed / total * 100) if total > 0 else 0
    
    # Calculate class average
    avg = sum(r['grade']['final_grade'] for r in roster if r['grade']) / total if total > 0 else 0
    
    # Grade distribution
    dist = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
    for r in roster:
        if r['grade'] and r['grade']['letter_grade'] in dist:
            dist[r['grade']['letter_grade']] += 1
    
    return render_template('course_detail.html',
                         course=course,
                         roster=roster,
                         components=components,
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
    
    # Get course info
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Get grading components
    cursor.execute('''
        SELECT * FROM grading_components WHERE course_id = ?
    ''', (course_id,))
    components = cursor.fetchall()
    
    # Get students
    cursor.execute('''
        SELECT s.* FROM students s
        JOIN course_students cs ON s.id = cs.student_id
        WHERE cs.course_id = ?
        ORDER BY s.last_name, s.first_name
    ''', (course_id,))
    students = cursor.fetchall()
    
    if request.method == 'POST':
        bigrade = request.form.get('bigrade', 'prelim_mid')
        student_id = request.form.get('student_id')
        
        # Save grades
        for comp in components:
            score = request.form.get(f'grade_{comp["id"]}')
            if score:
                try:
                    score = float(score)
                except:
                    score = 0
            else:
                score = 0
            
            # Update or insert grade
            cursor.execute('''
                SELECT * FROM grades WHERE course_id = ? AND student_id = ?
            ''', (course_id, student_id))
            grade = cursor.fetchone()
            
            if grade:
                if bigrade == 'prelim_mid':
                    # Parse existing scores
                    import json
                    pm_scores = json.loads(grade['prelim_mid_scores']) if grade['prelim_mid_scores'] else {}
                    pm_scores[comp['name']] = score
                    cursor.execute('''
                        UPDATE grades SET prelim_mid_scores = ? WHERE id = ?
                    ''', (json.dumps(pm_scores), grade['id']))
                else:
                    sf_scores = json.loads(grade['semis_final_scores']) if grade['semis_final_scores'] else {}
                    sf_scores[comp['name']] = score
                    cursor.execute('''
                        UPDATE grades SET semis_final_scores = ? WHERE id = ?
                    ''', (json.dumps(sf_scores), grade['id']))
            else:
                if bigrade == 'prelim_mid':
                    pm_scores = {comp['name']: score}
                    cursor.execute('''
                        INSERT INTO grades (course_id, student_id, prelim_mid_scores)
                        VALUES (?, ?, ?)
                    ''', (course_id, student_id, json.dumps(pm_scores)))
                else:
                    sf_scores = {comp['name']: score}
                    cursor.execute('''
                        INSERT INTO grades (course_id, student_id, semis_final_scores)
                        VALUES (?, ?, ?)
                    ''', (course_id, student_id, json.dumps(sf_scores)))
        
        db.commit()
        flash('Grades saved successfully!', 'success')
        
        # Recalculate grades
        recalculate_grades(course_id)
        
        return redirect(url_for('grade_entry', course_id=course_id))
    
    # Get current student
    current_student_id = request.args.get('student_id', students[0]['id'] if students else None)
    
    return render_template('grade_entry.html',
                         course=course,
                         components=components,
                         students=students,
                         current_student_id=current_student_id)


def recalculate_grades(course_id):
    db = get_db()
    cursor = db.cursor()
    
    # Get course and components
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    cursor.execute('''
        SELECT * FROM grading_components WHERE course_id = ?
    ''', (course_id,))
    components = cursor.fetchall()
    
    # Get students
    cursor.execute('''
        SELECT s.id FROM students s
        JOIN course_students cs ON s.id = cs.student_id
        WHERE cs.course_id = ?
    ''', (course_id,))
    student_ids = [row[0] for row in cursor.fetchall()]
    
    import json
    for student_id in student_ids:
        cursor.execute('''
            SELECT * FROM grades WHERE course_id = ? AND student_id = ?
        ''', (course_id, student_id))
        grade = cursor.fetchone()
        
        if grade:
            prelim_mid_total = 0
            semis_final_total = 0
            
            if grade['prelim_mid_scores']:
                pm_scores = json.loads(grade['prelim_mid_scores'])
                for comp in components:
                    if comp['name'] in pm_scores:
                        raw_score = pm_scores[comp['name']]
                        weighted_score = (raw_score / comp['max_score']) * comp['prelim_mid_weight']
                        prelim_mid_total += weighted_score
            
            if grade['semis_final_scores']:
                sf_scores = json.loads(grade['semis_final_scores'])
                for comp in components:
                    if comp['name'] in sf_scores:
                        raw_score = sf_scores[comp['name']]
                        weighted_score = (raw_score / comp['max_score']) * comp['semis_final_weight']
                        semis_final_total += weighted_score
            
            ec = grade['extra_credit']
            prelim_mid_total = min(100, prelim_mid_total + ec/2)
            semis_final_total = min(100, semis_final_total + ec/2)
            
            final_grade = (prelim_mid_total + semis_final_total) / 2
            
            # Get letter grade
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
                UPDATE grades SET 
                    prelim_mid_total = ?,
                    semis_final_total = ?,
                    final_grade = ?,
                    letter_grade = ?,
                    remarks = ?
                WHERE id = ?
            ''', (prelim_mid_total, semis_final_total, final_grade, letter_grade, remarks, grade['id']))
    
    db.commit()


@app.route('/course/<int:course_id>/grading-criteria', methods=['GET', 'POST'])
def grading_criteria(course_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('dashboard'))
    
    cursor.execute('''
        SELECT * FROM grading_components WHERE course_id = ?
    ''', (course_id,))
    components = cursor.fetchall()
    
    total_prelim = sum(comp['prelim_mid_weight'] for comp in components)
    total_semis = sum(comp['semis_final_weight'] for comp in components)
    total_overall = total_prelim + total_semis
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name')
            prelim = float(request.form.get('prelim', 0))
            semis = float(request.form.get('semis', 0))
            max_score = float(request.form.get('max_score', 100))
            
            cursor.execute('''
                INSERT INTO grading_components (course_id, name, prelim_mid_weight, semis_final_weight, max_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (course_id, name, prelim, semis, max_score))
            db.commit()
            flash('Component added!', 'success')
            
        elif action == 'update':
            comp_id = request.form.get('comp_id')
            name = request.form.get('name')
            prelim = float(request.form.get('prelim', 0))
            semis = float(request.form.get('semis', 0))
            max_score = float(request.form.get('max_score', 100))
            
            cursor.execute('''
                UPDATE grading_components SET 
                    name = ?,
                    prelim_mid_weight = ?,
                    semis_final_weight = ?,
                    max_score = ?
                WHERE id = ?
            ''', (name, prelim, semis, max_score, comp_id))
            db.commit()
            flash('Component updated!', 'success')
            recalculate_grades(course_id)
            
        elif action == 'delete':
            comp_id = request.form.get('comp_id')
            cursor.execute('DELETE FROM grading_components WHERE id = ?', (comp_id,))
            db.commit()
            flash('Component deleted!', 'success')
            recalculate_grades(course_id)
        
        return redirect(url_for('grading_criteria', course_id=course_id))
    
    return render_template('grading_criteria.html',
                         course=course,
                         components=components,
                         total_prelim=total_prelim,
                         total_semis=total_semis,
                         total_overall=total_overall)


@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        
        course_code = request.form.get('course_code')
        course_title = request.form.get('course_title')
        offering_number = request.form.get('offering_number', '1')
        description = request.form.get('description', '')
        schedule = request.form.get('schedule', '')
        room = request.form.get('room', '')
        days = request.form.get('days', '')
        
        cursor.execute('''
            INSERT INTO courses (course_code, course_title, offering_number, description, schedule, room, days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (course_code, course_title, offering_number, description, schedule, room, days))
        course_id = cursor.lastrowid
        db.commit()
        
        # Add default grading components
        components = [
            ('Assignments', 10.0, 10.0),
            ('Oral Recitation', 5.0, 5.0),
            ('Seatwork', 5.0, 5.0),
            ('Quizzes', 30.0, 30.0),
            ('Pre / Semi exam', 25.0, 25.0),
            ('Mid / Fin exam', 25.0, 25.0),
        ]
        
        for name, prelim, semis in components:
            cursor.execute('''
                INSERT INTO grading_components (course_id, name, prelim_mid_weight, semis_final_weight)
                VALUES (?, ?, ?, ?)
            ''', (course_id, name, prelim, semis))
        db.commit()
        
        flash('Course added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_course.html')


@app.route('/edit-course/<int:course_id>', methods=['GET', 'POST'])
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
        offering_number = request.form.get('offering_number', '1')
        description = request.form.get('description', '')
        schedule = request.form.get('schedule', '')
        room = request.form.get('room', '')
        days = request.form.get('days', '')
        
        cursor.execute('''
            UPDATE courses SET 
                course_code = ?,
                course_title = ?,
                offering_number = ?,
                description = ?,
                schedule = ?,
                room = ?,
                days = ?
            WHERE id = ?
        ''', (course_code, course_title, offering_number, description, schedule, room, days, course_id))
        db.commit()
        
        flash('Course updated successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course_id))
    
    return render_template('edit_course.html', course=course)


@app.route('/import-students', methods=['GET', 'POST'])
def import_students():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        file = request.files.get('file')
        
        if not file:
            flash('No file uploaded', 'error')
            return redirect(url_for('import_students'))
        
        if not course_id:
            flash('No course selected', 'error')
            return redirect(url_for('import_students'))
        
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                flash('Unsupported file format', 'error')
                return redirect(url_for('import_students'))
            
            imported = 0
            for _, row in df.iterrows():
                last_name = str(row.get('Last Name', row.get('Last', row.get('LNAME', '')))).strip()
                first_name = str(row.get('First Name', row.get('First', row.get('FNAME', '')))).strip()
                id_number = str(row.get('ID Number', row.get('ID', row.get('IDNO', '')))).strip()
                email = str(row.get('Email Address', row.get('Email', row.get('EMAIL', '')))).strip()
                
                if last_name and first_name and id_number:
                    # Check if student exists
                    cursor.execute('SELECT id FROM students WHERE id_number = ?', (id_number,))
                    student = cursor.fetchone()
                    
                    if not student:
                        cursor.execute('''
                            INSERT INTO students (last_name, first_name, id_number, email)
                            VALUES (?, ?, ?, ?)
                        ''', (last_name, first_name, id_number, email))
                        student_id = cursor.lastrowid
                    else:
                        student_id = student['id']
                    
                    # Link to course
                    cursor.execute('''
                        INSERT OR IGNORE INTO course_students (course_id, student_id)
                        VALUES (?, ?)
                    ''', (course_id, student_id))
                    
                    # Create grade record if not exists
                    cursor.execute('''
                        INSERT OR IGNORE INTO grades (course_id, student_id)
                        VALUES (?, ?)
                    ''', (course_id, student_id))
                    
                    imported += 1
            
            db.commit()
            flash(f'Successfully imported {imported} students!', 'success')
            return redirect(url_for('course_detail', course_id=course_id))
            
        except Exception as e:
            db.rollback()
            flash(f'Error importing file: {str(e)}', 'error')
            return redirect(url_for('import_students'))
    
    return render_template('import_students.html', courses=courses)


@app.route('/master-list')
def master_list():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM students ORDER BY last_name, first_name')
    students = cursor.fetchall()
    
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    
    # Get all grades for master list
    master_data = []
    for student in students:
        grades = []
        for course in courses:
            cursor.execute('''
                SELECT g.* FROM grades g
                JOIN course_students cs ON g.student_id = cs.student_id AND g.course_id = cs.course_id
                WHERE g.student_id = ? AND g.course_id = ?
            ''', (student['id'], course['id']))
            grade = cursor.fetchone()
            if grade:
                grades.append(f"{course['course_code']}: {grade['final_grade']:.2f}")
            else:
                grades.append(f"{course['course_code']}: N/A")
        
        master_data.append({
            'student': student,
            'grades': ', '.join(grades)
        })
    
    # Get course statistics
    course_stats = []
    for course in courses:
        cursor.execute('''
            SELECT COUNT(*) FROM course_students WHERE course_id = ?
        ''', (course['id'],))
        total = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM grades WHERE course_id = ? AND remarks = 'Passed'
        ''', (course['id'],))
        passed = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM grades WHERE course_id = ? AND remarks = 'Failed'
        ''', (course['id'],))
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
    
    cursor.execute('''
        SELECT * FROM grading_components WHERE course_id = ?
    ''', (course_id,))
    components = cursor.fetchall()
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = course['course_code']
    
    # Course info
    ws.append([f"{course['course_title']} ({course['course_code']})"])
    ws.append([f"Schedule: {course['schedule']} {course['days']} | Room: {course['room']}"])
    ws.append([])
    
    ws.append(["Course Information"])
    ws.append(["Course Code", course['course_code']])
    ws.append(["Course Title", course['course_title']])
    ws.append(["Offering Number", course['offering_number']])
    ws.append(["Description", course['description']])
    ws.append([])
    
    # Grading criteria
    ws.append(["GRADING CRITERIA"])
    ws.append(["Component", "Prelim-Mid %", "Semis-Final %", "Total %"])
    for comp in components:
        ws.append([comp['name'], comp['prelim_mid_weight'], comp['semis_final_weight'], 
                   comp['prelim_mid_weight'] + comp['semis_final_weight']])
    
    total_prelim = sum(comp['prelim_mid_weight'] for comp in components)
    total_semis = sum(comp['semis_final_weight'] for comp in components)
    ws.append(["TOTALS", total_prelim, total_semis, total_prelim + total_semis])
    ws.append([])
    
    # Statistics
    passed = sum(1 for s in students if any(g['remarks'] == 'Passed' for g in 
                 [cursor.execute('SELECT remarks FROM grades WHERE course_id = ? AND student_id = ?', (course_id, s['id'])).fetchone()]))
    
    ws.append(["CLASS STATISTICS"])
    ws.append(["Total Students", len(students)])
    ws.append(["Passed", passed])
    ws.append(["Failed", len(students) - passed])
    ws.append([])
    
    # Student roster
    ws.append(["STUDENT ROSTER"])
    headers = ["No", "Last Name", "First Name", "ID Number"]
    for comp in components:
        headers.append(f"{comp['name']} (PM)")
    headers.extend(["PM Total", "SF Total", "Final", "Letter", "Remarks"])
    ws.append(headers)
    
    for idx, student in enumerate(students, 1):
        cursor.execute('''
            SELECT * FROM grades WHERE course_id = ? AND student_id = ?
        ''', (course_id, student['id']))
        grade = cursor.fetchone()
        
        row = [idx, student['last_name'], student['first_name'], student['id_number']]
        
        if grade:
            import json
            pm_scores = json.loads(grade['prelim_mid_scores']) if grade['prelim_mid_scores'] else {}
            sf_scores = json.loads(grade['semis_final_scores']) if grade['semis_final_scores'] else {}
            
            for comp in components:
                row.append(pm_scores.get(comp['name'], ''))
            
            row.extend([
                grade['prelim_mid_total'],
                grade['semis_final_total'],
                grade['final_grade'],
                grade['letter_grade'],
                grade['remarks']
            ])
        else:
            row.extend([''] * (len(components) + 5))
        
        ws.append(row)
    
    # Style headers
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True)
    
    # Save to bytes
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
        # Get course data
        cursor.execute('''
            SELECT s.* FROM students s
            JOIN course_students cs ON s.id = cs.student_id
            WHERE cs.course_id = ?
            ORDER BY s.last_name, s.first_name
        ''', (course['id'],))
        students = cursor.fetchall()
        
        cursor.execute('''
            SELECT * FROM grading_components WHERE course_id = ?
        ''', (course['id'],))
        components = cursor.fetchall()
        
        # Create sheet
        ws = wb.create_sheet(title=course['course_code'])
        
        # Course info
        ws.append([f"{course['course_title']} ({course['course_code']})"])
        ws.append([f"Schedule: {course['schedule']} {course['days']} | Room: {course['room']}"])
        ws.append([])
        
        ws.append(["Course Information"])
        ws.append(["Course Code", course['course_code']])
        ws.append(["Course Title", course['course_title']])
        ws.append(["Offering Number", course['offering_number']])
        ws.append(["Description", course['description']])
        ws.append([])
        
        # Grading criteria
        ws.append(["GRADING CRITERIA"])
        ws.append(["Component", "Prelim-Mid %", "Semis-Final %", "Total %"])
        for comp in components:
            ws.append([comp['name'], comp['prelim_mid_weight'], comp['semis_final_weight'], 
                       comp['prelim_mid_weight'] + comp['semis_final_weight']])
        
        total_prelim = sum(comp['prelim_mid_weight'] for comp in components)
        total_semis = sum(comp['semis_final_weight'] for comp in components)
        ws.append(["TOTALS", total_prelim, total_semis, total_prelim + total_semis])
        ws.append([])
        
        # Statistics
        passed = 0
        for s in students:
            cursor.execute('''
                SELECT remarks FROM grades WHERE course_id = ? AND student_id = ?
            ''', (course['id'], s['id']))
            g = cursor.fetchone()
            if g and g[0] == 'Passed':
                passed += 1
        
        ws.append(["CLASS STATISTICS"])
        ws.append(["Total Students", len(students)])
        ws.append(["Passed", passed])
        ws.append(["Failed", len(students) - passed])
        ws.append([])
        
        # Student roster
        ws.append(["STUDENT ROSTER"])
        headers = ["No", "Last Name", "First Name", "ID Number"]
        for comp in components:
            headers.append(f"{comp['name']} (PM)")
        headers.extend(["PM Total", "SF Total", "Final", "Letter", "Remarks"])
        ws.append(headers)
        
        for idx, student in enumerate(students, 1):
            cursor.execute('''
                SELECT * FROM grades WHERE course_id = ? AND student_id = ?
            ''', (course['id'], student['id']))
            grade = cursor.fetchone()
            
            row = [idx, student['last_name'], student['first_name'], student['id_number']]
            
            if grade:
                import json
                pm_scores = json.loads(grade['prelim_mid_scores']) if grade['prelim_mid_scores'] else {}
                sf_scores = json.loads(grade['semis_final_scores']) if grade['semis_final_scores'] else {}
                
                for comp in components:
                    row.append(pm_scores.get(comp['name'], ''))
                
                row.extend([
                    grade['prelim_mid_total'],
                    grade['semis_final_total'],
                    grade['final_grade'],
                    grade['letter_grade'],
                    grade['remarks']
                ])
            else:
                row.extend([''] * (len(components) + 5))
            
            ws.append(row)
        
        # Style headers
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)
    
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
    
    cursor.execute('''
        SELECT * FROM grading_components WHERE course_id = ?
    ''', (course_id,))
    components = cursor.fetchall()
    
    # Create PDF
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
    
    # Statistics
    passed = sum(1 for s in students if any(g[0] == 'Passed' for g in 
                 [cursor.execute('SELECT remarks FROM grades WHERE course_id = ? AND student_id = ?', (course_id, s['id'])).fetchone()]))
    avg = sum(g['final_grade'] for g in 
              [cursor.execute('SELECT final_grade FROM grades WHERE course_id = ? AND student_id = ?', (course_id, s['id'])).fetchone() 
               for s in students] if g) / len(students) if students else 0
    
    elements.append(Paragraph("Class Statistics", heading_style))
    stats_data = [
        ["Total Students", str(len(students))],
        ["Passed", f"{passed} ({passed/len(students)*100:.1f}%)" if students else "0"],
        ["Failed", f"{len(students)-passed} ({100-(passed/len(students)*100):.1f}%)" if students else "0"],
        ["Class Average", f"{avg:.2f}"],
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
    
    # Student roster
    elements.append(Paragraph("Student Roster", heading_style))
    headers = ["No", "Last Name", "First Name", "ID", "PM Total", "SF Total", "Final", "Letter", "Remarks"]
    roster_data = [headers]
    
    for idx, student in enumerate(students, 1):
        cursor.execute('''
            SELECT * FROM grades WHERE course_id = ? AND student_id = ?
        ''', (course_id, student['id']))
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
        ('FONTSIZE', (0, 0), (-1, 0), 9),
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
    app.run(debug=True, host='0.0.0.0', port=5000)
