# Prompt Template

You will be provided with a transcript of a conversation. Based on the keyword (`keyword=xx`), perform the following tasks:

## Input Format

keyword=<keyword> conversation:
Speaker SPEAKER_00: <Text>
Sentiment: <Sentiment>
Intent: <Intent>
Emotion: <Emotion>
Speaker SPEAKER_01: <Text>
Sentiment: <Sentiment>
Intent: <Intent>
Emotion: <Emotion>
...

## Task 1: Action Items

- **Objective**: If `keyword = action`, determine the list of tasks from the conversation, assign them to a speaker or person, and return as a `List[str]`.

## Task 2: Summary

- **Objective**: If `keyword = summary`, summarize the conversation, This analysis provides a comprehensive overview of a conversation by examining various elements: determining the role of each speaker, analyzing overall sentiment (positive, negative, mixed), detecting bad words and offensive intents, identifying action items, detecting emotions (joy, anger, sadness), identifying intents (request, command, suggestion), extracting key topics and keywords, recognizing named entities (people, organizations, dates), assessing conversational dynamics (turn-taking, interruptions), evaluating silence and filler words ("um," "uh"), and summarizing the conversation with main points and transitions , and return all results as JSON object:

  "summary": "[A narrative overview of the conversation, describing main topics and transitions.]",
  
  "roles": "[SPEAKER_00: Role, Role]\n[SPEAKER_01: Role, Role]",

  "overall_sentiment": "[Overall sentiment, e.g., Positive, Negative, Mixed]",

  "bad_words": ["List any detected bad words, or indicate 'None'],

  "offensive_intents": ["List any detected offensive intents, or indicate 'None'],

  "action_items": ["List any action items identified in the conversation, or indicate 'None']",

  "emotion_detection": "[A description of the detected emotions, such as joy, anger, sadness, etc.]",
  
  "intent_detection": "[A description of the underlying intents behind statements, e.g., request, command, suggestion]",
  
  "topic_detection": "[Key topics or themes discussed in the conversation]",

  "keyword_extraction": ["List of significant keywords or phrases from the conversation"],

  "speaker_identification_and_role_classification": "[Identified speakers and their inferred roles in the conversation]",
  
  "named_entity_recognition": ["List of identified entities such as people, organizations, dates, etc."],
  
  "conversational_dynamics": "[Analysis of the conversation's flow, such as turn-taking and interruptions]",

  "offensive_language_detection": ["List of detected offensive language, or indicate 'None']",

  "silence_and_filler_word_analysis": "[Amount of silence and filler words detected, e.g., 'um,' 'uh']",

  "conversational_summary": "[A concise summary of the entire conversation, with human readable form of all values detected in  roles, overall_sentiment, bad_words, offensive_intents, action_items, emotion_detection, intent_detection, topic_detection, keyword_extraction, speaker_identification_and_role_classification, named_entity_recognition, conversational_dynamics, offensive_language_detection, silence_and_filler_word_analysis, conversational_summary]"
  
## Task 3: other questions

- **Objective**: If `keyword = others  question=<question>`, determine the answer of the question from the conversation,  and return as a `str`

## Task 4: speaker profile

- **Objective**: If `keyword = speaker`, determine the pofile of each speaker,  and return as a JOSN object Array [profile1, profile2,...] , each profile has JSON object format:
arrary

json obj1
"gender" : [str] - identified the gender of speaker ,
"age" : [str] - identified the age of speaker ,
"name" : [str] - identified the name of speaker if possible ,
"role" : [str] - identified the role of speaker ,
"behavior" : [str] - identified the behavior of speaker ,
"thesis" : [str] - identified the speaker's main arguement or thesis ,
"action" : [str] - identified the speaker's action items ,
json obj2 .....

## Task 5: clean
- **Objective**: If `keyword = clean`, you are a senior executive assistant, you will be given a text [str] with json object, similar to this, write a professional business memo ((format as HTML)), with date, title,theme,action items, and speaker identities. do not display raw json, apply proper indents, heading tags such as h1, h2,h3 and proper list and paragraph tags.
The text you will be given has a format roughly, replace all newline character (\n)  with  space   , do not show "\n" in output : 

    "conversation_transcript": 
        
            "speaker": "SPEAKER_ID",
            "text": "TEXT",
            "sentiment": "SENTIMENT",
            "intent": "INTENT",
            "emotion": "EMOTION"
        
    "summary": "SUMMARY",
    "emotional_summary": "EMOTIONAL desription of each speaker",
    "speaker_profiles": "SPEAKER_PROFILES"

---
Expected Out format:

<h1>Memo</h1>

<!-- Date Section -->
<b><p class="section-title">Date:</p></b> Today's date

<!-- Subject Section -->
<b><p class="section-title">Subject:</p></b> [Brief Description of the Subject]

<!-- Summary Section -->
<b><p class="section-title">Summary:</p></b>
<p>[A brief description of the overall theme or focus of the memorandum]</p>
<p>[A detailed summary of the key points and discussion covered in the memorandum]</p>

<!-- Speaker Identities Section -->
<b><p class="section-title">Speakers:</p></b>
<ul>
    <li><strong>[SPEAKER_00]:</strong> [Role and behavior of the first speaker]</li>
    <li><strong>[SPEAKER_01]:</strong> [Role and behavior of the second speaker]</li>
</ul>

<!-- Action Items Section -->
<b><p class="section-title">Action(s) to follow:</p></b>
<ul>
    <li>[Specific actions that need to be taken, if any]</li>
</ul>

<!-- Appendix Section -->
<b><p class="section-title">Appendix:</p></b>
<p>[Additional materials or references, such as a transcript or data, can be attached or referenced here]</p>


# Examples

## Task 1: Action Items

### Example 1

keyword=action conversation:
Speaker SPEAKER_00: Alice, can you send the report by the end of the day?
Sentiment: NEUTRAL
Intent: request
Emotion: neutral
Speaker SPEAKER_01: Sure, I'll get it done.
Sentiment: POSITIVE
Intent: agreement
Emotion: confidence
Speaker SPEAKER_00: Also, let's schedule a meeting with the marketing team for next week.
Sentiment: NEUTRAL
Intent: request
Emotion: neutral
Speaker SPEAKER_02: I'll handle the scheduling.
Sentiment: POSITIVE
Intent: commitment
Emotion: determination

**Action Items**:
- "SPEAKER_00: Send report by end of day, assigned to Alice"
- "SPEAKER_02: Schedule meeting with marketing team next week"

### Example 2

keyword=action conversation:
Speaker SPEAKER_00: John, please follow up with us about the project status.
Sentiment: NEUTRAL
Intent: request
Emotion: neutral
Speaker SPEAKER_01: I will provide an update by tomorrow.
Sentiment: POSITIVE
Intent: commitment
Emotion: confidence
Speaker SPEAKER_02: And let's review the budget next week.
Sentiment: NEUTRAL
Intent: suggestion
Emotion: neutral
Speaker SPEAKER_03: I'll arrange the review session.
Sentiment: POSITIVE
Intent: commitment
Emotion: determination


**Action Items**:
- "SPEAKER_00: Follow up on project status, assigned to John"
- "SPEAKER_03: Arrange budget review session next week"

## Task 2: Summary

### Example 1

keyword=summary conversation:
Speaker SPEAKER_00: Alice, can you send the report by the end of the day?
Sentiment: NEUTRAL
Intent: request
Emotion: neutral
Speaker SPEAKER_01: Sure, I'll get it done.
Sentiment: POSITIVE
Intent: agreement
Emotion: confidence
Speaker SPEAKER_00: Also, let's schedule a meeting with the marketing team for next week.
Sentiment: NEUTRAL
Intent: request
Emotion: neutral
Speaker SPEAKER_02: I'll handle the scheduling.
Sentiment: POSITIVE
Intent: commitment
Emotion: determination


**Summary**:
  "summary": "The conversation primarily involved task assignments, conducted with a neutral to positive sentiment.",
  
  "roles": "SPEAKER_00: Manager\nSPEAKER_01: Team Member\nSPEAKER_02: Team Member",

  "overall_sentiment": "Positive",

  "bad_words": [],

  "offensive_intents": [],

  "action_items": ["Alice to send the report by end of day", "Schedule a meeting with the marketing team for next week"],

  "emotion_detection": "Neutral, confidence, determination",
  
  "intent_detection": "Request, agreement, commitment",
  
  "topic_detection": "Task assignments, scheduling meetings",

  "keyword_extraction": ["Report", "Meeting", "Marketing team"],

  "speaker_identification_and_role_classification": "SPEAKER_00 identified as Manager, SPEAKER_01 and SPEAKER_02 as Team Members",
  
  "named_entity_recognition": ["Alice", "Marketing team"],
  
  "conversational_dynamics": "Turn-taking between manager and team members",

  "offensive_language_detection": [],

  "silence_and_filler_word_analysis": "Minimal filler words detected",

   "conversational_summary": "The conversation involved a manager (SPEAKER_00) assigning tasks to team members (SPEAKER_01 and SPEAKER_02), with the overall sentiment being positive. No bad words or offensive intents were detected. Action items include Alice sending the report by the end of the day and scheduling a meeting with the marketing team for next week. The detected emotions were neutral, confidence, and determination, with intents such as request, agreement, and commitment. The conversation topics included task assignments and scheduling meetings. Keywords like 'Report' and 'Meeting' were extracted. The conversation flowed smoothly with clear roles identified, minimal filler words, and no offensive language."
    



### Example 2

keyword=summary conversation:
Speaker SPEAKER_00: John, please follow up with us about the project status.
Sentiment: NEUTRAL
Intent: request
Emotion: neutral
Speaker SPEAKER_01: I will provide an update by tomorrow.
Sentiment: POSITIVE
Intent: commitment
Emotion: confidence
Speaker SPEAKER_02: And let's review the budget next week.
Sentiment: NEUTRAL
Intent: suggestion
Emotion: neutral
Speaker SPEAKER_03: I'll arrange the review session.
Sentiment: POSITIVE
Intent: commitment
Emotion: determination


**Summary**: 
  "summary": "The conversation opened with a request for follow-up, moving to budget review plans, reflecting a shift from neutral to positive engagement.",
  
  "roles": "SPEAKER_00: Project Leader\nSPEAKER_01: Team Member\nSPEAKER_02: Team Member\nSPEAKER_03: Team Member",

  "overall_sentiment": "Mixed, trending positive",

  "bad_words": ["disaster"],

  "offensive_intents": [],

  "action_items": ["Follow up on project status", "Review the budget next week"],

  "emotion_detection": "Neutral, confidence, determination",
  
  "intent_detection": "Request, commitment, suggestion",
  
  "topic_detection": "Project follow-up, budget review",

  "keyword_extraction": ["Project status", "Budget", "Review"],

  "speaker_identification_and_role_classification": "SPEAKER_00 identified as Project Leader, others as Team Members",
  
  "named_entity_recognition": ["John"],
  
  "conversational_dynamics": "Smooth flow with clear commitments from team members",

  "offensive_language_detection": ["disaster"],

  "silence_and_filler_word_analysis": "Minimal silence and filler words",

  "conversational_summary": "The conversation started with a project leader (SPEAKER_00) requesting follow-up on the project status and discussing budget review plans with team members (SPEAKER_01, SPEAKER_02, and SPEAKER_03), with the sentiment being mixed but trending positive. The word 'disaster' was detected as potentially negative language. Action items include following up on project status and reviewing the budget next week. Detected emotions were neutral, confidence, and determination, with intents such as request, commitment, and suggestion. Topics focused on project follow-up and budget review, with keywords like 'Project status' and 'Budget' identified. The conversation was dynamic with smooth commitments, minimal filler words, and the roles of each speaker clearly defined."

**other**
Example 1
Keyword="others" question="Do you know if the report has been finalized?"

Conversation Transcript:
Speaker SPEAKER_00: Do you know if the report has been finalized?
Sentiment: NEUTRAL
Intent: question
Emotion: curiosity

Speaker SPEAKER_01: Yes, the report was finalized yesterday.
Sentiment: POSITIVE
Intent: statement
Emotion: confidence

Speaker SPEAKER_00: Great, thanks for confirming.
Sentiment: POSITIVE
Intent: gratitude
Emotion: relief

Answer: "Yes, the report was finalized yesterday."

Example 2
Keyword="others" question="what is speak1 emotion state? give some details"

Conversation Transcript:
Speaker SPEAKER_00: I think we should consider changing the project timeline.
Sentiment: NEUTRAL
Intent: suggestion
Emotion: thoughtful

Speaker SPEAKER_01: I'm worried about how that might affect our deadline.
Sentiment: NEGATIVE
Intent: concern
Emotion: anxiety

Speaker SPEAKER_00: We can discuss this with the team to find a solution.
Sentiment: POSITIVE
Intent: reassurance
Emotion: supportive

Speaker SPEAKER_01: That sounds like a good idea. I feel a bit better now.
Sentiment: POSITIVE
Intent: agreement
Emotion: relief

"Answer": 
Initial Emotion: Anxiety. Evidence: SPEAKER_01 expresses concern about the potential impact of changing the project timeline on the deadline, indicating a state of worry and anxiety.

**speaker**
Example 1
Keyword="speaker"  "

Conversation Transcript:
Speaker SPEAKER_00: Do you know if the report has been finalized?
Sentiment: NEUTRAL
Intent: question
Emotion: curiosity

Speaker SPEAKER_01: Yes, the report was finalized yesterday.
Sentiment: POSITIVE
Intent: statement
Emotion: confidence

Speaker SPEAKER_00: Great, thanks for confirming.
Sentiment: POSITIVE
Intent: gratitude
Emotion: relief


Speaker Roles 
<array>
    <json obj1>
    speaker1:
        "gender": "female",
        "age": "adult",
        "name": "Alice",
        "role": "Manager",
        "behavior": "directive",
        "thesis": "Managing tasks and scheduling meetings.",
        "action": "Requesting a report and scheduling a meeting with the marketing team."
    ,
    <json obj2>
    speaker2:
        "gender": "unknown",
        "age": "unknown",
        "name": "unknown",
        "role": "Team Member",
        "behavior": "agreeable",
        "thesis": "Acknowledging task assignments.",
        "action": "Agreeing to complete the report."
        ....
        ....