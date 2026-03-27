# PythonAnywhere Deployment Guide for Gantt Chart Fix

## Problem Summary
- Gantt works locally but not on PythonAnywhere
- Tasks not loading from database
- 404 errors on POST requests
- Empty array returned from GET requests

## Solution Overview
1. Push latest code to GitHub
2. Pull and update PythonAnywhere
3. Verify API endpoints
4. Clear caches

---

## STEP 1: Push Local Code to GitHub

### Open PowerShell or Command Prompt on your local machine

### Navigate to your project directory
```powershell
cd "C:\Users\user\Desktop\Travail\WEB\CRM CAE"
```

### Check current git status
```powershell
git status
```

### Add all changes
```powershell
git add .
```

### Commit changes with descriptive message
```powershell
git commit -m "Fix Gantt chart: date timezone issue, add delete button, improve modal styling"
```

### Push to GitHub
```powershell
git push origin main
```

### Verify push was successful
- Visit: https://github.com/oussamaattia0309-bit/construction-crm
- Check that the latest commit appears at the top

---

## STEP 2: Update PythonAnywhere

### 1. Go to PythonAnywhere Console
- Visit: https://www.pythonanywhere.com/user/Oussamaattia1994/consoles/45879458/
- This opens your Bash console

### 2. Navigate to your site directory
```bash
cd ~/mysite
```

### 3. Check current git status
```bash
git status
```

### 4. Pull latest changes from GitHub
```bash
git pull origin main
```

### 5. Verify the pull was successful
```bash
git log -1
```
You should see your latest commit message

### 6. Activate virtual environment
```bash
source venv/bin/activate
```

### 7. Install/update dependencies
```bash
pip install -r requirements.txt
```

### 8. Update database schema if needed
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 9. Reload your web application
```bash
touch /var/www/oussamaattia1994_pythonanywhere_com_wsgi.py
```

### 10. Verify the reload
- Check your web app logs at: https://www.pythonanywhere.com/user/Oussamaattia1994/webapps/
- Look for any errors

---

## STEP 3: Verify API Endpoints

### Check API endpoint in JavaScript
The API endpoint is defined in `templates/project_detail.html`:

```javascript
let currentProjectId = {{ project.id }};
```

This dynamically sets the project ID based on the current project being viewed.

### Verify the API endpoint is correct
1. On PythonAnywhere, open your project page
2. Open browser Developer Tools (F12)
3. Go to Network tab
4. Refresh the page
5. Look for requests to `/api/project/{id}/tasks`
6. Verify the project ID is correct

### Test API endpoint directly
Open this in your browser (replace {project_id} with actual project ID):
```
https://oussamaattia1994.pythonanywhere.com/api/project/1/tasks
```

You should see JSON data with your tasks, not an empty array.

---

## STEP 4: Clear JavaScript Cache

### Method 1: Browser Cache Clear
1. Open Developer Tools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Method 2: Add Cache Busting to Static Files
If you have static JavaScript files, add version numbers:

In `project_detail.html`, update script tags:
```html
<script src="/static/js/gantt.js?v={{ version }}"></script>
```

### Method 3: PythonAnywhere Web App Reload
1. Go to: https://www.pythonanywhere.com/user/Oussamaattia1994/webapps/
2. Find your web app
3. Click "Reload" button

### Method 4: Clear PythonAnywhere Static Files Cache
In PythonAnywhere Bash console:
```bash
cd ~/mysite
find static -type f -name "*.js" -o -name "*.css" | xargs touch
touch /var/www/oussamaattia1994_pythonanywhere_com_wsgi.py
```

---

## STEP 5: Verify Database Data

### Check if tasks exist in database
In PythonAnywhere Bash console:
```bash
cd ~/mysite
source venv/bin/activate
python
```

Then run:
```python
from app import app, db, ProjectTask
with app.app_context():
    tasks = ProjectTask.query.all()
    print(f"Total tasks: {len(tasks)}")
    for task in tasks:
        print(f"ID: {task.id}, Name: {task.name}, Project: {task.project_id}")
```

### If no tasks exist, you need to sync data
Use the data sync commands from your `update cmnds.txt` file.

---

## STEP 6: Verify Database Path

### Check local database path
In `app.py`, line 16:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///construction_crm.db'
```

### On PythonAnywhere, the database should be in the instance folder
Check if the database exists:
```bash
cd ~/mysite
ls -la instance/construction_crm.db
```

If the database doesn't exist or is in a different location, update the path in `app.py` on PythonAnywhere.

---

## TROUBLESHOOTING

### Issue 1: 404 Error on POST /api/project/1/tasks
**Possible causes:**
- Route not defined in app.py
- Wrong project ID
- CSRF token missing

**Solution:**
1. Verify route exists in app.py
2. Check project ID is correct
3. Add CSRF token if needed

### Issue 2: Empty array from GET /api/project/1/tasks
**Possible causes:**
- No tasks in database
- Wrong project ID
- Database connection issue

**Solution:**
1. Check database has tasks (see STEP 5)
2. Verify project ID
3. Check database connection

### Issue 3: Tasks showing "Nouvelle tâche" instead of real data
**Possible causes:**
- JavaScript using default data
- API not returning correct data
- Cache issue

**Solution:**
1. Clear browser cache (STEP 4)
2. Verify API returns correct data (STEP 3)
3. Check JavaScript is loading latest version

---

## QUICK REFERENCE COMMANDS

### Local (PowerShell)
```powershell
cd "C:\Users\user\Desktop\Travail\WEB\CRM CAE"
git add .
git commit -m "Update"
git push origin main
```

### PythonAnywhere (Bash)
```bash
cd ~/mysite
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python -c "from app import app, db; app.app_context().push(); db.create_all()"
touch /var/www/oussamaattia1994_pythonanywhere_com_wsgi.py
```

---

## VERIFICATION CHECKLIST

After completing all steps, verify:

- [ ] Latest code is pushed to GitHub
- [ ] PythonAnywhere has pulled latest code
- [ ] Virtual environment is activated
- [ ] Dependencies are installed
- [ ] Database schema is up to date
- [ ] Web app is reloaded
- [ ] Browser cache is cleared
- [ ] API endpoint returns correct data
- [ ] Tasks display correctly in Gantt chart
- [ ] Adding tasks works
- [ ] Dragging tasks works
- [ ] Deleting tasks works

---

## CONTACT

If you still have issues after following this guide:
1. Check PythonAnywhere web app logs for errors
2. Verify all steps were completed
3. Try clearing browser cache again
4. Check that the correct project ID is being used
