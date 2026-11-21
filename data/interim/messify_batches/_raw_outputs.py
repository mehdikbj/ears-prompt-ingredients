import json

RAW = {}

RAW["clarus_low"] = r'''[{"id": "PURE-001", "messified_text": "So with Clarus, I really want us to think hard about cutting down those delays, whatever's slowing stuff up — the design needs to figure out a smart way to shrink that lag so data actually moves through the system quick enough, you know, without everything backing up."}, {"id": "PURE-002", "messified_text": "For the CAUI thing, whoever's got admin rights should be able to go in and manage all the info about contributors — like their details and whatnot, just so someone can keep that stuff organized and up to date."}, {"id": "PURE-003", "messified_text": "Oh, and the Clarus system, it needs to be able to pull in observations about road surface conditions — pavement stuff, basically, whatever's going on with the roads — so we've got that data coming in."}, {"id": "PURE-004", "messified_text": "Also, Clarus should be able to take in data, but it's gotta come through that standard interface we set up for it — not just any random way, it needs to go through the proper channel we built."}, {"id": "PURE-005", "messified_text": "The EMC, I think, needs to keep track of contact details for pretty much everyone involved — each contributor, each collector, and every station sensor out there — so we always know who to reach if something comes up."}, {"id": "PURE-006", "messified_text": "On the QEDC side, when you add up everything across all the Clarus hosts we've got running, it needs to be able to handle somewhere around — well, the engineers will know what I mean about the exact number — 470 million observations that are current at once."}, {"id": "PURE-007", "messified_text": "I want people to be able to go in and set up a request for a data subscription — like, however they want to sign up to get certain data — the system should just let them create that themselves."}, {"id": "PURE-008", "messified_text": "And the SS thing, it should be able to kick off a QEDS response on its own when needed — I'm not exactly sure of all the technical ins and outs, but it needs to be able to trigger that response."}]'''

RAW["eirene_fun_7"] = r'''[{"id": "PURE-009", "messified_text": "Oh, for the network side, we need it to handle at least a decent minimum data rate — like, don't go below 2.4 kbit/s or whatever, that's the floor we can't dip under."}, {"id": "PURE-010", "messified_text": "So during a call, whoever's leading the group should be able to just kick someone out of it whenever they want, doesn't matter what point they're at in the call, they just need that option available."}, {"id": "PURE-011", "messified_text": "And if someone's put a call on hold, they should be able to jump back into it whenever, like there shouldn't be some window where they're locked out of getting back in."}, {"id": "PURE-012", "messified_text": "For that emergency priority thing we talked about earlier in the doc, it needs to hook up automatically to a specific bunch of receiving mobiles and whoever's controlling things, like a set list that's already figured out ahead of time."}, {"id": "PURE-013", "messified_text": "When that driver safety thing gets triggered, it should just automatically make the cab radio fire off a data message on its own, nobody should have to do anything extra to make that happen."}, {"id": "PURE-014", "messified_text": "When a call's coming in, we want just a quick little heads up — like a short beep and something flashing on screen — nothing long or annoying, just enough so they notice."}, {"id": "PURE-015", "messified_text": "There should be some kind of alarm, both a sound and something you can see, that kicks in when the battery's getting low enough that you'd only get roughly 10 more minutes of a proper two-way call out of it."}, {"id": "PURE-016", "messified_text": "Oh, and if someone's on a network that doesn't actually have EIRENE, they need some way to know — like, something on the screen so they're not just sitting there wondering if it's working."}]'''

