# Knowledge Gaps Report â€” Campus Life & Co-Curricular Cluster (Level 1)

**Team:** Campus Life & Co-Curricular  
**Cluster Type:** Campus & Co-Curricular  
**Layer Focus:** Level 1 (Static / Already Collected Information)  
**Evaluation Date:** 2026-06-09 23:42  
**Evaluation Mode:** LIVE â€” Direct pipeline call (`top_k=1`)  
**Total Questions Evaluated:** 250  
**Question Bank:** `student_campus_life_QuestionBank.csv`  

---

## ðŸ“Š Summary Statistics

| Metric | Count | % |
|---|---|---|
| **Total Questions** | 250 | 100% |
| âœ… **PASS** | 13 | 5.2% |
| âš ï¸ **PARTIAL FAIL** | 198 | 79.2% |
| âŒ **FAIL** | 39 | 15.6% |
| **Overall Pass Rate** | **13/250** | **5.2%** |
| **Avg Response Latency** | 8.42s | â€” |

> [!IMPORTANT]
> This is a **LIVE evaluation** â€” questions were answered by the actual RAG
> pipeline using `top_k=1` (single retrieved document per query).

---

## âŒ Knowledge Gaps by Subcategory

### Campus Amenities

| QID | Question | Status | Reason |
|---|---|---|---|
| Q179 | How many food courts are there on the DAU campus? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q180 | What types of cuisine are available at DAU food courts? | FAIL | Exception: Error code: 503 - {'error': {'message': 'qwen/qwen3-32b is currently over capacity. Please try again and back off exponentially. Visit https://groqstatus.com to see if there is an active incident.', 'type': 'internal_server_error'}} |
| Q181 | Is non-vegetarian and egg food available on the DAU campus? | FAIL | Exception: Error code: 503 - {'error': {'message': 'qwen/qwen3-32b is currently over capacity. Please try again and back off exponentially. Visit https://groqstatus.com to see if there is an active incident.', 'type': 'internal_server_error'}} |
| Q182 | Are Amul products available at the DAU food courts? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q183 | How are the food courts managed at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q184 | Is there a food court at DAU specifically serving breakfastâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q185 | Is there a food court at DAU serving fruit and fruit juices? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Campus Infrastructure

| QID | Question | Status | Reason |
|---|---|---|---|
| Q221 | What campus security arrangement does DAU have (round the clock)? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q222 | Who administers and monitors campus security at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q223 | Can security staff ask students or visitors for identification? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Campus Maps & Locations

| QID | Question | Status | Reason |
|---|---|---|---|
| Q227 | Where is the DAU campus located? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q228 | What is the full official name of the university (DAU)? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Cultural Activities

| QID | Question | Status | Reason |
|---|---|---|---|
| Q217 | What cultural activities does the Cultural Committee organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q218 | What is Synapse at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q219 | What is HackOut at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q220 | What is YouthRun at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q235 | Which dance club won WALTZ in 2024? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q236 | What are the notable achievements of the DAU Theatres Group? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Dean of Students

| QID | Question | Status | Reason |
|---|---|---|---|
| Q001 | Who is the Dean of Students at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q002 | What is the email address of the Dean of Students office? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q003 | What is the phone number of the Executive Assistant to theâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q004 | Who is the Executive Assistant to the Dean of Students? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q005 | What does the Dean of Students oversee at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Hostel Facilities

