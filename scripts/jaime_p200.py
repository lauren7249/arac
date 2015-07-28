import requests
from prime.utils import headers
import json
from prime.prospects.models import PiplEmail, Prospect
from prime.prospects.get_prospect import session, from_linkedin_id, from_url, average_wealth_score
from prime.utils import r
from consume.get_gender import get_firstname, get_gender

pipl = "http://api.pipl.com/search/v3/json/?key=uegvyy86ycyvyxjhhbwsuhj9&pretty=true&email="

jaime = from_linkedin_id("6410262")
email_list = "abby.coufal@gmail.com abilash.jaikumar@tresvista.com adam.yormack@yormackpa.com adavidsburg@gmail.com adelaidemaria.gemsandjewelry@gmail.com adildhalla@gmail.com aek32087@optonline.net agreen724@gmail.com agross26@pride.hofstra.edu akobin@kobinintegratedmarketing.com akraft@appnexus.com alanaeliaskornfeld@gmail.com alexandra@freeandforsale.com alexpavone@gmail.com alieber103@hotmail.com alieberm@stern.nyu.edu Alisaadler@aol.com alixfellman@gmail.com aliyahjacobson@yahoo.com allymarieus@yahoo.com alyssa.blank@gmail.com alyssabfrank@gmail.com am_guillen@hotmail.com amy.wigler@logostaff.com andrew_min@hotmail.com angeline.sandmann@hotmail.com apattick@gmail.com aramisben@gmail.com areading5664@gmail.com arkady.fridman@gmail.com arkady63@hotmail.com artorres9313@gmail.com ashack_973@yahoo.com asheralon@gmail.com ashleyrdinsdale@gmail.com ashleyvitha@gmail.com atuchman@simplicityinfo.net avavolandes@gmail.com babblesheep21@yahoo.com becca.dauer@gmail.com beckiehubertus@gmail.com behravankaveh@gmail.com ben@itvalliance.org bertina.hu@gmail.com bgrieninger@gmail.com bobbyharouni@gmail.com brandon@kognito.com brendonratnercasting@gmail.com brimuldoon84@gmail.com bteagno@gmail.com btodorovic@fordham.edu buchick@alum.bu.edu byronraff@hotmail.com bzagoria@yahoo.com caelynng@gmail.com cam@getnovel.com candace_sue@hotmail.com carlyeconomos@gmail.com caroldg@thecharlesgroupinc.com caroljansen@charter.net caroljansen@yahoo.com casey.pola@gmail.com cassie.orzano@gmail.com cebele.marquez@billboard.com christinecosta1220@gmail.com christophermengland@gmail.com cindychen@alumni.duke.edu cklube@gmail.com clarerams@gmail.com cluong786@gmail.com colbydee@hotmail.com concierge@jeffreylevin.com concierge@jeffreylevin.com croman@gmail.com croman@gmail.com cvance@wework.com cynthiaclaravall@yahoo.com dadamo.linda@gmail.com dana.bobb@gmail.com dana.michaelson@gmail.com dananichols14@gmail.com danielle.yadaie@gmail.com danremin89@gmail.com dave.b.kaplan@gmail.com dave@corporaterentalsinc.com david.b.linden@gmail.com david.broxmeyer@gmail.com davideckstein1@gmail.com deborah@appliedbrilliance.com deckstein.mje@gmail.com deena.barselah@gmail.com deidrewest@gmail.com dino.buro@gmail.com doccohen@comcast.net Dodie.Kent@axa-financial.com doyleanne@hotmail.com duffyceline@yahoo.com dykstra.jesse@yahoo.com eddya92@yahoo.com egan.amelia@gmail.com egellar@ewsnyc.com eidowning@gmail.com eisenbergsteve@hotmail.com ekobzan@gmail.com ekrecko@gmail.com eldandy33@yahoo.com emayers@synthenai.com emily.herzlin@gmail.com emily@thegarrgroup.com emily_fowler@cookiesforkidscancer.org emilyksheahan@gmail.com emilynfowler@gmail.com emilyrforrest@gmail.com erica.kaplan@gmail.com erica.swirsky@gmail.com erica@cookiesforkidscancer.org Erin.Allinger@gmail.com erin@cookiesforkidscancer.org errol.eisner@gmail.com esswired@hotmail.com etrosen@gmail.com fadia@b4belite.com fbgeneralsmike@gmail.com fkamelhar@gmail.com fkoatz@gleasonkoatz.com florence.s.ng@gmail.com flrachael@gmail.com fng@elliman.com fraya@fraya.com fritzkuhnlenz@gmail.com fscille@onwardsearch.com gabrieltajes@gmail.com gb@brulteco.com gbienstocks@gmail.com GHolt@oxo.com gijew8@yahoo.com giranid@verizon.net glevin1118@yahoo.com glrmls25@gmail.com goldhar93@gmail.com grantsilverstein@gmail.com grayson.brulte@gbrulte.com graz.rox@gmail.com gregory.m.ginsburg@gmail.com gregory.rudin@gmail.com grossman.deborah@gmail.com hannah@hanbancan.com happelbaum72@gmail.com helenyee8@verizon.net hillary@hillaryfriedman.com hlaufer@sas.upenn.edu hoffmer99@gmail.com ilene@idesignandco.com info@getkolder.com info@melissasubatchdesign.com info@razkeren.com ishay255@yahoo.com Israel.Michael@gmail.com jalberici@wingsbeersports.com Jamie@birthdaywishes.org jamilm@google.com jasonmadhosingh@gmail.com jeanne.m.haight@gmail.com jeffrey.gershner@gmail.com jeffrey.middleman@gmail.com jenkelly16@gmail.com jennifer_newman1@comcast.net jennyslp823@yahoo.com jenoleniczak@gmail.com jeremiah.kaplan@viahome.com jeremy.zander@gmail.com jessaschwartz76@gmail.com jessehmorris@gmail.com jessturco@gmail.com jgaviria@wework.com jgrogers@bu.edu jhnivin@gmail.com jhuege@yahoo.com jillagoldstein@gmail.com jjnewman220@gmail.com jkaplan1181@gmail.com jkennedy@hsksearch.com jlapointe12@gmail.com jmlingram@gmail.com Jodi@jicny.com jodiheatherlaub@gmail.com joelleaberman@gmail.com John.scaturro@macerich.com jon.reinstein@gmail.com jonathan.t.davis1@gmail.com jongor000@gmail.com joseph.e.sherman@gmail.com Joyce.Keller@morganstanley.com jrodino@nyhrc.com jrosepal@newyorklife.com js@jsgilbert.com jsimons@yoursltd.com jtornoe@cultural-strategies.com jugo031@hotmail.com juliacn@gmail.com julie.christopher@kingarthurflour.com julie.zhang.skev@statefarm.com karandia@gmail.com karenhaberberg@gmail.com karin.zahavi@gmail.com karl.vontz@gmail.com katie@katieweeks.net katzortho@gmail.com kavitasupersadsingh@gmail.com kaynapfeiffer@gmail.com kcross214@yahoo.com keithlevinson@gmail.com kellypeppers@gmail.com kinneretkohn@gmail.com kirsten.saur@gmail.com kirsten.saur@gmail.com knybergh@gmail.com kpogo412@gmail.com KROsoccer@aol.com ktellstory@gmail.com laragoldberg90@gmail.com lars.scofield@alumni.duke.edu laura.swirsky@gmail.com lauramestelschwartz@gmail.com laurenyormack@gmail.com lavish4lifenyc@yahoo.com ldadamo@vnubusinessmedia.com ldmiller@optonline.net ldmiller@optonline.net leahasilver@gmail.com leeh1818@hotmail.com leichtmann_nathalie@hotmail.com lesvasvari@gmail.com lindad68@optonline.net lionelchitty@gmail.com Lisa.m.Cusano@gmail.com Lisa@FamilyAffairDist.com lisa_costa27@yahoo.com lisaann.green@gmail.com lisamechanick@gmail.com liturner227@gmail.com lizwood1982@yahoo.com lkandel988@gmail.com Lpollack208@gmail.com lruimy@gmail.com m.leichtling81@gmail.com madeleine.grace.asplundh@gmail.com marao09@yahoo.com MarcLGreenberg@aol.com margaret_o_shea@hotmail.com mariolawiatrak@yahoo.com Marissa.J.Falkoff.C01@alumni.upenn.edu Marleen.litt@gmail.com marty@eventprosgroup.com maryanncoskery@hotmail.com maryannmacb@yahoo.com matt@streetsmartsmedia.com matt4456@gmail.com mattace8@aol.com mattace8@aol.com matti@aishconnections.com mattlgoldman@gmail.com maxwell.rubin@gmail.com mchen79@binghamton.edu meaches99@aol.com megan.balcarczyk@jjay.cuny.edu meganlevinson@gmail.com megmcdaniel@mac.com megmcdaniel@mac.com melissa.f.rosen@gmail.com melissamadani@gmail.com meredithcroft@hotmail.com mfayer@gmail.com mfox@explorenetwork.org mgain@verizon.net mhatherill@pdnonline.com mheiss@poppin.com mib6unh@gmail.com michaelm_01@yahoo.com.au michele.allison@mac.com michelleleone11@gmail.com mistermaxharris@gmail.com mitchell@golnerassociates.com mjfrankel@gmail.com mkobin@gmail.com mloeb62@yahoo.com mohit.sagar@alphabet-media.com mohitsagar@me.com mojdehmoheban@gmail.com mojdehmoheban@gmail.com mosherothchild@gmail.com mperrino@jpaltd.com mperrino@jpaltd.com mrandrebermudez@gmail.com mslemberg@msn.com msmcapital2@gmail.com myalony@gmail.com nataliealagna@yahoo.co.uk natashadavidhays@gmail.com natashadavidhays@gmail.com nathanyadgar@gmail.com nechama@nekcpa.com ngc219@verizon.net ngc219@verizon.net nickchic29@aol.com Nicole_fiehler@cookiesforkidscancer.org nicolegevents@gmail.com nikki.ziolkowski@gmail.com nsgerber@gmail.com olenickc@gmail.com olomanany@optonline.net ozzybelle@gmail.com paris875@gmail.com paris875@gmail.com parkerslavin@yahoo.com parkerslavin@yahoo.com patti.campion@gmail.com pattyscull@gmail.com pattyscull@gmail.com paulschwartz212@gmail.com polarte@synthenai.com polarte@synthenai.com preshcc@gmail.com pwagner@horanandwagner.com radelson@optonline.net ragini_dass@hotmail.com ramo.rebecca@gmail.com randi_halperin@yahoo.com raphis@salemglobal.com rbchppll@aol.com rebekasmall@hotmail.com renayael@mac.com revlis2x2@aol.com richard.rozo@gmail.com rjgolden@gmail.com rjgolden@gmail.com rlevin@rriny.com rmattei@csa.canon.com rmcdonald@iirusa.com roblevin@msn.com rogerjarman@yahoo.com ron@kognito.com rosa.puerto@yahoo.com rr@conusfund.com rs312@aol.com rtuchman@goviva.com Ruth.Katz@morganstanley.com rwmarie@gmail.com sagerdeveloping@aol.com samantha.erle@gmail.com samsingarora@googlemail.com sarahjalbert@gmail.com Sarahvaracalli@gmail.com sarardavidson@gmail.com sconning@hotmail.com scott@snowberrygroup.com sean@seaninireland.com sean@seaninireland.com seato83@gmail.com selegnacra@yahoo.com seri@littlemisspartyplanner.com seth.weisleder@gmail.com seth.weisleder@gmail.com shane.wicks@gmail.com sharon@triumph-staffing.com shawna@rosengrouppr.com shhirth@shhirthassoc.com shhirth@shhirthassoc.com shininglory27@yahoo.com shlomitlevy30@gmail.com sjheinz04@yahoo.com sm121881@aol.com smarcus@newyorklife.com smorris@coach.com smulrich1@gmail.com sodar@mba2008.hbs.edu sofiagaladza@gmail.com sofiagaladza@gmail.com sontzu411@gmail.com southbrooklyn@gmail.com ssteiman@steimanlaw.com stacey.russell@nielsen.com stacy@chadickellig.com stacyjmalin@gmail.com stacyjmalin@gmail.com steve@sieratzkilaw.com steve_jaffee@hotmail.com steven.schwartz@corpsyn.com superjessa@msn.com Susan_Marcus@newyorklife.com susand@thecharlesgroupinc.com suzie.m.schwartz@gmail.com tanner.mcauley@gmail.com tburke2@pride.hofstra.edu tjn2117@columbia.edu tnargozian@gmail.com tnuge@bu.edu tomdelpizzo@gmail.com tstreet8@gmail.com uncleharry67@aol.com vanness.derick@gmail.com victor@misterpromotion.com vkalman@ft.newyorklife.com vkbeall@gmail.com wendy.paler@gmail.com whitneykirkland@outlook.com williemoree@yahoo.com wwinter@gmail.com wynson.ng@gmail.com x.cindytran.x@gmail.com yanivlei@hotmail.com Yeeassoc@aol.com ymsabir@gmail.com yourowncfo@aol.com yvonnechao@gmail.com zilzproductions@icloud.com designstation@gmail.com info@glasslessmirror.com adamklipper@voicesagainstbraincancer.org alisa@greentoys.com msqwellness@gmail.com allison@glopandglam.com angela@selectofficesuites.com areichenberger@4imprint.com anna@puppetree.com annette@putumayo.com annie@mandarintreehouse.org annie@supersoccerstars.com akolodner@aol.com ashleigh@niceshirtbaby.com info@magformersworld.com audrarox@earthlink.net BaballoonNyc@aol.com barb@graphicice.com bmendoza@branders.com bmccall@elenis.com Bianca@SuperSoccerStars.com bbaron@discountschoolsupply.com BBeasley@hohnerusa.com blair@blairwear.com bob.c@funtastictoy.com bret@gearedforimagination.com brian@parentplay.com shorelinesoffice@yahoo.com bls292@aol.com chadiw@gmail.com chelsea.moreno@mslworldwide.com Cperrone@upsilonventures.com sales@plantoysinc.com cgreen@rocketdognyc.com coricohen@mac.com info@helium.net Dan@biggreenie.com dana@awisco.net dmaharba@gmail.com DTousignant@uline.com dave@thinkbigpromos.com dave@wabafun.com David@nycphotobooth.com david@printny.net davitte@dtvproductions.com dkennedy@AlexToys.com drexel@putumayo.com gshibley@rinovelty.com hwinters@studio-on-hudson.com heidi@heidigreen.com herb@promowearhouse.com jtravis@nyhrc.com jackiem@dallisbroscoffee.com Jamie@birthdaywishes.org jeff@balloonsaloon.com jeff4toys@hotmail.com jeffgarb@repgroup.com JSilverstein@TheAdvanceGRP.com jthomas@thebabytimes.com sales@jonesawards.com orders@digginactive.com jeremiah@upspringbaby.com jessi@tastebudscook.com jessica@AClassActNY.com jill@balloonkingsny.com ToyguyJames@aol.com johnwalsh@dmcwater.com sales@abracadabrazoo.com kari@littleadventures.com staff@modernseed.com krisoconnor@littlekidsinc.com Kristen.LaFond@timepaymentcorp.com LKoster@uline.com lloo@wayfair.com lisak@pepperspollywogs.com MCORNEJO@PAPERMART.COM mrake@learningresources.com melisa.schulman@barefootbooks.com MAloisio@upsilonventures.com MDachsent@aol.com mchanin@drinkwatermatic.com MHerinean@tumbadorchocolate.com mwinters@adtenna.com NancyRockford@Applepark.com lajacksondds@aol.com nhill@littlekidsinc.com pfrink@rinovelty.com pena.reneeeva@gmail.com rgarcia@rocketdognyc.com ruth@resilite.com samira@shoptwoowls.com sassiactress@yahoo.com todd@balloonshow.com todd@printny.net Topher.McGibbon@KidCarNY.com tmccrory@bendonpub.com artfarmnyc@gmail.com viki@plumorganics.com yolanda@yolipoli.com aaronshort@me.com abby.coufal@gmail.com alishasoper@gmail.com aqberna@appleseedsplay.com aschlanger@appleseedsplay.com allisondobyns@gmail.com alyssaraefulmer@gmail.com amanda.soled@gmail.com agheckm@gmail.com amber.toye@yahoo.com asalaam@stanfordalumni.org amy.beckerman@gmail.com bastidas@icsny.org areyes2300@gmail.com annemarievantricht@verizon.net ans.delong@gmail.com ayou@versaprints.com satta42@gmail.com asheralon@gmail.com asherreedominguez8@gmail.com arnoa505@newschool.edu ajeisenstadt@gmail.com ashtonevans2010@gmail.com bertina.hu@gmail.com rberna@appleseedsplay.com bwaring@rebeccaschool.org bradbrockman@gmail.com bcm269@nyu.edu carinesaint_jean@yahoo.com carole@carolescuts.com sales@bskinz.com cassidy.hooker@gmail.com cassie.orzano@gmail.com seezama@aol.com dmataylor@live.com guitarjohnny72@hotmail.com hamiltonc@tiffin.edu cindytran@fitnyc.edu chmcginley@comcast.net cschlanger@appleseedsplay.com griffithbooking@gmail.com dana.bobb@gmail.com dmart630@gmail.com dashkenazy24@gmail.com selegnacra@yahoo.com clown.yoga@gmail.com dmccloskey1@yahoo.com dorispang10.2@gmail.com dgcjlm@gmail.com elissafutt@gmail.com noni.c.culotta@gmail.com ELLEN_HUNTER@fitnyc.edu emily_lambert@me.com emw312@nyu.edu egilerman@gmail.com eugenedmngz@yahoo.com enachmusic@gmail.com gzeit9@gmail.com GerardCanonico@gmail.com gillian@nysee.com hellyschtevie@gmail.com hudsonmueller@gmail.com isabelle.arditi@lombardrisk.com  jaquan_garcia@yahoo.com jarrett_mcgirt7@yahoo.com njeffg@gmail.com theatrejeno@hotmail.com jstrausser@appleseedsplay.com jhurley@manhattanmedia.com jolinemujica@gmail.com shwahtoyou@hotmail.com dicterow@gmail.com kuhrinuh@gmail.com katharinediehl91@gmail.com kathleen.shea87@gmail.com sakata11226@yahoo.com katie11792@gmail.com katiefromkansas@hotmail.com katie.proulx@gmail.com Kindel136@yahoo.com, klewis2@nybloodcenter.org coachkris@bestversioncoaching.com laralorenzana@gmail.com laura.a.riley@gmail.com laura_hawthorne2004@yahoo.com leland.rad1989@gmail.com lianastampur@gmail.com lillian4289@gmail.com lkozinn@yahoo.com toothdoc20@yahoo.com lyss@divalyssciousmoms.com marianbrock@gmail.com marilyngupta75@gmail.com mvaskevich8@gmail.com medcannon@nyc.rr.com mattytee@gmail.com megansarak@gmail.com bellingermel@aol.com archangel_181@yahoo.com msinenskeee@aol.com michaelgomez325@gmail.com meaches99@aol.com nicknick5f@yahoo.com ngoodri@gmail.com njjanisch@gmail.com lajacksondds@aol.com otis.wash@yahoo.com pattyscull@gmail.com paulajaak@hotmail.com paulakjaakkola@gmail.com rroberge30@yahoo.com zenekramirez@gmail.com robertmotero@gmail.com rgolden@tsfexhibit.com rdejak@gmail.com samluddy@gmail.com lilgymnast333@comcast.net serotherm@aol.com sarahgraceholcomb@gmail.com seanswan@yahoo.com la_quimba@hotmail.com s.kolder@hotmail.com shauna.axelrod@gmail.com shylah.chiera@gmail.com sophieroselaird@gmail.com music.soyoung@gmail.com swpurcell@gmail.com stormyperez@gmail.com tstreet8@gmail.com franken@post.harvard.edu reddot522@yahoo.com tpizzo04@hotmail.com u22hall@hotmail.com veronica@holaplaygroup.com bhankrose@gmail.com nycicecream@gmail.com adamk@libertypaperjanitorial.com al@magic-al.com ANarins@MelissaAndDoug.Com andrew@mirrorimaging.net AUihlein@uline.com ayou@versaprints.com avitha@madisonsquarepark.org ben@oasisCD.com mr.bbrede@gmail.com brothenhaus@nyc.rr.com cpascucci@prestigeemployee.com chw321@gmail.com kikiscott@gmail.com info@diabeticfriendly.com dcoady@optonline.net dbaia@mirrornyc.com carol@repgroup.com dougw@magnatag.com esarson@ginsey.com elvin.santos@intplay.com info@idesignandco.com BestEntAround@aol.com joanieleeds@gmail.com klombardo@libertyoffice.com kimberlyh@rainbowballoons.com contactus@familyaffairdist.com wondermax@gmail.com michael@lovesac.com MDachsent@aol.com mchanin@drinkwatermatic.com nan@wabafun.com nicole@prestigeemployee.com ptversky@aol.com pkrep@comcast.net rick@naturalgfoods.com juniorsrentals@optonline.net ruth@resilite.com sarah@dmcwater.com sarah@sarahmerians.com victor@misterpromotion.com ybarra@discountschoolsupply.com bigapplewelding@gmail.com wmichal@prestigeemployee.com Thomas.Au@verizonwireless.com zarah@stevespangler.com".split(" ")

