from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import pandas as pd
import io
import csv
import json
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
    type = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def relation(self):
        """Parse relation from notes (relation:good|average|bad)"""
        import re
        if not self.notes:
            return None
        m = re.search(r'relation:(good|average|bad)', self.notes)
        return m.group(1) if m else None

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
    status = db.Column(db.String(50))
    description = db.Column(db.Text)
    budget_total = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    client_receipts = db.Column(db.Float, default=0.0)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    item_name = db.Column(db.String(100), nullable=False)
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)
    
    project = db.relationship('Project', backref=db.backref('budget_items', lazy=True))

class ProjectExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    date = db.Column(db.Date)
    nature = db.Column(db.String(200))
    amount = db.Column(db.Float)
    comment = db.Column(db.Text)
    category = db.Column(db.String(50))
    
    project = db.relationship('Project', backref=db.backref('expenses', lazy=True))

class ProjectReceipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    date = db.Column(db.Date)
    amount = db.Column(db.Float)
    comment = db.Column(db.Text)
    
    project = db.relationship('Project', backref=db.backref('receipts', lazy=True))

class ProjectFinancialParams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), unique=True)
    sale_price = db.Column(db.Float, default=0)
    estimated_budget = db.Column(db.Float, default=0)
    devis_ref = db.Column(db.Float, default=0)
    
    project = db.relationship('Project', backref=db.backref('financial_params', uselist=False))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== AUTH ROUTES ====================
@app.route('/project/<int:project_id>/financial/update-summary', methods=['POST'])
@login_required
def update_financial_summary(project_id):
    """Update financial summary - syncs with Project (selling_price, client_receipts) and ProjectFinancialParams"""
    try:
        project = Project.query.get_or_404(project_id)
        financial = ProjectFinancialParams.query.filter_by(project_id=project_id).first()
        if not financial:
            financial = ProjectFinancialParams(project_id=project_id)
            db.session.add(financial)
        
        data = request.get_json()
        
        # Update Project (same fields as project detail page)
        if 'sale_price' in data:
            project.selling_price = float(data.get('sale_price', 0))
        if 'client_received' in data:
            project.client_receipts = float(data.get('client_received', 0))
        
        # Update ProjectFinancialParams
        financial.sale_price = float(data.get('sale_price', project.selling_price or 0))
        financial.estimated_budget = float(data.get('estimated_budget', financial.estimated_budget or 0))
        financial.devis_ref = float(data.get('devis_ref', financial.devis_ref or 0))
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
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

# ==================== CONTACT ROUTES ====================
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

