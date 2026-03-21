import sys
import os
sys.path.append(os.getcwd())
from app import app, Project, ProjectMemo, ProjectPlan, ProjectContract, ProjectInvoice

with app.app_context():
    p = Project.query.get(3)
    print(f'Project 3: {p.name if p else "Not Found"}')
    if p:
        print(f'Memos: {ProjectMemo.query.filter_by(project_id=3).count()}')
        print(f'Plans: {ProjectPlan.query.filter_by(project_id=3).count()}')
        print(f'Contracts: {ProjectContract.query.filter_by(project_id=3).count()}')
        print(f'Invoices: {ProjectInvoice.query.filter_by(project_id=3).count()}')
