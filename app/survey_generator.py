"""
Survey Form Generator using OpenAI Agents SDK
Generates structured survey JSON based on user requirements.
"""

import asyncio
import json
from typing import Any, Dict
from dotenv import load_dotenv
from agents import Agent, Runner, set_default_openai_client
from pydantic import BaseModel

from app.get_client import ClientName, get_client, get_model_for_client

# Load environment variables
load_dotenv(override=True)


class SurveyResponse(BaseModel):
    """Structured response for survey generation."""
    message: str
    form_data: list[Dict[str, Any]]


def create_survey_agent(client_name: ClientName = "openai") -> Agent:
    """
    Create a survey generator agent with detailed instructions.
    """
    model = get_model_for_client(client_name)

    # Optimized system prompt
    instructions = f"""Survey JSON Generator - Return ONLY valid JSON: {{"message": "...", "form_data": [...]}}

CORE SCHEMA (all fields):
{{
  "fieldID": "1,2,3...", "fieldTitleId": "UUIDv4", "fieldType": "see_below",
  "title": "Question text", "required": false, "isPublished": false, "isDisabled": false,
  "isDataElementRequired": true, "hideFromAppEnabled": false, "sortOrder": 1,
  "dynamicColumnEnable": true, "skipRules": {{}}, "calculationRules": {{}},
  "jumpRules": [], "readonlyRules": {{}}
}}

FIELD TYPES & EXTRAS:
• text/tel: +dbColumnName, +dataElementId (same, snake_case, <50 chars), +displayText, +minLength(1), +maxLength(null), +regex(""), +errorMessage(""), +validationFormula({{"queryWithIds":"","queryWithNames":""}}), +hint(""), +defaultValue(null), +enableUniquenessCheckOnAnswer(false), +isTextArea(false), +isNumeric(false)
• number/decimal: +dbColumnName, +dataElementId, +displayText, +minValue(null), +maxValue(null), +decimalPrecision(null), +defaultValue(null), +errorMessage(""), +enableUniquenessCheckOnAnswer(false)
• date: +dbColumnName, +dataElementId, +displayText, +dateOnly(false), +monthOnly(false), +yearOnly(false), +timeOnly(false), +fromDate(""), +toDate(""), +fromDateConfig(""), +toDateConfig(""), +customDatasetFilterEnabled(false), +customDatasetId(""), +customDatasetFromColumn(""), +customDatasetToColumn(""), +isTodayAsDefault(false), +autoCaptureDateEnabled(false), +defaultValue(null), +validationFormula
• radio/dropdown/checkbox: +dbColumnName, +dataElementId, +displayText, +fieldOptions[], +defaultValue(optionValue OR comma-separated), +isMultiSelect(false), +isInt(false), +errorMessage(""), +enableUniquenessCheckOnAnswer(false), +validationFormula(null for radio/dropdown)
  checkbox ONLY: +minItemToSelect(""), +maxItemToSelect(""), +minItemToSelectNumber(""), +maxItemToSelectNumber("")
• boolean: +dbColumnName, +dataElementId, +displayText, +defaultValue(true/false/null), +validationFormula
• image/video/document: +dbColumnName, +dataElementId, +displayText, +validationFormula
  image: +maxPhotoUploads, +imageHeight, +imageWidth, +isSizeRestricted, +canChooseFromGallery, +canUploadFromWeb
  video/document: +maxFileUploads
• geolocation: +dbColumnName, +dataElementId, +displayText, +latitude(0), +longitude(0), +altitude(0), +precision(0), +autoCaptureGeolocationEnable(true), +validationFormula
• geopolygon: +dbColumnName, +dataElementId, +displayText, +maxNumberOfPolygons(1), +validationFormula
• colorpicker: +dbColumnName, +dataElementId, +displayText, +defaultValue(null)
• note: ONLY core attrs (NO dbColumnName/dataElementId/displayText)
• section: +items[] (nested questions), +repeaterSectionConfig:{{"isRepeater":false,"isTabularView":false,"linkDataElementId":null,"repeaterSectionId":"section_fieldID","dbTableName":null,"repeaterLabelDataElementId":"","attributeConfig":{{}},"minItems":0,"UniqueConstraintAttributes":[]}}
  Repeater(isRepeater:true): dbTableName REQUIRED & unique, repeaterLabelDataElementId=comma-separated dataElementIds

OPTION SCHEMA (radio/dropdown/checkbox):
{{"optionTitle":"Text","optionTitleId":"UUIDv4","optionValue":"code","optionID":"UUIDv4","optionOrder":1,"nextID":"","skipRules":{{}},"titles":{{"default":"Text","undefined":"Text"}}}}
Auto-generate optionValue as "01","02","03"... if not specified

PUBLISHED FIELD PROTECTION (⚠️ CRITICAL):
If isPublished=true:
• CANNOT delete/remove from form_data (MUST preserve)
• CANNOT change: dbColumnName, dataElementId, fieldType, isPublished
• CAN modify: title, displayText, required, defaultValue, hint
• On delete request: keep field, explain in message why not deleted
• NEVER change isPublished status (true↔false)

DB NAMING:
• dbColumnName = dataElementId (ALWAYS identical & required)
• displayText = short UI label (ALWAYS required with dbColumnName)
• Snake_case, <50 chars, concise ("What is your name?" → "your_name")
• Unpublished: can update both together

RULES SYNTAX (alasql):
• skipRules: {{"queryWithNames":"{{dataElementId}}='val'","queryWithIds":"{{dataElementId}}='val'","viewType":"skipRule"}}
• calculationRules: {{"queryWithNames":"{{field1}}+{{field2}}","queryWithIds":"{{field1}}+{{field2}}","applyWhenQueryWithNames":"","applyWhenQueryWithIds":""}}
• validationFormula: {{"queryWithNames":"{{id}}='cond'","queryWithIds":"{{id}}='cond'"}}
• jumpRules: [{{"jumpTo":"END|{{dataElementId}}","queryWithNames":"...","queryWithIds":"..."}}]
• readonlyRules: {{"queryWithNames":"...","queryWithIds":"..."}}
Functions: today(), yeardiff(), daydiff(), monthdiff(), getTimeDiff(), IsChecked(), hasAny(), ifElseV2(), isNullOrEmpty(), toInt(), toDouble(), getRepeaterArrayLength(), getRepeaterPropertySum(), ifAnyOfRepeaterItems(), floor(), ceiling()

AUTO-CONFIG:
• Email: isTextArea=false, isNumeric=false, email regex
• Textarea: isTextArea=true
• UUIDv4 for all ID fields
• sortOrder reindex on reorder (no fieldID changes)

FINAL CHECK:
✓ All isPublished=true fields present
✓ Published fields only modified in allowed properties
✓ Deletion of published explained in message"""

    agent = Agent(
        name="Survey Generator",
        instructions=instructions,
        model=model,
    )
    return agent


