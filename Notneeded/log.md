# Implementation Log: Revision Timetable Website

This document tracks all implementation details, decisions, and explanations for the revision timetable website.

## Project Overview

The project is a revision timetable website with a confidence-based learning system that helps students prioritize their study efficiently. Key features include:

- Dual database setup (local for testing, Railway for production)
- Confidence-based task generation
- Subtopic prioritization system
- User authentication and preferences
- Aesthetic glass-morphism UI with light/dark mode

## Implementation Details

### Database Schema

The database schema is designed to support:
1. User management and authentication
2. Curriculum structure (subjects, topics, subtopics)
3. Confidence tracking for each user's topics/subtopics
4. Task generation and management
5. User preferences and settings

### Application Structure

The application follows a clear separation of concerns:
- Backend: Python with Flask framework
- Frontend: HTML, JavaScript, and CSS
- Database: PostgreSQL (local and Railway)

### Confidence System

The confidence system uses a 1-5 scale where:
- 1 = Least confident
- 5 = Most confident

Topics with lower confidence levels are weighted more heavily in the task generation algorithm, calculated as (7 - confidence_level)². This ensures students focus on areas where they need the most improvement.

### Task Generation Algorithm

Tasks are generated based on:
1. User's study hours and preferences
2. Subject balance across the curriculum
3. Confidence-weighted topic selection
4. Prioritization of subtopics marked as important
5. Estimated duration (15-20 minutes per subtopic)

### User Interface

The UI implements a glass-morphism aesthetic:
- Light mode: Opaque white glass with accents
- Dark mode: Tinted opaque glass with complementary accents
- Responsive design for different devices
- Clear visualization of confidence levels and priorities
