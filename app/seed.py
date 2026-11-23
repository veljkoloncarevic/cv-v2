"""Seed the database with the current live-site content.

Logo/photo files are NOT included — upload them through /admin after first boot,
or drop them into data/uploads/ and set the filenames here before seeding.
"""
from .db import execute, query

PROFILE = dict(
    full_name="Veljko Lončarević",
    headline="Data Scientist",
    birthdate="2002-01-01",          # <- set your real date; age renders automatically
    bio=(
        "Master Engineer of Information Technology, PhD student at University of "
        "Kragujevac. Working as a Data Scientist in the Business Intelligence "
        "Department (Enterprise Effectiveness) for Brezna and Avnet Business Services "
        "(EMEA). Certified in Machine Learning, Artificial Intelligence, and Databases "
        "by Microsoft, Google, Oracle, Huawei, IBM, Deeplearning.AI. Finished an "
        "internship for a Back-end developer.\n"
        "Was engaged as a Student Assistant and an Industry Fellow; currently working "
        "as a Research Assistant at the Faculty of Technical Sciences in Čačak.\n"
        "Working on cutting-edge research within the field of Artificial Intelligence, "
        "driving innovation and advancing knowledge in this dynamic domain.\n"
        "Passionate about leveraging technology to solve complex challenges and drive "
        "organizational success."
    ),
    email="contact@veljkoloncarevic.in.rs",
    phone="+381 61 297 3553",
    location="Čačak, Serbia",
    github_label="@theharoold",
    github_url="https://github.com/theharoold",
    linkedin_label="Veljko Lončarević",
    linkedin_url="https://www.linkedin.com/in/veljkoloncarevic/",
    photo_path=None,
    pdf_path=None,
)

PAGES = [
    dict(slug="", title="Veljko Lončarević | Resume", nav_label="Home", nav_icon="fa-house",
         meta_description="Data Scientist, PhD student and AI/ML researcher based in "
                          "Čačak, Serbia. Resume, work experience and publications.",
         sort_order=10),
    dict(slug="resume", title="Veljko Lončarević | Resume", nav_label="Resume",
         nav_icon="fa-file-lines",
         meta_description="Work experience, internships and education.", sort_order=20),
    dict(slug="literature", title="Veljko Lončarević | Literature", nav_label="Literature",
         nav_icon="fa-book",
         meta_description="Poems and verse by Veljko Lončarević.",
         sort_order=30),
]

SECTIONS = [
    # (page_slug, slug, title, col, layout, sort_order)
    ("", "work-experience", "Work Experience", "left", "timeline", 10),
    ("", "summer-internships", "Summer Internships", "left", "timeline", 20),
    ("", "education", "Education", "left", "timeline", 30),
    ("", "publications", "Publications", "right", "publications", 10),
]

