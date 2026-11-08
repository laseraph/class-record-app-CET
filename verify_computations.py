"""
Verify Instance-Based Grading Computations
This script demonstrates the CORRECT way to compute grades from instances

The key insight: Each instance has a weight that represents its contribution
to the component. The sum of instance weights for a component should equal
the component's total weight.

For example:
- Assignments component = 10% of Prelim-Mid
- 5 Assignment instances, each with weight 2% (2% * 5 = 10%)
- Each Assignment instance: (score/max) * 2%
- Sum of all Assignment instances = Assignments component contribution
"""

def get_letter_grade(grade):
    if grade >= 95:
        return 'A - Passed'
    elif grade >= 90:
        return 'B - Passed'
    elif grade >= 85:
        return 'C - Passed'
    elif grade >= 80:
        return 'D - Passed'
    elif grade >= 75:
        return 'E - Passed'
    else:
        return 'F - Failed'


# Define the grading structure
# Component: (name, category, prelim_weight, semis_weight)
components = [
    ('Assignments', 'class_standing', 10.0, 10.0),
    ('Oral Recitation', 'class_standing', 5.0, 5.0),
    ('Seatwork', 'class_standing', 5.0, 5.0),
    ('Quizzes', 'class_standing', 30.0, 30.0),
    ('Pre / Semi exam', 'major_exam', 25.0, 0.0),
    ('Mid / Fin exam', 'major_exam', 0.0, 25.0),
]

# Define instances for each component
# Format: (component_name, instance_number, title, max_score, weight)
# Note: The weight here is the percentage this instance contributes to the PERIOD
# Sum of weights for a component should equal the component's weight
prelim_instances = [
    # Assignments (5 instances, total = 10% for component, so each = 2% of period)
    ('Assignments', 1, 'Assignment 1', 100.0, 2.0),
    ('Assignments', 2, 'Assignment 2', 100.0, 2.0),
    ('Assignments', 3, 'Assignment 3', 100.0, 2.0),
    ('Assignments', 4, 'Assignment 4', 100.0, 2.0),
    ('Assignments', 5, 'Assignment 5', 100.0, 2.0),
    
    # Oral Recitation (5 instances, total = 5% for component, so each = 1% of period)
    ('Oral Recitation', 1, 'Recitation 1', 100.0, 1.0),
    ('Oral Recitation', 2, 'Recitation 2', 100.0, 1.0),
    ('Oral Recitation', 3, 'Recitation 3', 100.0, 1.0),
    ('Oral Recitation', 4, 'Recitation 4', 100.0, 1.0),
    ('Oral Recitation', 5, 'Recitation 5', 100.0, 1.0),
    
    # Seatwork (5 instances, total = 5% for component, so each = 1% of period)
    ('Seatwork', 1, 'Seatwork 1', 50.0, 1.0),
    ('Seatwork', 2, 'Seatwork 2', 50.0, 1.0),
    ('Seatwork', 3, 'Seatwork 3', 50.0, 1.0),
    ('Seatwork', 4, 'Seatwork 4', 50.0, 1.0),
    ('Seatwork', 5, 'Seatwork 5', 50.0, 1.0),
    
    # Quizzes (3 instances, total = 30% for component, so each = 10% of period)
    ('Quizzes', 1, 'Quiz 1', 100.0, 10.0),
    ('Quizzes', 2, 'Quiz 2', 100.0, 10.0),
    ('Quizzes', 3, 'Quiz 3', 100.0, 10.0),
    
    # Prelim Exam (1 instance, total = 25% for component, so = 25% of period)
    ('Pre / Semi exam', 1, 'Prelim Exam', 100.0, 25.0),
]

semis_instances = [
    # Assignments (5 instances, each = 2% of period)
    ('Assignments', 1, 'Assignment 6', 100.0, 2.0),
    ('Assignments', 2, 'Assignment 7', 100.0, 2.0),
    ('Assignments', 3, 'Assignment 8', 100.0, 2.0),
    ('Assignments', 4, 'Assignment 9', 100.0, 2.0),
    ('Assignments', 5, 'Assignment 10', 100.0, 2.0),
    
    # Oral Recitation (5 instances, each = 1% of period)
    ('Oral Recitation', 1, 'Recitation 6', 100.0, 1.0),
    ('Oral Recitation', 2, 'Recitation 7', 100.0, 1.0),
    ('Oral Recitation', 3, 'Recitation 8', 100.0, 1.0),
    ('Oral Recitation', 4, 'Recitation 9', 100.0, 1.0),
    ('Oral Recitation', 5, 'Recitation 10', 100.0, 1.0),
    
    # Seatwork (5 instances, each = 1% of period)
    ('Seatwork', 1, 'Seatwork 6', 50.0, 1.0),
    ('Seatwork', 2, 'Seatwork 7', 50.0, 1.0),
    ('Seatwork', 3, 'Seatwork 8', 50.0, 1.0),
    ('Seatwork', 4, 'Seatwork 9', 50.0, 1.0),
    ('Seatwork', 5, 'Seatwork 10', 50.0, 1.0),
    
    # Quizzes (3 instances, each = 10% of period)
    ('Quizzes', 1, 'Quiz 4', 100.0, 10.0),
    ('Quizzes', 2, 'Quiz 5', 100.0, 10.0),
    ('Quizzes', 3, 'Quiz 6', 100.0, 10.0),
    
    # Midterm Exam (1 instance, = 25% of period)
    ('Mid / Fin exam', 1, 'Midterm Exam', 100.0, 25.0),
]