| QID | Question | Status | Reason |
|---|---|---|---|
| Q127 | How many Halls of Residence are there at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q128 | What are the wings in the New Men's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q129 | What is the capacity of the New Men's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q130 | How many wings does the old Men's Hall of Residence have? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q131 | What is the capacity of the old Men's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q132 | What is the total capacity of the Women's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q133 | What wings are in the Women's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q134 | What furniture is provided in DAU hostel rooms? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q135 | Is internet provided in DAU hostels? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q136 | Is hot water available in the DAU hostels? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q137 | Is there a laundry/dhobi facility at DAU hostels? | FAIL | Bot returned fallback/refusal |
| Q138 | Are there TV rooms in DAU hostels? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q139 | Are mattresses provided in DAU hostel rooms? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q140 | Is hostel accommodation mandatory for B.Tech students? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q141 | Can PG students get hostel accommodation at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q142 | Is there a mess (dining hall) inside the DAU hostel? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q143 | Is there a guest room available in the Women's hostel and forâ€¦ | FAIL | Bot returned fallback/refusal |
| Q144 | What security arrangements exist for the Women's Hall ofâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q145 | Are CCTV cameras installed in the Men's hostel? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q146 | Who is the Warden for the Men's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q147 | Who is the Warden for the Women's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q148 | Who is the Resident Warden at DAU and what is their email? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q149 | What is the contact number of the Resident Warden? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q150 | Who are the Hostel Supervisors and what are their contacts? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q229 | What are the room types available in the New Men's HoR? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q230 | What type of internet connection is available in the Women's HoR? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Hostel Rules & Policies

| QID | Question | Status | Reason |
|---|---|---|---|
| Q151 | How is room allocation done for new students in the hostel? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q153 | For how many years can a UG student avail hostel accommodation? | FAIL | Bot returned fallback/refusal |
| Q154 | What is the curfew (return to campus) time for hostel residents? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q158 | Is smoking allowed on the DAU campus? | FAIL | Bot returned fallback/refusal |
| Q159 | Can men enter the Women's Hall of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q160 | What is the fine for having someone stay in your room withoutâ€¦ | FAIL | Bot returned fallback/refusal |
| Q161 | Is ragging allowed at DAU and what are the consequences? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q164 | Which electrical appliances are prohibited in DAU hostel rooms? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q165 | Is cooking allowed in the Halls of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q169 | Are visitors allowed inside the Halls of Residence? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q171 | What is the guest room rent for non-resident DAU studentsâ€¦ | FAIL | Bot returned fallback/refusal |
| Q172 | What is the fine for entertaining a visitor without priorâ€¦ | FAIL | Bot returned fallback/refusal |
| Q174 | What is the fine for losing a hostel room key? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q175 | What is the fine for leaving a hostel room unlocked and vacant? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q176 | Can residents use their own locks in the hostel room? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q177 | What is the minimum fine for breaking any hostel rule? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q178 | Who are the members of the Hostel Management Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Medical Facilities

| QID | Question | Status | Reason |
|---|---|---|---|
| Q186 | How many doctors visit the DAU Medical Centre daily? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q187 | What are the visiting hours of Dr. Arvindsinh Vaghela at theâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q188 | What are the visiting hours of Dr. Charulata Harshe at theâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q189 | What are the visiting hours of Dr. Anjana Ved at the Medicalâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q190 | Are medical consultations at the DAU Medical Centre free forâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q191 | Are medicines dispensed at the Medical Centre free of charge? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q192 | Which hospitals have signed an MoU with DAU for studentâ€¦ | FAIL | Bot returned fallback/refusal |
| Q193 | How far is Aashka Hospital from the DAU campus? | FAIL | Bot returned fallback/refusal |
| Q194 | Is there a 24x7 vehicle available for medical emergencies at DAU? | FAIL | Bot returned fallback/refusal |
| Q195 | What is the Group Mediclaim Insurance coverage amount for DAUâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q196 | Which insurance company provides the DAU Group Mediclaim policy? | FAIL | Bot returned fallback/refusal |
| Q197 | What type of medical treatment does the DAU Mediclaim policyâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q198 | What is the emergency intercom number for the DAU Medical Centre? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q199 | What is the landline number of the DAU Medical Centre forâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q200 | Who are the nurses at the Medical Centre and what are theirâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q201 | Is nursing staff available on weekends at the DAU Medical Centre? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q202 | What is the contact email of the DAU Medical Centre? | FAIL | Bot returned fallback/refusal |
| Q203 | What hospitals are empanelled with DAU for student treatmentâ€¦ | FAIL | Bot returned fallback/refusal |
| Q204 | What is the emergency contact number for SGVNS Swaminarayanâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q205 | What is the emergency contact number for Apollo Hospitalâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q206 | Does DAU have a counselling or stress management centre forâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q207 | Who are the counsellors at the Stress Management Centre andâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q208 | Where is Dr. Nandini Banerjee's counselling room on campus? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q244 | How can DAU students generate their Group Mediclaim insuranceâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q245 | What should students do in a medical emergency outside Medicalâ€¦ | FAIL | Exception: Error code: 429 - {'error': {'message': 'Rate limit reached for model `qwen/qwen3-32b` in organization `org_01jyqyzetzfkcvz8zc3v8wew3r` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5032, Requested 995. Please try again in 269.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing', 'type': 'tokens', 'code': 'rate_limit_exceeded'}} |
| Q246 | Is there a 24x7 ambulance facility on the DAU campus? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q247 | What is the Kashka Hospital contact number for emergencies? | FAIL | Bot returned fallback/refusal |

