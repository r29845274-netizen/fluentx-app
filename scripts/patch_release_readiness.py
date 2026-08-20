#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

pubspec = root / 'pubspec.yaml'
if pubspec.exists():
    text = pubspec.read_text()
    import re
    text = re.sub(r'^version:\s*[^\n]+$', 'version: 1.0.0+1', text, flags=re.M)
    pubspec.write_text(text)

settings = root / 'lib/features/settings/presentation/screens/settings_screen.dart'
if settings.exists():
    text = settings.read_text().replace("trailing: Text('0.1.0')", "trailing: Text('1.0.0')")
    settings.write_text(text)

legal = root / 'lib/features/settings/presentation/screens/legal_document_screen.dart'
if legal.exists():
    text = legal.read_text()
    start = text.find('  static const privacySections')
    end = text.find('\n  @override', start)
    if start != -1 and end != -1:
        replacement = r'''  static const privacySections = <(String, String)>[
    ('Data we collect', 'FluentX may process account details, profile information, learning goals, placement results, lesson progress, vocabulary and grammar activity, writing submissions, speaking or interview responses, AI practice messages, device notification tokens, subscription status, and technical diagnostics needed to operate the service.'),
    ('How we use data', 'We use this information to authenticate your account, personalize learning paths, save progress, provide practice features, generate AI-assisted feedback, maintain streaks and achievements, deliver notifications you enable, support subscriptions, prevent abuse, troubleshoot errors, and improve reliability.'),
    ('Voice, writing, and AI processing', 'When you use AI, speaking, writing, placement, or interview features, the content you submit may be sent securely to service providers that perform AI inference, speech processing, hosting, authentication, or related infrastructure. Do not submit confidential information that is unnecessary for language practice.'),
    ('Payments', 'Google Play and RevenueCat may process purchase and subscription information. FluentX receives subscription and entitlement status but does not store your complete payment-card details.'),
    ('Analytics, crash reporting, and notifications', 'Firebase services may process app-instance, device, crash, diagnostic, analytics, and notification-delivery information to help us understand reliability and deliver enabled notifications.'),
    ('Data sharing', 'We do not sell personal data. Data is shared only with service providers needed to operate FluentX, when required by law, to protect users and the service, or as part of a legitimate business transfer subject to applicable safeguards.'),
    ('Retention', 'Account and learning data may be retained while your account is active and for a limited period afterward where required for security, legal, fraud-prevention, backup, or accounting purposes. Account deletion removes user-linked application data according to the deletion process and provider retention rules.'),
    ('Your controls', 'You can edit supported profile settings, change notification preferences, restore purchases, sign out, and request permanent account deletion from Settings. You may also contact support for privacy-related requests where required by applicable law.'),
    ('Security', 'FluentX uses authenticated requests, Supabase row-level security, server-side secrets for privileged services, and restricted backend functions. No system can guarantee absolute security, so keep your sign-in account protected.'),
    ('Children', 'FluentX is not intended to knowingly collect personal information from children below the minimum age required to consent to online services in their jurisdiction without appropriate authorization.'),
    ('Changes', 'We may update this policy as FluentX evolves. Material changes should be reflected in the published policy and, where required, communicated in the app or through another appropriate channel.'),
  ];

  static const termsSections = <(String, String)>[
    ('Using FluentX', 'FluentX is a language-learning and communication-practice service. You may use it only for lawful purposes and in accordance with these terms and applicable platform rules.'),
    ('Your account', 'You are responsible for maintaining the security of your account and for activity performed through it. Provide accurate account information and do not attempt to access another user account.'),
    ('Learning and AI feedback', 'Scores, corrections, model answers, interview coaching, placement estimates, and other AI-generated outputs are educational aids. They can be incomplete or inaccurate and should not be treated as professional, legal, medical, employment, or other guaranteed advice.'),
    ('Acceptable use', 'Do not abuse, reverse engineer, disrupt, overload, scrape, exploit, bypass security, misuse AI features, upload unlawful content, or interfere with FluentX, its providers, or other users.'),
    ('Subscriptions and free trials', 'Paid plans, trials, renewals, cancellations, refunds, and billing are governed by the purchase information shown in FluentX and the applicable Google Play or payment-provider terms. Subscription access may remain available until the end of a paid period after cancellation.'),
    ('Content and intellectual property', 'FluentX software, branding, lesson structure, original learning content, and product design remain protected by applicable intellectual-property laws. These terms grant you a personal, limited, non-transferable right to use the service.'),
    ('Availability and changes', 'We may maintain, improve, add, remove, or replace features and content. Temporary interruptions may occur because of maintenance, internet conditions, app-store services, or third-party infrastructure.'),
    ('Account suspension or termination', 'We may restrict or terminate access where reasonably necessary for security, fraud prevention, unlawful activity, material abuse, or repeated violation of these terms. You may delete your account from Settings.'),
    ('Limitation', 'To the extent permitted by applicable law, FluentX is provided on an as-available basis without a guarantee that every feature or AI result will always be uninterrupted, error-free, or suitable for every purpose.'),
    ('Changes to terms', 'These terms may be updated as the service changes. Continued use after an effective update may constitute acceptance where permitted by law.'),
  ];
'''
        text = text[:start] + replacement + text[end:]
        legal.write_text(text)

print('Release-readiness patch applied')
