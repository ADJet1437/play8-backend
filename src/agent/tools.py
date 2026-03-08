import json
import uuid

from langchain_core.tools import tool
from pydantic import BaseModel, Field


# Play8 PongBot Pace S Series training card schemas for Tennis & Padel
class DrillItem(BaseModel):
    """A single drill in a training plan todo list"""
    name: str = Field(description="Drill name (3-5 words, e.g., 'Crosscourt Backhand Rally')")
    duration: str = Field(description="Duration for this drill (e.g., '5 min', '10 min')")
    focus: str = Field(description="One sentence describing the drill focus")


class TrainingPlanCard(BaseModel):
    """Training plan card with simple todo list and drills"""
    title: str = Field(description="Training session title (3-6 words)")
    description: str = Field(description="One sentence describing the training goal")
    total_duration: str = Field(description="Total session duration (e.g., '30 min', '45 min')")
    difficulty: str = Field(description="beginner, intermediate, advanced, or elite")
    sport: str = Field(description="tennis or padel", default="tennis")
    drills: list[DrillItem] = Field(description="List of 4-6 drills in sequence")
    training_plan_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID to correlate with drill cards (auto-generated if not provided)"
    )


class BallSettings(BaseModel):
    """Settings for a single ball in a drill sequence"""
    ball_number: int = Field(description="Ball number in sequence (1-6 only, every drill has exactly 6 balls)", ge=1, le=6)
    spin_type: str = Field(description="Spin type: 'Topspin', 'No Spin', or 'Underspin'")
    spin_strength: int = Field(description="Spin intensity 0-10 (0=flat, 10=heavy spin)", ge=0, le=10)
    speed: int = Field(description="Ball speed 0-10 (0=very slow, 10=competition speed)", ge=0, le=10)
    drop_point: int = Field(description="Horizontal landing position -10 to +10 (negative=left, positive=right, 0=center)", ge=-10, le=10)
    depth: int = Field(description="Landing depth 0-20 (0=net, 20=deep baseline)", ge=0, le=20)
    feed: float = Field(description="Time to next ball in seconds (0.8-5.0)", ge=0, le=5.0)


class DrillCard(BaseModel):
    """Ball machine drill card with ball sequence and machine settings"""
    title: str = Field(description="Drill title (3-5 words)")
    description: str = Field(description="One sentence describing what to practice")
    drill_number: int = Field(description="Sequence number in the training plan (1-indexed)")
    duration: str = Field(description="Duration for this drill (e.g., '5 min', '10 min')")
    machine_position: str = Field(description="Machine placement - MUST be one of: 'Baseline Center', 'Baseline Left Corner', 'Baseline Right Corner' (tennis) OR 'Center Back Glass', 'Left Back Glass', 'Right Back Glass' (padel)")
    ball_sequence: list[BallSettings] = Field(description="EXACTLY 6 ball settings in sequence (ball_number 1-6)", min_length=6, max_length=6)
    sequence_repetitions: int = Field(description="Number of times to repeat the 6-ball sequence (1-20)", ge=1, le=20)
    focus_points: list[str] = Field(description="2-3 technique focus points for the player")
    training_plan_id: str = Field(default="", description="ID matching the parent TrainingPlanCard (auto-populated)")


class TrainingSession(BaseModel):
    """Complete training session with plan and drill cards"""
    plan: TrainingPlanCard = Field(description="Training plan with overview and drill list")
    drills: list[DrillCard] = Field(description="4-6 detailed drill cards with PongBot settings")