RAW["ertms"] = r'''[
  {"id": "PURE-017", "messified_text": "So the ETCS side of things, I just need it to keep the driver in the loop enough that they can actually drive the train safely — like, give them whatever info they need to make good calls up there. Doesn't have to be fancy, just useful and safe."},
  {"id": "PURE-018", "messified_text": "Oh, and the driver's screen thing, it should show whether the self-check passed or not — I don't want the driver left guessing whether everything's actually working before they head out."},
  {"id": "PURE-019", "messified_text": "When the driver picks the option to leave shunting mode, that should just... happen right then, that's the whole trigger for getting out of it, nothing more complicated needed there."},
  {"id": "PURE-020", "messified_text": "If the train's already stopped and there's an emergency brake situation going on, the driver should be able to clear that themselves — like, undo it once they're safely at a standstill, not stuck waiting on something else."},
  {"id": "PURE-021", "messified_text": "Whatever letters and symbols the thing uses, it needs to handle more than just one language — I don't want it breaking or looking weird just because someone's typing in something other than English."},
  {"id": "PURE-022", "messified_text": "And if the train just can't physically pull up at wherever the new stopping point got set to, don't let it accept that change — just tell it no and stick with whatever the old stopping spot was."}
]'''

RAW["fishing"] = r'''[
  {"id": "PURE-023", "messified_text": "So the product profile thing, that's basically a questionnaire, and whoever's supplying the ELSS needs to fill it out — it should cover what features are required, what's optional, and what only applies sometimes, so we know what their product actually does."},
  {"id": "PURE-024", "messified_text": "The system needs some screens where people can actually type in all that logbook, transhipment, and landing declaration info — the stuff that eventually has to get sent off to the UK fisheries people's ERS system, whatever that setup's called."},
  {"id": "PURE-025", "messified_text": "For the subject line on these things, it needs to start with 'ERS –' and then just tack on whatever that GBRRN number is from the logbook data being sent — the engineers will know exactly what format that number takes."},
  {"id": "PURE-026", "messified_text": "Oh, one more thing — whenever something gets deleted, it should be pretty obvious when you're looking at the screen, like you shouldn't have to go hunting to figure out that something was removed."},
  {"id": "PURE-027", "messified_text": "Every installed copy of the thing needs its own kind of unique ID number, something internal I guess, and it should just automatically pop into every message that goes out so we can tell which installation actually sent the report."},
  {"id": "PURE-028", "messified_text": "Also if the vessel's master changes partway through a trip, that needs to get flagged in whatever the next LOG message is — can't just let it slide by unmentioned."}
]'''

RAW["gemini"] = r'''[
  {"id": "PURE-029", "messified_text": "Oh also, whatever the monitor person is typing on their keyboard, that shouldn't leak into or mess with the observer's side of things at all — like it should just stay completely separate, no crossover, no weird side effects on their setup."},
  {"id": "PURE-030", "messified_text": "And one more thing, whatever weather data is coming off that station out there, I'd want that piped into one central spot everybody can check, instead of it just sitting off on its own somewhere nobody can get to."},
  {"id": "PURE-031", "messified_text": "Yeah, and ideally you shouldn't have to care which machine or location it's actually running from — like it just works the same no matter where it's sitting on the network, totally invisible to whoever's using it."},
  {"id": "PURE-032", "messified_text": "So basically all the really important stuff — aside from the remote observing part — needs to run on gear that's actually ours, stuff we control, like those leased line connections, not just whatever random outside resource happens to be around."},
  {"id": "PURE-033", "messified_text": "One way or another, whenever someone's running things remotely, they need to be able to keep an eye on stuff from the Gemini base facilities too, plus have some kind of tools handy for poking around and testing when something needs checking out."},
  {"id": "PURE-034", "messified_text": "I guess every subsystem, while it's up and doing its thing, ought to have something quietly running in the background keeping tabs on it — you know, power levels, temps, how it's performing, whether it's actually responding right when you send it commands."},
  {"id": "PURE-035", "messified_text": "And realistically, to make that safe you're gonna need a whole stack of safeguards — physical stoppers, some electrical interlocks, hard and soft limit switches, limits baked into the software, plus watchdog stuff keeping an eye on it all."},
  {"id": "PURE-036", "messified_text": "Also for the database, people need to be able to get at it remotely, and the data itself should be spread out across places rather than sitting in just one location."}
]'''

