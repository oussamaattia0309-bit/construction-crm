from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import pandas as pd
import io
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///construction_crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    type = db.Column(db.String(50))  # 'client' or 'provider'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    service_type = db.Column(db.String(100))
    notes = db.Column(db.Text)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50))  # 'planned', 'in_progress', 'completed'
    description = db.Column(db.Text)
    budget_total = db.Column(db.Float, default=0.0)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    item_name = db.Column(db.String(100), nullable=False)
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    category = db.Column(db.String(50))  # 'materials', 'labor', 'equipment', 'other'
    notes = db.Column(db.Text)
    
    project = db.relationship('Project', backref=db.backref('budget_items', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect')
        elif new_password != confirm_password:
            flash('New passwords do not match')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!')
            return redirect(url_for('index'))
    
    return render_template('change_password.html')

# Contact routes
@app.route('/contacts')
@login_required
def contacts():
    contacts_list = Contact.query.all()
    return render_template('contacts.html', contacts=contacts_list)

@app.route('/contacts/add', methods=['POST'])
@login_required
def add_contact():
    contact = Contact(
        name=request.form.get('name'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        company=request.form.get('company'),
        type=request.form.get('type'),
        notes=request.form.get('notes')
    )
    db.session.add(contact)
    db.session.commit()
    flash('Contact added successfully')
    return redirect(url_for('contacts'))

@app.route('/contacts/delete/<int:id>')
@login_required
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted')
    return redirect(url_for('contacts'))

# Provider routes
@app.route('/providers')
@login_required
def providers():
    providers_list = Provider.query.all()
    return render_template('providers.html', providers=providers_list)

@app.route('/providers/add', methods=['POST'])
@login_required
def add_provider():
    provider = Provider(
        name=request.form.get('name'),
        contact_person=request.form.get('contact_person'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        address=request.form.get('address'),
        service_type=request.form.get('service_type'),
        notes=request.form.get('notes')
    )
    db.session.add(provider)
    db.session.commit()
    flash('Provider added successfully')
    return redirect(url_for('providers'))

@app.route('/providers/delete/<int:id>')
@login_required
def delete_provider(id):
    provider = Provider.query.get_or_404(id)
    db.session.delete(provider)
    db.session.commit()
    flash('Provider deleted')
    return redirect(url_for('providers'))

# Project routes
@app.route('/projects')
@login_required
def projects():
    projects_list = Project.query.all()
    return render_template('projects.html', projects=projects_list)

@app.route('/projects/add', methods=['POST'])
@login_required
def add_project():
    project = Project(
        name=request.form.get('name'),
        client_name=request.form.get('client_name'),
        address=request.form.get('address'),
        start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d') if request.form.get('start_date') else None,
        end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None,
        status=request.form.get('status'),
        description=request.form.get('description')
    )
    db.session.add(project)
    db.session.commit()
    flash('Project added successfully')
    return redirect(url_for('projects'))

@app.route('/projects/<int:id>')
@login_required
def project_detail(id):
    project = Project.query.get_or_404(id)
    return render_template('project_detail.html', project=project)

# Budget routes
@app.route('/budgets')
@login_required
def budgets():
    budgets_list = Budget.query.all()
    projects_list = Project.query.all()
    return render_template('budgets.html', budgets=budgets_list, projects=projects_list)

@app.route('/budgets/add', methods=['POST'])
@login_required
def add_budget():
    budget = Budget(
        project_id=request.form.get('project_id'),
        item_name=request.form.get('item_name'),
        estimated_cost=float(request.form.get('estimated_cost')) if request.form.get('estimated_cost') else None,
        actual_cost=float(request.form.get('actual_cost')) if request.form.get('actual_cost') else None,
        category=request.form.get('category'),
        notes=request.form.get('notes')
    )
    db.session.add(budget)
    db.session.commit()
    flash('Budget item added successfully')
    return redirect(url_for('budgets'))

@app.route('/budgets/delete/<int:id>')
@login_required
def delete_budget(id):
    budget = Budget.query.get_or_404(id)
    db.session.delete(budget)
    db.session.commit()
    flash('Budget item deleted')
    return redirect(url_for('budgets'))

# API routes
@app.route('/api/dashboard')
@login_required
def dashboard_data():
    total_contacts = Contact.query.count()
    total_providers = Provider.query.count()
    active_projects = Project.query.filter_by(status='in_progress').count()
    total_budget = db.session.query(db.func.sum(Budget.estimated_cost)).scalar() or 0
    
    return jsonify({
        'contacts': total_contacts,
        'providers': total_providers,
        'active_projects': active_projects,
        'total_budget': total_budget
    })

@app.route('/api/projects/recent')
@login_required
def recent_projects():
    projects = Project.query.order_by(Project.id.desc()).limit(5).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'status': p.status
    } for p in projects])

# ==================== CONTACT UPLOAD ====================
@app.route('/contacts/upload', methods=['POST'])
@login_required
def upload_contacts():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('contacts'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('contacts'))
    
    # Read the file
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            flash('Please upload CSV or Excel file')
            return redirect(url_for('contacts'))
        
        # Track success/failure
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Map Excel columns to database fields
                contact = Contact(
                    name=str(row.get('Name', '')),
                    phone=str(row.get('Phone', '')),
                    email=str(row.get('Email', '')),
                    company=str(row.get('Company', '')),
                    type='client',  # Default type
                    notes=f"Speciality: {row.get('Speciality', '')} | Address: {row.get('Address', '')} | Comments: {row.get('Comments', '')}"
                )

                # Basic validation
                if not contact.name:
                    errors.append(f"Row {index + 2}: Name is required")
                    error_count += 1
                    continue

                db.session.add(contact)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                error_count += 1
        
        # Commit all successful entries
        db.session.commit()
        
        # Flash summary
        if success_count > 0:
            flash(f'✅ Successfully imported {success_count} contacts')
        if error_count > 0:
            flash(f'⚠️ Failed to import {error_count} contacts. Check your file format.')
            for error in errors[:5]:  # Show first 5 errors
                flash(f'Error: {error}')
        
    except Exception as e:
        flash(f'Error reading file: {str(e)}')
    
    return redirect(url_for('contacts'))

# ==================== PROVIDER UPLOAD ====================
@app.route('/providers/upload', methods=['POST'])
@login_required
def upload_providers():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('providers'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('providers'))
    
    # Read the file
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            flash('Please upload CSV or Excel file')
            return redirect(url_for('providers'))
        
        # Track success/failure
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Map Excel columns to database fields
                provider = Provider(
                    name=str(row.get('Company Name', '')),
                    contact_person=str(row.get('Contact Person', '')),
                    phone=str(row.get('Phone', '')),
                    email=str(row.get('Email', '')),
                    address=str(row.get('Address', '')),
                    service_type=str(row.get('Speciality', '')),  # Map Speciality to service_type
                    notes=str(row.get('Comments', ''))
                )
                
                # Basic validation
                if not provider.name:
                    errors.append(f"Row {index + 2}: Company Name is required")
                    error_count += 1
                    continue
                
                db.session.add(provider)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                error_count += 1
        
        # Commit all successful entries
        db.session.commit()
        
        # Flash summary
        if success_count > 0:
            flash(f'✅ Successfully imported {success_count} providers')
        if error_count > 0:
            flash(f'⚠️ Failed to import {error_count} providers. Check your file format.')
            for error in errors[:5]:  # Show first 5 errors
                flash(f'Error: {error}')
        
    except Exception as e:
        flash(f'Error reading file: {str(e)}')
    
    return redirect(url_for('providers'))

# ==================== DOWNLOAD TEMPLATE ====================
@app.route('/contacts/template')
@login_required
def download_contacts_template():
    # Create a template DataFrame with your preferred columns
    template = pd.DataFrame({
        'Name': ['Ahmed Ben Ali', 'Sarra Mansour'],
        'Phone': ['+216 22 123 456', '+216 55 789 012'],
        'Email': ['ahmed@email.com', 'sarra@email.com'],
        'Company': ['ABC Construction', 'XYZ Materials'],
        'Speciality': ['Project Management', 'Electrical Engineering'],
        'Comments': ['Good client, multiple projects', 'Reliable supplier'],
        'Address': ['Tunis, Centre Ville', 'Sousse, Rue de la Liberté']
    })
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        template.to_excel(writer, index=False, sheet_name='Contacts')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='contacts_template.xlsx'
    )

