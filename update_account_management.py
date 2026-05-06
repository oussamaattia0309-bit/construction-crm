import re

# Read the original file with utf-8 encoding
with open('c:\\Users\\USER\\Desktop\\stuff\\web\\CRM CAE\\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the pattern to match the account_management function
pattern = r'def account_management\(\):[\s\S]*?return render_template\(\'account_management\.html\',[\s\S]*?active_sessions=active_sessions\)'

# Define the replacement with the updated function
replacement = """def account_management():
    # Mock current session data (replace with actual session tracking)
    current_session = {
        'browser': 'Chrome',
        'os': 'Windows'
    }

    # Mock active sessions (replace with actual session tracking)
    active_sessions = []

    # Get all users from the database
    all_users = User.query.order_by(User.created_at.desc()).all()

    return render_template('account_management.html',
                          current_session=current_session,
                          active_sessions=active_sessions,
                          all_users=all_users)"""

# Replace the content
new_content = re.sub(pattern, replacement, content)

# Write the updated content back to the file with utf-8 encoding
with open('c:\\Users\\USER\\Desktop\\stuff\\web\\CRM CAE\\app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
