import 'package:flutter/material.dart';

/// The 5 learning goals offered during onboarding, matching the
/// product spec's personalization step.
enum OnboardingGoal {
  interviewPrep,
  dailyEnglish,
  businessEnglish,
  examPrep,
  generalFluency;

  String get storageValue => switch (this) {
        OnboardingGoal.interviewPrep => 'interview_prep',
        OnboardingGoal.dailyEnglish => 'daily_english',
        OnboardingGoal.businessEnglish => 'business_english',
        OnboardingGoal.examPrep => 'exam_prep',
        OnboardingGoal.generalFluency => 'general_fluency',
      };

  String get label => switch (this) {
        OnboardingGoal.interviewPrep => 'Interview Prep',
        OnboardingGoal.dailyEnglish => 'Daily English',
        OnboardingGoal.businessEnglish => 'Business English',
        OnboardingGoal.examPrep => 'Exam Prep',
        OnboardingGoal.generalFluency => 'General Fluency',
      };

  String get description => switch (this) {
        OnboardingGoal.interviewPrep => 'Ace job interviews with confidence',
        OnboardingGoal.dailyEnglish => 'Speak naturally in everyday situations',
        OnboardingGoal.businessEnglish => 'Communicate professionally at work',
        OnboardingGoal.examPrep => 'Prepare for English proficiency exams',
        OnboardingGoal.generalFluency => 'Build overall speaking confidence',
      };

  IconData get icon => switch (this) {
        OnboardingGoal.interviewPrep => Icons.work_outline,
        OnboardingGoal.dailyEnglish => Icons.chat_bubble_outline,
        OnboardingGoal.businessEnglish => Icons.business_outlined,
        OnboardingGoal.examPrep => Icons.school_outlined,
        OnboardingGoal.generalFluency => Icons.auto_awesome,
      };
}
