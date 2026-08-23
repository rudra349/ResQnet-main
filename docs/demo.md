# ResQNet — 3-Minute Hackathon Demo Script

## Demo Script & Flow

### Scene 1: Emergency Operations Center Dashboard (0:00 - 0:30)
- Open `http://localhost:3000`.
- Point out the dark-themed command center dashboard.
- Show the interactive map displaying Village Alpha, Village Bravo, Village Charlie, shelters, hospitals, and relief teams.
- Highlight the active government flood alert: *"SEVERE FLOOD WARNING: Region Alpha..."*

### Scene 2: Submitting a Field Report & Storing Memory (0:30 - 1:00)
- Click **Report Incident**.
- Enter: *"Road 17 is flooded near Shelter 7. Truck 17 cannot reach Sector B."*
- Select **Critical** severity. Click **Submit Report**.
- Point out that this event is immediately converted into an **episodic and semantic memory** inside CockroachDB.

### Scene 3: AI Retrieval & Reasoning (1:00 - 1:45)
- Click **AI Assistant**.
- Click the demo query: *"How can Team 4 reach Shelter Alpha with Road 17 flooded?"*
- Observe the agent in real time:
  1. Executes `search_memories`.
  2. Retrieves 2024 historical memory where Road 5 was used as an alternate route.
  3. Recommends routing via Road 5.
  4. Displays Confidence: 94% and lists retrieved CockroachDB memory IDs.

### Scene 4: Offline PWA & Sync Queue (1:45 - 2:30)
- Open Chrome DevTools → Network tab → Toggle **Offline**.
- Note the top status badge instantly changes to **OFFLINE MODE**.
- Navigate to **Report Incident** and enter: *"Water shortage at Shelter Alpha: 300 units needed."*
- Click **Save Report (Offline)**.
- Note the message: *"Report saved offline into local IndexedDB queue."*
- Go to **Sync Queue** page — see `1 pending sync` item with client UUID.
- Toggle Network back to **Online**.
- Watch the PWA automatically trigger batch sync: `1 report synchronized`.

### Scene 5: Intelligence Maintained Post-Sync (2:30 - 3:00)
- Return to **AI Assistant**.
- Ask: *"Where is water most urgently needed right now?"*
- The AI retrieves the newly synchronized offline report and recommends dispatching water to Shelter Alpha!
- Conclude: *"ResQNet — An AI agent that remembers operational experience and continues functioning despite unreliable connectivity."*
