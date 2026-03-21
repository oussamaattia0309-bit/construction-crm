import sys, os
sys.path.append(os.getcwd())
from app import app
from flask import render_template

with app.app_context():
    try:
        render_template('project_docs/memos.html', project={'name': 'Test'}, memos=[])
        print('Memos template found')
        render_template('project_docs/plans.html', project={'name': 'Test'}, plans=[])
        print('Plans template found')
        render_template('project_docs/contracts.html', project={'name': 'Test'}, contracts=[])
        print('Contracts template found')
        render_template('project_docs/invoices.html', project={'name': 'Test'}, invoices=[])
        print('Invoices template found')
    except Exception as e:
        print(f'Error: {e}')
