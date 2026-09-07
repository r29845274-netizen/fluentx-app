import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/router/auth_status.dart';
import '../core/router/page_transitions.dart';
import '../core/router/router_notifier.dart';
import '../features/achievements/presentation/screens/achievements_screen.dart';
import '../features/certificates/presentation/screens/certificates_screen.dart';
import '../features/admin/presentation/screens/admin_console_screen.dart';
import '../features/ai_practice/presentation/screens/ai_practice_hub_screen.dart';
import '../features/authentication/presentation/screens/forgot_password_screen.dart';
import '../features/authentication/presentation/screens/login_screen.dart';
import '../features/authentication/presentation/screens/otp_verification_screen.dart';
import '../features/authentication/presentation/screens/signup_screen.dart';
import '../features/communication_dna/presentation/screens/communication_dna_screen.dart';
import '../features/grammar/presentation/screens/grammar_screen.dart';
import '../features/home/presentation/screens/home_screen.dart';
import '../features/interview_prep/presentation/screens/interview_prep_screen.dart';
import '../features/learn/presentation/screens/business_english_screen.dart';
import '../features/learn/presentation/screens/idioms_phrases_screen.dart';
import '../features/learn/presentation/screens/learn_hub_screen.dart';
import '../features/learn/presentation/screens/learning_path_screen.dart';
import '../features/learn/presentation/screens/pronunciation_practice_screen.dart';
import '../features/learn/presentation/screens/personalized_daily_practice_screen.dart';
import '../features/listening/presentation/screens/listening_screen.dart';
import '../features/onboarding/presentation/screens/onboarding_screen.dart';
import '../features/premium/presentation/screens/premium_screen.dart';
import '../features/profile/presentation/screens/daily_goals_screen.dart';
import '../features/profile/presentation/screens/help_support_screen.dart';
import '../features/profile/presentation/screens/profile_screen.dart';
import '../features/profile/presentation/screens/referral_screen.dart';
import '../features/progress/presentation/screens/progress_screen.dart';
import '../features/progress/presentation/screens/share_progress_card_screen.dart';
import '../features/settings/presentation/screens/edit_profile_screen.dart';
import '../features/settings/presentation/screens/legal_document_screen.dart';
import '../features/settings/presentation/screens/legal_compliance_center_screen.dart';
import '../features/settings/presentation/screens/legal_request_screen.dart';
import '../features/settings/presentation/screens/settings_screen.dart';
import '../features/splash/presentation/screens/splash_screen.dart';
import '../features/vocabulary/presentation/screens/vocabulary_screen.dart';
import '../features/writing/presentation/screens/writing_screen.dart';
import '../shared/widgets/navigation/app_shell.dart';
import 'route_paths.dart';

/// Root navigator key — needed so top-level routes (pushed on top of
/// the bottom-nav shell, e.g. Vocabulary, Settings) don't get trapped
/// inside a single tab's stack.
final _rootNavigatorKey = GlobalKey<NavigatorState>();

final _routerStartedAt = DateTime.now();
const _minimumSplashDuration = Duration(milliseconds: 1200);

/// Paths reachable without an authenticated + onboarded session.
const _publicPaths = {
  RoutePaths.splash,
  RoutePaths.login,
  RoutePaths.signup,
  RoutePaths.forgotPassword,
  RoutePaths.verifyEmailOtp,
};

