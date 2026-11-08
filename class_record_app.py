#!/usr/bin/env python3
"""
Class Record System - Modern UI Version
Uses PySimpleGUI for a modern, professional user interface.
"""

import sys
import PySimpleGUI as sg
import pandas as pd
import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class Student:
    def __init__(self, last_name, first_name, id_number, email):
        self.last_name = last_name
        self.first_name = first_name
        self.id_number = id_number
        self.email = email
        self.status = "Active"
    
    def full_name(self):
        return f"{self.last_name}, {self.first_name}"


class GradingComponent:
    def __init__(self, name, prelim_mid_weight=0.0, semis_final_weight=0.0):
        self.name = name
        self.prelim_mid_weight = prelim_mid_weight
        self.semis_final_weight = semis_final_weight
        self.max_score = 100.0
    
    def total_weight(self):
        return self.prelim_mid_weight + self.semis_final_weight


class Course:
    def __init__(self, course_code, course_title, offering_number="1", 
                 description="", schedule="", room="", days=""):
        self.course_code = course_code
        self.course_title = course_title
        self.offering_number = offering_number
        self.description = description
        self.schedule = schedule
        self.room = room
        self.days = days
        self.students = []
        self.grading_components = []
        self.grades = {}
        self.extra_credits = {}
    
    def full_name(self):
        return f"{self.course_title} ({self.course_code})"
    
    def add_student(self, student):
        self.students.append(student)
        self.grades[student.id_number] = {
            "prelim_mid_scores": {},
            "semis_final_scores": {},
            "prelim_mid_total": 0,
            "semis_final_total": 0,
            "final_grade": 0,
            "letter_grade": "F",
            "remarks": ""
        }
        self.extra_credits[student.id_number] = 0
    
    def add_grading_component(self, component):
        self.grading_components.append(component)
    
    def calculate_grades(self):
        for student in self.students:
            student_id = student.id_number
            if student_id not in self.grades:
                continue
            grade_data = self.grades[student_id]
            prelim_mid_total = 0
            semis_final_total = 0
            for comp in self.grading_components:
                if comp.name in grade_data["prelim_mid_scores"]:
                    raw_score = grade_data["prelim_mid_scores"][comp.name]
                    weighted_score = (raw_score / comp.max_score) * comp.prelim_mid_weight
                    prelim_mid_total += weighted_score
                if comp.name in grade_data["semis_final_scores"]:
                    raw_score = grade_data["semis_final_scores"][comp.name]
                    weighted_score = (raw_score / comp.max_score) * comp.semis_final_weight
                    semis_final_total += weighted_score
            ec = self.extra_credits.get(student_id, 0)
            prelim_mid_total = min(100, prelim_mid_total + ec/2)
            semis_final_total = min(100, semis_final_total + ec/2)
            grade_data["prelim_mid_total"] = prelim_mid_total
            grade_data["semis_final_total"] = semis_final_total
            final_grade = (prelim_mid_total + semis_final_total) / 2
            grade_data["final_grade"] = final_grade
            letter_grade, remarks = self._get_letter_grade(final_grade)
            grade_data["letter_grade"] = letter_grade
            grade_data["remarks"] = remarks
    
    def _get_letter_grade(self, grade):
        if grade >= 95:
            return "A", "Passed"
        elif grade >= 90:
            return "B", "Passed"
        elif grade >= 85:
            return "C", "Passed"
        elif grade >= 80:
            return "D", "Passed"
        elif grade >= 75:
            return "E", "Passed"
        else:
            return "F", "Failed"
    
    def get_pass_fail_stats(self):
        total = len(self.students)
        if total == 0:
            return {"passed": 0, "failed": 0, "dropped": 0, "pass_rate": 0, "fail_rate": 0}
        passed = sum(1 for s in self.students 
                     if self.grades.get(s.id_number, {}).get("remarks") == "Passed")
        failed = sum(1 for s in self.students 
                     if self.grades.get(s.id_number, {}).get("remarks") == "Failed")
        dropped = sum(1 for s in self.students if s.status == "Dropped")
        pass_rate = (passed / total) * 100 if total > 0 else 0
        fail_rate = (failed / total) * 100 if total > 0 else 0
        return {
            "passed": passed,
            "failed": failed,
            "dropped": dropped,
            "pass_rate": pass_rate,
            "fail_rate": fail_rate
        }
    
    def get_grade_distribution(self):
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
        total = len(self.students)
        for student in self.students:
            letter_grade = self.grades.get(student.id_number, {}).get("letter_grade", "F")
            if letter_grade in distribution:
                distribution[letter_grade] += 1
        for key in list(distribution.keys()):
            distribution[f"{key}_pct"] = (distribution[key] / total * 100) if total > 0 else 0
        return distribution
    
    def get_class_average(self):
        if not self.students:
            return 0
        total = sum(self.grades.get(s.id_number, {}).get("final_grade", 0) 
                   for s in self.students)
        return total / len(self.students)