@app.route('/contacts/<int:contact_id>/update-type', methods=['POST'])
@login_required
def update_contact_type(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    data = request.get_json()
    new_type = data.get('type')
    if new_type:
        contact.type = new_type
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/contacts/<int:contact_id>/update-relation', methods=['POST'])
@login_required
def update_contact_relation(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    data = request.get_json()
    relation = data.get('relation', '')
    
    notes = contact.notes or ''
    import re
    notes = re.sub(r'relation:(good|average|bad)\s*', '', notes)
    
    if relation:
        notes = notes.strip() + f' relation:{relation}'
    
    contact.notes = notes.strip()
    db.session.commit()
    return jsonify({'success': True})

# ==================== PROVIDER ROUTES ====================
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

# ==================== PROJECT ROUTES ====================
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

@app.route('/projects/<int:id>', methods=['POST'])
@login_required
def update_project(id):
    project = Project.query.get_or_404(id)
    
    # Update basic fields
    project.name = request.form.get('name')
    project.client_name = request.form.get('client_name')
    project.status = request.form.get('status')
    
    # Handle financial fields (synced with project financial page)
    selling_price = request.form.get('selling_price', '0')
    project.selling_price = float(selling_price) if selling_price else 0.0
    
    client_receipts = request.form.get('client_receipts', '0')
    project.client_receipts = float(client_receipts) if client_receipts else 0.0
    
    # Sync ProjectFinancialParams.sale_price
    financial = ProjectFinancialParams.query.filter_by(project_id=id).first()
    if financial:
        financial.sale_price = project.selling_price
    
    db.session.commit()
    flash('Project updated successfully')
    
    return redirect(url_for('project_detail', id=id))

@app.route('/projects/delete/<int:id>')
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    try:
        Budget.query.filter_by(project_id=id).delete()
        db.session.delete(project)
        db.session.commit()
        flash(f'✅ Project "{project.name}" deleted successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error deleting project: {str(e)}')
    return redirect(url_for('index'))

# ==================== BUDGET ROUTES ====================
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

# ==================== API ROUTES ====================
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

@app.route('/api/projects/list')
@login_required
def projects_list():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).limit(10).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'status': p.status,
            'start_date': p.start_date.strftime('%Y-%m-%d') if p.start_date else None,
            'end_date': p.end_date.strftime('%Y-%m-%d') if p.end_date else None,
            'budget_total': p.budget_total,
            'address': p.address,
            'contact_name': p.client_name,
            'contact_phone': 'À venir'
        } for p in projects])
    except Exception as e:
        print(f"Error in projects_list: {e}")
        return jsonify([]), 500

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
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            flash('Please upload CSV or Excel file')
            return redirect(url_for('contacts'))
        
        success_count = 0
        error_count = 0
        errors = []
        
        def clean(val):
            s = str(val).strip()
            return '' if s.lower() == 'nan' else s
        
        for index, row in df.iterrows():
            try:
                contact = Contact(
                    name=clean(row.get('Name', '')),
                    phone=clean(row.get('Phone', '')),
                    email=clean(row.get('Email', '')),
                    company=clean(row.get('Company', '')),
                    type='client',
                    notes=f"Speciality: {clean(row.get('Speciality', ''))} | Address: {clean(row.get('Address', ''))} | Comments: {clean(row.get('Comments', ''))}"
                )

                if not contact.name:
                    errors.append(f"Row {index + 2}: Name is required")
                    error_count += 1
                    continue

                db.session.add(contact)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        if success_count > 0:
            flash(f'✅ Successfully imported {success_count} contacts')
        if error_count > 0:
            flash(f'⚠️ Failed to import {error_count} contacts.')
            for error in errors[:5]:
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
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            flash('Please upload CSV or Excel file')
            return redirect(url_for('providers'))
        
        success_count = 0
        error_count = 0
        errors = []
        
        def clean(val):
            s = str(val).strip()
            return '' if s.lower() == 'nan' else s
        
        for index, row in df.iterrows():
            try:
                provider = Provider(
                    name=clean(row.get('Company Name', '')),
                    contact_person=clean(row.get('Contact Person', '')),
                    phone=clean(row.get('Phone', '')),
                    email=clean(row.get('Email', '')),
                    address=clean(row.get('Address', '')),
                    service_type=clean(row.get('Speciality', '')),
                    notes=clean(row.get('Comments', ''))
                )
                
                if not provider.name:
                    errors.append(f"Row {index + 2}: Company Name is required")
                    error_count += 1
                    continue
                
                db.session.add(provider)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        if success_count > 0:
            flash(f'✅ Successfully imported {success_count} providers')
        if error_count > 0:
            flash(f'⚠️ Failed to import {error_count} providers.')
            for error in errors[:5]:
                flash(f'Error: {error}')
        
    except Exception as e:
        flash(f'Error reading file: {str(e)}')
    
    return redirect(url_for('providers'))

