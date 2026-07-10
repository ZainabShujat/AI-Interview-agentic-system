"""
Scheduling Agent · An AB Talks Open Agent

Pure scheduling intelligence. No Zoom, no SMTP, no database.
Returns decisions and reasoning — the caller acts on them.
Uses Gemini to select the optimal slot if multiple conflict-free options exist.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional
import google.generativeai as genai


class SchedulingAgent:
    """
    Autonomous Scheduling Agent.

    Makes decisions, resolves conflicts, explains reasoning.
    Uses LLM for the final slot selection based on preferences.
    """
    
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if key:
            genai.configure(api_key=key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def schedule(
        self,
        recruiter_slots: List[str],
        candidate_slots: List[str],
        existing_meetings: List[dict],
        duration_minutes: int = 30,
        buffer_minutes: int = 15,
        recruiter_preferences: str = "",
        candidate_preferences: str = ""
    ) -> dict:
        """
        Full agent pipeline:
        1. Divide availability into meeting-duration-sized windows
        2. Find overlapping windows between recruiter and candidate
        3. Conflict detection against existing meetings (with buffer)
        4. (NEW) Select best slot using Gemini reasoning
        5. Return decision + reasoning
        """
        reasoning = []

        recruiter_windows = self._divide_into_windows(recruiter_slots, duration_minutes)
        candidate_windows = self._divide_into_windows(candidate_slots, duration_minutes)

        reasoning.append(f"Recruiter has {len(recruiter_windows)} possible {duration_minutes}-min windows")
        reasoning.append(f"Candidate has {len(candidate_windows)} possible {duration_minutes}-min windows")

        if not recruiter_windows or not candidate_windows:
            return {
                "status": "no_overlap",
                "selected_slot": None,
                "end_time": None,
                "reasoning": reasoning + ["Missing availability windows"],
            }

        overlaps = self._find_overlaps(recruiter_windows, candidate_windows)
        reasoning.append(f"{len(overlaps)} overlapping windows found")

        if not overlaps:
            return {
                "status": "no_overlap",
                "selected_slot": None,
                "end_time": None,
                "reasoning": reasoning + ["No overlapping availability between recruiter and candidate"],
            }

        active_meetings = [m for m in existing_meetings if m.get("status", "scheduled") == "scheduled"]
        
        valid_options = []

        for start, end in overlaps:
            slot_label = start.strftime("%A %I:%M %p")

            if self._has_conflict(start, end, active_meetings, role="recruiter", buffer_minutes=buffer_minutes):
                reasoning.append(f"{slot_label} skipped — recruiter busy")
                continue

            if self._has_conflict(start, end, active_meetings, role="candidate", buffer_minutes=buffer_minutes):
                reasoning.append(f"{slot_label} skipped — candidate busy")
                continue

            valid_options.append((start, end, slot_label))
            
        if not valid_options:
            return {
                "status": "all_conflicts",
                "selected_slot": None,
                "end_time": None,
                "reasoning": reasoning + ["All overlapping slots have conflicts — no valid slot available"],
            }
            
        reasoning.append(f"{len(valid_options)} conflict-free slots identified")

        # Step 4: AI Decision Logic
        if len(valid_options) == 1 or not self.model:
            best_start, best_end, best_label = valid_options[0]
            if not self.model and len(valid_options) > 1:
                reasoning.append("LLM disabled/no key — defaulting to earliest slot")
            reasoning.append(f"{best_label} selected as the optimal slot")
            if buffer_minutes > 0:
                reasoning.append(f"{buffer_minutes}-minute buffer respected")
            
            return {
                "status": "scheduled",
                "selected_slot": best_start.isoformat(),
                "end_time": best_end.isoformat(),
                "reasoning": reasoning,
            }
            
        # Use Gemini to pick the best slot
        prompt = self._build_prompt(valid_options, duration_minutes, recruiter_preferences, candidate_preferences)
        
        try:
            response = self.model.generate_content(prompt)
            reply = response.text.strip()
            
            # Extract the chosen index from the response. 
            # We ask the LLM to output just the index number on the first line.
            lines = reply.split('\n')
            index_str = lines[0].strip()
            
            try:
                selected_idx = int(index_str) - 1
                if selected_idx < 0 or selected_idx >= len(valid_options):
                    selected_idx = 0
            except ValueError:
                selected_idx = 0
                
            best_start, best_end, best_label = valid_options[selected_idx]
            reasoning.append(f"Gemini selected {best_label}")
            
            # The rest of the LLM response is the reasoning
            ai_reasoning = "\n".join(lines[1:]).strip()
            if ai_reasoning:
                reasoning.append(f"AI Reasoning: {ai_reasoning}")
                
        except Exception as e:
            # Fallback
            best_start, best_end, best_label = valid_options[0]
            reasoning.append(f"AI selection failed ({str(e)}) — defaulted to {best_label}")
            
        if buffer_minutes > 0:
            reasoning.append(f"{buffer_minutes}-minute buffer respected")

        return {
            "status": "scheduled",
            "selected_slot": best_start.isoformat(),
            "end_time": best_end.isoformat(),
            "reasoning": reasoning,
        }

    def _build_prompt(self, valid_options: List[tuple], duration: int, rec_pref: str, can_pref: str) -> str:
        options_text = ""
        for i, (s, e, label) in enumerate(valid_options):
            options_text += f"{i+1}. {label}\n"
            
        return f"""You are an intelligent scheduling agent. 
Here are the valid, conflict-free {duration}-minute meeting slots:
{options_text}

Recruiter preferences: {rec_pref or 'None specified'}
Candidate preferences: {can_pref or 'None specified'}

Choose the best interview slot.
Your response MUST have exactly this format:
<Slot Number>
<One sentence explaining why you chose this slot based on the preferences>

Example response:
2
This slot best matches the candidate's preference for afternoons and the recruiter's preference to avoid Fridays.
"""

    def _divide_into_windows(self, slots: List[str], duration_minutes: int) -> List[tuple]:
        windows = []
        duration = timedelta(minutes=duration_minutes)
        block_length = timedelta(hours=1) 
        for slot_str in slots:
            try:
                start = datetime.fromisoformat(slot_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
            block_end = start + block_length
            current = start
            while current + duration <= block_end:
                windows.append((current, current + duration))
                current += duration
        windows.sort(key=lambda w: w[0])
        return windows

    def _find_overlaps(self, recruiter_windows: List[tuple], candidate_windows: List[tuple]) -> List[tuple]:
        recruiter_set = {w[0] for w in recruiter_windows}
        overlaps = []
        for start, end in candidate_windows:
            if start in recruiter_set:
                overlaps.append((start, end))
        overlaps.sort(key=lambda w: w[0])
        return overlaps

    def _has_conflict(self, start: datetime, end: datetime, existing_meetings: List[dict], role: str, buffer_minutes: int = 0) -> bool:
        buffer = timedelta(minutes=buffer_minutes)
        buffered_start = start - buffer
        buffered_end = end + buffer
        for meeting in existing_meetings:
            try:
                m_start = datetime.fromisoformat(str(meeting.get("start_time", "")).replace("Z", "+00:00"))
                m_end = datetime.fromisoformat(str(meeting.get("end_time", "")).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
            if buffered_start < m_end and buffered_end > m_start:
                return True
        return False
