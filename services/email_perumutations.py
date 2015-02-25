import argparse
import string

def first(domain, first_name, last_name):
    return "{}@{}".format(first_name, domain).lower()

def last(domain, first_name, last_name):
    return "{}@{}".format(last_name, domain).lower()

def first_dash_last(domain, first_name, last_name):
    return "{}-{}@{}".format(first_name, last_name, domain).lower()

def firstint_dot_last(domain, first_name, last_name):
    return "{}.{}@{}".format(first_name[0], last_name, domain).lower()

def last_first(domain, first_name, last_name):
    return "{}{}@{}".format(last_name, first_name, domain).lower()

def last_score_firstint(domain, first_name, last_name):
    return "{}_{}@{}".format(last_name, first_name[0], domain).lower()

def last_dash_first(domain, first_name, last_name):
    return "{}-{}@{}".format(last_name, first_name, domain).lower()

def last_firstint(domain, first_name, last_name):
    return "{}{}@{}".format(last_name, first_name[0], domain).lower()

def first_score_last(domain, first_name, last_name):
    return "{}_{}@{}".format(first_name, last_name, domain).lower()

def last_twoltrsfirst(domain, first_name, last_name):
    return "{}{}@{}".format(last_name, first_name[0:2], domain).lower()

def first_last(domain, first_name, last_name):
    return "{}{}@{}".format(first_name, last_name, domain).lower()

def last_dot_first(domain, first_name, last_name):
    return "{}.{}@{}".format(first_name, last_name, domain).lower()

def first_lastint(domain, first_name, last_name):
    return "{}{}@{}".format(first_name, last_name[0], domain).lower()

def first_init_last(domain, first_name, last_name):
    return "{}{}@{}".format(first_name[0], last_name, domain).lower().lower()

def first_dot_last(domain, first_name, last_name):
    return "{}.{}@{}".format(first_name, last_name, domain).lower()

def last_score_first(domain, first_name, last_name):
    return "{}_{}@{}".format(last_name, first_name, domain).lower()

def firsttwoltrsfirst_last(domain, first_name, last_name):
    return "{}{}@{}".format(first_name[0:2], last_name, domain).lower()


def first_dot_middle_dot_last(domain, first_name, last_name):
    emails = []
    for a in string.lowercase:
        emails.append("{}.{}.{}@{}".format(first_name, a, last_name, domain).lower())
    return emails

def first_score_middleint_score_last(domain, first_name, last_name):
    emails =[]
    for a in string.lowercase:
        emails.append("{}_{}_{}@{}".format(first_name, a, last_name, domain).lower())
    return emails


def first_dot_middleint_dot_last(domain, first_name, last_name):
    emails =[]
    for a in string.lowercase:
        emails.append("{}.{}.{}@{}".format(first_name, a, last_name,
            domain).lower())
    return emails

def firstint_middleint_last(domain, first_name, last_name):
    emails =[]
    for a in string.lowercase:
        emails.append("{}{}{}@{}".format(first_name[0], a, last_name, domain).lower())
    return emails

def last_dot_firstint_middleint(domain, first_name, last_name):
    emails =[]
    for a in string.lowercase:
        emails.append("{}.{}{}@{}".format(last_name, first_name[0], a, domain).lower())
    return emails

def firstint_middleint_last_int(domain, first_name, last_name):
    emails =[]
    for a in string.lowercase:
        emails.append("{}{}{}@{}".format(first_name[0], a, last_name[0], domain).lower())
    return emails

def last_firstint_middleint(domain, first_name, last_name):
    emails =[]
    for a in string.lowercase:
        emails.append("{}{}{}@{}".format(last_name, first_name[0], a, domain))
    return emails

def firstint_middleint_last(domain, first_name, last_name):
    emails =[]
    for a in string.lowercase:
        emails.append("{}{}{}@{}".format(first_name[0], a, last_name, domain).lower())
    return emails


def generate_email_perms(first_name, last_name, domain):
    emails = []
    emails.append(first(domain, first_name, last_name))
    emails.append(last(domain, first_name, last_name))
    emails.append(first_dash_last(domain, first_name, last_name))
    emails.append(firstint_dot_last(domain, first_name, last_name))
    emails.append(last_first(domain, first_name, last_name))
    emails.append(last_score_firstint(domain, first_name, last_name))
    emails.append(last_dash_first(domain, first_name, last_name))
    emails.append(last_firstint(domain, first_name, last_name))
    emails.append(first_score_last(domain, first_name, last_name))
    emails.append(last_twoltrsfirst(domain, first_name, last_name))
    emails.append(first_last(domain, first_name, last_name))
    emails.append(last_dot_first(domain, first_name, last_name))
    emails.append(first_lastint(domain, first_name, last_name))
    emails.append(first_init_last(domain, first_name, last_name))
    emails.append(first_dot_last(domain, first_name, last_name))
    emails.append(last_score_first(domain, first_name, last_name))
    emails.append(firsttwoltrsfirst_last(domain, first_name, last_name))

    #Middle names
    emails.extend(first_dot_middle_dot_last(domain, first_name, last_name))
    emails.extend(first_score_middleint_score_last(domain, first_name, last_name))
    emails.extend(first_dot_middleint_dot_last(domain, first_name, last_name))
    emails.extend(firstint_middleint_last(domain, first_name, last_name))
    emails.extend(last_dot_firstint_middleint(domain, first_name, last_name))
    emails.extend(firstint_middleint_last_int(domain, first_name, last_name))
    emails.extend(last_firstint_middleint(domain, first_name, last_name))
    emails.extend(firstint_middleint_last(domain, first_name, last_name))
    print len(emails)
    return emails

if __name__ == '__main__':
    generate_email_perms("James", "Johnson", "google.com")
