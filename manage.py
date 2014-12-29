#!/usr/bin/env python
import os

from flask.ext.migrate import MigrateCommand, Migrate
from flask.ext.script import Manager, Shell

from prime import create_app, db


app = create_app(os.getenv('AC_CONFIG', 'beta'))
migrate = Migrate(app, db)

if __name__ == '__main__':
    manager = Manager(app)

    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(use_ipython=True))
    #manager.add_command('shell', Shell(make_context=make_shell_context, use_ipython=True))
    manager.run()
