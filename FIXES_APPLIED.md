# Fixes Applied to HCDC Class Record App

## Summary
Fixed critical issues in the HCDC Class Record web application based on user feedback.

## Issues Fixed

### 1. **Import Functionality - Merged Cells Support** ⭐ CRITICAL
**Problem**: Excel files with merged cells (like HCDC Class Record format) were not being imported correctly. All columns were showing as "Unnamed: X" and wrong data was being imported.

**Solution**: Modified `import_grades()` function in `app_instance.py` to:
- Read Excel files with `header=None` to prevent pandas from auto-detecting headers
- Search for the row containing "LAST NAME", "FIRST NAME", "ID NUMBER" to identify the actual header row
- Use that row as the column headers
- Skip metadata rows (Items:, Date:, Type Names, etc.)
- Import only actual student data

**Files Changed**: `app_instance.py` (lines ~2213-2270)

---

### 2. **Dark Mode Notification Colors** ⭐ CRITICAL  
**Problem**: In dark mode, notification text was white on white background, making it unreadable.

**Solution**: Updated CSS in `static/css/style.css` to:
- Set explicit text colors for all notice types in dark mode
- Use `!important` to override any conflicting styles
- Ensure proper contrast for success, error, warning, and info notices
- Fixed the `.notice strong` selector for dark mode

**Files Changed**: `static/css/style.css` (lines ~314-340)

---

### 3. **Duplicate Code Removal**
**Problem**: There was duplicate code for detecting the start of student data in the import function, causing potential confusion and bugs.

**Solution**: Removed the duplicate start_row detection block (lines 2363-2398 in the original file).

**Files Changed**: `app_instance.py`

---

## What Still Needs to Be Done

### By the User:

1. **Delete old database file**
   ```bash
   rm class_record_instance.db
   ```
   This will allow the app to create a fresh database with the correct schema.

2. **Pull latest changes**
   ```bash
   cd class-record-app-CET
   git pull origin main
   ```

3. **Run the app**
   ```bash
   python3 run_app.py
   ```

4. **Import your Excel file**
   - Go to "Import Grades" page
   - Upload your `ClassRecord1stSem2627-OLD-BACKUP.xlsx` file
   - The app should now correctly identify course sheets and import student data

### Known Limitations:

1. **Grading Structure**: The app currently supports instance-based grading. You need to:
   - Create a course
   - Go to "Manage Grading Criteria"
   - Add components (Assignments, Quizzes, etc.) with correct weights
   - Add instances for each component
   - Then enter grades

2. **Dummy Data**: The app no longer inserts dummy data automatically. The database is created empty.

3. **Grade Entry**: To enter grades:
   - Go to course detail page
   - Click "Enter Grades"
   - Select a student
   - Enter scores for each assessment instance
   - Click "Save Grades"

---

## Testing Instructions

1. **Test Dark Mode**
   - Click the moon/sun icon in the navbar
   - Verify notifications are readable in both light and dark mode
   - Verify all text is visible

2. **Test Import**
   - Upload your Excel file
   - Verify that course sheets are correctly identified
   - Verify that student data (LAST NAME, FIRST NAME, ID NUMBER) is imported correctly
   - Verify that metadata rows (Time:, Days:, Room:) are skipped

3. **Test Grade Entry**
   - Create a course
   - Add students
   - Go to "Manage Grading Criteria"
   - Add components with correct weights
   - Add instances
   - Go to "Enter Grades"
   - Enter scores and save

---

## Technical Details

### Import Function Changes
```python
# Before (didn't work with merged cells):
df = pd.read_excel(file, sheet_name=sheet_name)

# After (handles merged cells):
df_raw = pd.read_excel(file, sheet_name=sheet_name, header=None)
# Find header row
header_row = None
for i in range(len(df_raw)):
    row = df_raw.iloc[i]
    row_str = ' '.join(str(c) for c in row if pd.notna(c)).lower()
    if 'last name' in row_str and 'first name' in row_str and 'id number' in row_str:
        header_row = i
        break

# Set header and clean up
df = df_raw.iloc[header_row:].copy()
df.columns = df.iloc[0]
df = df.drop(header_row).reset_index(drop=True)
df = df.dropna(how='all')

# Skip metadata rows
start_row = 0
for i in range(len(df)):
    row = df.iloc[i]
    row_str = ' '.join(str(c) for c in row if pd.notna(c)).lower()
    if any(p in row_str for p in ['items:', 'date:', 'type names', 'tinted cells',
                                   'student information', 'category weights', 'grade distribution']):
        start_row = i + 1
        continue
    # Check for student data
    has_data = False
    for col in ['LAST NAME', 'FIRST NAME', 'ID NUMBER']:
        if col in df.columns:
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                has_data = True
                break
    if has_data:
        start_row = i
        break

if start_row > 0:
    df = df.iloc[start_row:].copy().reset_index(drop=True)
```

### CSS Changes
```css
/* Dark mode notice styles - ensure visibility */
html.dark-mode .notice {
    color: var(--ink);
}

html.dark-mode .notice strong {
    color: var(--ink) !important;
}

html.dark-mode .notice.success {
    color: #ffffff !important;
    background: var(--ok-bg) !important;
    border-color: var(--ok-border) !important;
}

html.dark-mode .notice.error {
    color: #ffffff !important;
    background: var(--bad-bg) !important;
    border-color: var(--bad-border) !important;
}

html.dark-mode .notice.info {
    color: #ffffff !important;
    background: var(--hcdc-primary-dark) !important;
    border-color: var(--hcdc-primary) !important;
}

html.dark-mode .notice.warning {
    color: #ffffff !important;
    background: var(--warn-bg) !important;
    border-color: var(--warn-border) !important;
}
```

---

## Version Information

- **Last Commit**: dffaaf7
- **Date**: 2024
- **Files Modified**: 2
  - `app_instance.py`: +83 lines, -40 lines
  - `static/css/style.css`: Minor changes to notification styles

---

## Next Steps

If you still experience issues after applying these fixes:

1. **Clear your browser cache** - Old CSS/JS might be cached
2. **Delete the database file** - `rm class_record_instance.db`
3. **Restart the Flask server**
4. **Try a different browser** - Some browsers cache aggressively

If issues persist, please provide:
- Screenshot of the error
- Exact steps to reproduce
- Browser console errors (F12 -> Console)