@app.route('/providers/template')
@login_required
def download_providers_template():
    # Create a template DataFrame with your preferred columns
    template = pd.DataFrame({
        'Company Name': ['Matériaux Tunisie', 'Électro Plus'],
        'Contact Person': ['Karim Ben Salem', 'Leila Mansour'],
        'Phone': ['+216 71 123 456', '+216 72 789 012'],
        'Email': ['karim@materiaux.tn', 'leila@electroplus.tn'],
        'Speciality': ['Construction Materials', 'Electrical Supplies'],
        'Comments': ['Good prices, fast delivery', 'Certified products'],
        'Address': ['Tunis, Zone Industrielle', 'Sousse, Route de la Plage']
    })
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        template.to_excel(writer, index=False, sheet_name='Providers')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='providers_template.xlsx'
    )

# ==================== DOWNLOAD ALL CONTACTS ====================
@app.route('/contacts/download-all')
@login_required
def download_all_contacts():
    """Download all contacts as Excel file"""
    try:
        # Get all contacts
        contacts = Contact.query.all()
        
        # Create a list of dictionaries for pandas
        data = []
        for contact in contacts:
            # Parse notes to extract speciality, address, comments if needed
            notes = contact.notes or ""
            
            data.append({
                'Name': contact.name,
                'Email': contact.email or '',
                'Phone': contact.phone or '',
                'Company': contact.company or '',
                'Type': contact.type or '',
                'Notes': notes
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='All Contacts')
        
        output.seek(0)
        
        # Generate filename with current date
        from datetime import datetime
        filename = f"all_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        flash(f'Error downloading contacts: {str(e)}')
        return redirect(url_for('contacts'))
    
@app.route('/contacts/download-selected', methods=['POST'])
@login_required
def download_selected_contacts():
    """Download selected contacts as Excel file"""
    try:
        selected_ids = json.loads(request.form.get('selected_ids', '[]'))
        
        if not selected_ids:
            flash('No contacts selected')
            return redirect(url_for('contacts'))
        
        contacts = Contact.query.filter(Contact.id.in_(selected_ids)).all()
        
        data = []
        for contact in contacts:
            data.append({
                'Name': contact.name,
                'Email': contact.email or '',
                'Phone': contact.phone or '',
                'Company': contact.company or '',
                'Type': contact.type or '',
                'Notes': contact.notes or ''
            })
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Selected Contacts')
        
        output.seek(0)
        
        from datetime import datetime
        filename = f"selected_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        flash(f'Error downloading contacts: {str(e)}')
        return redirect(url_for('contacts'))

@app.route('/contacts/<int:contact_id>/details')
@login_required
def get_contact_details(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return jsonify({
        'id': contact.id,
        'name': contact.name,
        'email': contact.email,
        'phone': contact.phone,
        'company': contact.company,
        'type': contact.type,
        'notes': contact.notes
    })

@app.route('/contacts/<int:contact_id>/edit', methods=['POST'])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    contact.name = request.form.get('name')
    contact.email = request.form.get('email')
    contact.phone = request.form.get('phone')
    contact.company = request.form.get('company')
    contact.type = request.form.get('type')
    contact.notes = request.form.get('notes')
    
    db.session.commit()
    flash('Contact updated successfully')
    return redirect(url_for('contacts'))

@app.route('/contacts/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_contacts():
    data = request.get_json()
    ids = data.get('ids', [])
    
    if ids:
        Contact.query.filter(Contact.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True, 'count': len(ids)})
    
    return jsonify({'success': False}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('changeme')
            db.session.add(admin)
            db.session.commit()
            print('Default user created: admin / changeme')
    
    app.run(debug=True, host='0.0.0.0', port=5000)