final appRouterProvider = Provider<GoRouter>((ref) {
  final routerNotifier = ref.watch(routerNotifierProvider);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: RoutePaths.splash,
    debugLogDiagnostics: false,
    refreshListenable: routerNotifier,
    redirect: (context, state) async {
      final authStatus = routerNotifier.authStatus;
      final onboardingComplete = routerNotifier.isOnboardingComplete;
      final currentPath = state.matchedLocation;

      // Still resolving the persisted session — stay put on splash.
      if (authStatus == AuthStatus.unknown) {
        return currentPath == RoutePaths.splash ? null : RoutePaths.splash;
      }

      if (currentPath == RoutePaths.splash) {
        final elapsed = DateTime.now().difference(_routerStartedAt);
        final remainingMs =
            _minimumSplashDuration.inMilliseconds - elapsed.inMilliseconds;
        if (remainingMs > 0) {
          await Future<void>.delayed(Duration(milliseconds: remainingMs));
        }
      }

      final isPublicPath = _publicPaths.contains(currentPath);

      if (authStatus == AuthStatus.unauthenticated) {
        // Fresh signed-out launch: show splash briefly, then open login.
        if (currentPath == RoutePaths.splash) {
          return RoutePaths.login;
        }

        return isPublicPath ? null : RoutePaths.login;
      }

      // From here on, authStatus == authenticated.
      if (!onboardingComplete) {
        return currentPath == RoutePaths.onboarding ? null : RoutePaths.onboarding;
      }

      // Authenticated + onboarded but sitting on a pre-auth screen
      // (e.g. deep-link back to /login, or splash finished resolving)
      // → send them into the app.
      if (isPublicPath || currentPath == RoutePaths.onboarding) {
        return RoutePaths.home;
      }

      return null;
    },
    routes: [
      GoRoute(
        path: RoutePaths.splash,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const SplashScreen(),
        ),
      ),
      GoRoute(
        path: RoutePaths.onboarding,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const OnboardingScreen(),
        ),
      ),
      GoRoute(
        path: RoutePaths.login,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LoginScreen(),
        ),
      ),
      GoRoute(
        path: RoutePaths.signup,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const SignupScreen(),
        ),
      ),
      GoRoute(
        path: RoutePaths.forgotPassword,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const ForgotPasswordScreen(),
        ),
      ),
      GoRoute(
        path: RoutePaths.verifyEmailOtp,
        pageBuilder: (context, state) {
          final email = state.uri.queryParameters['email'] ?? '';
          final mode = state.uri.queryParameters['mode'] ?? 'login';
          return buildPageWithTransition(
            context: context,
            state: state,
            child: OtpVerificationScreen(
              email: email,
              isSignup: mode == 'signup',
            ),
          );
        },
      ),

      // ---- Bottom-nav shell: Home / Learn / Practice / Progress / Profile ----
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) => AppShell(
          navigationShell: navigationShell,
        ),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: RoutePaths.home,
                pageBuilder: (context, state) => buildPageWithTransition(
                  context: context,
                  state: state,
                  child: const HomeScreen(),
                ),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: RoutePaths.learn,
                pageBuilder: (context, state) => buildPageWithTransition(
                  context: context,
                  state: state,
                  child: const LearnHubScreen(),
                ),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: RoutePaths.aiPractice,
                pageBuilder: (context, state) => buildPageWithTransition(
                  context: context,
                  state: state,
                  child: const AiPracticeHubScreen(),
                ),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: RoutePaths.progress,
                pageBuilder: (context, state) => buildPageWithTransition(
                  context: context,
                  state: state,
                  child: const ProgressScreen(),
                ),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: RoutePaths.profile,
                pageBuilder: (context, state) => buildPageWithTransition(
                  context: context,
                  state: state,
                  child: const ProfileScreen(),
                ),
              ),
            ],
          ),
        ],
      ),

      // ---- Pushed on top of the shell (full-screen, own back stack) ----
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.learningPath,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LearningPathScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.vocabulary,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const VocabularyScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.grammar,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const GrammarScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.listening,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const ListeningScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.writing,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const WritingScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.personalizedDailyPractice,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const PersonalizedDailyPracticeScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.pronunciation,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const PronunciationPracticeScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.idiomsPhrases,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const IdiomsPhrasesScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.businessEnglish,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const BusinessEnglishScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.interviewPrep,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const InterviewPrepScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.shareProgress,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: ShareProgressCardScreen(
            mode: state.uri.queryParameters['mode'] ?? 'progress',
          ),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.communicationDna,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const CommunicationDnaScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.achievements,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const AchievementsScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.certificates,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const CertificatesScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.premium,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const PremiumScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.settings,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const SettingsScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.dailyGoals,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const DailyGoalsScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.referral,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const ReferralScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.helpSupport,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const HelpSupportScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.editProfile,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const EditProfileScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.privacyPolicy,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LegalDocumentScreen(
            title: 'Privacy Policy',
            sections: LegalDocumentScreen.privacySections,
          ),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.termsOfService,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LegalDocumentScreen(
            title: 'Terms of Service',
            sections: LegalDocumentScreen.termsSections,
          ),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.legalCompliance,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LegalComplianceCenterScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.ipPolicy,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LegalDocumentScreen(
            title: 'IP & Copyright Policy',
            sections: LegalDocumentScreen.ipSections,
          ),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.dataCompliance,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LegalDocumentScreen(
            title: 'Data & Compliance',
            sections: LegalDocumentScreen.dataComplianceSections,
          ),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.legalRequest,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const LegalRequestScreen(),
        ),
      ),
      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.adminConsole,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const AdminConsoleScreen(),
        ),
      ),
    ],
  );
});
