from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
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