RAW["inventory_2_0"] = r'''[
  {"id": "PURE-037", "messified_text": "Oh, also that Unique Tag thing — it can't be super long, keep it pretty short, like no more than 18 characters or so, otherwise it'll probably break something downstream."},
  {"id": "PURE-038", "messified_text": "One thing that's important — the name we give an item in the details, that can't repeat anywhere else in the whole inventory. Every one needs to be its own distinct thing, no duplicates floating around."},
  {"id": "PURE-039", "messified_text": "And yeah, if somebody picks that 'Other' option for the reason, we probably want to make them type in a little note explaining what they actually mean, otherwise 'Other' doesn't tell us anything useful."},
  {"id": "PURE-040", "messified_text": "Whatever info originally came over from the CRM about how the item was acquired, that needs to just stay as-is — we shouldn't be letting whatever gets typed in here stomp on it and replace it."},
  {"id": "PURE-041", "messified_text": "When someone sets a sale price, that shouldn't mess with or replace the original price we've got on file for the item in inventory — those two things need to stay separate."},
  {"id": "PURE-042", "messified_text": "I guess we just need the thing to be up and running whenever Construction Junction is actually open for business — like during their regular hours, it should just work, no downtime."},
  {"id": "PURE-043", "messified_text": "For the staff over at Construction Junction, they shouldn't be able to just open up the app and start using it — they need to log in first, like some kind of check that it's actually them."},
  {"id": "PURE-044", "messified_text": "Same deal but for departments — whatever unique tag gets assigned to a department, that can't be reused anywhere else in the inventory, needs to be one-of-a-kind across the board."}
]'''

RAW["keepass"] = r'''[
  {"id": "PURE-045", "messified_text": "Oh yeah, before anything else can happen, someone's gotta actually grab KeePass and get it set up on their machine — it's not doing anybody any good just sitting as a download link somewhere, it needs to be properly installed first."},
  {"id": "PURE-046", "messified_text": "Quick thing on the databases — if two of them end up with the same name, that preview panel gets weird and just swaps out, replacing whichever one was showing. So yeah, give each one its own distinct name so you don't lose track of which preview's which."},
  {"id": "PURE-047", "messified_text": "For the printing thing, I guess it's kind of obvious, but you can't really print anything out of a database that's empty — there's gotta be at least a few entries actually sitting in there before that printing option even makes any sense to use."},
  {"id": "PURE-048", "messified_text": "Oh, and when someone's making a new entry, it can't just float around on its own — it needs to be tucked under some group, otherwise the whole thing doesn't really make sense to create in the first place."},
  {"id": "PURE-049", "messified_text": "So if someone types something into the password box, yeah, they should probably have to fill in that repeat-password box too — just so we're not letting people set a password without confirming it a second time."},
  {"id": "PURE-050", "messified_text": "Also, that auto-type sequence thing — keep it to one line, nothing crazy long, so like under 60 characters or so."},
  {"id": "PURE-051", "messified_text": "Oh, one more thing — if the file path's got a space in it anywhere, you'll want to wrap the whole thing in quotes, otherwise it tends to get chopped up wrong when it's being read."},
  {"id": "PURE-052", "messified_text": "And if someone's using that combined key setup, they're gonna need both pieces — the master password and the key file — you can't get away with just one or the other in that case."}
]'''

