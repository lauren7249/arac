require 'rubygems'
require 'selenium-webdriver'
require 'fileutils'
require 'aws-sdk'
require 'aws-sdk-core'
require 'rspec/expectations'
require 'open3'

include RSpec::Matchers

$bucket_name = 'advisorconnect-bigfiles'
#locate AWS s3 bucket 
Aws.config = {
  :access_key_id => 'AKIAIZZBJ527CKPNY6YQ',
  :secret_access_key => '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',
  :region => 'us-east-1'
}
$s3 = Aws::S3::Client.new

stdin, stdout, stderr = Open3.popen3("nohup firefox")
profile = Selenium::WebDriver::Firefox::Profile.new
$browser = Selenium::WebDriver.for :firefox, :profile => profile
$wait = Selenium::WebDriver::Wait.new(:timeout => 4)

class linkedin_pirate

	def initialize(username, password)
		$browser.get "https://www.linkedin.com"
		element = $browser.find_element(:name, 'session_key');
		element.send_keys username
		element = $browser.find_element(:name, 'session_password');
	    element.send_keys password
	 	element = $browser.find_element(:name, 'signin');
		element.click

		$wait.until { $browser.find_element(:class, 'account-toggle') }		
		element = $browser.find_element(:class, 'account-toggle');
		link = element.attribute("href")
		#get current user linkedin id
		@root_linkedin_id = getLinkedInID(link)		

	end

	def get_first_degree_connections
		all_first_degree_ids = []
		#go to connections page
		$wait.until { $browser.find_element(:link_text, 'Connections') }
		element = $browser.find_element(:link_text, 'Connections')
		element.click

		more_results = true
		current_count = 0
		#keep scrolling until you have all the contacts
		while more_results
			#scroll the first block so that number of connections is visible
			$wait.until { 
				$browser.find_elements(:class, "contact-item-view").last 
			}	
			$wait.until { 
				$browser.find_elements(:class, "contact-item-view").last.location_once_scrolled_into_view
			}	

			
			# Scroll to the last image currently loaded
			$browser.find_elements(:class, "contact-item-view").last.location_once_scrolled_into_view
			
			begin
				more_results = $wait.until {current_count < $browser.find_elements(:class, "contact-item-view").length}	
				if current_count == $browser.find_elements(:class, "contact-item-view").length 
					more_results = false
					break
				end			
			rescue 
				more_results = false
				break
			end

			current_count = $browser.find_elements(:class, "contact-item-view").length
		end	

		#get info for all contacts
		all_views = $browser.find_elements(:class, "contact-item-view")
		all_friend_links = []

		all_views.each { |view|
			element = view.find_element(:class, 'image')
			link = element.attribute("href")
			all_friend_links << link
		}

		all_friend_links.each { |link|
			linkedin_id = getLinkedInID(link)
			all_first_degree_ids << linkedin_id
		}

		all_first_degree_ids
	end
	def get_second_degree_connections(second_degree_id)
		$browser.get "https://www.linkedin.com/profile/view?trk=contacts-contacts-list-contact_name-0&id=" + second_degree_id

		begin
			element = $wait.until { $browser.find_element(:class, 'connections-link')}	
			element.click	
		rescue
			return
		end

		all_friend_ids = []
		while true		
			$wait.until { 
				$browser.find_elements(:class, 'connections-photo')
			}	
			
			all_friend_ids = findConnections(all_friend_ids)
			$wait.until { 
				$browser.find_element(:class, 'connections-paginate')
			}				
			connections_view = $browser.find_element(:class, 'connections-paginate')
			buttons = connections_view.find_elements(:tag_name, 'button')
			begin
				next_button = buttons[1]
				next_button.click		
			rescue Exception => e
				break
			end
		end
		all_friend_ids
	end

	def findConnections(all_friend_ids)
		all_views = $browser.find_elements(:class, "connections-photo")
		all_views.each { |view|
			begin
				link = view.attribute("href")
				linkedin_id = getLinkedInID(link)
			rescue
				begin
					oops_link = $browser.find_element(:class, "error-search-retry")
					oops_link.click
					$wait.until { $browser.find_elements(:class, 'connections-photo')}	
					all_friend_ids = findConnections(all_friend_ids)				
				rescue
					all_friend_ids = findConnections(all_friend_ids)
				end
			end
			all_friend_ids << linkedin_id
		}
		all_friend_ids
	end


	def getLinkedInID(link)
		link = link.split("&")[0]
		linkedin_id = link.split("=")[1]
		if linkedin_id.include? "li_"
			linkedin_id = linkedin_id.split("_")[1]
			return linkedin_id
		end
		$browser.get link
		url = $browser.current_url
		linkedin_id = url.split("=")[-1]
		return linkedin_id
	end 

end