jaime_json = jaime.json

#696
jaime_json["email_contacts"] = email_list
session.query(Prospect).filter_by(id=jaime.id).update({"json": jaime_json})
session.commit()

#343 profiles
#318 unique pipl linkedin profiles
for email in jaime.email_contacts:
	if session.query(PiplEmail).get(email) is None:
		req = pipl + email
		response = requests.get(req, headers=headers, verify=False)
		if response.status_code == 200:
			pipl_json = json.loads(response.content)
			linkedin_url = None
			for record in pipl_json.get("records"):
				if record.get('@query_params_match') and not record.get("source").get("@is_sponsored") and record.get("source").get("domain") == "linkedin.com":
					linkedin_url = record.get("source").get("url")
					r.sadd("urls",linkedin_url) #for scraper
					break
			piplrecord = PiplEmail(email=email, linkedin_url=linkedin_url, pipl_response=pipl_json)
			session.add(piplrecord)
			session.commit()

jaime_friends = set()
pipl_recs =0
friend_recs=0
rescrape = set()
for email in jaime.email_contacts:
	pipl_rec = session.query(PiplEmail).get(email)
	if pipl_rec: 
		pipl_recs+=1
		linkedin_url = pipl_rec.linkedin_url
		friend = from_url(linkedin_url)
		if friend: 
			jaime_friends.add(friend.linkedin_id)
			friend_recs+=1
		else:
			rescrape.add(linkedin_url)

