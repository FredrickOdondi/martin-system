# ECOWAS Summit AI System - Implementation Specification

> **Important:** This document serves as the authoritative reference for all implementation decisions.  
> Cross-check all features against this specification to ensure alignment with the Lazarus architectural mandates.

---

## Agent Workflows and Capabilities

Each agent follows a structured workflow to support its TWG through the lifecycle of meetings and outputs. Below is an outline of how a typical TWG cycle might operate with AI support, highlighting the agents' capabilities at each stage:

---

## 1. Meeting Scheduling & Invitations

When a TWG needs to convene (e.g. for a bi-weekly virtual call or an in-person workshop), the TWG's AI agent helps schedule the meeting:

### Time Proposal & Conflict Detection
- The agent can propose a meeting time (based on availability data or preset cadence) or confirm a time given by the TWG lead
- It considers time zones of all participants
- Checks against any known conflicts (the **Supervisor agent** helps avoid cross-TWG clashes)

### Structured Invitation Email
The agent prepares a structured invitation email to participants, including:
- A clear subject line (e.g. "Energy TWG Meeting – [Date]: Agenda & Materials")
- A formal salutation and introduction, referencing the Summit and TWG purpose
- Key details: date, time (with time zone), duration, and platform/venue (with video call link or address)
- An **.ics calendar invite file** so participants can add the event to their calendars easily
- Mention of attached materials (agenda, background docs) and any preparation expected
- A polite closing, using the Summit Secretariat or TWG chair's name/title as appropriate

### Agenda Drafting
The agenda for the meeting is drafted at the time of invitation using a template:
```
Agenda:
1) Review of Action Items from last meeting
2) Policy Proposal: Regional Power Pool Expansion (discussion led by [Name])
3) Investment Pipeline Update – review candidate projects
4) AOB & Next Steps
```

### Meeting Pack (Attachments & Pre-reads)
The agent automatically compiles a meeting pack, which could include:
- **The Agenda (PDF)**, formatted on summit letterhead
- **Pre-read documents**: concept notes, relevant treaties, or last meeting's minutes
- Any presentations or papers participants should read beforehand
- All attachments follow naming conventions (e.g. `EnergyTWG_Agenda_2026-01-15.pdf`)

### Personalization
- By default, uses broad address (e.g. "Dear TWG Members")
- Can personalize greetings for VIPs if needed

---

## 2. Reminders and Follow-ups

Once invites are sent, the agent monitors responses:

- **RSVP Tracking**: Keeps track of RSVPs using calendar API or parsing email replies
- **Reminder Emails**: Sends gentle reminder a few days before the meeting to non-responders
- **Day-of Confirmation**: Sends confirmation with meeting link and last-minute updates
- **Reschedule Handling**: If someone proposes a new time or has a conflict, alerts TWG lead

---

## 3. Meeting Facilitation (During Meeting)

The AI agent can play a rapporteur/secretary role:

### Virtual Meetings
- Join the call as a bot to record/transcribe the discussion (Zoom/Teams integration)
- Speech-to-text for accurate minutes
- Monitor agenda progression
- Prompt chair if time is running low or speaker is absent
- Capture key decisions and action items in real time
- Display live shared notes document

### Physical Meetings
- Relies on human uploading audio recording or notes afterward
- Workflow shifts to after-meeting summarization

---

## 4. Post-Meeting Minutes & Outcomes

After the meeting, the TWG agent automatically produces Meeting Minutes and Summary of Outcomes:

### Minutes Format
Using transcript or notes, draft minutes in standard format:
- List of participants (and who was absent/apologies)
- Recap of each agenda point: key discussion points and conclusions
- **Decisions made**: clearly highlighted
- **Action items**: with owner and due date

### Quality Control
- Minutes phrased formally and objectively
- Cross-checks facts/figures against knowledge base
- Flags anything it cannot verify for human review

### Distribution
- Sends minutes to all participants via email
- Structured email with key decisions summarized
- Urgent action items in email body for visibility