### Research Body Government

| QID | Question | Status | Reason |
|---|---|---|---|
| Q015 | What is the RBG and who does it serve? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q016 | Who is the Convenor of the RBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q017 | What is the email address of the RBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Sports Facilities

| QID | Question | Status | Reason |
|---|---|---|---|
| Q114 | How many sports facilities does DAU have in total? | FAIL | Bot returned fallback/refusal |
| Q115 | How many basketball courts does DAU have? | FAIL | Exception: Error code: 503 - {'error': {'message': 'qwen/qwen3-32b is currently over capacity. Please try again and back off exponentially. Visit https://groqstatus.com to see if there is an active incident.', 'type': 'internal_server_error'}} |
| Q117 | Does DAU have a cricket field? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q118 | What is the length of the athletic track at DAU? | FAIL | Bot returned fallback/refusal |
| Q119 | How many volleyball courts does DAU have? | FAIL | Bot returned fallback/refusal |
| Q120 | How many table tennis tables are in the DAU Table Tennis Hall? | FAIL | Bot returned fallback/refusal |
| Q121 | Does DAU have a gymnasium? | FAIL | Bot returned fallback/refusal |
| Q122 | Is there a yoga and meditation zone on the DAU campus? | FAIL | Bot returned fallback/refusal |
| Q123 | What are the two coaching phases for sports at DAU? | FAIL | Bot returned fallback/refusal |
| Q124 | When does Phase I of sports coaching take place at DAU? | FAIL | Bot returned fallback/refusal |
| Q125 | When does Phase II of sports coaching take place at DAU? | FAIL | Bot returned fallback/refusal |
| Q126 | What inter-collegiate tournaments does DAU participate in atâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q240 | What sports disciplines does DAU compete in atâ€¦ | FAIL | Bot returned fallback/refusal |
| Q241 | What is the vision of the DAU Sports Department? | FAIL | Bot returned fallback/refusal |

### Student Activity Board Structure

| QID | Question | Status | Reason |
|---|---|---|---|
| Q209 | What is the SBG structure in terms of committees and clubs? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q210 | What is the overall role of the Student Body Government at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Student Body Government

| QID | Question | Status | Reason |
|---|---|---|---|
| Q006 | How many student committees are there under the SBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q007 | How many student clubs are there under the SBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q008 | What does SBG stand for? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q009 | What is the email address of the SBG? | FAIL | Bot returned fallback/refusal |
| Q010 | Who is the Convenor of the SBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q011 | Who is the Deputy Convenor of the SBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q012 | Who is the Treasurer of the SBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q013 | Who is the Secretary of the SBG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q014 | What are the goals of the Student Body Government? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Student Chapters & Societies