RAW["nasa_x38"] = r'''[
  {"id": "PURE-053", "messified_text": "So for the scheduling piece, I think it needs to handle a handful of rate groups per vehicle mode — three feels like plenty, that's the ceiling we'd want it to work with, don't need more than that realistically."},
  {"id": "PURE-054", "messified_text": "Whatever it's doing for the scheduler and that Time Services overhead stuff in each rate group, it needs to be quick — like, done within a millisecond, tops, so it's not eating into everything else's time."},
  {"id": "PURE-055", "messified_text": "For those instant message-passing things going between the virtual groups, from one processor over to the other, I'd only want that limited to whatever's running in the top-priority rate group on the FCP side — nowhere else should get to use it."},
  {"id": "PURE-056", "messified_text": "Oh, and if the power-up checks or that initial built-in test stuff fails on a processor, it shouldn't just stop dead — the fault-tolerant setup needs to keep that processor going anyway and not give up."},
  {"id": "PURE-057", "messified_text": "When the memory-scrubbing thing finds a problem, it needs to let the application know about it, matching across all the channels the same way, going through some kind of service call so it ends up in the telemetry data too."},
  {"id": "PURE-058", "messified_text": "The fault-tolerant API thing needs some kind of map laid out that shows where the lines are — like which memory's lined up and shared the same way, which shared memory's already set up at start, and which bits are just separate and don't match across channels."},
  {"id": "PURE-059", "messified_text": "Basically whenever something goes wrong, I want the support side to try and find a path between the two processor types that's actually working, hopping between channels back and forth if it has to, in pretty much any failure situation."},
  {"id": "PURE-060", "messified_text": "Also, that fault-tolerant software should be able to hand over a decent chunk of start-up info — up to 600 bits worth — just showing what state the whole triple system was in while it was booting."},
  {"id": "PURE-061", "messified_text": "The whole fault-tolerant setup needs to be able to boot and keep running even if only three out of the five processing lanes are actually alive, no matter which three of the five they are."},
  {"id": "PURE-062", "messified_text": "There's also that timeout limit tied to the clock — it needs to land right at 327.68 microseconds, which comes from 256 of those clock ticks where each one's 1.28 microseconds. I know that's oddly specific but that's the number the engineers need."}
]'''

RAW["nde"] = r'''[
  {"id": "PURE-063", "messified_text": "Oh, also, when things get rough resource-wise, we need some kind of backup mode where it keeps chugging along but just picks a handful of the most important outputs to make, based on whatever priority makes sense and however much juice it's actually got left to work with."},
  {"id": "PURE-064", "messified_text": "And obviously the whole thing needs to actually be able to make the data products in the first place, that's kind of the whole point, so yeah, it should be able to churn those out."},
  {"id": "PURE-065", "messified_text": "One more thing, once we've got those data products, it should be able to convert them over into that GRIB2 format, I think that's what the downstream folks need to read them properly."},
  {"id": "PURE-066", "messified_text": "It'd be nice if whoever signed up for updates could get pinged when something changes with how the whole thing's running, like some kind of heads-up about its status."},
  {"id": "PURE-067", "messified_text": "If some data product goes missing or gets garbled, I want it to just go ahead and ask the IDPS folks to resend it on its own, without someone having to notice and manually request that."},
  {"id": "PURE-068", "messified_text": "We also need it to just run stuff on its own schedule, like set it up once and it kicks off tasks whenever they're supposed to happen, no one babysitting it."},
  {"id": "PURE-069", "messified_text": "When we roll out some kind of tech refresh or upgrade down the line, it shouldn't have to go offline for that, everything just keeps running while we swap things in."},
  {"id": "PURE-070", "messified_text": "And if a drive dies or something else hardware-wise goes sideways, the NDE data needs to stay intact, we can't have it getting corrupted just because a disk decided to fail on us."}
]'''