### Knowledge Base Update
- Action items logged in task tracker
- Important decisions indexed for future context
- New documents expected later trigger follow-up reminders

---

## 5. TWG Output Preparation

Throughout the cycle, agents assist in drafting TWG deliverables:

### Policy Drafts & Concept Notes ("Rapporteur Mode")
- Generate initial "zero drafts" of policy papers or TWG reports
- Use inputs from discussions and knowledge repository
- Humans review, edit, and refine drafts

### Session Briefs and Talking Points
- Create session brief documents for summit panels
- Include talking points for speakers, slide outlines, background info

### Investment Project Pipeline
- Each thematic agent maintains internal list of project ideas
- Resource Mobilization agent pulls together into central database
- Evaluates using scoring criteria (alignment %, readiness score)
- Produces brief for each potential flagship project
- Flags missing data for follow-up
- Generates ranked list of top projects

### Cross-TWG Synthesis (Supervisor Agent)
- **Weekly Progress Reports**: summarizing what each TWG accomplished, risks/blockers
- **Draft Abuja Declaration**: assembles policy recommendations from all TWGs
- Ensures language consistency and no contradictory targets
- **Freetown Communiqué**: similar approach for ministerial communique

---

## 6. Iteration and Next Meeting

After each meeting's outputs:

- **Auto-schedule Next Meeting**: Proposes date (e.g. two weeks out) and repeats cycle
- **Timeline Tracker**: Visible on portal showing upcoming meetings and milestones
- **Escalation Alerts**: If TWG is falling behind, alerts Secretariat and suggests extra meeting

---

## User Experience and Portal Design

The front-end is a web-based portal (desktop and mobile) for human users to interact with AI agents.

### User Roles

| Role | Description | Portal Access |
|------|-------------|---------------|
| **TWG Facilitators** | Secretariat staff/TWG leads | Full access to their TWG workspace |
| **Summit Administrators** | Secretariat Leadership | Cross-TWG oversight, dashboards, settings |
| **TWG Members** | Invited participants (ministry reps, experts) | Email/calendar only (no portal login) |
| **Technical Support** | Lazarus team | Admin interface for monitoring |

---

## Human Oversight Mandates

> **Critical**: The AI drafts, but humans approve every substantive output without exception.

### Approval Gates
1. **Before Send Invites**: Conflict Check via Supervisor Agent
2. **Agenda Generation**: Human review before sending
3. **Minutes**: Mandatory "Approve & Send" gate before distribution
4. **Action Items**: Review extracted items before confirming
5. **Policy Drafts**: Multiple review cycles with human editors

### Citation Checks
- AI-generated policy claims must link back to authorized source documents
- Prevents hallucinations in official communications

### Data Sovereignty
- TWG pillar isolation: each agent's context strictly isolated to that group's data
- No cross-TWG data leakage without explicit Supervisor coordination

---

## Example Scenario

> The Energy TWG lead logs into the portal and sees that the AI agent has already prepared a draft agenda for the next meeting, based on the previous meeting's unresolved items and upcoming timeline checkpoints. They make a minor tweak (adding an item about a newly proposed hydro project) and click "Send Invites."
>
> The agent emails everyone with the structured invite and attachments. A day after the meeting, the agent presents the draft minutes for approval. The lead corrects a couple of points and approves – the agent then emails it out and updates the shared "Decisions Log."
>
> Meanwhile, the Supervisor agent has taken note of a decision affecting another TWG (Agriculture's fertilizer initiative depends on Energy's power project) and notifies the Agriculture agent to include that in their next agenda. This kind of seamless, behind-the-scenes coordination is what the system will deliver.

---

## Analogy: Diplomatic Briefing Room

Think of this process as a **Diplomatic Briefing Room**:

- **TWG Agent** = The diligent junior aide who prepares all the folders and notes (the "worker bee")
- **Human Facilitator** = The Senior Diplomat who reviews the folder and physically signs off on contents
- **Nothing leaves the room** or is added to the official record until the Senior Diplomat approves
