#!/usr/bin/env python
import os

from flask.ext.migrate import MigrateCommand, Migrate
from flask.ext.script import Manager, Shell

from prime import create_app, db


app = create_app(os.getenv('AC_CONFIG', 'default'))
app.debug=True

migrate = Migrate(app, db)
if __name__ == '__main__':
    manager = Manager(app)

    @manager.command
    def generate_fake():
        from prime.users.models import db, User
        from prime.managers.models import ManagerProfile
        session = db.session
        u = User('Test', 'Person', 'jamesjohnson11@gmail.com', '123123123')
        session.add(u)
        u2 = User('Test', 'Manager', 'laurentracytalbot@gmail.com', '123123123')
        session.add(u2)
        mp = ManagerProfile()
        mp.user = u2
        mp.users.append(u)
        session.add(mp)
        session.commit()

    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(use_ipython=True))
    #manager.add_command('shell', Shell(make_context=make_shell_context, use_ipython=True))
    manager.run()