| QID | Question | Status | Reason |
|---|---|---|---|
| Q082 | What is the IEEE Student Branch's objective at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q083 | Who is the Convenor of the IEEE Student Branch? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q084 | What is the email of the IEEE Student Branch? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q085 | What events does the IEEE Student Branch organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q110 | What is DCEI and when was it established? | FAIL | Exception: Error code: 503 - {'error': {'message': 'qwen/qwen3-32b is currently over capacity. Please try again and back off exponentially. Visit https://groqstatus.com to see if there is an active incident.', 'type': 'internal_server_error'}} |
| Q111 | What is the mission of DCEI? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q112 | How many incubates has DCEI produced? | FAIL | Bot returned fallback/refusal |
| Q113 | Who supports DCEI financially / institutionally? | FAIL | Exception: Error code: 503 - {'error': {'message': 'qwen/qwen3-32b is currently over capacity. Please try again and back off exponentially. Visit https://groqstatus.com to see if there is an active incident.', 'type': 'internal_server_error'}} |
| Q237 | What is i.Fest and which club organizes it? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

### Student Clubs

| QID | Question | Status | Reason |
|---|---|---|---|
| Q043 | What is the AI Club about and what activities does it organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q044 | Who is the Convenor of the AI Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q045 | What is the email of the AI Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q046 | What publications does the Press Club produce? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q047 | Who is the Convenor of the Press Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q048 | What is the email of the Press Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q049 | What is DebSoc and what events does it organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q050 | Who is the Convenor of the Debating Society? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q051 | What is the email of the Debating Society? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q052 | What is DADC and what are its notable achievements? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q053 | Who is the Convenor of the Dance Club (DADC)? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q054 | What is the email of the Dance Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q055 | What does the Programming Club do and what competitions doesâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q056 | Who is the Convenor of the Programming Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q057 | What is the email of the Programming Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q058 | What does the Music Club offer to students? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q059 | Who is the Convenor of the Music Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q060 | What is the email of the Music Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q061 | What type of performances does the DAU Theatres Group do? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q062 | Who is the Convenor of the DAU Theatres Group? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q063 | What is the email of the DAU Theatres Group? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q064 | What is the Research Club about? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q065 | Who is the Convenor of the Research Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q066 | What is the email of the Research Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q067 | What does the Chess Club do on campus? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q068 | Who is the Convenor of the Chess Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q069 | What is the email of the Chess Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q070 | What does the Electronics Hobby Club (EHC) work with? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q071 | Who is the Convenor of the EHC? | FAIL | Bot returned fallback/refusal |
| Q072 | What is the email of the EHC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q073 | What does PMMC stand for and what does the club focus on? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q074 | Who is the Convenor of the Photography and Movie Making Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q075 | What is the email of the PMMC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q076 | What events does the Film Club organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q077 | Who is the Convenor of the Film Club? | FAIL | Exception: Error code: 503 - {'error': {'message': 'qwen/qwen3-32b is currently over capacity. Please try again and back off exponentially. Visit https://groqstatus.com to see if there is an active incident.', 'type': 'internal_server_error'}} |
| Q078 | What is the email of the Film Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q079 | What does the Google Developer Group (GDG) at DAU do? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q080 | Who is the Convenor of GDG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q081 | What is the email of GDG? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q086 | What does the Khelaiya Club do? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q087 | Who is the Convenor of the Khelaiya Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q088 | What is the email of the Khelaiya Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q089 | What does the Cubing Club do on campus? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q090 | Who is the Convenor of the Cubing Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q091 | What is the email of the Cubing Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q092 | What events does The Radio Club organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q093 | Who is the Convenor of The Radio Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q094 | What is the email of The Radio Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q095 | What is Headrush and what does it do? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q096 | Who is the Convenor of the Headrush Quizzing Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q097 | What is the email of the Quizzing Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q098 | What does the Business Club do? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q099 | Who is the Convenor of the Business Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q100 | What is the email of the Business Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q101 | What does MSTC stand for and what events does it organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q102 | Who is the Convenor of MSTC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q103 | What is the email of MSTC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q104 | What is Muse – The Designing Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q105 | Who is the Convenor of Muse? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q106 | What is the email of Muse? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q107 | What does CINS stand for and what does the club focus on? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q108 | Who is the Convenor of the CINS Club? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q109 | What is the email of CINS? | FAIL | Exception: Error code: 503 - {'error': {'message': 'qwen/qwen3-32b is currently over capacity. Please try again and back off exponentially. Visit https://groqstatus.com to see if there is an active incident.', 'type': 'internal_server_error'}} |
| Q238 | What is the flagship magazine published by the Press Club at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q239 | What is the campus newsletter published by the DAU Press Clubâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q250 | How many clubs under SBG focus on technologyâ€¦ | FAIL | Bot returned fallback/refusal |

