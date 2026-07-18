import csv
import random

# Base topics from the cluster image
level1_topics = [
    "Academic Regulations", "Programme Handbooks", "Teaching Schedule",
    "Examination Guidelines", "Academic Calendar Updates", "HR Policies",
    "CEP Guidelines Policy", "Consultancy Policy", "Seed Grant Policy",
    "CEA Guidelines", "Teaching Load & Timetable Updates", "Committee Terms of Reference",
    "Department Documents"
]

level2_topics = [
    "Lab Equipment Booking & Availability", "Laboratory Schedules",
    "Research Grant Deadlines", "Committee Meeting Schedules",
    "Circular & Notice Updates", "Accreditation Preparation Tips",
    "Teaching & Pedagogy Best Practices", "Student Academic Records & Performance Analytics",
    "Consultancy Timetable", "Student Mentoring Strategies", "Publication & Research Impact Advice"
]

level3_topics = [
    "Senior Faculty Mentorship & Guidance", "Curriculum Improvement Suggestions",
    "Departmental Best Practices", "Committee Experience & Guidance",
    "Consultancy Experience Sharing", "Conference Recommendations",
    "Administrative Workflow Guidance"
]

level4_topics = [
    "LMS Integration", "ERP Integration", "AI Faculty Dashboard",
    "AI Curriculum Assistant", "Research Collaboration Engine",
    "Multi-Agent Faculty Assistant", "Accreditation Assistant",
    "Meeting Summarizer AI", "Integration with Digital Library",
    "AI Report Generation", "Document Management System", "Faculty Analytics & Insights"
]

questions = []

def add_q(q, cat, lvl, top, src, ans, ftype):
    questions.append({
        "Question": q.replace('"', ''),
        "Category": cat,
        "Cluster_Level": lvl,
        "Topic": top,
        "Expected_Source": src,
        "Expected_Answer": ans.replace('"', ''),
        "Failure_Type": ftype
    })

# --- Level 1 ---
for i, topic in enumerate(level1_topics):
    add_q(f"What are the general guidelines for {topic} at DA-IICT?", "Level1_Static", "Level 1", topic, "faculty-handbook", f"The general guidelines for {topic} define the standard operating procedures and static rules.", "Retrieval Miss")
    add_q(f"Where can a new faculty member find the {topic} document?", "Level1_Static", "Level 1", topic, "faculty-handbook", f"It can be found in the faculty portal under the static information section.", "Retrieval Miss")
    add_q(f"Who is responsible for updating the {topic} at DAU?", "Level1_Static", "Level 1", topic, "faculty-handbook", "The relevant Dean or administrative office is responsible.", "Role Confusion")
    if i % 2 == 0:
        add_q(f"Is the {topic} applicable to visiting faculty as well?", "Level1_Static", "Level 1", topic, "faculty-handbook", "Generally yes, but specific clauses may apply differently to visiting faculty.", "Policy Edge Case")

# --- Level 2 ---
for i, topic in enumerate(level2_topics):
    add_q(f"How often are the {topic} updated?", "Level2_Dynamic", "Level 2", topic, "faculty-handbook", f"They are updated continuously or dynamically based on real-time data.", "Retrieval Miss")
    add_q(f"What system integrations are required to fetch data for {topic}?", "Level2_Dynamic", "Level 2", topic, "faculty-handbook", "It requires integrations with ERP, LMS, portals, and dashboards.", "Cross-Domain")
    add_q(f"Who should a faculty member contact if there is an error in their {topic}?", "Level2_Dynamic", "Level 2", topic, "faculty-handbook", "They should contact the respective administrative department handling dynamic records.", "Role/Contact")
    if i % 2 != 0:
        add_q(f"Can faculty access {topic} from off-campus networks?", "Level2_Dynamic", "Level 2", topic, "faculty-handbook", "Yes, typically through a secure VPN or official portal.", "Policy Edge Case")

# --- Level 3 ---
for i, topic in enumerate(level3_topics):
    add_q(f"What tacit knowledge is captured under {topic}?", "Level3_Human", "Level 3", topic, "faculty-handbook", "It captures best practices, experiences, and practical guidance from senior faculty and experts.", "Retrieval Miss")
    add_q(f"How can junior faculty benefit from the {topic} repository?", "Level3_Human", "Level 3", topic, "faculty-handbook", "By learning from documented strategies and experiences of senior peers.", "Retrieval Miss")
    add_q(f"Who contributes content to the {topic} module?", "Level3_Human", "Level 3", topic, "faculty-handbook", "Senior faculty, committee members, and domain experts.", "Role/Contact")

# --- Level 4 ---
for i, topic in enumerate(level4_topics):
    add_q(f"Is the {topic} currently available for faculty use?", "Level4_Future", "Level 4", topic, "faculty-handbook", f"No, {topic} is planned for future integration and automation.", "Future/Planned")
    add_q(f"What is the expected timeline for deploying the {topic}?", "Level4_Future", "Level 4", topic, "faculty-handbook", "It is part of the future roadmap and planning is in progress.", "Future/Planned")
    add_q(f"How will the {topic} improve faculty workflows once implemented?", "Level4_Future", "Level 4", topic, "faculty-handbook", "It will provide long-term capability expansion, automation, and intelligent services.", "Future/Planned")

# Add some specific Cross-Cluster questions
add_q("How does Level 1 static info differ from Level 2 dynamic info?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "Level 1 is complete policies/handbooks, while Level 2 requires real-time system integrations and is updating continuously.", "Cross-Domain")
add_q("Which levels of the Faculty Intelligence AI Platform are currently marked as complete?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "Level 1 (Static Information) and Level 3 (Human-Provided Knowledge) are complete.", "Cross-Domain")
add_q("Why is the overall faculty cluster readiness at 95%?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "Because Levels 1 and 3 are complete, Level 2 is initiated, and only Level 4 is planned, leaving a small gap for future integrations.", "Number Trap")
add_q("If a faculty wants to know both their Academic Regulations and their Lab Schedule, which levels are involved?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "Academic Regulations are Level 1 (Static) and Lab Schedules are Level 2 (Dynamic).", "Cross-Domain")
add_q("Does the AI Faculty Dashboard depend on the ERP Integration?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "Both are planned under Level 4 Future Integrations, likely to be interconnected.", "Cross-Domain")

# Specifics from the cluster legend
add_q("What does the blue ring represent in the cluster legend?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "The blue ring represents Level 1 - Collected (Static) information.", "Retrieval Miss")
add_q("What does the green ring represent in the cluster legend?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "The green ring represents Level 2 - Dynamic information.", "Retrieval Miss")
add_q("What does the yellow ring represent in the cluster legend?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "The yellow ring represents Level 3 - Human Provided knowledge.", "Retrieval Miss")
add_q("What does the purple ring represent in the cluster legend?", "Cross_Cluster", "Cross Level", "Overall Platform", "faculty-cluster", "The purple ring represents Level 4 - Future Integrations.", "Retrieval Miss")

# Write to CSV
keys = questions[0].keys()
with open('eval/cluster_questions.csv', 'w', newline='', encoding='utf-8') as output_file:
    dict_writer = csv.DictWriter(output_file, fieldnames=keys)
    dict_writer.writeheader()
    dict_writer.writerows(questions)

print(f"Successfully generated {len(questions)} questions.")