RAW["npac"] = r'''[
  {"id": "PURE-071", "messified_text": "So, quick one on passwords — whatever we're storing needs to be encrypted, and honestly only folks who are actually authorized should be able to even look at them. Nobody else should have a way in, if that makes sense."},
  {"id": "PURE-072", "messified_text": "For the Service Provider side, when they're adding in their NPA-NXX info, I want them to be able to pick basically any effective date — could be something from before, right now, or way down the line, doesn't matter which."},
  {"id": "PURE-073", "messified_text": "We also need some kind of written-down process for backing up the data, like actual steps someone can follow, not just tribal knowledge sitting in someone's head."},
  {"id": "PURE-074", "messified_text": "I'd like our folks to be able to pull up every subscription version tied to a given NPA-NXX, just so they can see the whole picture in one shot."},
  {"id": "PURE-075", "messified_text": "Oh, and on the monitoring side — if the security thresholds get crossed, the system needs to ping our people right away through that SNMP thing, no delay, so nobody's caught off guard."},
  {"id": "PURE-076", "messified_text": "We need some way to control who can even log in, especially for the higher-access folks, and it should work per port or connection point — something we can configure however makes sense for us."},
  {"id": "PURE-077", "messified_text": "Same deal but for software this time — we need documented steps for backing that up too, written down somewhere real, not just in someone's head."},
  {"id": "PURE-078", "messified_text": "For that long business day setting, the tunable one, let's just have it default to 12 hours right out of the box, unless someone goes in and changes it."},
  {"id": "PURE-079", "messified_text": "The admin person should be able to go in and tweak that LSMS retry interval setting whenever they need to — basically just give them the ability to change it themselves."},
  {"id": "PURE-080", "messified_text": "And for the short conflict resolution thing, the one about new service providers, let's default that to 6 business hours unless somebody decides to change it later."},
  {"id": "PURE-081", "messified_text": "We need the database extract files sitting out on our FTP spot so the Local SMS side can just grab them whenever they need to pull data down."},
  {"id": "PURE-082", "messified_text": "When that indicator's flipped on, I want the NPA-NXX and LRN data to come down automatically, either through the Local SMS connection or the SOA one, whichever's actually set up."},
  {"id": "PURE-083", "messified_text": "For that report we talked about — the one from RR9-16 — sort it by the new provider's ID first, then by the phone number after that, so it's easy to scan."}
]'''

RAW["peering"] = r'''[
  {
    "id": "PURE-084",
    "messified_text": "So for the service info stuff, we need to nail down how that's actually laid out — like, whatever format we send it in should be spelled out somewhere clear, not just whatever comes to mind on the day, so everyone's building against the same thing."
  },
  {
    "id": "PURE-085",
    "messified_text": "Oh, and the back-and-forth between the web server thing and that mediator piece — someone needs to spell out exactly how those two talk to each other, like what gets sent, in what order, all that, so it's not left up in the air."
  },
  {
    "id": "PURE-086",
    "messified_text": "If something sketchy comes in trying to mess with us, the system should notice and just turn it away — I don't need every detail on how, just that shady requests get caught and shut down before they cause trouble."
  },
  {
    "id": "PURE-087",
    "messified_text": "We also need the conversations between the mediator and the other bits — the SR one, the PR one, and the PA one — all mapped out so it's clear who says what to whom and in what order, not just improvised."
  },
  {
    "id": "PURE-088",
    "messified_text": "And for the PAs talking amongst themselves, we should figure out and write down however they're supposed to communicate with each other, so it's not a mystery every time two of them need to interact."
  },
  {
    "id": "PURE-089",
    "messified_text": "Once we've picked which CDN peers we're going with, they need to actually sit down, so to speak, and hash out some kind of agreement between themselves before anything real starts happening."
  }
]'''

RAW["peppol"] = r'''[
  {"id": "PURE-090", "messified_text": "So whatever pilot each country builds under that WP2 part of PEPPOL, it needs to stick to the mapping thing we sketched out in stage one — the pre-VCD one — otherwise it just won't line up with everyone else's."},
  {"id": "PURE-091", "messified_text": "That simple VCD package from stage two, it's basically the foundation everything else — the VCD creation and those later services in stages three and four — builds on, so every country involved really needs to get those core stage-two ideas up and running, not just some of them."},
  {"id": "PURE-092", "messified_text": "Whatever classification stuff we're using — for goods, services, code lists, all that — it'd be good if that was out in the open somewhere, like publicly visible, and tagged clearly inside the actual documents so people know what they're looking at."},
  {"id": "PURE-093", "messified_text": "Whoever's running the tender, I think they should pick out just the bits of evidence that actually matter for that particular call, rather than dumping the whole giant list of possible evidence on people every time."},
  {"id": "PURE-094", "messified_text": "Also, someone needs to actually go through whatever data protection rules apply in each country and think it through properly, not just skim it — that has to happen before we go further."},
  {"id": "PURE-095", "messified_text": "We also need to nail down some kind of process for how documents get handled that actually lines up with the legal side of things — especially all that data protection stuff, that's the big one to get right."},
  {"id": "PURE-096", "messified_text": "Whoever's taking part in this, we need a way to tell them apart from everyone else — like, each person or organization involved should have their own distinct identity, no mixing anyone up or having duplicates floating around."},
  {"id": "PURE-097", "messified_text": "The whole PEPPOL setup needs to actually be able to send a VCD over to whoever's running the tender — the contracting authority or whatever platform they're using — that sending part has to just work."}
]'''