# ==================== DOWNLOAD TEMPLATES ====================
@app.route('/contacts/template')
@login_required
def download_contacts_template():
    template = pd.DataFrame({
        'Name': ['Ahmed Ben Ali', 'Sarra Mansour'],
        'Phone': ['+216 22 123 456', '+216 55 789 012'],
        'Email': ['ahmed@email.com', 'sarra@email.com'],
        'Company': ['ABC Construction', 'XYZ Materials'],
        'Speciality': ['Project Management', 'Electrical Engineering'],
        'Comments': ['Good client, multiple projects', 'Reliable supplier'],
        'Address': ['Tunis, Centre Ville', 'Sousse, Rue de la Liberté']
    })
    
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
    template = pd.DataFrame({
        'Company Name': ['Matériaux Tunisie', 'Électro Plus'],
        'Contact Person': ['Karim Ben Salem', 'Leila Mansour'],
        'Phone': ['+216 71 123 456', '+216 72 789 012'],
        'Email': ['karim@materiaux.tn', 'leila@electroplus.tn'],
        'Speciality': ['Construction Materials', 'Electrical Supplies'],
        'Comments': ['Good prices, fast delivery', 'Certified products'],
        'Address': ['Tunis, Zone Industrielle', 'Sousse, Route de la Plage']
    })
    
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

@app.route('/financial/template')
@login_required
def download_financial_template():
    """Download the financial Excel template"""
    try:
        # Path to your actual template file
        template_path = os.path.join(app.root_path, 'templates', 'financial_template.xlsx')
        
        # Check if file exists
        if not os.path.exists(template_path):
            flash('Template file not found. Please contact administrator.')
            return redirect(request.referrer or url_for('index'))
        
        return send_file(
            template_path,
            as_attachment=True,
            download_name='financial_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error downloading template: {str(e)}')
        return redirect(request.referrer or url_for('index'))

# ==================== DOWNLOAD CONTACTS ====================
@app.route('/contacts/download-all')
@login_required
def download_all_contacts():
    try:
        contacts = Contact.query.all()
        
        data = []
        for contact in contacts:
            notes = contact.notes or ""
            data.append({
                'Name': contact.name,
                'Email': contact.email or '',
                'Phone': contact.phone or '',
                'Company': contact.company or '',
                'Type': contact.type or '',
                'Notes': notes
            })
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='All Contacts')
        
        output.seek(0)
        
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

# ==================== PROJECT FINANCIAL ROUTES ====================
@app.route('/project/<int:project_id>/financial')
@login_required
def project_financial(project_id):
    project = Project.query.get_or_404(project_id)
    
    financial = ProjectFinancialParams.query.filter_by(project_id=project_id).first()
    if not financial:
        financial = ProjectFinancialParams(project_id=project_id)
        db.session.add(financial)
        db.session.commit()
    
    expenses = ProjectExpense.query.filter_by(project_id=project_id).order_by(ProjectExpense.date.desc()).all()
    total_expenses = sum(e.amount for e in expenses)
    
    receipts = ProjectReceipt.query.filter_by(project_id=project_id).all()
    # Use project.selling_price and project.client_receipts (same as project detail page)
    sale_price = project.selling_price or financial.sale_price or 0
    client_received = project.client_receipts if project.client_receipts is not None else 0
    current_cash = client_received - total_expenses
    estimated_margin = sale_price - financial.estimated_budget
    current_result = sale_price - total_expenses
    balance_remaining = sale_price - client_received  # Solde Restant (amount client still owes)
    
    categories = {}
    for expense in expenses:
        categories[expense.category] = categories.get(expense.category, 0) + expense.amount
    
    category_totals = []
    colors = {'Ouvrier': '#4DA8DA', 'Matériau': '#28a745', 'Divers': '#FF6600'}  # accent-glow, success, accent
    for cat, amount in categories.items():
        category_totals.append({
            'category': cat,
            'total': amount,
            'percentage': (amount / total_expenses * 100) if total_expenses > 0 else 0,
            'color': colors.get(cat, '#6c757d')
        })
    
    return render_template('project_financial.html', 
                         project=project,
                         financial={
                             'client_received': client_received,
                             'current_cash': current_cash,
                             'sale_price': sale_price,
                             'estimated_budget': financial.estimated_budget,
                             'estimated_margin': estimated_margin,
                             'total_expenses': total_expenses,
                             'current_result': current_result,
                             'depenses_reelles': total_expenses, # données projet #5: sum of expenses
                             'gain_actuel': current_result,      # données projet #6: Prix de Vente - Dépenses Réelles
                             'devis_ref': financial.devis_ref,
                             'balance_remaining': balance_remaining
                         },
                         expenses=expenses,
                         receipts=receipts,
                         total_expenses=total_expenses,
                         category_totals=category_totals)

