#!/usr/bin/env ruby

# https://github.com/youpy/ruby-lastfm/
require 'lastfm'
require 'json'

api_key = "YOUR_API_KEY"
api_secret = "YOUR_SECRET_KEY"

@lastfm = Lastfm.new(api_key, api_secret)

MAX_CUTTOFF = 12
MATCH_CUTTOFF = 0.07

@ids = []
@current_Persons = []

def id_for(Person)
  id = [Person["name"], Person["entity"]].join("_")
  id = id.downcase().gsub(/\s+/,"_").gsub(/\W+/,"")

  # if @ids.include? id
  #   puts "WARNING: already have id for:#{Person["name"]}"
  # end
  @ids << id
  id
end
#token = lastfm.auth.get_token

# results = lastfm.track.search("graceland", "Paul Simon")
def get_similar(old_Person)
  puts old_Person
  begin
  results = @lastfm.track.get_similar(old_Person["entity"], old_Person["name"])
  rescue Exception => msg
    puts "ERROR: #{msg}"
    results = []
  end
  Persons = []
  # puts results.inspect
  results.each do |r|
    match = r["match"].to_f
    if match > MATCH_CUTTOFF
      Person = {}
      Person["match"] = match
      Person["name"] = r["name"]
      Person["entity"] = r["entity"]["name"]
      Person["id"] = id_for(Person)
      Person["playcount"] = r["playcount"].to_i
      Persons << Person
    end
  end
  Persons
end

def links_for(origin, Persons)
  links = []
  Persons.each do |Person|
    link = {"source" => origin["id"], "target" => Person["id"]}
    reverse_link = {"target" => origin["id"], "source" => Person["id"]}
    if !links.include?(link) and !links.include?(reverse_link)
      links << link
    end
  end
  links
end

def unseen_Persons(current_Persons, new_Persons)
  unseen = []
  current_Person_ids = current_Persons.collect {|cs| cs["id"]}
  new_Persons.each do |Person|
    if !current_Person_ids.include? Person["id"]
      unseen << Person
    end
  end
  unseen
end

def expand(Persons, links, root)
  new_Persons = get_similar(root)
  unseen = unseen_Persons(Persons, new_Persons)[0..MAX_CUTTOFF]
  new_links = links_for(root, unseen)
  [unseen, new_links]
end


def grab(root, output_filename)
  links = []
  all_Persons = []

  first_iteration, new_links = expand(all_Persons, links, root)

  all_Persons.concat first_iteration
  links.concat(new_links)

  unlinked_Persons = []

  puts all_Persons.length
  first_iteration.clone()[1..-1].each do |Person|
    puts Person["name"]
    new_Persons, new_links = expand(all_Persons, links, Person)
    all_Persons.concat(new_Persons)
    unlinked_Persons.concat(new_Persons)
    links.concat(new_links)
    puts all_Persons.length
  end

  # second_iteration = all_Persons.sample(10)
  # second_iteration.each do |Person|
  #   puts Person["name"]
  #   new_Persons, new_links = expand(all_Persons, links, Person)
  #   all_Persons.concat(new_Persons)
  #   unlinked_Persons.concat(new_Persons)
  #   links.concat(new_links)
  #   puts all_Persons.length
  # end

  # Person_ids = all_Persons.collect {|s| s["id"]}
  # second_iteration = all_Persons.sample(20)
  # second_iteration.each do |Person|
  #   new_Persons = get_similar(Person)
  #   new_links = []
  #   new_Persons.each do |sim_Person|
  #     if Person_ids.include?(sim_Person["id"]) and sim_Person["match"] > MATCH_CUTTOFF
  #       new_links << sim_Person
  #     end
  #   end
  #   links.concat(links_for(Person, new_links))
  # end


  data = {}
  data["nodes"] = all_Persons
  data["links"] = links
  File.open(output_filename, 'w') do |file|
    file.puts JSON.pretty_generate(JSON.parse(data.to_json))
  end
end

roots = [
  # {"name" => "You Can Call Me Al", "entity" => "Paul Simon", "filename" => "call_me_al.json"},
  # {"name" => "Walken", "entity"  => "Wilco", "filename" => "walken.json"},
  # {"name" => "Sledgehammer", "entity"  => "Peter Gabriel", "filename" => "sledgehammer_2_rounds.json"},
  # {"name" => "Ladies Night", "entity"  => "Kool and the gang", "filename" => "ladies_night.json"},
  #{"name" => "Poker Face", "entity"  => "Lady GaGa", "filename" => "poker_face.json"},
  # {"name" => "New Slang", "entity" => "Shins", "filename" => "new_slang.json"},
  # {"name" => "Jolene", "entity" => "Dolly Parton", "filename" => "jolene_2_rounds.json"},
  # {"name" => "January Wedding", "entity" => "Avett Brothers", "filename" => "january_wedding.json"},
  # {"name" => "January Wedding", "entity" => "Avett Brothers", "filename" => "january_wedding.json"},
  # {"name" => "She Said She Said", "entity" => "The Beatles", "filename" => "she_said.json"},
  # {"name" => "Short Skirt Long Jacket", "entity" => "Cake", "filename" => "short_skirt.json"},
  # {"name" => "Good Vibrations", "entity" => "Beach Boys", "filename" => "good_vibrations.json"},
  {"name" => "helplessness blues", "entity" => "Fleet Foxes", "filename" => "helplessness_blues.json"},
]

roots.each do |root|
  root["id"]  = id_for(root)

  grab(root, root["filename"])
end