RAW["phin"] = r'''[
  {"id": "PURE-098", "messified_text": "Oh, one more thing — we really need some kind of backup plan for keeping stuff running when whatever's supporting our outbreak tracking work goes down. Like, if the systems are out, people still need to know what to do next instead of just stopping cold."},
  {"id": "PURE-099", "messified_text": "For the outbreak management side, I'd like the wording it uses to actually match whatever field we're working in — you know, terms that make sense for that specific area — and ideally we could tweak that vocabulary ourselves instead of being stuck with generic labels."},
  {"id": "PURE-100", "messified_text": "When we're logging an animal as part of one of these investigations, I think we should also grab some kind of ID for that particular subject — just so we can tell them apart later, not a huge deal but it'd help."},
  {"id": "PURE-101", "messified_text": "So when someone's got a trip with multiple legs, I want us to capture the details for each individual leg, but also keep the bigger picture info about the overall trip itself — basically both levels, not just one or the other."},
  {"id": "PURE-102", "messified_text": "Whatever's running the outbreak management stuff needs to be flexible enough to grab all sorts of one-off details depending on what's actually happening with a given case — like, the data fields kind of change based on the event, so it can't be locked into some rigid form."},
  {"id": "PURE-103", "messified_text": "We also need a way to actually manage those investigation questionnaires — like being able to set them up however we want and then track changes to them over time, since they'll probably need tweaking as things evolve."},
  {"id": "PURE-104", "messified_text": "When we're linking a person's record to the epi data, it needs to pull together everything tied to them — their symptoms, whatever survey answers they gave, any samples that got taken, the lab results, and whatever treatment or preventive stuff they got. All of it connected, not scattered."},
  {"id": "PURE-105", "messified_text": "For tracing who's been exposed to who, the setup needs to handle it both ways — one contact could end up tied to a bunch of different cases, and on the flip side, a single case might have a whole bunch of contacts linked to it too."}
]'''

RAW["pontis"] = r'''[{"id": "PURE-106", "messified_text": "So one thing I want is to be able to hop between the different preset structure lists we've got — like flip from one saved list to another without a hassle, whichever ones are already set up, so I'm not stuck looking at just one at a time."}, {"id": "PURE-107", "messified_text": "Also, when I'm setting up a brand new structure, I'd love if I could just grab an existing one and copy everything over from it, all the details, so I'm not starting from scratch every single time — just clone it and tweak from there."}, {"id": "PURE-108", "messified_text": "When someone's kicking off a new inspection, it'd be nice if they had the choice to just pull over the notes from the last one instead of retyping everything — like a copy option, not forced, just there if they want it."}, {"id": "PURE-109", "messified_text": "If someone's got the right access, they should be able to remove an inspection that's already in the system — unless, I guess, it's been locked down somehow, in which case just leave that one alone, don't touch it."}, {"id": "PURE-110", "messified_text": "Oh and when those fields that ratings depend on get changed, the thing ought to notice and give a heads-up, then let whoever's using it decide if they want to redo the ratings or just leave them as they are."}, {"id": "PURE-111", "messified_text": "I also want to be able to tweak the technical settings behind the simulation — stuff like the numbers driving the improvement model and however the simulation rules are set, just give me the ability to adjust those knobs myself."}, {"id": "PURE-112", "messified_text": "For the data checks, it should be able to run both the individual field checks and the ones that compare across fields on that NBI data, and do it in batch mode, going through a bunch of records at once, not just one at a time."}, {"id": "PURE-113", "messified_text": "Under normal day-to-day running, Pontis needs to be up and working about 98 percent of the time — I know that's oddly precise but that's the number the engineers are targeting."}]'''

