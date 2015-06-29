from web import app
from flask import render_template, request, url_for, redirect, session
import re, json
from sexting.sexting import Sexting
from sexting.lib.contactloader import ContactLoader
from formencode.variabledecode import variable_decode

@app.route('/')
def message_input():
    message = session.get('message', '')
    return render_template('message_input.html', message=message)

@app.route('/message', methods=['POST'])
def submit_message():
    message = request.form['message']

    session['message'] = message

    return redirect(url_for('contacts_input'))

@app.route('/contacts')
def contacts_input():
    contacts = session.get('contacts', [{}])
    contacts_json = json.dumps(contacts)
    return render_template('contacts_input.html', contacts_json=contacts_json)

@app.route('/contacts', methods=['POST'])
def submit_contacts():
    contacts = __decode_contacts(request.form)

    session['contacts'] = contacts

    return redirect(url_for('contacts_input'))

def __decode_contacts(form):
    contacts = []
    form_data = variable_decode(form)

    for key in form_data:
        if re.match('^c[0-9]+$', key):
            index = int(key[1:])
            contact = __decode_contact(form_data[key])
            if contact is not None:
                contacts.append((index, contact))

    contacts.sort(key=lambda t: t[0])
    return map(lambda t: t[1], contacts)

def __decode_contact(d):
    if 'name' not in d or not d['name'].strip():
        return None

    name = d['name']
    del d['name']

    __decode_checkbox(d, 'contactless')
    __decode_checkbox(d, 'twitter')

    return {'name': name, 'data': d}

def __decode_checkbox(d, field):
    if field in d and d[field] == 'on':
        d[field] = True

@app.route('/instructions')
def view_instructions():
    message = session.get('message', '')
    contacts = session.get('contacts', [{}])
    start_hour = 11

    contacts_instructions = __transform(message, contacts, start_hour)
    return render_template('instructions.html', contacts_instructions=contacts_instructions)

def __transform(message, contacts, start_hour):
    contacts = ContactLoader().all_from_dicts(contacts)
    all_instructions = Sexting(contacts, message, start_hour).process()

    instructions_by_contact = {}
    for i in all_instructions:
        if i.contact().name() not in instructions_by_contact:
            instructions_by_contact[i.contact().name()] = (i.contact(), [])
        instructions_by_contact[i.contact().name()][1].append(i)

    return instructions_by_contact.values()