ITEMS = {
    "work-experience": [
        dict(title="Data Scientist", org="Brezna D.O.O Belgrade",
             date_text="October 2023 - present",
             description=(
                 "Responsible for developing predictive models, conducting exploratory "
                 "data analysis, and collaborating with cross-functional teams to "
                 "identify opportunities for process optimization and revenue "
                 "enhancement in the Business Intelligence department for a Fortune 500 "
                 "company (Avnet EMEA). Proficient in leveraging SQL, Python, Pandas, "
                 "NumPy, Matplotlib, Seaborn, Plotly, Scikit-learn, Azure cloud "
                 "services, Thoughtspot, SQL Server Management Studio (SSMS), "
                 "Databricks machine learning, Apache Spark, MLflow, and MLlib to "
                 "extract insights and drive data-driven decisions.")),
        dict(title="Research Assistant", org="Faculty of Technical Sciences Čačak",
             date_text="February 2025 - present",
             description=(
                 "Published over 10 research papers in international scientific "
                 "conferences, including TIE, INFOTEH, CNN Tech, ICITTBT, and IcETRAN, "
                 "with a research focus on AI/ML. Award recipient for the best research "
                 "paper in the field of acoustics at IcETRAN 2025. Contributed 2 book "
                 "chapters to monographs (edited academic volumes) published by "
                 "Springer. Previously engaged in Industry Fellow and Student "
                 "Demonstrator roles at the same institution from 2021 onward.")),
    ],
    "summer-internships": [
        dict(title="DevOps Engineer Intern",
             subtitle="Edit 2023 - Comtrade System Integrations",
             org="Team Charlie | Winners of Edit 2023",
             date_text="July 2023",
             description=(
                 "As part of Team Charlie (Application delivery in a Continuous, "
                 "Automated, and Sustainable Way), I participated in the Dockerization "
                 "process and creation of a Kubernetes deployment, service, and "
                 "Horizontal Pod Autoscaler for our application. I orchestrated a "
                 "comprehensive Tekton CI/CD pipeline integrated with GitHub web hooks "
                 "and Red Hat OpenShift, ensuring seamless automation and deployment "
                 "workflows.")),
        dict(title="Backend Developer Intern", org="Del Systems D.O.O",
             date_text="July 2022 - October 2022",
             description=(
                 "I contributed to a team tasked with developing a scalable, reliable, "
                 "and highly performant back-end solution for an HR application. We "
                 "utilized Golang with the Gin Gonic framework to build robust "
                 "functionalities, ensuring seamless performance. Leveraging MySQL "
                 "RDBMS, we designed and implemented efficient data storage and "
                 "retrieval mechanisms to meet the application's demands. Additionally, "
                 "we built a RESTful API to facilitate seamless communication between "
                 "the front-end and back-end components of the application.")),
    ],
    "education": [
        dict(title="Master's degree in Information Technology",
             org="Faculty of Technical Sciences Čačak",
             subtitle="Grade: 10.00/10.00",
             date_text="October 2023 - June 2024"),
        dict(title="Bachelor's degree in Information Technology",
             org="Faculty of Technical Sciences Čačak"),
    ],
    "publications": [
        dict(group_label="IcETRAN 2025 — Čačak | IEEE",
             title="A Comparative Analysis of Different Wavelet Transformations on "
                   "Normal and Whisper Speech Recognition",
             badge="Published (M33)", date_text="June 11th, 2025"),
        dict(group_label="IcETRAN 2025 — Čačak | IEEE",
             title="Route-Based Geospatial Clustering With Unsupervised Machine Learning",
             badge="Published (M33)", date_text="June 11th, 2025"),
        dict(group_label="TIE 2024 — Čačak",
             title="Predicting Student Academic Success with Hidden Markov Models",
             badge="Published (M33)", date_text="September 21st, 2024"),
        dict(group_label="TIE 2024 — Čačak",
             title="Horizontal Scaling with Session Preservation of PHP Applications "
                   "with MVC Architecture",
             badge="Published (M33)", date_text="September 21st, 2024"),
        dict(group_label="CNN Tech — Belgrade | Springer",
             title="Proactive Code Churn Management with Version Control Systems and "
                   "Artificial Intelligence",
             badge="Published (M14)", date_text="January 7th, 2025"),
        dict(group_label="Infoteh — Jahorina | IEEE",
             title="Unified Workflow for Training and Offline Evaluation of "
                   "Recommendation Systems",
             badge="Published (M33)", date_text="March 21st, 2025"),
        dict(group_label="Infoteh — Jahorina | IEEE",
             title="Comparative Analysis of Decision Tree-Based Algorithms for "
                   "Detecting Anomalies in Web Traffic",
             badge="Published (M33)", date_text="March 22nd, 2024"),
        dict(group_label="Infoteh — Jahorina | IEEE",
             title="Predictive Modeling of Time Spent on Website with Linear Regression "
                   "and K-means",
             badge="Published (M33)", date_text="March 22nd, 2024"),
    ],
}


def seed():
    if query("SELECT id FROM profile WHERE id = 1", one=True) is None:
        cols = ", ".join(PROFILE)
        marks = ", ".join("?" * len(PROFILE))
        execute(f"INSERT INTO profile (id, {cols}) VALUES (1, {marks})",
                tuple(PROFILE.values()))

    page_ids = {}
    for p in PAGES:
        row = query("SELECT id FROM pages WHERE slug = ?", (p["slug"],), one=True)
        if row:
            page_ids[p["slug"]] = row["id"]
            continue
        page_ids[p["slug"]] = execute(
            """INSERT INTO pages (slug, title, meta_description, nav_label, nav_icon,
               sort_order) VALUES (?,?,?,?,?,?)""",
            (p["slug"], p["title"], p["meta_description"], p["nav_label"],
             p["nav_icon"], p["sort_order"]),
        )

    for page_slug, slug, title, col, layout, order in SECTIONS:
        page_id = page_ids[page_slug]
        existing = query(
            "SELECT id FROM sections WHERE page_id = ? AND slug = ?",
            (page_id, slug), one=True,
        )
        if existing:
            continue
        section_id = execute(
            """INSERT INTO sections (page_id, slug, title, col, layout, sort_order)
               VALUES (?,?,?,?,?,?)""",
            (page_id, slug, title, col, layout, order),
        )
        for i, item in enumerate(ITEMS.get(slug, []), start=1):
            execute(
                """INSERT INTO section_items (section_id, title, subtitle, org,
                   description, date_text, badge, link_url, group_label, sort_order)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (section_id, item.get("title"), item.get("subtitle"), item.get("org"),
                 item.get("description"), item.get("date_text"), item.get("badge"),
                 item.get("link_url"), item.get("group_label"), i * 10),
            )