### Student Committees

| QID | Question | Status | Reason |
|---|---|---|---|
| Q018 | List all 8 student committees at DAU. | FAIL | Bot returned fallback/refusal |
| Q019 | What does the Academic Committee do? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q020 | Who is the Convenor of the Academic Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q021 | What is the email address of the Academic Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q022 | What events does the Annual Festival Committee organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q023 | Who is the Convenor of the Annual Festival Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q024 | What is the email address of the Annual Festival Committee /â€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q025 | What is the Cafeteria Management Committee (CMC) responsible for? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q026 | Who is the Convenor of the CMC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q027 | What is the email of the CMC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q028 | What does the Cultural Committee do? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q029 | Who is the Convenor of the Cultural Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q030 | What is the email of the Cultural Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q031 | What is the Hostel Management Committee (HMC) responsible for? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q032 | Who is the Convenor of the HMC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q033 | What is the email of the HMC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q034 | What does the TechSupport Committee handle? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q035 | Who is the Convenor of the TechSupport Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q036 | What is the email of the TechSupport Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q037 | What flagship events does the Sports Committee organize? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q038 | Who is the Convenor of the Sports Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q039 | What is the email of the Sports Committee? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q040 | What is the Student Placement Cell (SPC) responsible for? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q041 | Who is the Convenor of the SPC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q042 | What is the email of the SPC? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q231 | What is Concours in the context of DAU sports? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q232 | What is DCL (DAU Cricket League)? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q233 | What is the Inter-Wing Tournament at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q234 | What is Freshers' Weekend at DAU? | FAIL | Bot returned fallback/refusal |

### Student Support Services

| QID | Question | Status | Reason |
|---|---|---|---|
| Q211 | What is the Disciplinary Action Committee (DAC) and who areâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q212 | What is the direct contact number of the Dean of Students? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q213 | What is the purpose of the Grievance Redressal Cell at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q214 | What types of grievances can students raise through the GRHS? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q215 | What matters are out of scope of the Grievance Redressalâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q216 | Where can students find anti-ragging information at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q224 | Is rural internship mandatory for B.Tech students at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q225 | What should first-year students expect when joining DAU campusâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q226 | What academic advice is given to first-year students at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q243 | How should students or employees resolve disputes at DAU as aâ€¦ | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q248 | Who are the members of the DAC (Disciplinary Action Committee)? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |
| Q249 | What are the key disciplinary rules for students at DAU? | PARTIAL FAIL | Answer present but expected source not in retrieved chunks |

---

## ðŸ“ Gaps Traced to Source Files

