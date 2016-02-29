

#For Deduping real emails
EXCLUDED_EMAIL_WORDS = ["reply","support","sales","info","feedback","noreply",\
"docs.google.com", "craigslist.org", "sale"]
NOT_REAL_JOB_WORDS = ["intern","candidate","student","summer","part-time","former","worked"]
EXCLUDED_COMPANIES = ['New York Life Insurance Company','NYLIFE Securities LLC','NYLIFE Securities, LLC','NYLIFE Securities','MassMutual Financial Group','First Financial Group, LLC', 'First Financial Group','First Financial Group LLC','MassMutual Metro New York','MassMutual Brooklyn','MassMutual NJ-NYC','MassMutual New Jersey-NYC','MassMutual Greater Long Island','MassMutual Westchester','Northwestern Mutual','Northwestern Mutual Life']
AWS_KEY = "AKIAIKCNCKG6RXJHWNFA"
AWS_SECRET = "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"
AWS_BUCKET = "aconn"

user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
GLOBAL_HEADERS ={'User-Agent':user_agent, 'Accept-Language': 'en-US,en;q=0.8', "Content-Language":"en"}

REDIS_URL='redis://169.55.28.216'

facebook_re = '^https*?://(www.)*facebook.com/(_/people/)*[^/]+'
pub_profile_re = '^https*?://(www.)*linkedin.com/pub(?!/dir/)(/.*)+'
in_profile_re = '^https*?://(www.)*linkedin.com/in/.*'
profile_re = '(' + pub_profile_re + ')|(' + in_profile_re +')'
bloomberg_company_re = '^http://www.bloomberg.com/research/stocks/private/snapshot.asp\?privcapid=[0-9]+'
plus_company_re = '^https://plus.google.com/[0-9a-zA-Z]+/about'
school_re = '^https://www.linkedin.com/edu/*'
company_re = '^https://www.linkedin.com/company/*'
email_re = '[^@]+@[^@]+\.[^@]+'

BROWSERSTACK_KEY='7qc2so9ApZBP6SWyGy7A'
BROWSERSTACK_USERNAME='laurentalbot1'

SAUCE_ACCESS_KEY='5245ef28-5c9a-4242-b5fe-b9feaa85800a'
SAUCE_USERNAME='laurenAC'
LINKEDIN_YAHOO_DOWNLOAD_URL="https://www.linkedin.com/people/export-action?outputType=yahoo"
LINKEDIN_EXPORT_URL  ='https://www.linkedin.com/addressBookExport?exportNetwork=Export&outputType=microsoft_outlook'
LINKEDIN_DOWNLOAD_URL='https://www.linkedin.com/addressBookExport?exportNetworkRedirect=&outputType=microsoft_outlook'
LINKEDIN_PIN_CHALLENGE_URL="https://www.linkedin.com/uas/ato-pin-challenge-submit?PinVerificationForm_pinParam="
LINKEDIN_CAPTCHA_CROP_DIMS = (20, 158, 319, 215)
ANTIGATE_ACCESS_KEY='0bebb0a526e59df337e4340f89a8e56b'

SOCIAL_DOMAINS = ["twitter","soundcloud","slideshare","plus","pinterest","facebook","linkedin","amazon","angel","foursquare","github","flickr","tumblr","goodreads"]
#image processing -- 1K calls/day
ALCHEMY_API_KEYS = ["b8d4b7af348984ce7113a4e9aeefdaaa7f906991","d0a43371f6ba8fa7214437b0d745ed352e428785","bdbe594c87316744fc3b7be8d595e5ae1169a77e","8bba403a0f041ebec65ec9bd0c62b326e6eeb6e9","61b6ce78bd662c1bdaf2284d2d1cdc8b0252fee9","90e9074da17fbf4da2d0e2bf8d15dbfeac28d9b9"]
CLEARBIT_KEY = 'f2512e10a605e3dcaff606205dbd3758'
SCRAPING_API_KEY = "0ca62d4f6c0345ef80af1c4a9868da0f"
bing_api_keys = ["xmiHcP6HHtkUtpRk/c6o9XCtuVvbQP3vi4WSKK1pKGg","VnjbIn8siy+aS9U2hjEmBgBGyhmiShWaTBARvh8lR1s","ETjsWwqMuHtuwV0366GtgJEt57BkFPbhnV4oT8lcfgU","CAkR9NrxB+9brLGVtRotua6LzxC/nZKqKuclWf9GjKU","hysOYscBLj0xtRDUst5wJLj2vWLyiueCDof6wGYD5Ls","FWyMRXjzB9NT1GXTFGxIdS0JdG3UsGHS9okxGx7mKZ0","U7ObwzZDTxyaTPbqwDkhPJ2wy+XfgMuVJ7k2BR/8HcE","VzTO15crpGKTYwkA8qqRThohTliVQTznqphD+WA5eVA"]
PIPL_SOCIAL_KEYS = ["ml2msz8le74d4nno7dyk0v7c",'24xx1svc2722l72m5fhmu94w','6yuvscvato7o16zxk8y8mmcb','lvtgjr2zjoztsdqp4dovid92','1jjs6mju38n6wpjcndkzikx1']
PIPL_PROFES_KEYS = ["uegvyy86ycyvyxjhhbwsuhj9","6cuq3648nfbqgch5verhcfte","z2ppf95933pmtqb2far8bnkd"]

