#!/usr/bin/env python3
"""
Phase 3: the manually-reviewed eligible pool per document.

Every entry below was read and judged by hand against docs/item_selection.md
Section 3 (inclusion/exclusion rules), starting from the Phase 2 shortlist
(data/interim/shortlist.json) plus, for clarus_low specifically, a corrected
-raw pdftotext extraction (the -layout extraction interleaved PDF table
columns into the requirement text for that document — see
scripts/screen_candidates.py's docstring and this file's CLARUS_LOW block).

`text` is the exact string to include in the final dataset. Where the raw
candidate contained extra material that isn't part of the requirement itself
(a bled-in section heading, a second unrelated sentence pulled in by
sentence-splitting, a trailing page number/footer), `text` here is a
VERBATIM SUBSTRING of that raw candidate/source document — trimmed to the
requirement's own boundary, never reworded. Each entry's `verify_in` names
the source file that substring must be found in; scripts/assemble_pure150.py
checks this mechanically before anything is written to the final dataset.

Documents are keyed exactly as in scripts/build_shortlist.py's DOC_CONFIG.
"""

# (text, section_label, source_requirement_id_if_any)
ELIGIBLE = {
    "npac": {
        "source_file": "2001 - npac [doc].txt",
        "cap": 13,
        "items": [
            ("NPAC SMS shall only allow access to encrypted passwords by authorized users.", "R7-16 Passwords, Encrypted - Privileged Users Access Control", "R7-16"),
            ("NPAC SMS shall allow Service Providers to add their NPA-NXX data with an effective date that is set to a past, present, or future date.", "RX3-1.1.2 Service Provider NPA-NXX Data Effective Date Validation", "RX3-1.1.2"),
            ("NPAC SMS shall have documented procedures for data backup.", "R7-84.2 Data Backup Procedures", "R7-84.2"),
            ("NPAC SMS shall allow NPAC personnel to view all Subscription Versions associated with an NPA-NXX.", "R4-24.3 Display of NPA-NXX and related subscription data", "R4-24.3"),
            ("NPAC SMS NMS shall notify the NPAC personnel immediately when security event thresholds are exceeded through the SNMP agent.", "R7-80.2 Security Event Notification", "R7-80.2"),
            ("NPAC SMS shall provide a mechanism to limit system entry for privileged NPAC SMS users on a specifiable per‑port basis.", "R7-42.2 System Access - Per-Port Basis", "R7-42.2"),
            ("NPAC SMS shall have documented procedures for software backup.", "R7-84.1 Software Backup Procedures", "R7-84.1"),
            ("NPAC SMS shall default the long Business Day Duration tunable parameter to 12 hours.", "RR3-12.4 Long Business Day Duration - Tunable Parameter Default", "RR3-12.4"),
            ("NPAC SMS shall allow the NPAC SMS Administrator to modify the LSMS Retry Interval tunable parameter.", "RR6-25 LSMS Retry Interval - Tunable Parameter Modification", "RR6-25"),
            ("NPAC SMS shall default the short Conflict Resolution New Service Provider Restriction tunable parameter to 6 business hours.", "RR5-12.6 Short Conflict Resolution New Service Provider Restriction - Tunable Parameter Default", "RR5-12.6"),
            ("NPAC SMS shall store database extract files at the NPAC SMS FTP site for Local SMS file retrieval.", "R3-15 FTP Site for Database Extracts", "R3-15"),
            ("NPAC SMS shall download NPA-NXX data and LRN data via the NPAC SMS to Local SMS Interface and/or the SOA to NPAC SMS interface if the indicator is ON.", "RR3-2 Service Provider Download Indicator", "RR3-2"),
            ("NPAC SMS shall sort the report listed in RR9-16, in the following order: (Previously R-141) New Service Provider SPID (primary sort) TN (secondary sort)", None, "RR9-16 (Previously R-141)"),
        ],
    },
    "tcs": {
        "source_file": "1999 - tcs.xml",
        "cap": 13,
        "items": [
            ("[SSS058] The TCS mission planning function shall provide a graphical user interface that gives the operator the ability to define waypoints on a map based display using a pointing device with full keyset redundancy.", "System Capability Requirements > Mission Planning Function", "SSS058", ["[SSS058] "]),
            ("The TCS will have the capability to control and monitor an AV, payload, data link, and C4I interfaces during the execution of a mission.", "System Capability Requirements > Mission Control And Monitoring Functions", None),
            ("The TCS shall have the capability to command the AV to use the navigation methods inherent to the selected AV.", "System Capability Requirements > Mission Control And Monitoring Functions > AV Control And Monitoring Capability > AV Navigation Control Task", None),
            ("[SSS146] TCS shall display a LOL timer to the operator initiating a LOL onset.", "AV Monitoring Task > AV Monitoring Displays", "SSS146", ["[SSS146] "]),
            ("[SSS163] The TCS shall support a LOS data link and SATCOM data link capability.", "Data Terminal Control Task", "SSS163", ["[SSS163] "]),
            ("The image enhancement capability shall include contrast, brightness, edge enhancement, and sharpness.", "Payload Product Management Function > Payload Product Exploitation Capability", None),
            ("The TCS will have the capability to manage all operational C4I interfaces across all 5 levels of interaction.", "C4I System Interface Function > C4I Interface Control Capability", None),
            ("[SSS278] As a minimum, the TCS shall restrict Operator access to this capability via password protection.", "System Capability Requirements > Software Upgrade Function", "SSS278", ["[SSS278] "]),
            ("The TCS shall provide the necessary hardware and software functionality to allow the TCS to integrate with JMCIS.", "System External Interface Requirements > TCS to C4I > TCS to JMCIS", None),
            ("The TCS will provide an interface between the TCS and a video cassette recorder.", "System Internal Interface Requirements > VCR", None),
            ("[SSS347] The TCS shall provide adequate capability to allow the operator to operate each UAV within its certified operational flight envelope.", "Safety Requirements > Air Vehicle Safety", "SSS347", ["[SSS347] "]),
            ("The TCS shall use standard military worldwide 110/220 volt 50/60 hertz generators and commercial power sources.", "Resource Requirements > Hardware Requirements > Power", None),
            ("The TCS software shall restrict the operator(s) from exercising levels of interaction not achievable by the system.", "Resource Requirements > Computer Software Requirements", None),
        ],
    },
    "nasa_x38": {
        "source_file": "2000 - nasa x38 [doc].txt",
        "cap": 10,
        "items": [
            ("The scheduler shall [SRS197] support up to 3 rate groups per vehicle mode.", None, "SRS197", ["[SRS197] "]),
            ("The scheduler shall [SRS034] take no longer than 1 millisecond to execute scheduler and Time Services FTSS overhead tasks in each rate group.", None, "SRS034", ["[SRS034] "]),
            ('Communication services shall [SRS050] restrict the use of "immediate" message passing services between virtual groups (from FCP to ICP) to tasks running in the highest rate group on the FCP.', None, "SRS050", ["[SRS050] "]),
            ("The FTSS shall [SRS262] configure each FCP to continue processing if any of the Power-up or Initial BIT tests fail.", None, "SRS262", ["[SRS262] "]),
            ("RAM scrub shall [SRS044] report detected errors to the application, congruently on all channels, via an API service for inclusion in the telemetry stream.", None, "SRS044", ["[SRS044] "]),
            ("The FTSS API shall [SRS217] specify a memory map that provides the boundaries for congruent aligned memory, congruent initialized memory, and non-congruent memory.", None, "SRS217", ["[SRS217] "]),
            ("In all error cases, Support Services shall [SRS222] attempt to choose an error-free FCC-MPCC path, switching back and forth between channels if necessary.", None, "SRS222", ["[SRS222] "]),
            ("In addition, the FTSS software shall [SRS280] provide up to 600 bits of start-up data that indicates the state of the FTPP system during start-up.", None, "SRS280", ["[SRS280] "]),
            ("The FTPP system shall (3.1.18) be capable of powering up and operating with any combination of 3 of the 5 FCR's active.", "3.1 FTPP System Requirements", "3.1.18", ["(3.1.18) "]),
            ("The maximum time-out value shall (3.2.2.3.7) be 327.68 microseconds (256 counts of the least significant bit of the fault tolerant clock which is 1.28 microseconds).", "3.2.2.3 Initial Synchronization (ISYNC)", "3.2.2.3.7", ["(3.2.2.3.7) "]),
        ],
    },
    "clarus_low": {
        "source_file": "2005 - clarus low [pdf].txt",
        "cap": 8,
        "items": [
            ("The Clarus system design must address how best to minimize these times to optimize the flow of data in a timely manner.", None, None),
            ("The CAUI shall enable administrators to manage contributor metadata.", None, "I-031C1"),
            ("The Clarus system shall collect pavement-related observations.", None, "F-231"),
            ("The Clarus system shall accept data through a Clarus standard interface.", None, "I-011"),
            ("The EMC shall be able to maintain contact info for each contributor, collector, and station sensor.", None, "H-120E3"),
            ("The QEDC combined from all available Clarus hosts shall support 470 million current observations.", None, "P-013I1"),
            ("The Clarus system shall allow users to create a data subscription request.", None, "I-033"),
            ("The SS shall be able to initiate a QEDS response.", None, "D-051K1"),
        ],
    },
    "eirene_fun_7": {
        "source_file": "2007-eirene_fun_7-2.xml",
        "cap": 8,
        "items": [
            ("2.3.8 The network shall support data rates of at least 2.4 kbit/s. (M)", "Network requirements > Data services", "2.3.8", ["2.3.8 "]),
            ("5.2.2.30 At any time during the call, the lead driver shall be able to remove a member of the group. (M)", "Cab radio > Driver call related functions", "5.2.2.30", ["5.2.2.30 "]),
            ("2.4.14 It shall be possible for the user to re-join the call which is on hold at any time. (M)", "Network requirements > Call related services", "2.4.14", ["2.4.14 "]),
            ("13.2.2.2 A connection of Railway emergency priority (see section 10.2) shall be established to a pre-determined set of receiving mobiles and controller(s). (M)", "Railway emergency calls > Management of Railway emergency calls > Stage 1: Warning", "13.2.2.2", ["13.2.2.2 "]),
            ("5.7.2 The activation of the driver safety device shall automatically trigger the Cab radio to send a data message. (M)", "Cab radio > Driver safety device interface", "5.7.2", ["5.7.2 "]),
            ("7.2.2.15 A short audible and visual indication of the incoming call shall be provided. (M)", "Operational radio functions", "7.2.2.15", ["7.2.2.15 "]),
            ("7.4.4.1 A visual and audible alarm shall be given when the remaining capacity of the battery is such as to enable only 10 minutes of full duplex call time. (M)", "Operational radio man-machine interface > Indications", "7.4.4.1", ["7.4.4.1 "]),
            ("10.5.2 Where EIRENE facilities are not available within the currently selected network, the user shall be given a visible indication. (M)", "Subscriber management > Network selection list", "10.5.2", ["10.5.2 "]),
        ],
    },
    "nde": {
        "source_file": "2007 - nde [pdf].txt",
        "cap": 8,
        "items": [
            ("The System shall provide the capability to operate in a Degraded System Mode, within which the system generates a subset of products based upon priority and availability of system resources.", "3.1.2 Degraded System Mode", "3.1.2"),
            ("The System shall be capable of generating Data Products.", "3.2.6 Data Product Generation", "3.2.6"),
            ("The System shall be capable of reformatting Data Products into GRIB2.", "3.2.6.9 GRIB2 Data Format", "3.2.6.9"),
            ("The System shall be capable of notifying registered users of the status of the System.", "3.2.10 System Status Notification", "3.2.10"),
            ("The System shall be capable of automatically submitting Ad Hoc Requests to the IDPS for retransmission of Data Products.", "3.3.1.5 Ad Hoc Requests to the IDPS", "3.3.1.5"),
            ("The System shall be capable of executing tasks according to a schedule.", "3.4.1 Schedule Tasks", "3.4.1"),
            ("The System shall be capable of accepting technology updates without System downtime.", "3.6.1 Technology Updates", "3.6.1"),
            ("The System shall be capable of protecting the integrity of NDE data in the event of a hardware malfunction such as a disk crash.", "3.7.8 Integrity - Protect from Hardware Malfunction", "3.7.8"),
        ],
    },
    "ertms": {
        "source_file": "2007-ertms.xml",
        "cap": 6,
        "items": [
            ("ETCS shall provide the driver with information to allow him to drive the train safely.", "General requirements > Basic functioning", None),
            ("The DMI shall indicate the result of the self-test.", "Operational Functions > On Board Equipment self Test", None),
            ("Exit from Shunting shall take place when the driver selects exit from shunting.", "Operational Functions > Shunting operation", None),
            ("The driver shall be able to release an ETCS emergency brake application when stationary.", "Trainborne Functions > Indication displayed on the DMI", None),
            ("The character set used shall support different languages.", "Additional Functions > Plain text transmission", None),
            ("If a train cannot stop at the proposed new target location it shall reject the request and keep the old target location.", "Functions related to RBC > Revocation of a Movement Authority", None),
        ],
    },
    "pontis": {
        "source_file": "2005 - pontis [pdf].txt",
        "cap": 8,
        "items": [
            ("The user shall be able to switch between predefined structure lists.", "1.2", "1.2"),
            ("The user shall be able to create a new structure by copying all data of an existing structure.", "5.2", "5.2"),
            ("The user shall have the option to copy the notes from previous inspection when creating a new inspection.", "6.5", "6.5"),
            ("Privileged users shall be able to delete an existing inspection unless it is “locked down”.", "6.19", "6.19"),
            ("The system shall be capable of prompting users when the dependent fields for ratings are changed and offer the user option to recalculate the ratings.", "7.6", "7.6"),
            ("The user shall be able to modify the technical parameters governing the simulation, including the parameters of the improvement model and the simulation rules.", "10.3", "10.3"),
            ("The system shall be capable of performing single-field and cross-field validation on NBI data items in batch mode.", "UC-15 Perform Data Validation, 15.1", "15.1"),
            ("During normal times of operation, Pontis shall achieve 98 percent up time.", None, None),
        ],
    },
    "rlcs": {
        "source_file": "2004 - rlcs [pdf].txt",
        "cap": 6,
        "items": [
            ("The RLCS software shall display information about active overrides: Which are active, and which devices have no currently active 'rules protection' against erroneous opening/closing.", None, None),
            ("The user shall be able to retrieve historic reports from the COTS reporting system based on date range and report name.", "3.2.1.9 Report Screen", None),
            ("Updating non-volatile memory-based tables shall be sufficient to accommodate future changes to the roadway.", None, None),
            ("Not including device and network response time, requests from the GUI for device status changes (control commands) shall not exceed 2 seconds.", "3.3.2 User Interface (GUI)", None),
            ("The RLCS shall incorporate a database to store, process, and retrieve all data necessary to secure the system from unauthorized use.", "3.5.2 Security", "3.5.2.1"),
            ("Safety screening shall be applied to all device commands at the originating control unit, and at all subordinate control units to which the device command or any of its subordinate device commands may be forwarded.", None, None),
        ],
    },
    "gemini": {
        "source_file": "1995 - gemini.xml",
        "cap": 8,
        "items": [
            ("The monitor's keyboard would not have any effect on the observer's environment", "Observing model requirements > Remote operations > Multipoint Monitoring", None),
            ("In particular also, the meteorological information coming from a weather station should be available centrally.", "Data Specifications > Control Information Flow", None),
            ("It should also be network transparent so that it does not matter where it is being run.", "External Interface Requirements > User Interface (UIF)", None),
            ("All essential tasks, not including remote observing, must take place on resources controlled by the project (such as leased lines).", "External Interface Requirements > Communication interface > Local area network (LAN)", None),
            ("In any case, remote operation must include remote monitoring from the Gemini 8m Telescopes base facilities, together with access tools for diagnostic and test use.", "General constraints > Hardware constraints", None),
            ("Each subsystem should have a background task running whenever that subsystem is operational, performing such tasks as checking power supply levels, temperatures, performance, correct responses to commands.", "Attributes > Maintainability > Maintenance Requirements", None),
            ("In general this will require mechanical hard stops, electrical interlocks, electrical hard limit switches, soft limit switches, software limits, and watch dogs,.", "Attributes > Security and Safety > Security and Safety Requirements", None),
            ("The database must support both remote access and distributed data.", "Other Controls and Software Requirements > On-line database subsystems", None),
        ],
    },
    "peppol": {
        "source_file": "2009 - peppol approved.xml",
        "cap": 8,
        "items": [
            ("Any national pilot solution that will be developed in the context of PEPPOL WP2 has to follow the pre- VCD mapping defined in stage 1.", "Organisational requirements > Conformance of national solution with pre-VCD mapping tool defined in stage 1", None),
            ("The VCD simple package (Stage 2) lays the basic ground for the creation of VCDs and the implementation of other services mentioned in stages 3 and 4 so the key concepts of Stage 2 MUST be implemented in each Member States.", "Semantic Requirements > Implementation approach with regard to stages of maturity", None),
            ("Classification schemes for goods, services and code lists SHOULD be publicly available and identified in the document objects.", "Semantic Requirements > Classification schemes awareness", None),
            ("The contracting authority SHOULD specify a subset of evidences from the superset evidences that are relevant to a specific Call for Tender.", "Legal Requirements > Legal effect of subset criteria and evidences", None),
            ("Relevant regulations of national data protection acts MUST be analysed and considered.", "Legal Requirements > Legal requirements regarding data protection", None),
            ("A process for document handling compliant with the relevant legal regulations MUST be defined (especially with respect to the data protection acts).", "Legal Requirements > Legal Validity", None),
            ("Every party participating MUST be uniquely identifiable", "Technical Requirements > Identity", None),
            ("The PEPPOL infrastructure MUST have the capability to submit a VCD to a contracting authority or tendering platform.", "Technical Requirements > Use of PEPPOL infrastructure to submit a VCD", None),
        ],
    },
    "fishing": {
        "source_file": "2010 - fishing [pdf].txt",
        "cap": 6,
        "items": [
            ("The product profile is a questionnaire which must be completed by an ELSS supplier to list the mandatory, optional and conditional features supported in their product.", None, None),
            ("The ELSS must provide data capture screens for the entry of the logbook, transhipment and landing declaration data that is required to be transmitted to the UK fisheries administrations’ ERS system.", "2.4 Capture Functions", None),
            ("The subject header must consist of a character string containing ‘ERS – ‘ prefixed to the contents of the GBRRN attribute of the Electronic Logbook data being transmitted.", "2.5 Data Transmission", None),
            ("All deletions must be easily identifiable within the ELSS user interface.", "2.5.3 Data Deletions", None),
            ("Each copy of the ELSS installed must be provided with a unique (internal?) number that is automatically entered into each transmission to identify the instance of the ELSS from which the report has been transmitted.", None, None),
            ("Any C change of vessel master during a voyage must be notified in the next LOG message.", None, None),
        ],
    },
    "inventory_2_0": {
        "source_file": "2009 - inventory 2.0 [pdf].txt",
        "cap": 8,
        "items": [
            ("The Unique Tag must be at most 18 characters long", None, "1.5"),
            ("The Item Detail Name must be unique across the inventory", None, "4.4"),
            ("If the „Other‟ reason is selected, the user must enter an additional comment", None, "2.2.2"),
            ("The original CRM acquisition data must be kept, not overridden by the values entered here", None, "3.9.6"),
            ("The sale price must not override the original item price in the inventory", None, "1.2"),
            ("The system must be available during normal Construction Junction operating hours.", "5.2 Availability", None),
            ("Access to the application by the Construction Junction staff must require user login.", "5.4 Security", None),
            ("Department‟s Unique Tag must be unique across the inventory", None, "3"),
        ],
    },
    "phin": {
        "source_file": "2005 - phin.xml",
        "cap": 8,
        "items": [
            ("A plan must be established for continuing activities when systems supporting OM are unavailable.", "System Security and Availability", "2.8"),
            ("Systems supporting OM should be capable of using configurable, domain-specific vocabulary.", "System Architecture", None),
            ("A Subject ID should also be collected for animals in an OM investigation.", "Data Requirements > Entity Data", None),
            ("Information about each leg of a trip, as well as the parent information about the trip, should be captured.", "Data Requirements > Travel History and Conveyance Data", None),
            ("Systems supporting OM must allow for dynamic, event-specific case investigation data to be captured.", "Data Requirements > Case Investigation and Exposure Contact Data", None),
            ("Systems supporting OM must provide the ability to control the configuration of and revisions to investigation-specific questionnaires.", "System Functions and Behaviors > Case Investigation", None),
            ("Entity-to-epi data links must match the entity to their symptoms, survey questions, specimens/samples collected, laboratory results, and prophylaxis and treatment data.", "System Functions and Behaviors > Linking", None),
            ("Systems supporting OM must support contact exposure tracing by allowing one contact to be linked to multiple cases, and allowing multiple contacts to be linked to a single case.", "System Functions and Behaviors > Contact Exposure Tracing", None),
        ],
    },
    "warc_iii": {
        "source_file": "2009 - warc III [pdf].txt",
        "cap": 6,
        "items": [
            ("The tools shall be able to scale to process large collections using distributed processing and\n  data transport (see FRS 10 and 11)", None, "NFR 2"),
            ("The tools shall offer best possible performance to correctly process large collections (I/O\n  bound)", None, "NFR 3"),
            ("The tools shall be compliant with Java development environments, by using web services,\n  RESTful API’s, etc.", None, "NFR 6"),
            ("The tools shall provide logging facilities, for example, to follow command progression, i.e.\n  process duration, output levels, etc.", None, "NFR 7"),
            ("The workflow system shall have a configurable management strategy for migration from ARCs\n  to WARCs.", None, "NFR 10"),
            ("The migration API will require inclusion of only one header file.", None, "FR 2"),
        ],
    },
    "stewards": {
        "source_file": "2006 - stewards [pdf].txt",
        "cap": 6,
        "items": [
            ("FR-2.1: View entire universe of watersheds from top-level screen for selection", "3. Functional Requirements > FR-2 Data Access", "FR-2.1", ["FR-2.1: "]),
            ("FR-2.3: Browse, query, and download individual sampling station data and metadata", "3. Functional Requirements > FR-2 Data Access", "FR-2.3", ["FR-2.3: "]),
            ("FR-3.2: Browse and query watershed metadata by theme or location", "3. Functional Requirements > FR-3 Metadata", "FR-3.2", ["FR-3.2: "]),
            ("SR-1:    Backup Software – Data and application backups will be managed through fully supported\n         backup software solutions.", "3.5 Software requirements", "SR-1", ["SR-1: Backup Software – "]),
            ("SR-2:    HTTP and GIS Server Applications – As the Web will be the primary delivery protocol\n         for the application, HTTP and related GIS server applications will be required to support\n         system functionality.", "3.5 Software requirements", "SR-2", ["SR-2: HTTP and GIS Server Applications – "]),
            ("SR-5:    Relational Database Management System - As the primary data storage mechanism for\n         the corporate standard relational database management system, Microsoft SQL Server will\n         be required to support system functionality.", "3.5 Software requirements", "SR-5", ["SR-5: Relational Database Management System - "]),
        ],
    },
    "keepass": {
        "source_file": "2008 - keepass.xml",
        "cap": 8,
        "items": [
            ("REQ-1: KeePass must be downloaded and installed", "New Database > Functional Requirements", "REQ-1", ["REQ-1: "]),
            ("Databases must have different names or else the previews one will be replace if selected", "Save Database > Functional Requirements", None),
            ("There must be entries in the database in order for them to be printed", "Print Database > Functional Requirements", None),
            ("An entry must belong to a group to be created", "Add Entry > Functional Requirements", None),
            ("When the password field is completed the repeat password field must be completed", "Add Entry > Functional Requirements", None),
            ("Sequence’s length must not be more than a line (59 characters)", "Auto-type > Functional Requirements", None),
            ("In case a space is found in the path, it must be enclosed into quotes", "Command Line Options > Functional Requirements", None),
            ("If there is a composite key, both master password and key file are required", "Composite Master Key > Functional Requirements", None),
        ],
    },
    "peering": {
        "source_file": "2008 - peering.xml",
        "cap": 6,
        "items": [
            ("The format for service information description is defined", "Service Registration > Functional Requirements", None),
            ("The interaction protocol between Web Server-SR, SR-mediator is defined.", "Service Registration > Functional Requirements", None),
            ("Malicious requests are detected and rejected.", "Request Initiation to Trigger Peering > Exceptions", None),
            ("Mediator-SR, mediator-PR, mediator-PA interaction protocols are defined.", "Mediator Invokes Creation of Negotiated Relationship > Exceptions", None),
            ("Interaction protocols between PAs are identified.", "Resource Discovery through PA > Exceptions", None),
            ("Negotiation is established between selected CDN peers.", "Operational Management > Exceptions", None),
        ],
    },
    "video_search": {
        "source_file": "2009 - video search.xml",
        "cap": 6,
        "items": [
            ("REQ-1: Torrent search will share the same search bar with the streaming search.", "Torrent Search > Functional Requirements", "REQ-1", ["REQ-1: "]),
            ("REQ-3: There will be a tick box to allow the user to choose to include torrent searching in the search.", "Torrent Search > Functional Requirements", "REQ-3", ["REQ-3: "]),
            ("REQ-6: Results will be arranged in size/date/alphabetical order by clicking on the column headers.", "Torrent Search > Functional Requirements", "REQ-6", ["REQ-6: "]),
            ("REQ-4: There will be a tick box to allow the user to choose to include video link searching in the search.", "Video Stream Search > Functional Requirements", "REQ-4", ["REQ-4: "]),
            ("The software will use hyperlinks to allow the user to open websites in their default web browser.", "External Interface Requirements > Software Interfaces", None),
            ("REQ-1: Query times will take no longer than 5 seconds to any website.", "Other Nonfunctional Requirements > Performance Requirements", "REQ-1", ["REQ-1: "]),
        ],
    },
}