boosted_ids = []
for friend in jaime_friends:
    if friend>1: boosted_ids.append(str(friend))

jaime_json["boosted_ids"] = boosted_ids
session.query(Prospect).filter_by(id=jaime.id).update({"json": jaime_json})
session.commit()

#263 scraped and id'd. average wealth score: 64
prospects = []
for friend in jaime.json.get("boosted_ids"):
	prospect = from_linkedin_id(friend)
	prospects.append(prospect)


#195 NY friends
#161 employed 
#152 not in financial services
#average wealth score 63
new_york_employed = []
states = {}
for prospect in prospects:
	if prospect.current_job is None: continue
    key = prospect.location_raw.split(",")[-1].strip()
    if key in ['New York','Greater New York City Area'] and prospect.industry_raw not in ['Insurance','Financial Services']: new_york_employed.append(prospect)
	count = states.get(key) 
	if count is None: count = 0
	count += 1
	states[key] = count    

#nothing really stands out here
industries = {}
for prospect in new_york_employed:
    industry = prospect.industry_raw
    count = industries.get(industry) 
    if count is None: count = 0
    count += 1
    industries[industry] = count
print sorted(industries, key=industries.get, reverse=True)


industries = {}
for prospect in new_york_employed:
    industry = prospect.industry_raw
    count = industries.get(industry) 
    if count is None: count = 0
    count += 1
    industries[industry] = count

