> **Team B – Campus Life & Co-curricular**  
> **Done By:** Parth Agrawal  
> **Date:** 2026-06-09  

---

# Knowledge Gaps: Campus Life & Co-curricular

**Purpose:** Identify missing knowledge based on failed evaluation questions and system audit from the live chatbot evaluation.

## Level 1 Gaps (Static Knowledge Missing)

### Gap 1
* **Question:** Are mattresses provided in DAU hostel rooms?
* **Failure Reason:** The expected source `halls_of_residence.md` lists furniture (bed, table, chair, cupboard) but does not mention mattresses. However, `hostel_rules_and_regulations.md` states that residents are expected to bring their own mattresses, creating a gap/discrepancy between the documents.
* **Missing Knowledge:** Clear confirmation in the core hostel facilities guide about whether mattresses are provided or must be purchased by students.
* **Required Source:** Hostel Management Committee / Warden Office.
* **Priority:** Medium

### Gap 2
* **Question:** Is hostel accommodation mandatory for B.Tech students?
* **Failure Reason:** The expected source `halls_of_residence.md` does not specify if hostel stay is mandatory for B.Tech students. Although the separate `dean_students.md` mentions that it is residential and mandatory, the core infrastructure document lacks this rule.
* **Missing Knowledge:** Clear statement of residential rules and residency requirements for B.Tech students in the primary halls of residence information guide.
* **Required Source:** Dean of Students Office.
* **Priority:** High

### Gap 3
* **Question:** What type of internet connection is available in the Women's HoR?
* **Failure Reason:** The document `halls_of_residence.md` only mentions that 'internet facility is provided free of cost' but does not specify the connection type (Wi-Fi vs LAN) for the Women's HoR, whereas the FAQ section in `dean_students.md` specifies that the Women's HoR has Wi-Fi and LAN connections.
* **Missing Knowledge:** Explicit specification of the type of internet connection (Wi-Fi/LAN) available across different hostels in the core facilities guide.
* **Required Source:** TechSupport Committee / Assistant Manager - Hostel.
* **Priority:** Low

### Gap 4
* **Question:** What is the full official name of the university (DAU)?
* **Failure Reason:** The expected file `location_contact.md` lists the acronyms DAU and DA-IICT and the postal address, but it never writes out the full official name 'Dhirubhai Ambani University' in the contact detail page.
* **Missing Knowledge:** Official university naming conventions, history of name change from DA-IICT to DAU, and legal notification on the contact pages.
* **Required Source:** Executive Registrar's Office.
* **Priority:** Medium

### Gap 5 (System Audit Gap)
* **Question:** Mess & Canteen Policies
* **Failure Reason:** The data folder lacks any document detailing Mess menu, Mess rebate policies, food court pricing guidelines, or canteens timings. The HMC and CMC are mentioned, but no actual operational rules are indexed.
* **Missing Knowledge:** Detailed mess rules, menus, canteen timings, rebate procedures, and food court operations guidelines.
* **Required Source:** Cafeteria Management Committee (CMC) / Food & Beverage Services.
* **Priority:** High

### Gap 6
* **Question:** Is there a 24x7 ambulance facility on the DAU campus?
* **Failure Reason:** The expected source `medical_assistance_sop.md` does not mention the availability of a 24x7 ambulance facility or emergency transport procedures, leading the model to trigger a fallback response.
* **Missing Knowledge:** Explicit confirmation and protocols regarding 24x7 ambulance/emergency vehicle services on campus.
* **Required Source:** Medical Centre Admin / Head of HR & Administration.
* **Priority:** High

## Retrieval-Related Gaps (RAG Routing Limitations)

A total of 41 questions failed due to retrieval routing errors in the pre-migration system (e.g., BGE/Pinecone matching alternative documents containing similar terminology instead of the expected file).

