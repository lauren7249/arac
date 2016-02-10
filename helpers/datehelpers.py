import dateutil.parser

DEFAULT_DATE = dateutil.parser.parse('January 1')
def parse_date(datestr):
    try:
        date = dateutil.parser.parse(datestr, default=DEFAULT_DATE)
    except:
        date = None
    return date

def date_overlap(start_date1, end_date1, start_date2, end_date2):
    if (start_date1 <= start_date2 <= end_date1):
        return (start_date2, end_date1)
    if (start_date2 <= start_date1 <= end_date2):
        return (start_date1, end_date2)
    return None