#{None: 14, 'Female': 87, 'Male': 51}
genders = {}
for prospect in new_york_employed:
    gender = get_gender(get_firstname(prospect.name))
    if gender==True: gender = 'Male'
	if gender==False: gender = 'Female' 
    count = genders.get(gender) 
    if count is None: count = 0
    count += 1
    genders[gender] = count

skills = {}
for prospect in new_york_employed:
	if not prospect.json: continue
	pskills = prospect.json.get("skills")
	for skill in pskills:
		count = skills.get(skill) 
		if count is None: count = 0
		count += 1
		skills[skill] = count
for skill in skills.keys():
    if skills[skill]>15: print skill + ": " + str(skills[skill])

#6 people -- all financial services and not local
#u = search_extended_network(jaime, limit=300)

#extended_network = {}
for prospect in new_york_employed:
	if extended_network.get(prospect.url) is None:
		u = search_extended_network(prospect, limit=300)
		extended_network.update({prospect.url: u})

#94 with college. wealth 62

noschool = 0
for prospect in new_york_employed:
	valid_school = False
    for education in prospect.schools:
    	if education.school_linkedin_id: valid_school = True
    if not valid_school: print prospect.url

    d = {"id":prospect.id, "name":prospect.name, "job":prospect.current_job.title, "company":prospect.current_job.company.name, "score":1}