CODER_WORDS = ["engineer","hacker","developer","programmer","coder","cto","data scientist","software","computer"]
PROGRAMMING_LANGUAGES = ["Java","C","C++","Python","C#","PHP","Visual Basic .NET",".NET","ASP.NET","Software Development" "JavaScript","jQuery","VB.NET","Visual Basic", "Perl","Ruby","Assembly Language","Delphi/Object Pascal","Delphi" "Swift","Objective-C","MATLAB","Pascal","R","PL/SQL","SQL", "COBOL","Ada","Fortran","D","Groovy","Dart","Scratch","SAS","Scala","LISP","ABAP","Lua","Transact-SQL","Erlang","F#","Logo","Prolog","RPG","Scheme","Haskell","OpenEdge ABL","ABL", "ActionScript","LabVIEW","FoxPro","Ladder Logic","Awk","Rust","VBScript","ML","Apex","Go","Software Engineering"]
TECH_DEGREE_WORDS = ['computer','physics','engineering','math','economics','information','statistic','machine','technology','software','hardware']

CATEGORY_ICONS = {'Agriculture': 'pagelines',
                 'Arts': 'paint-brush',
                 'Construction': 'building',
                 'Consulting': 'line-chart',
                 'Defense & Military': 'fighter-jet',
                 'Education': 'graduation-cap',
                 'Entertainment & Leisure': 'glass',
                 'Film & Media': 'film',
                 'Finance': 'usd',
                 'Goods & Retail': 'shopping-cart',
                 'Government': 'institution',
                 'HR & Staffing': 'user',
                 'Legal': 'gavel',
                 'Manufacturing': 'cogs',
                 'Medicine & Healthcare': 'medkit',
                 'Non-Profit Organizations': 'shield',
                 'Operations': 'briefcase',
                 'PR & Marketing': 'quote-left',
                 'Print Media': 'book',
                 'Real Estate': 'home',
                 'Research': 'flask',
                 'Services': 'wrench',
                 'Sports': 'futbol',
                 'Technology': 'laptop',
                 'Transportation': 'train'}   