@app.route('/project/<int:project_id>/expense/add', methods=['POST'])
@login_required
def add_project_expense(project_id):
    expense = ProjectExpense(
        project_id=project_id,
        date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
        nature=request.form.get('nature'),
        amount=float(request.form.get('amount')),
        comment=request.form.get('comment'),
        category=request.form.get('category')
    )
    db.session.add(expense)
    db.session.commit()
    flash('Expense added successfully')
    return redirect(url_for('project_financial', project_id=project_id))

@app.route('/project/<int:project_id>/receipt/add', methods=['POST'])
@login_required
def add_client_receipt(project_id):
    receipt = ProjectReceipt(
        project_id=project_id,
        date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
        amount=float(request.form.get('amount')),
        comment=request.form.get('comment')
    )
    db.session.add(receipt)
    db.session.commit()
    flash('Client receipt added successfully')
    return redirect(url_for('project_financial', project_id=project_id))

@app.route('/project/<int:project_id>/financial/update', methods=['POST'])
@login_required
def update_project_financial_params(project_id):
    financial = ProjectFinancialParams.query.filter_by(project_id=project_id).first()
    if not financial:
        financial = ProjectFinancialParams(project_id=project_id)
        db.session.add(financial)
    
    financial.sale_price = float(request.form.get('sale_price', 0))
    financial.estimated_budget = float(request.form.get('estimated_budget', 0))
    financial.devis_ref = float(request.form.get('devis_ref', 0))
    
    db.session.commit()
    flash('Project parameters updated')
    return redirect(url_for('project_financial', project_id=project_id))

@app.route('/project/<int:project_id>/expense/<int:expense_id>/edit', methods=['POST'])
@login_required
def edit_expense(project_id, expense_id):
    expense = ProjectExpense.query.get_or_404(expense_id)
    if expense.project_id != project_id:
        return redirect(url_for('project_financial', project_id=project_id))
    expense.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
    expense.nature = request.form.get('nature')
    expense.amount = float(request.form.get('amount'))
    expense.comment = request.form.get('comment') or None
    expense.category = request.form.get('category', 'Divers')
    db.session.commit()
    flash('Expense updated successfully')
    return redirect(url_for('project_financial', project_id=project_id))

