import pandas
matched_df = pandas.read_csv('scripts/touchpoints/matched.touchpoints.output.csv')
tp = pandas.read_csv("scripts/touchpoints/advisorCONNECT 6-10-15 Test Input.csv")

scraping_hours_in_test = 8.0 #guesstimate
#hopefully these numbers are right. we could always do another test
unique_names_in_test = 1996.0
unique_names_matched_in_test = 219.0
bing_calls_in_test = 5984.0
unique_urls_returned_in_test = 30691.0
records_in_test = 2161.0

#only includes variable costs
#amounts are in dollars
#ignores geocoding costs and other calculation costs on url result set

average_bing_pages_per_name = bing_calls_in_test/unique_names_in_test #based on first test
average_linkedin_results_per_name = unique_urls_returned_in_test/unique_names_in_test

#based on https://datamarket.azure.com/dataset/bing/searchweb
def cost_per_bing_page(bing_pages_per_month):
	if bing_pages_per_month<5000: return 0
	if bing_pages_per_month<10000: return 13/bing_pages_per_month
	if bing_pages_per_month<20000: return 25/bing_pages_per_month
	if bing_pages_per_month<50000: return 63/bing_pages_per_month
	if bing_pages_per_month<100000: return 125/bing_pages_per_month
	if bing_pages_per_month<250000: return 313/bing_pages_per_month
	if bing_pages_per_month<500000: return 625/bing_pages_per_month
	if bing_pages_per_month<1000000: return 1250/bing_pages_per_month
	if bing_pages_per_month<1500000: return 1875/bing_pages_per_month
	if bing_pages_per_month<2000000: return 2500/bing_pages_per_month
	if bing_pages_per_month<2500000: return 3125/bing_pages_per_month
	if bing_pages_per_month<3000000: return 3750/bing_pages_per_month
	if bing_pages_per_month<3500000: return 4375/bing_pages_per_month
	if bing_pages_per_month>=4000000: return 5000/bing_pages_per_month

def hit_rate(max_age):
	hits = float(len(set(matched_df[matched_df.Age <= max_age]["ID Number"].values)))
	total = float(len(set(tp[tp.Age <= max_age]["ID Number"].values)))
	return hits/total

def possible_linkedin_results(name):
	return average_linkedin_results_per_name

def bing_pages(name):
	return average_bing_pages_per_name

records_per_name = records_in_test/unique_names_in_test
scrapes_per_hour = unique_urls_returned_in_test/scraping_hours_in_test

def analyze(max_age = 50, 
			#how much we pay people per hour to monitor the scraping
			skilled_wage = 20.0, 
			working_hours_per_day = 8.0, #how many hours per day we can be available to monitor scraping
			computers_running = 10.0, #how many machines we have to run this thing on for all the working hours
			working_days_per_month = 20.0, #how many days our workers are working per month
			revenue_per_hit = 0.1, #how much we charge per hit
			skilled_hours_per_machine_per_scraping_hour = 0.1 #for every hour a machine is scraping, how many hours do we have to spend monitoring it?
			):
	linkedin_scrapes_per_month = scrapes_per_hour*working_hours_per_day*working_days_per_month*computers_running
	names_per_month = linkedin_scrapes_per_month/average_linkedin_results_per_name
	skilled_hours_per_machine_per_day = skilled_hours_per_machine_per_scraping_hour * working_hours_per_day
	bing_pages_per_month = names_per_month*average_bing_pages_per_name

	skilled_hours_per_day = skilled_hours_per_machine_per_day*computers_running
	#we can probably lower this
	linked_scrapes_per_day = scrapes_per_hour*computers_running*working_hours_per_day
	daily_scraping_cost = skilled_wage*skilled_hours_per_day

	cost_per_linkedin_scrape = daily_scraping_cost/linked_scrapes_per_day
	cost_per_name = (cost_per_linkedin_scrape * possible_linkedin_results(None)) + (cost_per_bing_page(bing_pages_per_month) * bing_pages(None))
	cost_per_record = cost_per_name/records_per_name
	cost_per_hit = cost_per_record/hit_rate(max_age)

	hits_per_month = names_per_month*records_per_name*hit_rate(max_age)
	revenue_per_month = hits_per_month*revenue_per_hit
	cost_per_month = hits_per_month*cost_per_hit
	profit_per_month = revenue_per_month - cost_per_month
	vars = locals()
	return vars


if __name__=="__main__":
	vars = analyze()
	for local in vars:
		print local + ": " + str(vars[local]) 	