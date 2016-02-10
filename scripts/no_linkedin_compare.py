from prime.users.models import *

emails = [  \
            "christopher_sorgie@newyorklife.com",
            "jrocchi@ft.newyorklife.com", \
            "cmollo@ft.newyorklife.com", \
            "dfcoug@yahoo.com" ]
for email in emails:
    user = User.query.filter(User.email==email).first()
    contacts, user = user.refresh_contacts()
    no_linkedin_contacts = []

    for contact in contacts:
        if contact.get("service") == 'LinkedIn': continue
        no_linkedin_contacts.append(contact)

    new_user = User(user.first_name, user.last_name, "nolinkedin_" + user.email, "123123123")
    new_user.manager_id = user.manager_id
    session = db.session
    session.add(new_user)
    manager = user.manager
    manager.users.append(new_user)
    session.add(manager)
    session.commit()
    new_user.account_created=True
    new_user.refresh_contacts(new_contacts=no_linkedin_contacts)
