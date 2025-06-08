# Accessibility Features for Emotional Wellness API

This document provides comprehensive information about the accessibility features implemented in the Emotional Wellness API to support differently abled users.

## Table of Contents

1. [Introduction](#introduction)
2. [Supported Disability Types](#supported-disability-types)
3. [Adaptation Types](#adaptation-types)
4. [User Preferences](#user-preferences)
5. [API Endpoints](#api-endpoints)
6. [Integration Guide](#integration-guide)
7. [Emotional Wellness Specific Adaptations](#emotional-wellness-specific-adaptations)
8. [Compliance Standards](#compliance-standards)
9. [Testing and Validation](#testing-and-validation)

## Introduction

The Emotional Wellness API includes comprehensive accessibility features designed to ensure that all users, regardless of ability, can benefit from emotional wellness services. These features include:

- **Content Adaptations**: Automatic adaptation of content based on user needs
- **User Preferences**: Customizable accessibility settings for each user
- **Specialized Adaptations**: Adaptations specific to emotional wellness content
- **WCAG and Section 508 Compliance**: Adherence to accessibility standards

## Supported Disability Types

The system supports adaptations for the following disability types:

| Disability Type | Description | Primary Adaptations |
|----------------|-------------|---------------------|
| Vision | Visual impairments including blindness, low vision | Screen reader compatibility, high contrast, large text |
| Hearing | Hearing impairments including deafness | Captioning, text alternatives, visual cues |
| Motor | Physical disabilities affecting movement | Alternative input methods, simplified navigation |
| Cognitive | Cognitive disabilities affecting processing | Text simplification, symbols, extended time |
| Speech | Speech impairments affecting communication | Alternative communication methods |
| Sensory | Sensory processing sensitivities | Sensory load reduction, simplified interfaces |
| Learning | Learning disabilities | Text simplification, emotional cues, extended time |
| Neurodiversity | Autism, ADHD, etc. | Sensory load reduction, emotional cues, structured content |

## Adaptation Types

The system provides the following types of adaptations:

| Adaptation Type | Description | Primary Beneficiaries |
|----------------|-------------|----------------------|
| Text Simplification | Simplifies complex text | Cognitive, Learning |
| Text-to-Speech | Converts text to spoken words | Vision |
| Speech-to-Text | Converts speech to text | Hearing, Speech |
| High Contrast | Enhances visual contrast | Vision |
| Large Text | Increases text size | Vision |
| Screen Reader Compatibility | Optimizes for screen readers | Vision |
| Alternative Input | Supports different input methods | Motor |
| Captioning | Provides text captions | Hearing |
| Symbols and Pictograms | Uses visual symbols | Cognitive, Learning |
| Emotional Cues | Explicit emotional context | Cognitive, Neurodiversity |
| Time Extension | Extends timeouts | Cognitive, Motor, Learning |
| Multi-Modal Communication | Multiple formats | All |
| Simplified Navigation | Easier interface navigation | Cognitive, Motor |
| Sensory Overload Reduction | Reduces sensory stimuli | Sensory, Neurodiversity |

## User Preferences

Users can customize their accessibility preferences through the API. Key preferences include:

- **Enabled/Disabled**: Toggle accessibility features
- **Disability Types**: Declare specific disabilities
- **Preferred Adaptations**: Select specific adaptations
- **Excluded Adaptations**: Exclude unwanted adaptations
- **Language Complexity**: Set preferred language complexity level (1-10)
- **Communication Mode**: Set preferred communication mode
- **Metaphor Usage**: Control use of metaphors in content
- **Crisis Alert Mode**: Set preferred crisis notification format
- **Sensory Load**: Toggle sensory load reduction
- **Timeout Extensions**: Toggle extended timeouts

## API Endpoints

### Get User Preferences

```
GET /accessibility/preferences
```

Returns the current user's accessibility preferences.

### Update User Preferences

```
PUT /accessibility/preferences
```

Update specific accessibility preferences.

Example request body:
```json
{
  "enabled": true,
  "disabilities": ["cognitive", "sensory"],
  "preferred_adaptations": ["text_simplification", "sensory_overload_reduction"],
  "language_complexity": 3,
  "use_symbols": true
}
```

### Get Recommended Adaptations

```
POST /accessibility/disabilities
```

Get recommended adaptations for specific disabilities.

Example request body:
```json
["vision", "cognitive"]
```

### Test Adaptation

```
GET /accessibility/test-adaptation?adaptation_type=text_simplification&sample_text=Your%20sample%20text
```

Test a specific adaptation on sample text.

### Enable for Disability Profile

```
POST /accessibility/bulk-enable
```

Enable recommended adaptations for a set of disabilities.

Example request body:
```json
["vision", "cognitive"]
```

## Integration Guide

### Application Setup

To integrate accessibility features into your application:

```python
from fastapi import FastAPI
from src.accessibility.integration import register_accessibility_features

app = FastAPI()

# Register accessibility features
register_accessibility_features(app)
```

### Using Accessibility Service

```python
from src.accessibility.integration import accessibility_service

async def handle_user_content(user_id: str, content: dict):
    # Adapt content for user's accessibility needs
    adapted_content = await accessibility_service.adapt_symbolic_content(
        user_id, content
    )
    return adapted_content
```

### Middleware Integration

The AccessibilityMiddleware automatically adapts JSON responses based on the user's preferences. No additional code is needed after registration.

## Emotional Wellness Specific Adaptations

The accessibility module includes specialized adaptations for emotional wellness content:

### Symbolic Pattern Adaptations

- **Descriptive Versions**: Text descriptions of symbolic patterns
- **Simplified Versions**: Simplified explanations of patterns
- **Low-Sensory Versions**: Reduced sensory impact versions
- **Emotional Cues**: Added emotional context for patterns

### Archetype Adaptations

- **Concrete Explanations**: Plain language explanations of archetypes
- **Emotional Meaning**: Explicit emotional context for archetypes

### Crisis Notification Adaptations

- **Multi-Modal Presentation**: Visual, audio, and symbol-based notifications
- **Simplified Explanations**: Clear, direct crisis information
- **Sensory-Sensitive Versions**: Gentler presentation of urgent information

### Emotional Weather Report Adaptations

- **Direct vs. Metaphorical**: Options for literal or metaphorical descriptions
- **Symbol Enhancement**: Added symbolic representations
- **Language Simplification**: Simplified language versions

### Therapist Communication Adaptations

- **Simplified Messages**: Simplified versions of therapist communications
- **Symbol Enhancement**: Added symbols to clarify meaning
- **Multi-Modal Options**: Text, audio, and visual communication options
- **Emotional Cues**: Added emotional context for communications

## Compliance Standards

The accessibility features are designed to comply with:

- **WCAG 2.1 Level AA**: Web Content Accessibility Guidelines
- **Section 508**: U.S. federal accessibility requirements
- **ADA**: Americans with Disabilities Act requirements

## Testing and Validation

To test accessibility features:

1. **User Preference Testing**:
   ```
   GET /accessibility/preferences
   ```

2. **Adaptation Testing**:
   ```
   GET /accessibility/test-adaptation?adaptation_type=text_simplification&sample_text=Test%20content
   ```

3. **Content Adaptation Testing**:
   ```python
   adapted = await accessibility_service.adapt_symbolic_content(
       user_id, content
   )
   ```

4. **Response Middleware Testing**:
   Make any API request with an authenticated user who has accessibility preferences enabled.

## Best Practices

1. **Always Respect User Preferences**: Honor user-specified accessibility settings
2. **Provide Multiple Modalities**: Offer information in multiple formats
3. **Test with Real Users**: Involve differently abled users in testing
4. **Use Clear Language**: Avoid jargon and complex terminology
5. **Provide Sufficient Time**: Allow extended time for interactions
6. **Maintain Consistency**: Keep navigation and interaction patterns consistent
7. **Offer Alternatives**: Provide alternatives for all content types
8. **Validate Adaptations**: Ensure adaptations maintain content integrity