class ClassRecordApp:
    def __init__(self):
        sg.theme("DarkTeal9")
        sg.set_options(font=("Segoe UI", 10))
        self.courses = []
        self.current_course = None
        self.master_student_list = []
        self.window = None
        self.load_sample_data()
        self.show_dashboard()

    def load_sample_data(self):
        course1 = Course("Math 201E (2018)", "Differential Equations", "1", 
                        "Advanced differential equations", "8:00-9:00 AM", "CH504", "MWF")
        course2 = Course("ES 201 (2018)", "Engineering Economy", "1",
                        "Economic analysis", "10:00-11:00 AM", "CH505", "TTh")
        components = [
            GradingComponent("Assignments", 10.0, 10.0),
            GradingComponent("Oral Recitation", 5.0, 5.0),
            GradingComponent("Seatwork", 5.0, 5.0),
            GradingComponent("Quizzes", 30.0, 30.0),
            GradingComponent("Pre / Semi exam", 25.0, 25.0),
            GradingComponent("Mid / Fin exam", 25.0, 25.0),
        ]
        for comp in components:
            course1.add_grading_component(comp)
            course2.add_grading_component(comp)
        sample_students = [
            Student("CELESTIAL", "Gerry Luz", "59844380", "gerry@email.com"),
            Student("DELA CRUZ", "Rojemie", "59842976", "rojemie@email.com"),
            Student("JAMERO", "Van Vincent", "59845710", "van@email.com"),
        ]
        for student in sample_students:
            course1.add_student(student)
            course2.add_student(student)
            self.master_student_list.append(student)
        for student in sample_students:
            course1.grades[student.id_number]["prelim_mid_scores"] = {
                "Assignments": 85, "Oral Recitation": 90, "Seatwork": 88, "Quizzes": 75, "Pre / Semi exam": 65
            }
            course1.grades[student.id_number]["semis_final_scores"] = {
                "Assignments": 90, "Oral Recitation": 85, "Seatwork": 92, "Quizzes": 80, "Mid / Fin exam": 70
            }
        course1.calculate_grades()
        course2.calculate_grades()
        self.courses.append(course1)
        self.courses.append(course2)

    def show_dashboard(self):
        if self.window:
            self.window.close()
        
        total_passed = sum(c.get_pass_fail_stats()["passed"] for c in self.courses)
        total_failed = sum(c.get_pass_fail_stats()["failed"] for c in self.courses)
        total_g = total_passed + total_failed
        overall_pass_rate = (total_passed / total_g * 100) if total_g > 0 else 0
        
        course_rows = []
        for course in self.courses:
            stats = course.get_pass_fail_stats()
            course_rows.append([
                course.full_name(), course.course_code,
                f"{course.schedule} {course.days}", course.room,
                len(course.students), f"{stats['pass_rate']:.1f}%"
            ])
        
        layout = [
            [sg.Text("Class Record System", font=("Segoe UI", 20, "bold"), text_color="#0078d4", pad=(20, 10))],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text(f"Total Courses: {len(self.courses)}", font=("Segoe UI", 11)),
             sg.Text(f"Total Students: {len(self.master_student_list)}", font=("Segoe UI", 11)),
             sg.Text(f"Overall Pass Rate: {overall_pass_rate:.1f}%", font=("Segoe UI", 11))],
            [sg.HorizontalSeparator()],
            [sg.Text("Courses", font=("Segoe UI", 14, "bold"), pad=(0, 10))],
            [sg.Table(course_rows, ["Course Name", "Code", "Schedule", "Room", "Students", "Pass Rate"],
                     auto_size_columns=True, alternating_row_color="#2d2d2d",
                     header_background_color="#0078d4", header_text_color="white",
                     key="-COURSE_TABLE-", enable_events=True, size=(900, 300))],
            [sg.HorizontalSeparator()],
            [sg.Button("View Course", size=(15, 2)), sg.Button("Add Course", size=(15, 2)),
             sg.Button("Import Students", size=(15, 2)), sg.Button("Grading Criteria", size=(15, 2))],
            [sg.HorizontalSeparator()],
            [sg.Text("Summary Statistics", font=("Segoe UI", 14, "bold"))],
            [sg.Text(f"Total Courses: {len(self.courses)}")],
            [sg.Text(f"Total Students: {len(self.master_student_list)}")],
            [sg.Text(f"Total Passed: {total_passed}")],
            [sg.Text(f"Total Failed: {total_failed}")],
            [sg.Text(f"Overall Pass Rate: {overall_pass_rate:.1f}%", text_color="#28a745", font=("Segoe UI", 11, "bold"))],
            [sg.Sizegrip()],
        ]
        
        self.window = sg.Window("Class Record - Dashboard", layout, finalize=True, 
                                size=(1000, 700), resizable=True, margins=(10, 10))
        
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                self.window.close()
                sys.exit(0)
            elif event == "-COURSE_TABLE-":
                selected = values["-COURSE_TABLE-"]
                if selected:
                    course_code = course_rows[selected[0]][1]
                    course = next((c for c in self.courses if c.course_code == course_code), None)
                    if course:
                        self.current_course = course
                        self.show_course_detail_view(course)
                        break
            elif event == "View Course":
                selected = values["-COURSE_TABLE-"]
                if selected:
                    course_code = course_rows[selected[0]][1]
                    course = next((c for c in self.courses if c.course_code == course_code), None)
                    if course:
                        self.show_course_detail_view(course)
                        break
            elif event == "Add Course":
                self.add_new_course()
                break
            elif event == "Import Students":
                self.import_students()
                break
            elif event == "Grading Criteria":
                if self.courses:
                    self.show_grading_criteria(self.courses[0])
                else:
                    sg.popup_error("Please create a course first!")
                break

    def show_course_detail_view(self, course):
        if self.window:
            self.window.close()
        
        stats = course.get_pass_fail_stats()
        avg_grade = course.get_class_average()
        dist = course.get_grade_distribution()
        
        roster_rows = []
        for student in course.students:
            gd = course.grades.get(student.id_number, {})
            roster_rows.append([student.last_name, student.first_name, student.id_number,
                               f"{gd.get('final_grade', 0):.2f}", gd.get("letter_grade", "F"), gd.get("remarks", "")])
        
        layout = [
            [sg.Text(course.full_name(), font=("Segoe UI", 18, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text("Course Information", font=("Segoe UI", 14, "bold"))],
            [sg.Text("Code:"), sg.Text(course.course_code)],
            [sg.Text("Schedule:"), sg.Text(f"{course.schedule} {course.days}")],
            [sg.Text("Room:"), sg.Text(course.room)],
            [sg.Text("Description:"), sg.Text(course.description)],
            [sg.HorizontalSeparator()],
            [sg.Text("Course Statistics", font=("Segoe UI", 14, "bold"))],
            [sg.Text(f"Total Students: {len(course.students)}")],
            [sg.Text(f"Passed: {stats['passed']} ({stats['pass_rate']:.1f}%)", text_color="#28a745")],
            [sg.Text(f"Failed: {stats['failed']} ({stats['fail_rate']:.1f}%)", text_color="#dc3545")],
            [sg.Text(f"Class Average: {avg_grade:.2f}")],
            [sg.HorizontalSeparator()],
            [sg.Text("Grade Distribution", font=("Segoe UI", 14, "bold"))],
        ]
        
        for grade in ["A", "B", "C", "D", "E", "F"]:
            count = dist[grade]
            pct = dist[f"{grade}_pct"]
            color = "#28a745" if grade in ["A", "B", "C"] else "#dc3545" if grade == "F" else "#ffc107"
            layout.append([sg.Text(f"{grade}: {count} ({pct:.1f}%)", text_color=color)])
        
        layout += [
            [sg.HorizontalSeparator()],
            [sg.Text("Student Roster", font=("Segoe UI", 14, "bold"))],
            [sg.Table(roster_rows, ["Last Name", "First Name", "ID", "Final", "Letter", "Remarks"],
                     auto_size_columns=True, alternating_row_color="#2d2d2d",
                     header_background_color="#0078d4", header_text_color="white",
                     size=(900, 200))],
            [sg.HorizontalSeparator()],
            [sg.Button("Back", size=(12, 2)), sg.Button("Enter Grades", size=(12, 2)),
             sg.Button("Edit Course", size=(12, 2)), sg.Button("Grading Criteria", size=(12, 2)),
             sg.Button("Export XLSX", size=(12, 2)), sg.Button("Export PDF", size=(12, 2))],
            [sg.Sizegrip()],
        ]
        
        self.window = sg.Window(f"HCDC - {course.full_name()}", layout, finalize=True,
                                size=(1000, 700), resizable=True)
        
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                self.window.close()
                sys.exit(0)
            elif event == "Back":
                self.show_dashboard()
                break
            elif event == "Enter Grades":
                self.show_grade_entry(course)
                break
            elif event == "Edit Course":
                self.edit_course(course)
                break
            elif event == "Grading Criteria":
                self.show_grading_criteria(course)
                break
            elif event == "Export XLSX":
                self.export_course_to_xlsx(course)
            elif event == "Export PDF":
                self.export_course_to_pdf(course)

    def add_new_course(self):
        layout = [
            [sg.Text("Add New Course", font=("Segoe UI", 16, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text("Course Code:"), sg.Input(key="-CODE-", size=(25, 1))],
            [sg.Text("Course Title:"), sg.Input(key="-TITLE-", size=(25, 1))],
            [sg.Text("Offering Number:"), sg.Input(key="-OFFERING-", size=(25, 1), default_text="1")],
            [sg.Text("Description:"), sg.Input(key="-DESC-", size=(25, 1))],
            [sg.Text("Schedule:"), sg.Input(key="-SCHEDULE-", size=(25, 1))],
            [sg.Text("Days:"), sg.Input(key="-DAYS-", size=(25, 1))],
            [sg.Text("Room:"), sg.Input(key="-ROOM-", size=(25, 1))],
            [sg.HorizontalSeparator()],
            [sg.Button("Save", size=(10, 2)), sg.Button("Cancel", size=(10, 2))],
        ]
        
        window = sg.Window("Add Course", layout, finalize=True, modal=True)
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "Cancel"):
                window.close()
                return
            elif event == "Save":
                code = values["-CODE-"]
                title = values["-TITLE-"]
                if not code or not title:
                    sg.popup_error("Code and Title required!")
                    continue
                if any(c.course_code == code for c in self.courses):
                    sg.popup_error(f"Course {code} already exists!")
                    continue
                course = Course(code, title, values["-OFFERING-"], values["-DESC-"],
                               values["-SCHEDULE-"], values["-ROOM-"], values["-DAYS-"])
                for comp in [GradingComponent("Assignments", 10, 10), GradingComponent("Oral Recitation", 5, 5),
                            GradingComponent("Seatwork", 5, 5), GradingComponent("Quizzes", 30, 30),
                            GradingComponent("Pre / Semi exam", 25, 25), GradingComponent("Mid / Fin exam", 25, 25)]:
                    course.add_grading_component(comp)
                self.courses.append(course)
                sg.popup_success(f"Course {course.full_name()} added!")
                window.close()
                self.show_dashboard()
                return

    def edit_course(self, course):
        layout = [
            [sg.Text(f"Edit: {course.full_name()}", font=("Segoe UI", 16, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text("Code:"), sg.Input(course.course_code, key="-CODE-", size=(25, 1))],
            [sg.Text("Title:"), sg.Input(course.course_title, key="-TITLE-", size=(25, 1))],
            [sg.Text("Offering:"), sg.Input(course.offering_number, key="-OFFERING-", size=(25, 1))],
            [sg.Text("Description:"), sg.Input(course.description, key="-DESC-", size=(25, 1))],
            [sg.Text("Schedule:"), sg.Input(course.schedule, key="-SCHEDULE-", size=(25, 1))],
            [sg.Text("Days:"), sg.Input(course.days, key="-DAYS-", size=(25, 1))],
            [sg.Text("Room:"), sg.Input(course.room, key="-ROOM-", size=(25, 1))],
            [sg.HorizontalSeparator()],
            [sg.Button("Save", size=(10, 2)), sg.Button("Cancel", size=(10, 2))],
        ]
        window = sg.Window("Edit Course", layout, finalize=True, modal=True)
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "Cancel"):
                window.close()
                return
            elif event == "Save":
                course.course_code = values["-CODE-"]
                course.course_title = values["-TITLE-"]
                course.offering_number = values["-OFFERING-"]
                course.description = values["-DESC-"]
                course.schedule = values["-SCHEDULE-"]
                course.days = values["-DAYS-"]
                course.room = values["-ROOM-"]
                sg.popup_success("Course updated!")
                window.close()
                self.show_course_detail_view(course)
                return

    def import_students(self):
        layout = [
            [sg.Text("Import Students", font=("Segoe UI", 16, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text("Select Course:")],
            [sg.Combo([c.full_name() for c in self.courses], key="-COURSE_SELECT-", size=(40, 1))],
            [sg.Text("File Type:")],
            [sg.Radio("CSV", "FILE_TYPE", key="-CSV-", default=True),
             sg.Radio("Excel (.xlsx)", "FILE_TYPE", key="-EXCEL-")],
            [sg.Text("File Path:")],
            [sg.Input(key="-FILE_PATH-", size=(40, 1)),
             sg.FileBrowse("Browse", file_types=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")])],
            [sg.HorizontalSeparator()],
            [sg.Multiline("File should contain: Last Name, First Name, ID Number, Email Address",
                         size=(50, 3), disabled=True, text_color="#666")],
            [sg.Button("Import", size=(10, 2)), sg.Button("Cancel", size=(10, 2))],
        ]
        window = sg.Window("Import Students", layout, finalize=True, modal=True)
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "Cancel"):
                window.close()
                return
            elif event == "Import":
                course_name = values["-COURSE_SELECT-"]
                file_path = values["-FILE_PATH-"]
                if not course_name or not file_path:
                    sg.popup_error("Please select course and file!")
                    continue
                course = next((c for c in self.courses if c.full_name() == course_name), None)
                if not course:
                    sg.popup_error("Course not found!")
                    continue
                try:
                    if values["-CSV-"]:
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)
                    imported_count = 0
                    for _, row in df.iterrows():
                        last_name = str(row.get("Last Name", row.get("Last", row.get("LNAME", "")))).strip()
                        first_name = str(row.get("First Name", row.get("First", row.get("FNAME", "")))).strip()
                        id_number = str(row.get("ID Number", row.get("ID", row.get("IDNO", "")))).strip()
                        email = str(row.get("Email Address", row.get("Email", row.get("EMAIL", "")))).strip()
                        if last_name and first_name and id_number:
                            student = Student(last_name, first_name, id_number, email)
                            course.add_student(student)
                            if student not in self.master_student_list:
                                self.master_student_list.append(student)
                            imported_count += 1
                    course.calculate_grades()
                    sg.popup_success(f"Imported {imported_count} students to {course_name}!")
                    window.close()
                    self.show_course_detail_view(course)
                    return
                except Exception as e:
                    sg.popup_error(f"Error importing file: {str(e)}")

    def show_grading_criteria(self, course):
        if self.window:
            self.window.close()
        
        comp_rows = []
        for comp in course.grading_components:
            comp_rows.append([
                comp.name, f"{comp.prelim_mid_weight}%", f"{comp.semis_final_weight}%",
                f"{comp.total_weight()}%", "Edit", "Delete"
            ])
        
        total_prelim = sum(c.prelim_mid_weight for c in course.grading_components)
        total_semis = sum(c.semis_final_weight for c in course.grading_components)
        total_overall = total_prelim + total_semis
        
        layout = [
            [sg.Text(f"Grading Criteria - {course.full_name()}", font=("Segoe UI", 16, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text(f"Prelim-Mid Total: {total_prelim}%", text_color="#28a745" if total_prelim == 50 else "#dc3545"),
             sg.Text(f"Semis-Final Total: {total_semis}%", text_color="#28a745" if total_semis == 50 else "#dc3545"),
             sg.Text(f"Overall Total: {total_overall}%", text_color="#28a745" if total_overall == 100 else "#dc3545")],
            [sg.HorizontalSeparator()],
            [sg.Table(comp_rows, ["Component", "Prelim-Mid %", "Semis-Final %", "Total %", "", ""],
                     auto_size_columns=True, alternating_row_color="#2d2d2d",
                     header_background_color="#0078d4", header_text_color="white",
                     key="-COMP_TABLE-", enable_events=True, size=(800, 200))],
            [sg.HorizontalSeparator()],
            [sg.Text("Add New Component:", font=("Segoe UI", 12, "bold"))],
            [sg.Text("Name:"), sg.Input(key="-NEW_COMP_NAME-", size=(20, 1))],
            [sg.Text("Prelim-Mid %:"), sg.Input("0", key="-NEW_PRELIM-", size=(8, 1))],
            [sg.Text("Semis-Final %:"), sg.Input("0", key="-NEW_SEMIS-", size=(8, 1))],
            [sg.Button("Add Component", size=(12, 2)), sg.Button("Back", size=(12, 2))],
            [sg.HorizontalSeparator()],
            [sg.Text("Extra Credits Settings:", font=("Segoe UI", 12, "bold"))],
            [sg.Text("Extra credits are automatically split equally between both bigrades")],
            [sg.Button("Set Extra Credits", size=(15, 2)), sg.Button("Apply to All Students", size=(20, 2))],
            [sg.Sizegrip()],
        ]
        
        self.window = sg.Window(f"Grading Criteria - {course.full_name()}", layout, finalize=True,
                                size=(900, 600), resizable=True)
        
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                self.window.close()
                sys.exit(0)
            elif event == "Back":
                self.show_course_detail_view(course)
                break
            elif event == "Add Component":
                name = values["-NEW_COMP_NAME-"]
                try:
                    prelim = float(values["-NEW_PRELIM-"] or 0)
                    semis = float(values["-NEW_SEMIS-"] or 0)
                except ValueError:
                    sg.popup_error("Please enter valid percentages!")
                    continue
                if not name:
                    sg.popup_error("Component name required!")
                    continue
                new_comp = GradingComponent(name, prelim, semis)
                course.add_grading_component(new_comp)
                course.calculate_grades()
                sg.popup_success(f"Added component: {name}")
                self.show_grading_criteria(course)
                break
            elif event == "Set Extra Credits":
                self.set_extra_credits(course)
                break
            elif event == "Apply to All Students":
                course.calculate_grades()
                sg.popup_success("Grades recalculated with current criteria!")
            elif event == "-COMP_TABLE-":
                selected = values["-COMP_TABLE-"]
                if selected:
                    row_idx = selected[0]
                    action_col = selected[1]
                    comp = course.grading_components[row_idx]
                    if action_col == 4:
                        self.edit_grading_component(course, comp)
                        break
                    elif action_col == 5:
                        if sg.popup_yes_no(f"Delete {comp.name}?", title="Confirm Delete") == "Yes":
                            course.grading_components.remove(comp)
                            course.calculate_grades()
                            sg.popup_success(f"Deleted {comp.name}")
                            self.show_grading_criteria(course)
                            break

    def edit_grading_component(self, course, component):
        layout = [
            [sg.Text(f"Edit: {component.name}", font=("Segoe UI", 14, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text("Name:"), sg.Input(component.name, key="-NAME-", size=(25, 1))],
            [sg.Text("Prelim-Mid Weight (%):"), sg.Input(str(component.prelim_mid_weight), key="-PRELIM-", size=(10, 1))],
            [sg.Text("Semis-Final Weight (%):"), sg.Input(str(component.semis_final_weight), key="-SEMIS-", size=(10, 1))],
            [sg.Text("Max Score:"), sg.Input(str(component.max_score), key="-MAX-", size=(10, 1))],
            [sg.HorizontalSeparator()],
            [sg.Button("Save", size=(10, 2)), sg.Button("Cancel", size=(10, 2))],
        ]
        window = sg.Window("Edit Component", layout, finalize=True, modal=True)
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "Cancel"):
                window.close()
                return
            elif event == "Save":
                try:
                    component.name = values["-NAME-"]
                    component.prelim_mid_weight = float(values["-PRELIM-"])
                    component.semis_final_weight = float(values["-SEMIS-"])
                    component.max_score = float(values["-MAX-"])
                    course.calculate_grades()
                    sg.popup_success("Component updated!")
                    window.close()
                    self.show_grading_criteria(course)
                    return
                except ValueError:
                    sg.popup_error("Please enter valid numbers!")

    def set_extra_credits(self, course):
        layout = [
            [sg.Text(f"Set Extra Credits - {course.full_name()}", font=("Segoe UI", 14, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text("Extra credits will be split equally between Prelim-Mid and Semis-Final")],
            [sg.HorizontalSeparator()],
        ]
        for student in course.students:
            current_ec = course.extra_credits.get(student.id_number, 0)
            layout.append([sg.Text(f"{student.full_name()}: "), sg.Input(str(current_ec), key=f"-EC_{student.id_number}-", size=(8, 1))])
        layout += [
            [sg.HorizontalSeparator()],
            [sg.Button("Save", size=(10, 2)), sg.Button("Cancel", size=(10, 2))],
        ]
        window = sg.Window("Set Extra Credits", layout, finalize=True, modal=True)
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "Cancel"):
                window.close()
                return
            elif event == "Save":
                for student in course.students:
                    try:
                        ec = float(values.get(f"-EC_{student.id_number}-", 0) or 0)
                        course.extra_credits[student.id_number] = ec
                    except ValueError:
                        pass
                course.calculate_grades()
                sg.popup_success("Extra credits updated!")
                window.close()
                return

    def show_grade_entry(self, course):
        if self.window:
            self.window.close()
        
        layout = [
            [sg.Text(f"Grade Entry - {course.full_name()}", font=("Segoe UI", 16, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text("Select Bigrade:")],
            [sg.Radio("Prelim-Mid", "BIGRADE", key="-PRELIM_MID-", default=True),
             sg.Radio("Semis-Final", "BIGRADE", key="-SEMIS_FINAL-")],
            [sg.HorizontalSeparator()],
            [sg.Text("Select Student:")],
            [sg.Combo([s.full_name() for s in course.students], key="-STUDENT_SELECT-", size=(40, 1), enable_events=True)],
            [sg.HorizontalSeparator()],
        ]
        
        grade_inputs = []
        for comp in course.grading_components:
            grade_inputs.append([sg.Text(f"{comp.name} (Max: {comp.max_score}):"),
                               sg.Input("0", key=f"-GRADE_{comp.name}-", size=(10, 1))])
        
        layout += grade_inputs
        layout += [
            [sg.HorizontalSeparator()],
            [sg.Button("Save Grades", size=(12, 2)), sg.Button("Save & Next", size=(12, 2)),
             sg.Button("Back", size=(12, 2))],
            [sg.Sizegrip()],
        ]
        
        self.window = sg.Window(f"Grade Entry - {course.full_name()}", layout, finalize=True,
                                size=(600, 500), resizable=True)
        
        current_student_idx = 0
        
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                self.window.close()
                sys.exit(0)
            elif event == "Back":
                self.show_course_detail_view(course)
                break
            elif event == "-STUDENT_SELECT-":
                pass
            elif event in ["Save Grades", "Save & Next"]:
                student_name = values["-STUDENT_SELECT-"]
                student = next((s for s in course.students if s.full_name() == student_name), None)
                if not student:
                    sg.popup_error("Please select a student!")
                    continue
                is_prelim = values["-PRELIM_MID-"]
                scores = {}
                for comp in course.grading_components:
                    try:
                        score = float(values.get(f"-GRADE_{comp.name}-", 0) or 0)
                        scores[comp.name] = score
                    except ValueError:
                        scores[comp.name] = 0
                if is_prelim:
                    course.grades[student.id_number]["prelim_mid_scores"] = scores
                else:
                    course.grades[student.id_number]["semis_final_scores"] = scores
                course.calculate_grades()
                sg.popup_success("Grades saved!")
                if event == "Save & Next":
                    current_student_idx = (current_student_idx + 1) % len(course.students)
                    self.window["-STUDENT_SELECT-"].update(value=course.students[current_student_idx].full_name())
                    self.update_grade_fields(course, course.students[current_student_idx])
                else:
                    self.show_grade_entry(course)
                    break

    def update_grade_fields(self, course, student):
        is_prelim = self.window["-PRELIM_MID-"].get()
        scores = course.grades.get(student.id_number, {}).get("prelim_mid_scores" if is_prelim else "semis_final_scores", {})
        for comp in course.grading_components:
            self.window[f"-GRADE_{comp.name}-"].update(value=str(scores.get(comp.name, 0)))

    def show_master_list(self):
        if self.window:
            self.window.close()
        
        master_rows = []
        for student in self.master_student_list:
            courses_grades = []
            for course in self.courses:
                if student in course.students:
                    gd = course.grades.get(student.id_number, {})
                    courses_grades.append(f"{course.course_code}: {gd.get('final_grade', 0):.2f}")
                else:
                    courses_grades.append(f"{course.course_code}: N/A")
            master_rows.append([
                student.last_name, student.first_name, student.id_number, student.email,
                ", ".join(courses_grades)
            ])
        
        layout = [
            [sg.Text("Master Student List", font=("Segoe UI", 18, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
            [sg.Text(f"Total Students: {len(self.master_student_list)}", font=("Segoe UI", 12))],
            [sg.HorizontalSeparator()],
            [sg.Table(master_rows, ["Last Name", "First Name", "ID", "Email", "Grades"],
                     auto_size_columns=True, alternating_row_color="#2d2d2d",
                     header_background_color="#0078d4", header_text_color="white",
                     size=(1000, 400))],
            [sg.HorizontalSeparator()],
            [sg.Text("Course Statistics:", font=("Segoe UI", 14, "bold"))],
        ]
        
        for course in self.courses:
            stats = course.get_pass_fail_stats()
            layout.append([
                sg.Text(f"{course.course_code}:", size=(20, 1)),
                sg.Text(f"Pass: {stats['passed']} ({stats['pass_rate']:.1f}%)", text_color="#28a745", size=(25, 1)),
                sg.Text(f"Fail: {stats['failed']} ({stats['fail_rate']:.1f}%)", text_color="#dc3545", size=(25, 1))
            ])
        
        layout += [
            [sg.HorizontalSeparator()],
            [sg.Button("Back", size=(12, 2)), sg.Button("Export All XLSX", size=(15, 2)),
             sg.Button("Export All PDF", size=(15, 2))],
            [sg.Sizegrip()],
        ]
        
        self.window = sg.Window("HCDC - Master List", layout, finalize=True,
                                size=(1100, 700), resizable=True)
        
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                self.window.close()
                sys.exit(0)
            elif event == "Back":
                self.show_dashboard()
                break
            elif event == "Export All XLSX":
                self.export_to_xlsx()
            elif event == "Export All PDF":
                self.export_to_pdf()

    def show_course_reports(self):
        if self.window:
            self.window.close()
        
        layout = [
            [sg.Text("Course Reports", font=("Segoe UI", 18, "bold"), text_color="#0078d4")],
            [sg.HorizontalSeparator(color="#0078d4")],
        ]
        
        for course in self.courses:
            stats = course.get_pass_fail_stats()
            avg = course.get_class_average()
            dist = course.get_grade_distribution()
            layout += [
                [sg.Text(course.full_name(), font=("Segoe UI", 14, "bold"))],
                [sg.Text(f"  Students: {len(course.students)} | Avg: {avg:.2f} | Pass Rate: {stats['pass_rate']:.1f}%")],
                [sg.Text(f"  Grade Dist: A:{dist['A']} B:{dist['B']} C:{dist['C']} D:{dist['D']} E:{dist['E']} F:{dist['F']}")],
                [sg.HorizontalSeparator()],
            ]
        
        layout += [
            [sg.Button("Back", size=(12, 2))],
            [sg.Sizegrip()],
        ]
        
        self.window = sg.Window("HCDC - Course Reports", layout, finalize=True,
                                size=(800, 600), resizable=True)
        
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                self.window.close()
                sys.exit(0)
            elif event == "Back":
                self.show_dashboard()
                break

    def export_course_to_xlsx(self, course):
        try:
            filepath = sg.popup_get_file("Save as XLSX", save_as=True, default_extension=".xlsx",
                                         file_types=[("Excel Files", "*.xlsx")],
                                         default_path=f"{course.course_code.replace(' ', '_')}_ClassRecord.xlsx")
            if not filepath:
                return
            self._export_course_to_xlsx(course, filepath)
            sg.popup_success(f"Exported {course.full_name()} to {filepath}")
        except Exception as e:
            sg.popup_error(f"Export failed: {str(e)}")

    def _export_course_to_xlsx(self, course, filepath):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = course.course_code
        
        ws.append([f"{course.full_name()}"])
        ws.append([f"Schedule: {course.schedule} {course.days} | Room: {course.room}"])
        ws.append([])
        
        ws.append(["Course Code", course.course_code])
        ws.append(["Course Title", course.course_title])
        ws.append(["Offering Number", course.offering_number])
        ws.append(["Description", course.description])
        ws.append([])
        
        ws.append(["GRADING CRITERIA"])
        ws.append(["Component", "Prelim-Mid %", "Semis-Final %", "Total %"])
        for comp in course.grading_components:
            ws.append([comp.name, comp.prelim_mid_weight, comp.semis_final_weight, comp.total_weight()])
        ws.append([])
        
        total_prelim = sum(c.prelim_mid_weight for c in course.grading_components)
        total_semis = sum(c.semis_final_weight for c in course.grading_components)
        ws.append(["TOTALS", total_prelim, total_semis, total_prelim + total_semis])
        ws.append([])
        
        ws.append(["CLASS STATISTICS"])
        stats = course.get_pass_fail_stats()
        avg = course.get_class_average()
        ws.append(["Total Students", len(course.students)])
        ws.append(["Passed", stats['passed'], f"({stats['pass_rate']:.1f}%)"])
        ws.append(["Failed", stats['failed'], f"({stats['fail_rate']:.1f}%)"])
        ws.append(["Class Average", f"{avg:.2f}"])
        ws.append([])
        
        ws.append(["STUDENT ROSTER"])
        headers = ["No", "Last Name", "First Name", "ID Number", "Email"]
        for comp in course.grading_components:
            headers.append(f"{comp.name} (PM)")
        headers.extend(["PM Total", "SF Total", "Final Grade", "Letter Grade", "Remarks", "Extra Credit"])
        ws.append(headers)
        
        for idx, student in enumerate(course.students, 1):
            row = [
                idx, student.last_name, student.first_name, student.id_number, student.email
            ]
            gd = course.grades.get(student.id_number, {})
            pm_scores = gd.get("prelim_mid_scores", {})
            sf_scores = gd.get("semis_final_scores", {})
            for comp in course.grading_components:
                row.append(pm_scores.get(comp.name, ""))
            row.extend([
                gd.get("prelim_mid_total", ""),
                gd.get("semis_final_total", ""),
                gd.get("final_grade", ""),
                gd.get("letter_grade", ""),
                gd.get("remarks", ""),
                course.extra_credits.get(student.id_number, 0)
            ])
            ws.append(row)
        
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)
        
        wb.save(filepath)

    def export_to_xlsx(self):
        try:
            filepath = sg.popup_get_file("Save All Courses as XLSX", save_as=True, default_extension=".xlsx",
                                         file_types=[("Excel Files", "*.xlsx")],
                                         default_path="HCDC_ClassRecords_All.xlsx")
            if not filepath:
                return
            wb = openpyxl.Workbook()
            del wb["Sheet"]
            for course in self.courses:
                self._export_course_to_xlsx_multi(course, wb, course.course_code)
            wb.save(filepath)
            sg.popup_success(f"Exported all courses to {filepath}")
        except Exception as e:
            sg.popup_error(f"Export failed: {str(e)}")

    def _export_course_to_xlsx_multi(self, course, wb, sheet_name):
        ws = wb.create_sheet(title=sheet_name)
        ws.append([f"{course.full_name()}"])
        ws.append([f"Schedule: {course.schedule} {course.days} | Room: {course.room}"])
        ws.append([])
        
        ws.append(["Course Code", course.course_code])
        ws.append(["Course Title", course.course_title])
        ws.append(["Offering Number", course.offering_number])
        ws.append(["Description", course.description])
        ws.append([])
        
        ws.append(["GRADING CRITERIA"])
        ws.append(["Component", "Prelim-Mid %", "Semis-Final %", "Total %"])
        for comp in course.grading_components:
            ws.append([comp.name, comp.prelim_mid_weight, comp.semis_final_weight, comp.total_weight()])
        ws.append([])
        
        total_prelim = sum(c.prelim_mid_weight for c in course.grading_components)
        total_semis = sum(c.semis_final_weight for c in course.grading_components)
        ws.append(["TOTALS", total_prelim, total_semis, total_prelim + total_semis])
        ws.append([])
        
        ws.append(["CLASS STATISTICS"])
        stats = course.get_pass_fail_stats()
        avg = course.get_class_average()
        ws.append(["Total Students", len(course.students)])
        ws.append(["Passed", stats['passed'], f"({stats['pass_rate']:.1f}%)"])
        ws.append(["Failed", stats['failed'], f"({stats['fail_rate']:.1f}%)"])
        ws.append(["Class Average", f"{avg:.2f}"])
        ws.append([])
        
        ws.append(["STUDENT ROSTER"])
        headers = ["No", "Last Name", "First Name", "ID Number", "Email"]
        for comp in course.grading_components:
            headers.append(f"{comp.name} (PM)")
        headers.extend(["PM Total", "SF Total", "Final Grade", "Letter Grade", "Remarks", "Extra Credit"])
        ws.append(headers)
        
        for idx, student in enumerate(course.students, 1):
            row = [
                idx, student.last_name, student.first_name, student.id_number, student.email
            ]
            gd = course.grades.get(student.id_number, {})
            pm_scores = gd.get("prelim_mid_scores", {})
            sf_scores = gd.get("semis_final_scores", {})
            for comp in course.grading_components:
                row.append(pm_scores.get(comp.name, ""))
            row.extend([
                gd.get("prelim_mid_total", ""),
                gd.get("semis_final_total", ""),
                gd.get("final_grade", ""),
                gd.get("letter_grade", ""),
                gd.get("remarks", ""),
                course.extra_credits.get(student.id_number, 0)
            ])
            ws.append(row)
        
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)

    def export_course_to_pdf(self, course):
        try:
            filepath = sg.popup_get_file("Save as PDF", save_as=True, default_extension=".pdf",
                                         file_types=[("PDF Files", "*.pdf")],
                                         default_path=f"{course.course_code.replace(' ', '_')}_ClassRecord.pdf")
            if not filepath:
                return
            self._export_course_to_pdf(course, filepath)
            sg.popup_success(f"Exported {course.full_name()} to {filepath}")
        except Exception as e:
            sg.popup_error(f"Export failed: {str(e)}")

    def _export_course_to_pdf(self, course, filepath):
        doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            name="Title",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#0078d4"),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            name="Heading2",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#0078d4"),
            spaceAfter=12,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            name="Normal",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=6
        )
        
        elements.append(Paragraph(f"{course.full_name()}", title_style))
        elements.append(Paragraph(f"Schedule: {course.schedule} {course.days} | Room: {course.room}", normal_style))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("Course Information", heading_style))
        info_data = [
            ["Course Code:", course.course_code],
            ["Course Title:", course.course_title],
            ["Offering Number:", course.offering_number],
            ["Description:", course.description],
        ]
        info_table = Table(info_data, colWidths=[120, 300])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("Grading Criteria", heading_style))
        criteria_data = [["Component", "Prelim-Mid %", "Semis-Final %", "Total %"]]
        for comp in course.grading_components:
            criteria_data.append([comp.name, f"{comp.prelim_mid_weight}%", f"{comp.semis_final_weight}%", f"{comp.total_weight()}%"])
        total_prelim = sum(c.prelim_mid_weight for c in course.grading_components)
        total_semis = sum(c.semis_final_weight for c in course.grading_components)
        criteria_data.append(["TOTALS", f"{total_prelim}%", f"{total_semis}%", f"{total_prelim + total_semis}%"])
        criteria_table = Table(criteria_data)
        criteria_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ]))
        elements.append(criteria_table)
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("Class Statistics", heading_style))
        stats = course.get_pass_fail_stats()
        avg = course.get_class_average()
        stats_data = [
            ["Total Students", str(len(course.students))],
            ["Passed", f"{stats['passed']} ({stats['pass_rate']:.1f}%)"],
            ["Failed", f"{stats['failed']} ({stats['fail_rate']:.1f}%)"],
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
        
        elements.append(Paragraph("Student Roster", heading_style))
        headers = ["No", "Last Name", "First Name", "ID", "PM Total", "SF Total", "Final", "Letter", "Remarks"]
        roster_data = [headers]
        for idx, student in enumerate(course.students, 1):
            gd = course.grades.get(student.id_number, {})
            roster_data.append([
                str(idx), student.last_name, student.first_name, student.id_number,
                f"{gd.get('prelim_mid_total', 0):.2f}",
                f"{gd.get('semis_final_total', 0):.2f}",
                f"{gd.get('final_grade', 0):.2f}",
                gd.get("letter_grade", ""),
                gd.get("remarks", "")
            ])
        roster_table = Table(roster_data)
        roster_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        elements.append(roster_table)
        
        doc.build(elements)

    def export_to_pdf(self):
        try:
            filepath = sg.popup_get_file("Save All Courses as PDF", save_as=True, default_extension=".pdf",
                                         file_types=[("PDF Files", "*.pdf")],
                                         default_path="HCDC_ClassRecords_All.pdf")
            if not filepath:
                return
            doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
            elements = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                name="Title",
                parent=styles["Heading1"],
                fontSize=20,
                textColor=colors.HexColor("#0078d4"),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            elements.append(Paragraph("Class Records - All Courses", title_style))
            elements.append(PageBreak())
            
            for course in self.courses:
                course_elements = []
                course_elements.append(Paragraph(f"{course.full_name()}", styles["Heading1"]))
                course_elements.append(Paragraph(f"Schedule: {course.schedule} {course.days} | Room: {course.room}", styles["Normal"]))
                course_elements.append(Spacer(1, 12))
                
                course_elements.append(Paragraph("Course Information", styles["Heading2"]))
                info_data = [
                    ["Course Code:", course.course_code],
                    ["Course Title:", course.course_title],
                    ["Offering Number:", course.offering_number],
                    ["Description:", course.description],
                ]
                info_table = Table(info_data, colWidths=[120, 300])
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ]))
                course_elements.append(info_table)
                course_elements.append(Spacer(1, 12))
                
                course_elements.append(Paragraph("Grading Criteria", styles["Heading2"]))
                criteria_data = [["Component", "Prelim-Mid %", "Semis-Final %", "Total %"]]
                for comp in course.grading_components:
                    criteria_data.append([comp.name, f"{comp.prelim_mid_weight}%", f"{comp.semis_final_weight}%", f"{comp.total_weight()}%"])
                criteria_table = Table(criteria_data)
                criteria_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ]))
                course_elements.append(criteria_table)
                course_elements.append(Spacer(1, 12))
                
                course_elements.append(Paragraph("Class Statistics", styles["Heading2"]))
                stats = course.get_pass_fail_stats()
                avg = course.get_class_average()
                stats_data = [
                    ["Total Students", str(len(course.students))],
                    ["Passed", f"{stats['passed']} ({stats['pass_rate']:.1f}%)"],
                    ["Failed", f"{stats['failed']} ({stats['fail_rate']:.1f}%)"],
                    ["Class Average", f"{avg:.2f}"],
                ]
                stats_table = Table(stats_data, colWidths=[150, 200])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ]))
                course_elements.append(stats_table)
                course_elements.append(Spacer(1, 12))
                
                course_elements.append(Paragraph("Student Roster", styles["Heading2"]))
                headers = ["No", "Last Name", "First Name", "ID", "PM Total", "SF Total", "Final", "Letter", "Remarks"]
                roster_data = [headers]
                for idx, student in enumerate(course.students, 1):
                    gd = course.grades.get(student.id_number, {})
                    roster_data.append([
                        str(idx), student.last_name, student.first_name, student.id_number,
                        f"{gd.get('prelim_mid_total', 0):.2f}",
                        f"{gd.get('semis_final_total', 0):.2f}",
                        f"{gd.get('final_grade', 0):.2f}",
                        gd.get("letter_grade", ""),
                        gd.get("remarks", "")
                    ])
                roster_table = Table(roster_data)
                roster_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0078d4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ]))
                course_elements.append(roster_table)
                course_elements.append(PageBreak())
                elements.extend(course_elements)
            
            doc.build(elements)
            sg.popup_success(f"Exported all courses to {filepath}")
        except Exception as e:
            sg.popup_error(f"Export failed: {str(e)}")


def main():
    app = ClassRecordApp()


if __name__ == "__main__":
    main()