INDUSTRY_CATEGORIES = {'Accounting': 'Finance',
                     'Airlines/Aviation': 'Transportation',
                     'Alternative Dispute Resolution': 'Legal',
                     'Alternative Medicine': 'Medicine & Healthcare',
                     'Animation': 'Film & Media',
                     'Apparel & Fashion': 'Goods & Retail',
                     'Architecture & Planning': 'Construction',
                     'Arts and Crafts': 'Arts',
                     'Automotive': 'Manufacturing',
                     'Aviation & Aerospace': 'Manufacturing',
                     'Banking': 'Finance',
                     'Biotechnology': 'Technology',
                     'Broadcast Media': 'Film & Media',
                     'Building Materials': 'Construction',
                     'Business Supplies and Equipment': 'Manufacturing',
                     'Capital Markets': 'Finance',
                     'Chemicals': 'Manufacturing',
                     'Civic & Social Organization': 'Non-Profit Organizations',
                     'Civil Engineering': 'Construction',
                     'Commercial Real Estate': 'Real Estate',
                     'Computer & Network Security': 'Technology',
                     'Computer Games': 'Entertainment & Leisure',
                     'Computer Hardware': 'Technology',
                     'Computer Networking': 'Technology',
                     'Computer Software': 'Technology',
                     'Construction': 'Construction',
                     'Consumer Electronics': 'Manufacturing',
                     'Consumer Goods': 'Goods & Retail',
                     'Consumer Services': 'Services',
                     'Cosmetics': 'Goods & Retail',
                     'Dairy': 'Agriculture',
                     'Defense & Space': 'Defense & Military',
                     'Design': 'Arts',
                     'E-Learning': 'Education',
                     'Education Management': 'Education',
                     'Electrical/Electronic Manufacturing': 'Manufacturing',
                     'Entertainment': 'Entertainment & Leisure',
                     'Environmental Services': 'Services',
                     'Events Services': 'Services',
                     'Executive Office': 'Government',
                     'Facilities Services': 'Services',
                     'Farming': 'Agriculture',
                     'Financial Services': 'Finance',
                     'Fine Art': 'Arts',
                     'Fishery': 'Agriculture',
                     'Food & Beverages': 'Goods & Retail',
                     'Food Production': 'Manufacturing',
                     'Fund-Raising': 'Non-Profit Organizations',
                     'Furniture': 'Goods & Retail',
                     'Gambling & Casinos': 'Entertainment & Leisure',
                     'Glass, Ceramics & Concrete': 'Manufacturing',
                     'Government Administration': 'Government',
                     'Government Relations': 'Government',
                     'Graphic Design': 'Arts',
                     'Health, Wellness and Fitness': 'Medicine & Healthcare',
                     'Higher Education': 'Education',
                     'Hospital & Health Care': 'Medicine & Healthcare',
                     'Hospitality': 'Entertainment & Leisure',
                     'Human Resources': 'HR & Staffing',
                     'Import and Export': 'Operations',
                     'Individual & Family Services': 'Non-Profit Organizations',
                     'Industrial Automation': 'Manufacturing',
                     'Information Services': 'Services',
                     'Information Technology and Services': 'Technology',
                     'Insurance': 'Finance',
                     'International Affairs': 'Government',
                     'International Trade and Development': 'Government',
                     'Internet': 'Technology',
                     'Investment Banking': 'Finance',
                     'Investment Management': 'Finance',
                     'Judiciary': 'Government',
                     'Law Enforcement': 'Government',
                     'Law Practice': 'Legal',
                     'Legal Services': 'Legal',
                     'Legislative Office': 'Government',
                     'Leisure, Travel & Tourism': 'Entertainment & Leisure',
                     'Libraries': 'Print Media',
                     'Logistics and Supply Chain': 'Operations',
                     'Luxury Goods & Jewelry': 'Goods & Retail',
                     'Machinery': 'Manufacturing',
                     'Management Consulting': 'Consulting',
                     'Maritime': 'Transportation',
                     'Market Research': 'Consulting',
                     'Marketing and Advertising': 'PR & Marketing',
                     'Mechanical or Industrial Engineering': 'Manufacturing',
                     'Media Production': 'Film & Media',
                     'Medical Devices': 'Medicine & Healthcare',
                     'Medical Practice': 'Medicine & Healthcare',
                     'Mental Health Care': 'Medicine & Healthcare',
                     'Military': 'Defense & Military',
                     'Mining & Metals': 'Manufacturing',
                     'Motion Pictures and Film': 'Film & Media',
                     'Museums and Institutions': 'Arts',
                     'Music': 'Arts',
                     'Nanotechnology': 'Technology',
                     'Newspapers': 'Print Media',
                     'Non-Profit Organization Management': 'Non-Profit Organizations',
                     'Nonprofit Organization Management': 'Non-Profit Organizations',
                     'Oil & Energy': 'Manufacturing',
                     'Online Media': 'Film & Media',
                     'Outsourcing/Offshoring': 'Operations',
                     'Package/Freight Delivery': 'Operations',
                     'Packaging and Containers': 'Manufacturing',
                     'Paper & Forest Products': 'Manufacturing',
                     'Performing Arts': 'Arts',
                     'Pharmaceuticals': 'Medicine & Healthcare',
                     'Philanthropy': 'Non-Profit Organizations',
                     'Photography': 'Arts',
                     'Plastics': 'Manufacturing',
                     'Political Organization': 'Government',
                     'Primary/Secondary Education': 'Education',
                     'Printing': 'Print Media',
                     'Professional Training & Coaching': 'Consulting',
                     'Program Development': 'Non-Profit Organizations',
                     'Public Policy': 'Government',
                     'Public Relations and Communications': 'PR & Marketing',
                     'Public Safety': 'Government',
                     'Publishing': 'Print Media',
                     'Railroad Manufacture': 'Manufacturing',
                     'Ranching': 'Agriculture',
                     'Real Estate': 'Real Estate',
                     'Recreational Facilities and Services': 'Services',
                     'Religious Institutions': 'Non-Profit Organizations',
                     'Renewables & Environmental': 'Manufacturing',
                     'Renewables & Environment': 'Manufacturing',
                     'Research': 'Research',
                     'Restaurants': 'Entertainment & Leisure',
                     'Retail': 'Goods & Retail',
                     'Security and Investigations': 'Services',
                     'Semiconductors': 'Technology',
                     'Shipbuilding': 'Manufacturing',
                     'Sporting Goods': 'Sports',
                     'Sports': 'Sports',
                     'Staffing and Recruiting': 'HR & Staffing',
                     'Supermarkets': 'Goods & Retail',
                     'Telecommunications': 'Technology',
                     'Textiles': 'Manufacturing',
                     'Think Tanks': 'Non-Profit Organizations',
                     'Tobacco': 'Goods & Retail',
                     'Translation and Localization': 'Services',
                     'Transportation/Trucking/Railroad': 'Transportation',
                     'Utilities': 'Manufacturing',
                     'Venture Capital & Private Equity': 'Finance',
                     'Veterinary': 'Medicine & Healthcare',
                     'Warehousing': 'Operations',
                     'Wholesale': 'Goods & Retail',
                     'Wine and Spirits': 'Goods & Retail',
                     'Wireless': 'Technology',
                     'Writing and Editing': 'Print Media'}

US_STATES = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}