@tool
def generate_training_session(session: TrainingSession) -> str:
    """Generate a complete PongBot Pace S training session for tennis or padel with ball sequences.

    **When to use this tool:**
    - User asks for a training session, workout, practice routine, or drill plan
    - User wants to work on specific skills (e.g., "improve my backhand", "crosscourt forehand")
    - User provides time constraints (e.g., "I have 30 minutes to train")
    - User specifies tennis or padel training

    **When NOT to use this tool:**
    - Casual conversation or greetings
    - General questions about technique (just explain in text)
    - Questions about the PongBot manual or settings (use search_pongbot_manual instead)

    **What to provide:**
    1. plan: TrainingPlanCard
       - title: Session name (e.g., "Crosscourt Forehand Training")
       - description: One sentence goal
       - total_duration: Total session time (e.g., "30 min", "45 min")
       - difficulty: beginner (level 1), intermediate (level 2), advanced (level 3), or elite (level 4)
       - sport: "tennis" or "padel"
       - drills: 4-6 DrillItem objects (name, duration, focus)

    2. drills: 4-6 DrillCard objects with ball sequences
       - title: Drill name (e.g., "Crosscourt Backhand Rally")
       - description: What to practice
       - drill_number: 1, 2, 3, etc. (match plan.drills order)
       - duration: Time for drill (e.g., "5 min")
       - machine_position: MUST be one of these EXACT names:
         * Tennis: "Baseline Center", "Baseline Left Corner", or "Baseline Right Corner"
         * Padel: "Center Back Glass", "Left Back Glass", or "Right Back Glass"
       - ball_sequence: EXACTLY 6 BallSettings objects (ball_number 1, 2, 3, 4, 5, 6)
       - sequence_repetitions: How many times to repeat the 6-ball sequence (1-20)
       - focus_points: 2-3 technique tips
       - training_plan_id: Leave empty (auto-generated)

    **Ball sequence design (ALWAYS 6 balls)**:
    Every drill must have exactly 6 balls numbered 1-6.

    **CRITICAL**: Each ball MUST include ALL 7 parameters below. Never omit any field:
    - ball_number: 1, 2, 3, 4, 5, or 6 (REQUIRED)
    - spin_type: "Topspin", "No Spin", or "Underspin" (REQUIRED)
    - spin_strength: 0-10 integer (REQUIRED, use formulas: beginner=2, intermediate=4, advanced=6, elite=8)
    - speed: 0-10 integer (REQUIRED, use formulas: beginner=4, intermediate=6, advanced=8, elite=10)
    - drop_point: -10 to +10 integer (REQUIRED, negative=left, positive=right; e.g., -6=backhand corner, +6=forehand corner)
      **Legal serve zones - Choose ONE box per drill**:
        - Deuce Court (Right): 0 to +4 (all balls must stay in this range)
        - Ad Court (Left): -4 to 0 (all balls must stay in this range)
        - ❌ NEVER mix boxes in serve drills (e.g., ball 1 at +2, ball 2 at -2)
      **Groundstrokes**: Can use full range (-10 to +10) and mix both sides, but explain context
    - depth: 0-20 (use formulas: beginner=10, intermediate=12, advanced=14, elite=16)
      **Legal serve zones**: Tennis = 1-10, Padel = 1-11 (net to service line)
      **Baseline drills**: 10-16 typical, 17-20 very deep
    - feed: 0.8-5.0 seconds (use formulas: beginner=3.0, intermediate=2.5, advanced=2.0, elite=1.5)

    **VISUALIZE THE COURT**: Before finalizing parameters, imagine the court diagram showing all 6 balls:
    - Each ball's drop_point and depth will be plotted visually on the court
    - For serve drills: ALL 6 balls must land in the SAME service box (choose deuce OR ad court)
    - For groundstroke drills outside service boxes, add educational context
    - Design the 6-ball sequence to create realistic rally patterns or tactical progressions

    **Example 6-ball sequence** (cross-court forehand drill for intermediate):
    [
      {"ball_number": 1, "spin_type": "Topspin", "spin_strength": 4, "speed": 6, "drop_point": -6, "depth": 12, "feed": 2.5},
      {"ball_number": 2, "spin_type": "Topspin", "spin_strength": 4, "speed": 6, "drop_point": 6, "depth": 12, "feed": 2.5},
      {"ball_number": 3, "spin_type": "Topspin", "spin_strength": 4, "speed": 6, "drop_point": -6, "depth": 10, "feed": 2.5},
      {"ball_number": 4, "spin_type": "Topspin", "spin_strength": 4, "speed": 6, "drop_point": 6, "depth": 14, "feed": 2.5},
      {"ball_number": 5, "spin_type": "Topspin", "spin_strength": 5, "speed": 6, "drop_point": 0, "depth": 12, "feed": 2.5},
      {"ball_number": 6, "spin_type": "Topspin", "spin_strength": 4, "speed": 6, "drop_point": 8, "depth": 11, "feed": 2.5}
    ]

    Notice: ALL 7 fields present for each ball. Never omit any field!

    **IMPORTANT - Explain drill logic in text:**
    After calling this tool, your text response should explain:
    - WHY you designed the drill this way (tactical purpose)
    - WHAT the player should focus on (technique points)
    - HOW the drill progression works (why this sequence)
    - Connection to match scenarios
    Keep it motivating and coach-like, but include these educational insights!"""
    # Auto-generate training_plan_id and ensure consistency
    result = session.model_dump()
    training_plan_id = result['plan']['training_plan_id']

    # Ensure all drills use the same ID
    for drill in result['drills']:
        drill['training_plan_id'] = training_plan_id

    return json.dumps(result)