| Source File | # Gaps | Question IDs |
|---|---|---|
| `data/student_services/dean_students.md` | 138 | Q009, Q018, Q071, Q077, Q109, Q234, Q250, Q001, Q002, Q003, Q004, Q005, Q006, Q007, Q008, Q010, Q011, Q012, Q013, Q014, Q015, Q016, Q017, Q019, Q020, Q021, Q022, Q023, Q024, Q025, Q026, Q027, Q028, Q029, Q030, Q031, Q032, Q033, Q034, Q035, Q036, Q037, Q038, Q039, Q040, Q041, Q042, Q043, Q044, Q045, Q046, Q047, Q048, Q049, Q050, Q051, Q052, Q053, Q054, Q055, Q056, Q057, Q058, Q059, Q060, Q061, Q062, Q063, Q064, Q065, Q066, Q067, Q068, Q069, Q070, Q072, Q073, Q074, Q075, Q076, Q078, Q079, Q080, Q081, Q082, Q083, Q084, Q085, Q086, Q087, Q088, Q089, Q090, Q091, Q092, Q093, Q094, Q095, Q096, Q097, Q098, Q099, Q100, Q101, Q102, Q103, Q104, Q105, Q106, Q107, Q108, Q142, Q145, Q146, Q147, Q148, Q149, Q150, Q209, Q210, Q211, Q212, Q216, Q217, Q218, Q219, Q220, Q224, Q231, Q232, Q233, Q235, Q236, Q237, Q238, Q239, Q248, Q249 |
| `data/infrastructure/halls_of_residence.md` | 19 | Q137, Q143, Q127, Q128, Q129, Q130, Q131, Q132, Q133, Q134, Q135, Q136, Q138, Q139, Q140, Q141, Q144, Q229, Q230 |
| `data/student_services/rules/hostel_rules_and_regulations.md` | 17 | Q153, Q158, Q160, Q171, Q172, Q151, Q154, Q159, Q161, Q164, Q165, Q169, Q174, Q175, Q176, Q177, Q178 |
| `data/student_services/medical_assistance_sop.md` | 15 | Q202, Q203, Q245, Q247, Q198, Q199, Q200, Q201, Q204, Q205, Q206, Q207, Q208, Q244, Q246 |
| `data/infrastructure/sports_complex.md` | 14 | Q114, Q115, Q118, Q119, Q120, Q121, Q122, Q123, Q124, Q125, Q240, Q241, Q117, Q126 |
| `data/infrastructure/medical_facility.md` | 12 | Q192, Q193, Q194, Q196, Q186, Q187, Q188, Q189, Q190, Q191, Q195, Q197 |
| `data/infrastructure/food_court.md` | 7 | Q180, Q181, Q179, Q182, Q183, Q184, Q185 |
| `data/student_services/committees/entrepreneurship_cell.md` | 4 | Q110, Q112, Q113, Q111 |
| `data/student_services/grievance_redressal_cell.md` | 4 | Q213, Q214, Q215, Q243 |
| `data/infrastructure/campus_security.md` | 3 | Q221, Q222, Q223 |
| `data/student_services/first_year_in_campus.md` | 2 | Q225, Q226 |
| `data/student_services/contact/location_contact.md` | 2 | Q227, Q228 |

---

## ðŸ”§ Prioritized Recommendations

### Priority 1 â€” Fix FAIL questions (39 questions, score = 0.0)

These questions received fallback responses. Likely causes:
- Source document **not indexed** in Pinecone (`qwen-local-rag`)
- Query embedding too dissimilar to any indexed chunk
- Document chunked poorly â€” key facts split across chunk boundaries

**Action:** Verify the source files below are uploaded & chunked in Pinecone.

- `data/student_services/dean_students.md` â€” 7 failures
- `data/infrastructure/halls_of_residence.md` â€” 2 failures
- `data/student_services/rules/hostel_rules_and_regulations.md` â€” 5 failures
- `data/student_services/medical_assistance_sop.md` â€” 4 failures
- `data/infrastructure/sports_complex.md` â€” 12 failures
- `data/infrastructure/medical_facility.md` â€” 4 failures
- `data/infrastructure/food_court.md` â€” 2 failures
- `data/student_services/committees/entrepreneurship_cell.md` â€” 3 failures

### Priority 2 â€” Review PARTIAL FAIL questions (198 questions, score = 0.5)

The bot answered but retrieved from a different document than expected.
The answers may still be factually correct (answered from an overlapping chunk).

**Action:** Increase `TOP_K` from 1 to 3 in `Pipeline/retrieve.py` for production.

---

## âš™ï¸ Configuration Used

| Parameter | Value |
|---|---|
| Retrieval model | `BAAI/bge-base-en-v1.5` |
| LLM | `qwen/qwen3-32b` via Groq |
| Pinecone Index | `qwen-local-rag` |
| `top_k` | `1` (testing config) |
| Total questions | 250 |
| Avg latency | 8.42s |

---

*Auto-generated by `direct_eval.py` on 2026-06-09 23:42*  
*Branch: `Dhruvam/campus-cocurricular-cluster`*