async def generate_survey(
    user_request: str,
    existing_form_data: list[Dict[str, Any]] = None,
    client_name: ClientName = "openai"
) -> SurveyResponse:
    """
    Generate survey JSON based on user request.

    Args:
        user_request: Natural language description of the survey fields needed
        existing_form_data: Optional existing form data to modify
        client_name: AI provider to use

    Returns:
        SurveyResponse with message and form_data
    """
    # Setup client
    client = get_client(client_name)

    # For OpenAI, use the Agents SDK
    if client_name == "openai":
        set_default_openai_client(client)

        # Create survey agent
        survey_agent = create_survey_agent(client_name)

        # Build the prompt
        prompt = user_request
        if existing_form_data:
            prompt = f"""Existing form data:
```json
{json.dumps(existing_form_data, indent=2)}
```

User request: {user_request}

Generate the updated form_data with all modifications applied."""

        # Run the agent - it will return JSON based on instructions
        result = await Runner.run(survey_agent, prompt)

        # Parse the response
        response_text = result.final_output.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()

        parsed_response = json.loads(response_text)

        return SurveyResponse(
            message=parsed_response["message"],
            form_data=parsed_response["form_data"]
        )

    # For DeepSeek and Gemini, use direct API
    else:
        model = get_model_for_client(client_name)

        # Build the prompt
        prompt = user_request
        if existing_form_data:
            prompt = f"""Existing form data:
```json
{json.dumps(existing_form_data, indent=2)}
```

User request: {user_request}

Generate the updated form_data with all modifications applied."""

        # Optimized system prompt
        instructions = f"""Survey JSON Generator - Return ONLY valid JSON: {{"message": "...", "form_data": [...]}}

CORE SCHEMA (all fields):
{{
  "fieldID": "1,2,3...", "fieldTitleId": "UUIDv4", "fieldType": "see_below",
  "title": "Question text", "required": false, "isPublished": false, "isDisabled": false,
  "isDataElementRequired": true, "hideFromAppEnabled": false, "sortOrder": 1,
  "dynamicColumnEnable": true, "skipRules": {{}}, "calculationRules": {{}},
  "jumpRules": [], "readonlyRules": {{}}
}}

FIELD TYPES & EXTRAS:
• text/tel: +dbColumnName, +dataElementId (same, snake_case, <50 chars), +displayText, +minLength(1), +maxLength(null), +regex(""), +errorMessage(""), +validationFormula({{"queryWithIds":"","queryWithNames":""}}), +hint(""), +defaultValue(null), +enableUniquenessCheckOnAnswer(false), +isTextArea(false), +isNumeric(false)
• number/decimal: +dbColumnName, +dataElementId, +displayText, +minValue(null), +maxValue(null), +decimalPrecision(null), +defaultValue(null), +errorMessage(""), +enableUniquenessCheckOnAnswer(false)
• date: +dbColumnName, +dataElementId, +displayText, +dateOnly(false), +monthOnly(false), +yearOnly(false), +timeOnly(false), +fromDate(""), +toDate(""), +fromDateConfig(""), +toDateConfig(""), +customDatasetFilterEnabled(false), +customDatasetId(""), +customDatasetFromColumn(""), +customDatasetToColumn(""), +isTodayAsDefault(false), +autoCaptureDateEnabled(false), +defaultValue(null), +validationFormula
• radio/dropdown/checkbox: +dbColumnName, +dataElementId, +displayText, +fieldOptions[], +defaultValue(optionValue OR comma-separated), +isMultiSelect(false), +isInt(false), +errorMessage(""), +enableUniquenessCheckOnAnswer(false), +validationFormula(null for radio/dropdown)
  checkbox ONLY: +minItemToSelect(""), +maxItemToSelect(""), +minItemToSelectNumber(""), +maxItemToSelectNumber("")
• boolean: +dbColumnName, +dataElementId, +displayText, +defaultValue(true/false/null), +validationFormula
• image/video/document: +dbColumnName, +dataElementId, +displayText, +validationFormula
  image: +maxPhotoUploads, +imageHeight, +imageWidth, +isSizeRestricted, +canChooseFromGallery, +canUploadFromWeb
  video/document: +maxFileUploads
• geolocation: +dbColumnName, +dataElementId, +displayText, +latitude(0), +longitude(0), +altitude(0), +precision(0), +autoCaptureGeolocationEnable(true), +validationFormula
• geopolygon: +dbColumnName, +dataElementId, +displayText, +maxNumberOfPolygons(1), +validationFormula
• colorpicker: +dbColumnName, +dataElementId, +displayText, +defaultValue(null)
• note: ONLY core attrs (NO dbColumnName/dataElementId/displayText)
• section: +items[] (nested questions), +repeaterSectionConfig:{{"isRepeater":false,"isTabularView":false,"linkDataElementId":null,"repeaterSectionId":"section_fieldID","dbTableName":null,"repeaterLabelDataElementId":"","attributeConfig":{{}},"minItems":0,"UniqueConstraintAttributes":[]}}
  Repeater(isRepeater:true): dbTableName REQUIRED & unique, repeaterLabelDataElementId=comma-separated dataElementIds

OPTION SCHEMA (radio/dropdown/checkbox):
{{"optionTitle":"Text","optionTitleId":"UUIDv4","optionValue":"code","optionID":"UUIDv4","optionOrder":1,"nextID":"","skipRules":{{}},"titles":{{"default":"Text","undefined":"Text"}}}}
Auto-generate optionValue as "01","02","03"... if not specified

PUBLISHED FIELD PROTECTION (⚠️ CRITICAL):
If isPublished=true:
• CANNOT delete/remove from form_data (MUST preserve)
• CANNOT change: dbColumnName, dataElementId, fieldType, isPublished
• CAN modify: title, displayText, required, defaultValue, hint
• On delete request: keep field, explain in message why not deleted
• NEVER change isPublished status (true↔false)

DB NAMING:
• dbColumnName = dataElementId (ALWAYS identical & required)
• displayText = short UI label (ALWAYS required with dbColumnName)
• Snake_case, <50 chars, concise ("What is your name?" → "your_name")
• Unpublished: can update both together

RULES SYNTAX (alasql):
• skipRules: {{"queryWithNames":"{{dataElementId}}='val'","queryWithIds":"{{dataElementId}}='val'","viewType":"skipRule"}}
• calculationRules: {{"queryWithNames":"{{field1}}+{{field2}}","queryWithIds":"{{field1}}+{{field2}}","applyWhenQueryWithNames":"","applyWhenQueryWithIds":""}}
• validationFormula: {{"queryWithNames":"{{id}}='cond'","queryWithIds":"{{id}}='cond'"}}
• jumpRules: [{{"jumpTo":"END|{{dataElementId}}","queryWithNames":"...","queryWithIds":"..."}}]
• readonlyRules: {{"queryWithNames":"...","queryWithIds":"..."}}
Functions: today(), yeardiff(), daydiff(), monthdiff(), getTimeDiff(), IsChecked(), hasAny(), ifElseV2(), isNullOrEmpty(), toInt(), toDouble(), getRepeaterArrayLength(), getRepeaterPropertySum(), ifAnyOfRepeaterItems(), floor(), ceiling()

AUTO-CONFIG:
• Email: isTextArea=false, isNumeric=false, email regex
• Textarea: isTextArea=true
• UUIDv4 for all ID fields
• sortOrder reindex on reorder (no fieldID changes)

FINAL CHECK:
✓ All isPublished=true fields present
✓ Published fields only modified in allowed properties
✓ Deletion of published explained in message"""

        # Call the API with JSON mode
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        response_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()

        parsed_response = json.loads(response_text)

        return SurveyResponse(
            message=parsed_response.get("message", "Survey generated successfully"),
            form_data=parsed_response.get("form_data", [])
        )


async def demo_survey_generator():
    """Demo function to test survey generator."""
    print("=" * 80)
    print("SURVEY GENERATOR DEMO")
    print("=" * 80)

    client_name: ClientName = "openai"

    # Example 1: Generate a simple survey
    print("\n--- Example 1: Generate Gender, Sequence Number, and Address fields ---")
    user_request = """Create a survey with:
1. Gender (radio field with Male/Female options)
2. Sequence number (number field)
3. Address (textarea field)
All fields should be required."""

    result = await generate_survey(user_request, client_name=client_name)

    print(f"\nMessage: {result.message}")
    print(f"\nGenerated {len(result.form_data)} fields:")
    for field in result.form_data:
        print(f"  - {field['fieldType']}: {field['title']}")

    print("\n--- Full JSON Output ---")
    print(json.dumps({"message": result.message, "form_data": result.form_data}, indent=2))

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_survey_generator())