RAW["rlcs"] = r'''[
  {"id": "PURE-114", "messified_text": "So the RLCS thing, I want it to show what overrides are currently on — like which ones are live — and also flag any devices that don't have that rules protection thing going, you know, in case something opens or closes when it shouldn't."},
  {"id": "PURE-115", "messified_text": "Also someone should be able to go pull up old reports out of that off-the-shelf reporting system we're using — search by like a date range or the report's name, whatever's easier at the time."},
  {"id": "PURE-116", "messified_text": "And whatever tables we've got stored in that permanent memory, I need updating those to be enough to handle whatever changes happen down the road with the actual roadway layout — future-proof it a bit, basically."},
  {"id": "PURE-117", "messified_text": "Leaving aside however long the device or network takes to actually respond, if someone kicks off a status change for some device from the screen — like a control command — that should come back in 2 seconds, tops."},
  {"id": "PURE-118", "messified_text": "The RLCS setup also needs some kind of database built in — something that can hold onto, work through, and pull back whatever data's needed to keep randos from getting into the system who shouldn't be there."},
  {"id": "PURE-119", "messified_text": "I think every command that goes out to a device needs to get checked for safety, and not just wherever it starts from — anywhere downstream it gets passed along to, any of those lower-level control units, it needs that same check too."}
]'''

RAW["stewards"] = r'''[
  {"id": "PURE-120", "messified_text": "So from that main starting screen, I want to be able to see like, the whole big picture — every single watershed we've got — all laid out so I can just pick the one I need instead of hunting around for it."},
  {"id": "PURE-121", "messified_text": "Also I need people to be able to poke around the individual monitoring spots, ask it questions about them, and just grab the data and whatever info goes along with it, straight from wherever those station records live — download it, basically."},
  {"id": "PURE-122", "messified_text": "And separately, someone should be able to look through and search the watershed info too, whether they're going by like, some topic or category, or just by where it's located — whatever makes sense to them."},
  {"id": "PURE-123", "messified_text": "For keeping our stuff safe, I want the backups — both the data and the actual application — handled by some proper, real backup tool, not some homegrown thing, something that's actually got support behind it."},
  {"id": "PURE-124", "messified_text": "Since folks are mostly going to be reaching this thing over the web, we're gonna need the usual web protocol stuff and those map-server type applications in place too, otherwise none of it's gonna actually work right."},
  {"id": "PURE-125", "messified_text": "And for where everything actually gets stored, since our go-to database setup around here is the relational kind, it's gonna have to run on that Microsoft database product — the SQL one — for it all to function."}
]'''

RAW["tcs"] = r'''[{"id": "PURE-126", "messified_text": "For mission planning, I want a proper visual screen where the operator can just click waypoints right onto a map, you know, using some kind of pointing device — and it's got to have backup keys too, so if one input fails there's still a full redundant way to punch it all in."}, {"id": "PURE-127", "messified_text": "Basically the box needs to be able to keep tabs on and steer the drone itself, whatever it's carrying, the comms link, and all those command-and-control interfaces, all while a mission's actually happening."}, {"id": "PURE-128", "messified_text": "It should be able to tell the aircraft to fly itself using whatever navigation approach is already built into that particular model — not force some other method on it."}, {"id": "PURE-129", "messified_text": "Oh, and when someone kicks off a loss-of-link situation, the operator needs to see some kind of countdown clock pop up so they know how long they've got before things go sideways."}, {"id": "PURE-130", "messified_text": "We need it to handle both that line-of-sight link and the satellite link — like, both flavors of data connection should be covered, not just one or the other."}, {"id": "PURE-131", "messified_text": "For the picture-fixing stuff, I'd want it to cover the basics — contrast, brightness, sharpening up the edges, and general sharpness — all of those tweaks in there."}, {"id": "PURE-132", "messified_text": "It also needs to be able to manage every one of those command-and-control interfaces, across all the interaction levels — I think there's five of them — so nothing gets left out."}, {"id": "PURE-133", "messified_text": "At the very least, we need some kind of password gate on that feature so not just anyone can waltz in and use it — operator access should be locked behind that, minimum."}, {"id": "PURE-134", "messified_text": "It should come with whatever hardware and software bits are needed so the whole thing can actually hook up and talk to JMCIS properly, nothing missing."}, {"id": "PURE-135", "messified_text": "There should also be some way to hook it up to a VCR — like an actual connection between the two so it can work with the tape recorder thing."}, {"id": "PURE-136", "messified_text": "It needs to give the operator enough room to actually fly each drone properly, staying within whatever flight limits it's cleared for — nothing that boxes them in below what's allowed."}, {"id": "PURE-137", "messified_text": "Power-wise it should run off the usual military generators you'd find anywhere in the world — both voltage flavors, either frequency — plus regular wall power too."}, {"id": "PURE-138", "messified_text": "The software also needs to stop operators from trying to use interaction levels the system just can't actually pull off — like, don't let them attempt stuff it's not built to do."}]'''

