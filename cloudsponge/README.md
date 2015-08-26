##CloudSponge Contacts Import API Python Client

###Overview

This module provides a minimal python client wrapping the
CloudSponge Contacts Import API.

###Requirements

    $ pip install requests

###Test

Run a quick test to verify setup.

    $ cp cloudsponge.conf.example cloudsponge.conf

Edit the file cloudsponge.conf and update with your
key and password received from registering with cloudsponge.

    $ python test.py <service>

Where `<service>` is `gmail|yahoo|windowslive`. Follow on-screen instructions.

###Meta

Licensed under the MIT license. http://opensource.org/licenses/MIT

Special Thanks to Alistair Robinson for his blog post from which I
borrowed profusely.
http://blog.alistairrobinson.com/importing-contacts-with-cloudsponge-ember-js-and-django-rest-framework/
