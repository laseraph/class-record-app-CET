"""
Verify Instance-Based Grading Computations - CORRECT VERSION

The CORRECT approach:
1. Each component has a weight (e.g., Assignments = 10% of period)
2. Each instance has a weight that is a FRACTION of its component (e.g., 0.2 for 1 of 5)
3. Instance contribution = (score/max) * instance_weight * component_weight
4. Sum all instance contributions to get period total

This ensures:
- Sum of all instance contributions for a component = (avg_score/max) * component_weight
- Sum of all component contributions = period total
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
    ('Assignments', 'class_standing', 10.0, 10.0),   # 10% of each period
    ('Oral Recitation', 'class_standing', 5.0, 5.0),  # 5% of each period
    ('Seatwork', 'class_standing', 5.0, 5.0),       # 5% of each period
    ('Quizzes', 'class_standing', 30.0, 30.0),      # 30% of each period
    ('Pre / Semi exam', 'major_exam', 25.0, 0.0),   # 25% of Prelim-Mid only
    ('Mid / Fin exam', 'major_exam', 0.0, 25.0),    # 25% of Semis-Final only
]

# Verify component weights sum to 50% for each period
prelim_total = sum(c[2] for c in components)
semis_total = sum(c[3] for c in components)
print("Component Weights Verification:")
print(f"  Prelim-Mid: {prelim_total}% (should be 50%)")
print(f"  Semis-Final: {semis_total}% (should be 50%)")
print()

# Define instances for each component
# Format: (component_name, instance_number, title, max_score, weight_fraction)
# weight_fraction = what fraction of the component this instance represents
# For 5 assignments: each has weight_fraction = 0.2 (1/5)
prelim_instances = [
    # Assignments (5 instances, each = 0.2 of the 10% component)
    ('Assignments', 1, 'Assignment 1', 100.0, 0.2),
    ('Assignments', 2, 'Assignment 2', 100.0, 0.2),
    ('Assignments', 3, 'Assignment 3', 100.0, 0.2),
    ('Assignments', 4, 'Assignment 4', 100.0, 0.2),
    ('Assignments', 5, 'Assignment 5', 100.0, 0.2),
    
    # Oral Recitation (5 instances, each = 0.2 of the 5% component)
    ('Oral Recitation', 1, 'Recitation 1', 100.0, 0.2),
    ('Oral Recitation', 2, 'Recitation 2', 100.0, 0.2),
    ('Oral Recitation', 3, 'Recitation 3', 100.0, 0.2),
    ('Oral Recitation', 4, 'Recitation 4', 100.0, 0.2),
    ('Oral Recitation', 5, 'Recitation 5', 100.0, 0.2),
    
    # Seatwork (5 instances, each = 0.2 of the 5% component)
    ('Seatwork', 1, 'Seatwork 1', 50.0, 0.2),
    ('Seatwork', 2, 'Seatwork 2', 50.0, 0.2),
    ('Seatwork', 3, 'Seatwork 3', 50.0, 0.2),
    ('Seatwork', 4, 'Seatwork 4', 50.0, 0.2),
    ('Seatwork', 5, 'Seatwork 5', 50.0, 0.2),
    
    # Quizzes (3 instances, each = 1/3 of the 30% component)
    ('Quizzes', 1, 'Quiz 1', 100.0, 1/3),
    ('Quizzes', 2, 'Quiz 2', 100.0, 1/3),
    ('Quizzes', 3, 'Quiz 3', 100.0, 1/3),
    
    # Prelim Exam (1 instance, = 1.0 of the 25% component)
    ('Pre / Semi exam', 1, 'Prelim Exam', 100.0, 1.0),
]

semis_instances = [
    # Assignments (5 instances)
    ('Assignments', 1, 'Assignment 6', 100.0, 0.2),
    ('Assignments', 2, 'Assignment 7', 100.0, 0.2),
    ('Assignments', 3, 'Assignment 8', 100.0, 0.2),
    ('Assignments', 4, 'Assignment 9', 100.0, 0.2),
    ('Assignments', 5, 'Assignment 10', 100.0, 0.2),
    
    # Oral Recitation (5 instances)
    ('Oral Recitation', 1, 'Recitation 6', 100.0, 0.2),
    ('Oral Recitation', 2, 'Recitation 7', 100.0, 0.2),
    ('Oral Recitation', 3, 'Recitation 8', 100.0, 0.2),
    ('Oral Recitation', 4, 'Recitation 9', 100.0, 0.2),
    ('Oral Recitation', 5, 'Recitation 10', 100.0, 0.2),
    
    # Seatwork (5 instances)
    ('Seatwork', 1, 'Seatwork 6', 50.0, 0.2),
    ('Seatwork', 2, 'Seatwork 7', 50.0, 0.2),
    ('Seatwork', 3, 'Seatwork 8', 50.0, 0.2),
    ('Seatwork', 4, 'Seatwork 9', 50.0, 0.2),
    ('Seatwork', 5, 'Seatwork 10', 50.0, 0.2),
    
    # Quizzes (3 instances)
    ('Quizzes', 1, 'Quiz 4', 100.0, 1/3),
    ('Quizzes', 2, 'Quiz 5', 100.0, 1/3),
    ('Quizzes', 3, 'Quiz 6', 100.0, 1/3),
    
    # Midterm Exam
    ('Mid / Fin exam', 1, 'Midterm Exam', 100.0, 1.0),
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

# Helper to get component weight
def get_component_weight(component_name, bigrade):
    for name, category, prelim, semis in components:
        if name == component_name:
            return prelim if bigrade == 'prelim' else semis
    return 0

print("=" * 80)
print("INSTANCE-BASED GRADING - CORRECT COMPUTATION METHOD")
print("=" * 80)
print()
print("Formula: (score/max) * instance_weight * component_weight")
print("         Sum all instances to get period total")
print()

# Calculate Prelim-Mid
print("PRELIM-MID PERIOD")
print("-" * 80)

prelim_total = 0.0
for comp_name, inst_num, title, max_score, weight_fraction in prelim_instances:
    score = prelim_scores.get(title, 0.0)
    comp_weight = get_component_weight(comp_name, 'prelim')
    pct_of_max = (score / max_score) * 100
    contribution = (score / max_score) * weight_fraction * comp_weight
    prelim_total += contribution
    
    print(f"{title:25s}: {score:6.1f}/{max_score:3.0f} = {pct_of_max:5.1f}% x {weight_fraction:4.2f} x {comp_weight:5.1f}% = {contribution:6.2f}%")

print(f"\nPrelim-Mid Total: {prelim_total:.2f}%")
print(f"Prelim-Mid (capped at 50%): {min(50, prelim_total):.2f}%")

# Calculate Semis-Final
print("\n" + "=" * 80)
print("SEMIS-FINAL PERIOD")
print("-" * 80)

semis_total = 0.0
for comp_name, inst_num, title, max_score, weight_fraction in semis_instances:
    score = semis_scores.get(title, 0.0)
    comp_weight = get_component_weight(comp_name, 'semis')
    pct_of_max = (score / max_score) * 100
    contribution = (score / max_score) * weight_fraction * comp_weight
    semis_total += contribution
    
    print(f"{title:25s}: {score:6.1f}/{max_score:3.0f} = {pct_of_max:5.1f}% x {weight_fraction:4.2f} x {comp_weight:5.1f}% = {contribution:6.2f}%")

print(f"\nSemis-Final Total: {semis_total:.2f}%")
print(f"Semis-Final (capped at 50%): {min(50, semis_total):.2f}%")

# Calculate Final Grade
final_grade = min(50, prelim_total) + min(50, semis_total)

print("\n" + "=" * 80)
print(f"FINAL GRADE: {final_grade:.2f}%")
print(f"LETTER GRADE: {get_letter_grade(final_grade)}")
print("=" * 80)

# Show grouped by component
print("\n" + "=" * 80)
print("GROUPED BY COMPONENT (Prelim-Mid)")
print("=" * 80)

prelim_by_comp = {}
for comp_name, inst_num, title, max_score, weight_fraction in prelim_instances:
    if comp_name not in prelim_by_comp:
        prelim_by_comp[comp_name] = []
    prelim_by_comp[comp_name].append((title, max_score, weight_fraction))

for comp_name, instances in prelim_by_comp.items():
    comp_weight = get_component_weight(comp_name, 'prelim')
    print(f"\n{comp_name} ({comp_weight}% of Prelim-Mid):")
    comp_total = 0.0
    for title, max_score, weight_fraction in instances:
        score = prelim_scores.get(title, 0.0)
        pct = (score / max_score) * 100
        contribution = (score / max_score) * weight_fraction * comp_weight
        comp_total += contribution
        print(f"  {title:20s}: {score:5.1f}/{max_score:3.0f} = {pct:5.1f}% x {weight_fraction:4.2f} -> {contribution:5.2f}%")
    print(f"  Component Total: {comp_total:.2f}%")

print("\n" + "=" * 80)
print("GROUPED BY COMPONENT (Semis-Final)")
print("=" * 80)

semis_by_comp = {}
for comp_name, inst_num, title, max_score, weight_fraction in semis_instances:
    if comp_name not in semis_by_comp:
        semis_by_comp[comp_name] = []
    semis_by_comp[comp_name].append((title, max_score, weight_fraction))

for comp_name, instances in semis_by_comp.items():
    comp_weight = get_component_weight(comp_name, 'semis')
    print(f"\n{comp_name} ({comp_weight}% of Semis-Final):")
    comp_total = 0.0
    for title, max_score, weight_fraction in instances:
        score = semis_scores.get(title, 0.0)
        pct = (score / max_score) * 100
        contribution = (score / max_score) * weight_fraction * comp_weight
        comp_total += contribution
        print(f"  {title:20s}: {score:5.1f}/{max_score:3.0f} = {pct:5.1f}% x {weight_fraction:4.2f} -> {contribution:5.2f}%")
    print(f"  Component Total: {comp_total:.2f}%")