@app.route('/project/<int:project_id>/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(project_id, expense_id):
    expense = ProjectExpense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully')
    return redirect(url_for('project_financial', project_id=project_id))

@app.route('/project/<int:project_id>/financial/delete-all', methods=['POST'])
@login_required
def delete_all_project_financial(project_id):
    """Delete all financial data for a project (expenses + receipts)"""
    try:
        ProjectExpense.query.filter_by(project_id=project_id).delete()
        ProjectReceipt.query.filter_by(project_id=project_id).delete()
        db.session.commit()
        flash('✅ All financial data deleted successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error deleting data: {str(e)}')
    return redirect(url_for('project_financial', project_id=project_id))

@app.route('/project/<int:project_id>/expenses/delete-all', methods=['POST'])
@login_required
def delete_all_expenses(project_id):
    """Delete all expenses for a project (expenses table only, not receipts)"""
    try:
        deleted = ProjectExpense.query.filter_by(project_id=project_id).delete()
        db.session.commit()
        flash(f'✅ {deleted} dépenses supprimées')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur: {str(e)}')
    return redirect(url_for('project_financial', project_id=project_id))

# ==================== PROJECT FINANCIAL EXPORT/IMPORT ====================
@app.route('/project/<int:project_id>/financial/export')
@login_required
def export_project_financial(project_id):
    """Export project financial data to Excel"""
    try:
        project = Project.query.get_or_404(project_id)
        expenses = ProjectExpense.query.filter_by(project_id=project_id).all()
        
        # Create DataFrame from expenses
        data = []
        for expense in expenses:
            data.append({
                'Date': expense.date.strftime('%d/%m/%Y'),
                'Nature': expense.nature,
                'Montant': expense.amount,
                'Commentaire': expense.comment or '',
                'Catégorie': expense.category
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dépenses')
        
        output.seek(0)
        
        filename = f"expenses_{project.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error exporting: {str(e)}')
        return redirect(url_for('project_financial', project_id=project_id))

@app.route('/project/<int:project_id>/financial/import', methods=['POST'])
@login_required
def import_project_financial(project_id):
    """Import expenses from Excel - follows financial_template.xlsx (sheet 'suivi chantier').
    Imported rows are ADDED to expenses, not replaced."""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('project_financial', project_id=project_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('project_financial', project_id=project_id))
    
    try:
        # Read the Excel file - use sheet 'suivi chantier' if present (template format)
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            xlsx = pd.ExcelFile(file)
            if 'suivi chantier' in xlsx.sheet_names:
                df = pd.read_excel(xlsx, sheet_name='suivi chantier')
            else:
                df = pd.read_excel(xlsx, sheet_name=0)  # first sheet
        
        # Track success/failure
        success_count = 0
        error_count = 0
        errors = []
        
        # Define clean function
        def clean(val):
            if pd.isna(val):
                return ''
            return str(val).strip()
        
        # Process each row - ADD to expenses (never replace)
        for index, row in df.iterrows():
            try:
                # Parse date (Excel may return datetime, or string)
                val = row.get('Date')
                if pd.isna(val):
                    date = datetime.now().date()
                elif hasattr(val, 'date'):
                    date = val.date()
                else:
                    date_str = clean(val)
                    if date_str:
                        try:
                            date = datetime.strptime(date_str, '%d/%m/%Y').date()
                        except:
                            try:
                                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except:
                                date = datetime.now().date()
                    else:
                        date = datetime.now().date()
                
                amount_str = clean(row.get('Montant', '0'))
                try:
                    amount = float(str(amount_str).replace(',', '.'))
                except:
                    amount = 0.0
                
                cat_val = 'Divers'
                for c in df.columns:
                    if 'cat' in c.lower():
                        cv = clean(row.get(c, 'Divers'))
                        if cv in ('Ouvrier', 'Matériau', 'Divers'):
                            cat_val = cv
                        elif 'ouvrier' in cv.lower():
                            cat_val = 'Ouvrier'
                        elif 'materiau' in cv.lower() or 'matériau' in cv.lower():
                            cat_val = 'Matériau'
                        break
                
                expense = ProjectExpense(
                    project_id=project_id,
                    date=date,
                    nature=clean(row.get('Nature', '')),
                    amount=amount,
                    comment=clean(row.get('Commentaire', '')),
                    category=cat_val
                )
                
                # Basic validation
                if not expense.nature:
                    errors.append(f"Row {index + 2}: Nature is required")
                    error_count += 1
                    continue
                
                if expense.amount <= 0:
                    errors.append(f"Row {index + 2}: Amount must be positive")
                    error_count += 1
                    continue
                
                db.session.add(expense)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                error_count += 1
        
        # Commit all successful entries
        db.session.commit()
        
        # Flash summary
        if success_count > 0:
            flash(f'✅ Successfully imported {success_count} expenses')
        if error_count > 0:
            flash(f'⚠️ Failed to import {error_count} expenses. Check your file format.')
            for error in errors[:5]:
                flash(f'Error: {error}')
        
    except Exception as e:
        flash(f'Error reading file: {str(e)}')
    
    return redirect(url_for('project_financial', project_id=project_id))

# ==================== MAIN ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('changeme')
            db.session.add(admin)
            db.session.commit()
            print('Default user created: admin / changeme')
    
    app.run(debug=True, host='0.0.0.0', port=5000)