# Sample scores from user's data
prelim_scores = {
    'Assignment 1': 85.0,
    'Assignment 2': 90.0,
    'Assignment 3': 88.0,
    'Assignment 4': 75.0,
    'Assignment 5': 82.0,
    'Recitation 1': 90.0,
    'Recitation 2': 85.0,
    'Recitation 3': 92.0,
    'Recitation 4': 88.0,
    'Recitation 5': 90.0,
    'Seatwork 1': 45.0,
    'Seatwork 2': 48.0,
    'Seatwork 3': 44.0,
    'Seatwork 4': 40.0,
    'Seatwork 5': 46.0,
    'Quiz 1': 75.0,
    'Quiz 2': 80.0,
    'Quiz 3': 65.0,
    'Prelim Exam': 65.0,
}

semis_scores = {
    'Assignment 6': 90.0,
    'Assignment 7': 85.0,
    'Assignment 8': 92.0,
    'Assignment 9': 80.0,
    'Assignment 10': 88.0,
    'Recitation 6': 85.0,
    'Recitation 7': 90.0,
    'Recitation 8': 88.0,
    'Recitation 9': 85.0,
    'Recitation 10': 92.0,
    'Seatwork 6': 48.0,
    'Seatwork 7': 45.0,
    'Seatwork 8': 50.0,
    'Seatwork 9': 42.0,
    'Seatwork 10': 47.0,
    'Quiz 4': 80.0,
    'Quiz 5': 85.0,
    'Quiz 6': 70.0,
    'Midterm Exam': 70.0,
}

print("=" * 80)
print("INSTANCE-BASED GRADING COMPUTATION - CORRECT METHOD")
print("=" * 80)
print()
print("Method: For each instance, calculate (score/max) * instance_weight")
print("        Sum all instance contributions to get period total")
print()

# Calculate Prelim-Mid
print("PRELIM-MID PERIOD")
print("-" * 80)

prelim_total = 0.0
for comp_name, inst_num, title, max_score, weight in prelim_instances:
    score = prelim_scores.get(title, 0.0)
    pct_of_max = (score / max_score) * 100
    contribution = (score / max_score) * weight
    prelim_total += contribution
    
    print(f"{title:25s}: {score:6.1f}/{max_score:3.0f} = {pct_of_max:5.1f}% x {weight:4.1f}% = {contribution:6.2f}%")

print(f"\nPrelim-Mid Total: {prelim_total:.2f}%")
print(f"Prelim-Mid (capped at 50%): {min(50, prelim_total):.2f}%")

# Calculate Semis-Final
print("\n" + "=" * 80)
print("SEMIS-FINAL PERIOD")
print("-" * 80)

semis_total = 0.0
for comp_name, inst_num, title, max_score, weight in semis_instances:
    score = semis_scores.get(title, 0.0)
    pct_of_max = (score / max_score) * 100
    contribution = (score / max_score) * weight
    semis_total += contribution
    
    print(f"{title:25s}: {score:6.1f}/{max_score:3.0f} = {pct_of_max:5.1f}% x {weight:4.1f}% = {contribution:6.2f}%")

print(f"\nSemis-Final Total: {semis_total:.2f}%")
print(f"Semis-Final (capped at 50%): {min(50, semis_total):.2f}%")

# Calculate Final Grade
final_grade = min(50, prelim_total) + min(50, semis_total)

print("\n" + "=" * 80)
print(f"FINAL GRADE: {final_grade:.2f}%")
print(f"LETTER GRADE: {get_letter_grade(final_grade)}")
print("=" * 80)

# Verify the weights sum to 100%
print("\n" + "=" * 80)
print("VERIFICATION: Weight Distribution")
print("=" * 80)

prelim_weight_sum = sum(weight for _, _, _, _, weight in prelim_instances)
semis_weight_sum = sum(weight for _, _, _, _, weight in semis_instances)

print(f"Prelim-Mid weights sum: {prelim_weight_sum:.1f}% (should be 50%)")
print(f"Semis-Final weights sum: {semis_weight_sum:.1f}% (should be 50%)")
print(f"Total: {prelim_weight_sum + semis_weight_sum:.1f}% (should be 100%)")

# Show by component
print("\nBy Component:")
print("-" * 80)

# Prelim-Mid by component
prelim_by_comp = {}
for comp_name, inst_num, title, max_score, weight in prelim_instances:
    if comp_name not in prelim_by_comp:
        prelim_by_comp[comp_name] = 0
    prelim_by_comp[comp_name] += weight

for comp_name, total_weight in prelim_by_comp.items():
    comp = next(c for c in components if c[0] == comp_name)
    print(f"  {comp_name:20s}: {total_weight:5.1f}% (component weight: {comp[2]:5.1f}%)")

# Semis-Final by component
semis_by_comp = {}
for comp_name, inst_num, title, max_score, weight in semis_instances:
    if comp_name not in semis_by_comp:
        semis_by_comp[comp_name] = 0
    semis_by_comp[comp_name] += weight

for comp_name, total_weight in semis_by_comp.items():
    comp = next(c for c in components if c[0] == comp_name)
    print(f"  {comp_name:20s}: {total_weight:5.1f}% (component weight: {comp[3]:5.1f}%)")