### Gap (Routing) - Q018
* **Question:** List all 8 student committees at DAU.
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'dean_students.md', 'dean_students_tab.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q071
* **Question:** Who is the Convenor of the EHC?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_annual_report_2024_25_25326_pdf.md', 'dean_students.md', 'daiict_ac_in_sites_default_files_other_files_annual_report_2024_25_25326_pdf.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q112
* **Question:** How many incubates has DCEI produced?
* **Failure Reason:** RAG routing error. Retrieved: ['entrepreneurship_cell.md', 'entrepreneurship_cell.md', 'entrepreneurship_cell.md'] instead of `data/student_services/committees/entrepreneurship_cell.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q114
* **Question:** How many sports facilities does DAU have in total?
* **Failure Reason:** RAG routing error. Retrieved: ['concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md', 'dean_students_tab.md', 'daiict_ac_in_sites_default_files_naac_addendum_final_pdf.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q115
* **Question:** How many basketball courts does DAU have?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_tender_renovation_of_basketball_cou.md', 'daiict_ac_in_sites_default_files_other_files_annual_report_2024_25_25326_pdf.md', 'programs_of_study.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q117
* **Question:** Does DAU have a cricket field?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students_tab.md', 'daiict_ac_in_sites_default_files_other_files_annual_report_2024_25_25326_pdf.md', 'concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q118
* **Question:** What is the length of the athletic track at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students_tab.md', 'bs_ms_data_science_artificial_intelligence_admissions.md', 'bs_ms_information_technology_admissions.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q119
* **Question:** How many volleyball courts does DAU have?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_annual_report_2024_25_25326_pdf.md', 'food_court.md', 'daiict_ac_in_sites_default_files_other_files_tender_renovation_of_basketball_cou.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q121
* **Question:** Does DAU have a gymnasium?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'dean_students_tab.md', 'concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q122
* **Question:** Is there a yoga and meditation zone on the DAU campus?
* **Failure Reason:** RAG routing error. Retrieved: ['dau_celebrated_international_day_of_yoga_2025.md', 'celebrate_international_yoga_day_at_dau.md', 'dau_celebrated_international_day_of_yoga_2025.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q124
* **Question:** When does Phase I of sports coaching take place at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md', 'dean_students_tab.md', 'undergraduate_admissions_gujarat_category.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q125
* **Question:** When does Phase II of sports coaching take place at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md', 'dean_students_tab.md', 'undergraduate_admissions_nri_and_foreign_national_category.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q126
* **Question:** What inter-collegiate tournaments does DAU participate in at state/national level?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students_tab.md', 'concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md', 'daiict_ac_in_sites_default_files_other_files_policy_student_research_excellence_.md'] instead of `data/infrastructure/sports_complex.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q127
* **Question:** How many Halls of Residence are there at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students_tab.md', 'hostel_rules_and_regulations.md', 'dean_students.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q134
* **Question:** What furniture is provided in DAU hostel rooms?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'dean_students_tab.md', 'admissions_msc_agriculture_analytics.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q135
* **Question:** Is internet provided in DAU hostels?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'admissions_msc_agriculture_analytics.md', 'dean_students_tab.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q136
* **Question:** Is hot water available in the DAU hostels?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'admissions_msc_agriculture_analytics.md', 'dean_students_tab.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q137
* **Question:** Is there a laundry/dhobi facility at DAU hostels?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'dean_students_tab.md', 'admissions_msc_agriculture_analytics.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q138
* **Question:** Are there TV rooms in DAU hostels?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'dean_students_tab.md', 'admissions_msc_agriculture_analytics.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q141
* **Question:** Can PG students get hostel accommodation at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['admissions_msc_agriculture_analytics.md', 'dean_students_tab.md', 'dean_students.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q143
* **Question:** Is there a guest room available in the Women's hostel and for what purpose?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_nep_2020.md', 'dean_students.md', 'daiict_ac_in_sites_default_files_other_files_hostel_rules_and_regulations_pdf.md'] instead of `data/infrastructure/halls_of_residence.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q161
* **Question:** Is ragging allowed at DAU and what are the consequences?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_anti_ragging_committee_2025_26_1808.md', 'curbing_ragging.md', 'disciplinary_rules.md'] instead of `data/student_services/rules/hostel_rules_and_regulations.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q166
* **Question:** Can students park 4-wheelers (cars) on the DAU campus?
* **Failure Reason:** RAG routing error. Retrieved: ['academic_policy_vehicle_rules_for_students.md', 'academic_policy_da_iict_vehicle_rules_for_students.md', 'vehicle_rules_for_students.md'] instead of `data/student_services/rules/hostel_rules_and_regulations.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q172
* **Question:** What is the fine for entertaining a visitor without prior intimation?
* **Failure Reason:** RAG routing error. Retrieved: ['vehicle_rules_for_students.md', 'vehicle_rules_for_students.md', 'vehicle_rules_for_students.md'] instead of `data/student_services/rules/hostel_rules_and_regulations.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q192
* **Question:** Which hospitals have signed an MoU with DAU for student medical treatment?
* **Failure Reason:** RAG routing error. Retrieved: ['medical_assistance_sop.md', 'medical_assistance_sop.md', 'academic_policy_medical_facilities_for_students_of_da_ii.md'] instead of `data/infrastructure/medical_facility.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q193
* **Question:** How far is Aashka Hospital from the DAU campus?
* **Failure Reason:** RAG routing error. Retrieved: ['location_contact.md', 'location_contact.md', 'workshop_on_rtl_to_gds_ii_vlsi_design_and_hardware_security_for_trusted_memory_s.md'] instead of `data/infrastructure/medical_facility.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q194
* **Question:** Is there a 24x7 vehicle available for medical emergencies at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['medical_assistance_sop.md', 'academic_policy_medical_facilities_for_students_of_da_ii.md', 'academic_policy_medical_facilities_emergency_procedure_for_students.md'] instead of `data/infrastructure/medical_facility.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q195
* **Question:** What is the Group Mediclaim Insurance coverage amount for DAU students?
* **Failure Reason:** RAG routing error. Retrieved: ['medical_assistance_sop.md', 'academic_policy_medical_facilities_emergency_procedure_for_students.md', 'academic_policy_medical_facilities_for_students_of_da_ii.md'] instead of `data/infrastructure/medical_facility.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q196
* **Question:** Which insurance company provides the DAU Group Mediclaim policy?
* **Failure Reason:** RAG routing error. Retrieved: ['medical_assistance_sop.md', 'academic_policy_medical_facilities_emergency_procedure_for_students.md', 'academic_policy_medical_facilities_for_students_of_da_ii.md'] instead of `data/infrastructure/medical_facility.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q197
* **Question:** What type of medical treatment does the DAU Mediclaim policy cover?
* **Failure Reason:** RAG routing error. Retrieved: ['medical_assistance_sop.md', 'medical_assistance_sop.md', 'academic_policy_medical_facilities_for_students_of_da_ii.md'] instead of `data/infrastructure/medical_facility.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q202
* **Question:** What is the contact email of the DAU Medical Centre?
* **Failure Reason:** RAG routing error. Retrieved: ['workshop_on_rtl_to_gds_ii_vlsi_design_and_hardware_security_for_trusted_memory_s.md', 'location_contact.md', 'dean_students.md'] instead of `data/student_services/medical_assistance_sop.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q203
* **Question:** What hospitals are empanelled with DAU for student treatment (full list)?
* **Failure Reason:** RAG routing error. Retrieved: ['medical_assistance_sop.md', 'medical_assistance_sop.md', 'academic_policy_medical_facilities_emergency_procedure_for_students.md'] instead of `data/student_services/medical_assistance_sop.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q216
* **Question:** Where can students find anti-ragging information at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_anti_ragging_committee_2025_26_1808.md', 'glimpses_of_students_participating_in_the_anti_ragging_week.md', 'daiict_ac_in_sites_default_files_other_files_anti_ragging_committee_2025_26_1808.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q219
* **Question:** What is HackOut at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['dau_drives_innovation_for_a_sustainable_future_with_hackout_25.md', 'dau_drives_innovation_for_a_sustainable_future_with_hackout_25.md', 'three_teams_from_da_iict_took_part_in_the_ingenious_hackathon_organised_at_ahmed.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q220
* **Question:** What is YouthRun at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_alumni_connect_vol_1_no_1_oct_dec_2.md', 'daiict_ac_in_sites_default_files_naac_evaluative_report_pdf.md', 'daiict_ac_in_themes_daiict_images_daiict_ar_2015_16_pdf.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q226
* **Question:** What academic advice is given to first-year students at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['dean_students.md', 'word_guidance.md', 'dean_students_tab.md'] instead of `data/student_services/first_year_in_campus.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q227
* **Question:** Where is the DAU campus located?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_annual_report_2024_25_25326_pdf.md', 'programs_of_study.md', 'workshop_on_tensor_computation_and_optimization_with_applications_in_data_scienc.md'] instead of `data/student_services/contact/location_contact.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q231
* **Question:** What is Concours in the context of DAU sports?
* **Failure Reason:** RAG routing error. Retrieved: ['concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md', 'concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md', 'daiict_ac_in_sites_default_files_other_files_annual_report_2024_25_25326_pdf.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q234
* **Question:** What is Freshers' Weekend at DAU?
* **Failure Reason:** RAG routing error. Retrieved: ['concours_2025_a_celebration_of_sports_and_spirit_at_dhirubhai_ambani_university.md', 'dau_organises_orientation_programme_for_its_undergraduate_students.md', 'undergraduate_admissions_gujarat_category.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q237
* **Question:** What is i.Fest and which club organizes it?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_annual_report_2022_23_pdf.md', 'daiict_ac_in_sites_default_files_other_files_6_1_1_vision_mission_strategic_plan.md', 'daiict_ac_in_sites_default_files_other_files_newsletter_vol_5_pdf.md'] instead of `data/student_services/dean_students.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

### Gap (Routing) - Q243
* **Question:** How should students or employees resolve disputes at DAU as a first step?
* **Failure Reason:** RAG routing error. Retrieved: ['daiict_ac_in_sites_default_files_other_files_dau_policy_against_sexual_harassmen.md', 'daiict_ac_in_sites_default_files_other_files_faculty_handbook_pdf.md', 'internal_complaint_committee.md'] instead of `data/student_services/grievance_redressal_cell.md`.
* **Missing Knowledge:** Query routing optimization and precise document metadata/chunk indexing for the expected file.
* **Required Source:** RAG Pipeline / Indexing Admin.
* **Priority:** Medium