RAW["video_search"] = r'''[
  {"id": "PURE-139", "messified_text": "Oh, one thing — when someone's looking for torrents, I don't want a separate search box for that, just have it use the same search bar as the regular streaming search, so people aren't hunting around for two different ones."},
  {"id": "PURE-140", "messified_text": "There should probably be a little checkbox or something so people can decide whether they want torrent stuff mixed into their search results or not, you know, just an on-off option for that."},
  {"id": "PURE-141", "messified_text": "I'd like it so whoever's looking at the results can just click on the top of a column — like size, or the date, or alphabetically — and have everything sort itself out that way, whatever order makes sense to them."},
  {"id": "PURE-142", "messified_text": "Similar idea but for video links — give people a checkbox so they can turn on or off whether those video link results show up when they search, just so they've got the choice."},
  {"id": "PURE-143", "messified_text": "Also, whenever there's a link showing up anywhere, clicking it should just pop open their normal browser, whatever they usually use, so they're not stuck inside our thing to go check out a website."},
  {"id": "PURE-144", "messified_text": "And however it's pulling stuff from other sites, it really shouldn't be sitting there forever — I want it capped so nothing ever takes more than 5 seconds to come back, no matter which website it's checking."}
]'''

RAW["warc_iii"] = r'''[
  {
    "id": "PURE-145",
    "messified_text": "One thing I need is for these tools to actually handle the big stuff — like, when we're dealing with huge batches of files, it can't just choke, it needs to spread the work across multiple machines and move the data around properly, kind of like what we talked about in those other two requirements."
  },
  {
    "id": "PURE-146",
    "messified_text": "I want the tools to run as fast as they possibly can when they're chewing through those big collections, especially since most of the slowdown is probably going to be all the reading and writing to disk rather than the actual processing."
  },
  {
    "id": "PURE-147",
    "messified_text": "Whatever we build needs to play nice with whatever Java setups people already have — so hook it up through web services or a RESTful-type API or something along those lines, nothing that forces them into a weird custom setup."
  },
  {
    "id": "PURE-148",
    "messified_text": "It'd be nice if there was some kind of logging built in, you know, so folks can actually see what's going on — like how long a command took to run, what level of detail is coming out, stuff like that."
  },
  {
    "id": "PURE-149",
    "messified_text": "For the workflow piece, I think we need some kind of adjustable strategy for handling the switch-over from the old ARC format to WARC — like, not hardcoded, something someone can tweak depending on how they want that migration managed."
  },
  {
    "id": "PURE-150",
    "messified_text": "Oh, and for that migration API — keep it simple, someone should only have to pull in a single header file to use it, not a whole pile of them."
  }
]'''

if __name__ == "__main__":
    all_items = []
    for k, v in RAW.items():
        items = json.loads(v)
        for it in items:
            all_items.append({"id": it["id"], "messified_text": it["messified_text"]})
    print(len(all_items))
    with open("data/interim/messify_batches/_combined_raw.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)
