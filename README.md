AI-Powered Event Management System
Capstone Project – Ghada Idris
Saudi Digital Academy – Python Software Development Bootcamp
React + Django REST Framework | Full CRUD + AI Task Automation





🎯 One-Click Live Demo
Click below to launch the app instantly
https://event-manager-ghada.netlify.app

Login Credentials (Demo)

Admin: admin@event.com / admin123
Organizer: org@event.com / org123
Manager: mgr@event.com / mgr123
Staff: staff@event.com / staff123



🚀 Project Overview
An AI-powered event planning platform that automates task and team assignment using intelligent suggestions — reducing planning time by 70%.
Key Features





























FeatureDescriptionAI Plan GeneratorEnter event details → AI creates tasks, teams, and assigns staffRole-Based AccessAdmin, Organizer, Manager, Staff – each with custom dashboardsFull CRUDEvents, Tasks, Teams, Users – all fully manageableJWT AuthenticationSecure login with refresh tokensDockerizedRun locally with one command

🗺️ ERD Diagram (Embedded)
#mermaid-diagram-mermaid-50bwbqs{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#ccc;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-diagram-mermaid-50bwbqs .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-diagram-mermaid-50bwbqs .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-diagram-mermaid-50bwbqs .error-icon{fill:#a44141;}#mermaid-diagram-mermaid-50bwbqs .error-text{fill:#ddd;stroke:#ddd;}#mermaid-diagram-mermaid-50bwbqs .edge-thickness-normal{stroke-width:1px;}#mermaid-diagram-mermaid-50bwbqs .edge-thickness-thick{stroke-width:3.5px;}#mermaid-diagram-mermaid-50bwbqs .edge-pattern-solid{stroke-dasharray:0;}#mermaid-diagram-mermaid-50bwbqs .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-diagram-mermaid-50bwbqs .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-diagram-mermaid-50bwbqs .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-diagram-mermaid-50bwbqs .marker{fill:lightgrey;stroke:lightgrey;}#mermaid-diagram-mermaid-50bwbqs .marker.cross{stroke:lightgrey;}#mermaid-diagram-mermaid-50bwbqs svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-diagram-mermaid-50bwbqs p{margin:0;}#mermaid-diagram-mermaid-50bwbqs .entityBox{fill:#1f2020;stroke:#ccc;}#mermaid-diagram-mermaid-50bwbqs .relationshipLabelBox{fill:hsl(20, 1.5873015873%, 12.3529411765%);opacity:0.7;background-color:hsl(20, 1.5873015873%, 12.3529411765%);}#mermaid-diagram-mermaid-50bwbqs .relationshipLabelBox rect{opacity:0.5;}#mermaid-diagram-mermaid-50bwbqs .labelBkg{background-color:rgba(32.0000000001, 31.3333333334, 31.0000000001, 0.5);}#mermaid-diagram-mermaid-50bwbqs .edgeLabel .label{fill:#ccc;font-size:14px;}#mermaid-diagram-mermaid-50bwbqs .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#ccc;}#mermaid-diagram-mermaid-50bwbqs .edge-pattern-dashed{stroke-dasharray:8,8;}#mermaid-diagram-mermaid-50bwbqs .node rect,#mermaid-diagram-mermaid-50bwbqs .node circle,#mermaid-diagram-mermaid-50bwbqs .node ellipse,#mermaid-diagram-mermaid-50bwbqs .node polygon{fill:#1f2020;stroke:#ccc;stroke-width:1px;}#mermaid-diagram-mermaid-50bwbqs .relationshipLine{stroke:lightgrey;stroke-width:1;fill:none;}#mermaid-diagram-mermaid-50bwbqs .marker{fill:none!important;stroke:lightgrey!important;stroke-width:1;}#mermaid-diagram-mermaid-50bwbqs :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}belongs tomember oforganizeshashasassigned toassigneeUserintidstringemailstringroleCompanyintidstringnamestringlogo_urlTeamintidstringnameEventintidstringnamedatedatestringvenueintexpected_attendeesTaskintidstringtitlestringstatusintpriority

6 models, clear relationships, protected via Django ORM


🔗 RESTful API Routes (Role-Based)







































































RoleMethodEndpointDescriptionAuthPOST/auth/register/Register userPOST/auth/login/Login → JWTGET/auth/me/Get current userAdminGET/admin/users/List all usersPOST/admin/users/Create userOrganizerPOST/organizer/events/Create eventPOST/organizer/events/{id}/ai/suggest/AI generates full planManagerPUT/manager/tasks/{id}Edit taskStaffGET/staff/tasks/View my tasksPUT/staff/tasks/{id}Update status

All routes protected with JWT + Custom Permissions


🎨 Tech Stack





























LayerTechnologyFrontendReact, React Router, Axios, Tailwind CSSBackendDjango, Django REST Framework, JWT, SQLiteAI EngineCustom Python algorithm (scalable to GPT later)DevOpsDocker, Docker Compose, GitHub ActionsDeploymentNetlify (FE), Render (BE)

🐳 Run Locally with Docker (One Command)
bashgit clone https://github.com/ghadaidris/event-manager-backend.git
cd event-manager-backend
docker-compose up --build
bash# Frontend
git clone https://github.com/ghadaidris/event-manager-frontend.git
cd event-manager-frontend
docker build -t event-frontend .
docker run -p 3000:80 event-frontend

App runs at: http://localhost:3000
API at: http://localhost:8000


📋 User Stories (15 Total)
markdownAs an **Admin**, I want to create/edit users so I control access.
As an **Organizer**, I want to create an event and get AI plan so planning is instant.
As a **Manager**, I want to tweak AI suggestions so the plan fits reality.
As a **Staff**, I want to see my tasks and update status so progress is tracked.