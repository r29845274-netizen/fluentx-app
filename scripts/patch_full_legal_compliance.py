from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# -----------------------------------------------------------------------------
# Legal center + legal request screen
# -----------------------------------------------------------------------------
legal_center = root / 'lib/features/settings/presentation/screens/legal_compliance_center_screen.dart'
legal_center.parent.mkdir(parents=True, exist_ok=True)
legal_center.write_text(r'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../../routes/route_paths.dart';

class LegalComplianceCenterScreen extends StatefulWidget {
  const LegalComplianceCenterScreen({super.key});

  @override
  State<LegalComplianceCenterScreen> createState() => _LegalComplianceCenterScreenState();
}

class _LegalComplianceCenterScreenState extends State<LegalComplianceCenterScreen> {
  Map<String, dynamic>? _status;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await Supabase.instance.client.rpc('get_my_legal_status');
      if (!mounted) return;
      setState(() {
        _status = data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final accepted = _status?['accepted_current'] == true;
    final openRequests = int.tryParse((_status?['open_requests'] ?? 0).toString()) ?? 0;
    return Scaffold(
      appBar: AppBar(title: const Text('Legal & Data Compliance')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Row(children: [Icon(Icons.verified_user_outlined), SizedBox(width: 8), Text('FluentX Legal Center', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900))]),
              const SizedBox(height: 8),
              const Text('Review the rules that govern FluentX, understand how data is handled, and submit privacy or intellectual-property requests.'),
              if (!_loading) ...[
                const SizedBox(height: 12),
                Wrap(spacing: 8, runSpacing: 8, children: [
                  Chip(avatar: Icon(accepted ? Icons.check_circle : Icons.info_outline, size: 18), label: Text(accepted ? 'Current terms accepted' : 'Legal acceptance needed')),
                  Chip(avatar: const Icon(Icons.inbox_outlined, size: 18), label: Text('$openRequests open request${openRequests == 1 ? '' : 's'}')),
                ]),
              ],
            ]),
          ),
          const SizedBox(height: 18),
          _LegalTile(
            icon: Icons.description_outlined,
            title: 'Terms of Use',
            subtitle: 'Account rules, acceptable use, subscriptions, AI disclaimer, liability and termination.',
            onTap: () => context.push(RoutePaths.termsOfService),
          ),
          _LegalTile(
            icon: Icons.privacy_tip_outlined,
            title: 'Privacy Policy',
            subtitle: 'Data collection, AI/voice processing, providers, retention, security and your controls.',
            onTap: () => context.push(RoutePaths.privacyPolicy),
          ),
          _LegalTile(
            icon: Icons.copyright_outlined,
            title: 'IP & Copyright Infringement',
            subtitle: 'Copyright/trademark rules, reporting requirements, review process and repeat-abuse handling.',
            onTap: () => context.push(RoutePaths.ipPolicy),
          ),
          _LegalTile(
            icon: Icons.shield_outlined,
            title: 'Data & Compliance',
            subtitle: 'Data categories, permissions, security controls, deletion, billing and Play compliance information.',
            onTap: () => context.push(RoutePaths.dataCompliance),
          ),
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: () => context.push(RoutePaths.legalRequest),
            icon: const Icon(Icons.assignment_outlined),
            label: const Text('Submit a Legal / Privacy Request'),
          ),
        ],
      ),
    );
  }
}

class _LegalTile extends StatelessWidget {
  const _LegalTile({required this.icon, required this.title, required this.subtitle, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 10),
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: CircleAvatar(child: Icon(icon)),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
      subtitle: Text(subtitle),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    ),
  );
}
''', encoding='utf-8')

request_screen = root / 'lib/features/settings/presentation/screens/legal_request_screen.dart'
request_screen.write_text(r'''import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class LegalRequestScreen extends StatefulWidget {
  const LegalRequestScreen({super.key});

  @override
  State<LegalRequestScreen> createState() => _LegalRequestScreenState();
}

class _LegalRequestScreenState extends State<LegalRequestScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _subject = TextEditingController();
  final _details = TextEditingController();
  final _work = TextEditingController();
  final _location = TextEditingController();
  String _type = 'data_question';
  bool _authority = false;
  bool _accuracy = false;
  bool _sending = false;

  bool get _isIp => _type == 'ip_infringement';

  @override
  void initState() {
    super.initState();
    final user = Supabase.instance.client.auth.currentUser;
    _email.text = user?.email ?? '';
    _name.text = (user?.userMetadata?['full_name'] ?? user?.userMetadata?['name'] ?? '').toString();
  }

  @override
  void dispose() {
    for (final c in [_name, _email, _subject, _details, _work, _location]) { c.dispose(); }
    super.dispose();
  }

  String? _required(String? value, int min, String label) {
    if ((value ?? '').trim().length < min) return '$label is required.';
    return null;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || !_accuracy || (_isIp && !_authority) || _sending) {
      if (!_accuracy || (_isIp && !_authority)) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please complete the required confirmations.')));
      }
      return;
    }
    setState(() => _sending = true);
    try {
      final data = await Supabase.instance.client.rpc('submit_legal_request', params: {
        'p_request_type': _type,
        'p_claimant_name': _name.text.trim(),
        'p_contact_email': _email.text.trim(),
        'p_subject': _subject.text.trim(),
        'p_details': _details.text.trim(),
        'p_original_work': _isIp ? _work.text.trim() : null,
        'p_material_location': _isIp ? _location.text.trim() : null,
        'p_authority_confirmed': _authority,
        'p_accuracy_confirmed': _accuracy,
      });
      if (!mounted) return;
      final map = data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Request received'),
          content: Text('Your request has been recorded. Reference: ${map['request_id'] ?? 'submitted'}'),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK'))],
        ),
      );
      if (mounted) Navigator.of(context).pop();
    } on PostgrestException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not submit the request. Please try again.')));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Legal / Privacy Request')),
    body: Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Request type', style: TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          DropdownButtonFormField<String>(
            value: _type,
            decoration: const InputDecoration(border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: 'data_question', child: Text('Data / privacy question')),
              DropdownMenuItem(value: 'privacy_access', child: Text('Access my personal data')),
              DropdownMenuItem(value: 'privacy_correction', child: Text('Correct my personal data')),
              DropdownMenuItem(value: 'privacy_deletion', child: Text('Privacy deletion request')),
              DropdownMenuItem(value: 'ip_infringement', child: Text('Copyright / IP infringement report')),
              DropdownMenuItem(value: 'other_legal', child: Text('Other legal request')),
            ],
            onChanged: (v) => setState(() => _type = v ?? 'data_question'),
          ),
          const SizedBox(height: 12),
          TextFormField(controller: _name, decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Your full name'), validator: (v) => _required(v, 2, 'Name')),
          const SizedBox(height: 12),
          TextFormField(controller: _email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Contact email'), validator: (v) => (v ?? '').contains('@') ? null : 'Enter a valid email.'),
          const SizedBox(height: 12),
          TextFormField(controller: _subject, maxLength: 180, decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Subject'), validator: (v) => _required(v, 3, 'Subject')),
          const SizedBox(height: 12),
          TextFormField(controller: _details, minLines: 5, maxLines: 10, maxLength: 8000, decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Detailed description'), validator: (v) => _required(v, 20, 'Detailed description')),
          if (_isIp) ...[
            const SizedBox(height: 12),
            TextFormField(controller: _work, minLines: 2, maxLines: 5, maxLength: 3000, decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Describe the original protected work'), validator: (v) => _required(v, 5, 'Original work description')),
            const SizedBox(height: 12),
            TextFormField(controller: _location, minLines: 2, maxLines: 5, maxLength: 3000, decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Identify the material and where it appears'), validator: (v) => _required(v, 5, 'Material location')),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: _authority,
              onChanged: (v) => setState(() => _authority = v ?? false),
              title: const Text('I am the rights holder or authorized to act for the rights holder.'),
            ),
          ],
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            value: _accuracy,
            onChanged: (v) => setState(() => _accuracy = v ?? false),
            title: const Text('I confirm the information in this request is accurate to the best of my knowledge.'),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(onPressed: _sending ? null : _submit, icon: const Icon(Icons.send_outlined), label: Text(_sending ? 'Submitting…' : 'Submit Request')),
        ],
      ),
    ),
  );
}
''', encoding='utf-8')

# -----------------------------------------------------------------------------
# Stronger legal document content: Terms, Privacy, IP, Data & Compliance.
# -----------------------------------------------------------------------------
legal = root / 'lib/features/settings/presentation/screens/legal_document_screen.dart'
text = legal.read_text(encoding='utf-8')
start = text.find('  static const privacySections')
end = text.find('\n  @override', start)
if start < 0 or end < 0:
    raise SystemExit('Legal document section markers not found')
replacement = r'''  static const privacySections = <(String, String)>[
    ('Effective date', 'Effective 24 August 2026. This policy explains how FluentX handles personal data when you use the Android app, AI features, learning services and related support channels.'),
    ('Information you provide', 'We may process account details, profile information, learning goals, native-language preference, placement answers, lesson progress, vocabulary and grammar activity, writing submissions, speaking or interview responses, AI practice messages, support requests and other information you intentionally submit.'),
    ('Device and service information', 'The service may process app-instance identifiers, device or operating-system information, notification tokens, diagnostics, crash information, timestamps, feature usage, security signals and similar technical data needed to operate and protect FluentX.'),
    ('Voice, microphone and speech recognition', 'Microphone access is requested only when you use a speaking feature. Spoken input may be processed by device speech services and/or service providers to convert speech to text or enable language-practice features. FluentX does not claim to perform biometric identification from your voice.'),
    ('AI processing', 'Text, transcribed speech, writing, interview answers and relevant conversation context may be sent to AI service providers to generate educational responses, corrections, scoring or feedback. AI outputs can be inaccurate; avoid entering confidential information that is not needed for language learning.'),
    ('Why we use data', 'We use data to authenticate users, personalize a learning path, save progress, operate Maya AI and other practice tools, generate educational feedback, maintain streaks and achievements, manage subscriptions, provide notifications you enable, respond to requests, prevent fraud or abuse, secure the service, troubleshoot failures and improve reliability.'),
    ('Payments and subscriptions', 'Google Play and RevenueCat may process purchase and subscription information. FluentX receives product, transaction and entitlement status needed to grant access. FluentX does not receive or store your complete payment-card number.'),
    ('Analytics, diagnostics and notifications', 'Firebase and similar infrastructure may process app-instance, device, diagnostic, crash, analytics and notification-delivery information. Analytics should be configured to support product reliability and usage measurement, not to sell personal data.'),
    ('Service providers and disclosures', 'We may disclose information to hosting, authentication, database, AI, speech, analytics, notification, billing and customer-support providers that help operate FluentX; when required by law; to protect rights, safety or the service; or in a legitimate business transfer subject to applicable safeguards. We do not sell personal data.'),
    ('Data retention', 'Data is retained only as reasonably needed for the purposes described here, account operation, security, fraud prevention, legal obligations, billing records and backups. Retention periods may differ by data category and provider. Data associated with a valid deletion request is removed or de-identified unless retention is legally required.'),
    ('Your rights and choices', 'Depending on applicable law, you may have rights to access, correct, delete or otherwise control personal data. FluentX provides profile controls, notification controls, in-app account deletion and a Legal / Privacy Request form. We may need to verify identity before fulfilling a request.'),
    ('Account deletion', 'You can request permanent deletion from Settings. The deletion process removes user-linked application data within FluentX systems, subject to limited retention required for security, fraud prevention, financial records, legal obligations and provider backup cycles.'),
    ('Security', 'FluentX uses authenticated requests, row-level database security, server-side privileged functions, restricted secrets and transport encryption provided by the platform. No internet service can guarantee absolute security.'),
    ('Children', 'FluentX is not intended to knowingly collect personal information from children below the minimum age required to consent to online services in their jurisdiction without appropriate parent or guardian authorization.'),
    ('International processing', 'Service providers may process data in countries other than your own. Where required, transfers should rely on appropriate contractual, legal or platform safeguards.'),
    ('Policy updates', 'We may update this policy as the app, providers or law changes. The effective date identifies the current version. Material changes should be communicated where required, and a new acceptance may be requested when appropriate.'),
  ];

  static const termsSections = <(String, String)>[
    ('Effective date and agreement', 'Effective 24 August 2026. By creating or using a FluentX account after accepting these Terms, you agree to these Terms of Use and acknowledge the Privacy Policy. If you do not agree, do not use the service.'),
    ('Eligibility and account', 'Use FluentX only if you are legally able to enter this agreement in your jurisdiction. You are responsible for accurate account information, keeping your sign-in method secure and activity performed through your account.'),
    ('License to use FluentX', 'FluentX grants you a limited, personal, revocable, non-exclusive and non-transferable right to use the app for lawful language-learning purposes, subject to these Terms and applicable platform rules.'),
    ('Learning and AI outputs', 'Lessons, CEFR estimates, pronunciation or clarity scores, corrections, model answers, interview coaching and AI-generated outputs are educational aids. They can be incomplete or inaccurate and do not guarantee exam results, employment, fluency, legal outcomes or professional advice.'),
    ('Acceptable use', 'Do not misuse, attack, overload, scrape, reverse engineer where prohibited, bypass security or subscription controls, obtain other users data, upload unlawful or infringing content, use FluentX to facilitate harmful or illegal activity, or interfere with the service or its providers.'),
    ('User submissions', 'You retain rights you lawfully hold in content you submit. You grant FluentX and its service providers a limited right to process that content only as needed to operate, secure and improve the requested service features, consistent with the Privacy Policy.'),
    ('Intellectual property', 'The FluentX name, branding, software, interfaces, original lessons, content selection, learning structures, graphics and other proprietary materials are protected by applicable intellectual-property laws. Except for the limited app-use license, no rights are transferred to you.'),
    ('Third-party rights', 'You must have the right to submit content you provide to FluentX. Do not upload copyrighted, trademarked, confidential or proprietary material in a way that violates another persons rights. Valid infringement reports may result in content restriction, removal or account action.'),
    ('Subscriptions, billing and cancellation', 'Paid subscriptions are processed through Google Play and supported billing infrastructure. Prices, billing periods, renewal terms and trial information are displayed before purchase. You can manage or cancel subscriptions using the applicable Google Play controls. Refunds are governed by applicable law and platform policies.'),
    ('Service changes and availability', 'We may maintain, improve, replace, limit or discontinue features and content. Temporary interruptions may occur because of maintenance, device limitations, connectivity, abuse prevention, app-store services or third-party infrastructure.'),
    ('Suspension and termination', 'We may restrict or terminate access when reasonably necessary for security, fraud prevention, unlawful activity, infringement, material abuse, non-payment or repeated violations. You may stop using FluentX and can request account deletion through Settings.'),
    ('Disclaimer', 'To the extent permitted by law, FluentX is provided on an as-available basis. We do not promise that every feature, AI output, speech-recognition result, score or learning result will always be accurate, uninterrupted or suitable for every purpose.'),
    ('Limitation of liability', 'To the extent permitted by applicable law, FluentX and its operators are not liable for indirect, incidental, special, consequential or punitive losses arising from use of the service. Nothing in these Terms excludes rights or liabilities that cannot legally be excluded.'),
    ('Changes to terms', 'We may update these Terms as FluentX evolves. The effective date identifies the current version. If a material change requires renewed agreement, FluentX may request a new acceptance before continued use.'),
  ];

  static const ipSections = <(String, String)>[
    ('Respect for intellectual property', 'FluentX respects copyright, trademark and other intellectual-property rights. Users must not use FluentX to submit or distribute content that they do not have the legal right to use.'),
    ('What can be reported', 'A rights holder or authorized representative can report material in FluentX that is believed to infringe copyright, trademark or another intellectual-property right. A report should identify both the protected work or right and the allegedly infringing material.'),
    ('Required report information', 'Provide your full name and contact email; identify or describe the original protected work; identify the allegedly infringing material and where it appears in FluentX; explain the claimed infringement; confirm that you are the rights holder or authorized representative; and confirm that the information supplied is accurate to the best of your knowledge.'),
    ('How to submit', 'Signed-in users can open Legal & Data Compliance → Submit a Legal / Privacy Request → Copyright / IP infringement report. The request is stored with a reference ID for review.'),
    ('Review and action', 'FluentX may request additional information, investigate the report, restrict or remove material, preserve evidence where appropriate, notify affected users where lawful, or reject reports that are incomplete, abusive or unsupported.'),
    ('Counter-information and mistakes', 'If material is restricted because of an infringement report and a user believes the action was mistaken, the user may submit an Other Legal Request with the reference information and an explanation. Applicable legal procedures and platform requirements may affect how a dispute is handled.'),
    ('Repeat infringement or abuse', 'Accounts repeatedly involved in substantiated infringement, or users who abuse the reporting process, may be restricted or terminated where appropriate and permitted by law.'),
    ('No ownership transfer', 'Submitting content to FluentX does not transfer ownership to FluentX. Processing rights are limited to operating the requested service as described in the Terms and Privacy Policy.'),
  ];

  static const dataComplianceSections = <(String, String)>[
    ('Data map', 'FluentX handles account/profile data, learning progress, AI and writing inputs, transcribed speech, subscription entitlement data, device/notification identifiers, analytics and diagnostics, referral or growth events, and support/legal requests. The Privacy Policy explains why each category is processed.'),
    ('Permissions', 'Microphone permission is used for speaking features and notification permission is used for reminders or updates that you enable. The app should request permissions in context and continue to provide non-dependent functions when a permission is denied.'),
    ('Authentication and authorization', 'User data access is protected by authenticated sessions and database row-level security. Sensitive operations such as account deletion, subscription synchronization, AI scoring and administrative functions use restricted backend functions.'),
    ('Secrets and privileged access', 'Provider secrets and service-role credentials belong on secure servers or protected build-secret systems, not in the mobile client, public repositories or user-visible logs.'),
    ('Data minimization and purpose limitation', 'Features should collect and process only information reasonably needed for authentication, learning, AI assistance, billing, reliability, security, analytics, support and legal obligations. New data uses should be evaluated against the Privacy Policy and platform disclosures before release.'),
    ('Retention and deletion', 'User-linked application data is subject to account deletion and privacy-request workflows. Limited records may be retained where required for billing, fraud prevention, security, legal obligations or provider backup cycles.'),
    ('AI and speech transparency', 'The app discloses that AI and speech providers may process submitted or transcribed content. AI output is educational and may be inaccurate. Voice features do not claim biometric identity analysis.'),
    ('Billing compliance', 'Android digital subscriptions use Google Play billing with RevenueCat entitlement synchronization. The app should show live store pricing and provide purchase restoration and subscription-management access where required.'),
    ('Google Play declarations', 'The repository contains a Play Data Safety worksheet and release checklist. Final Play Console declarations must match the exact production AAB, enabled SDKs, permissions and live data practices at submission time.'),
    ('User controls and requests', 'Users can manage supported profile data and notifications, restore purchases, delete their account, review legal documents and submit access, correction, deletion, data or IP requests from the Legal Center.'),
    ('Security response', 'Potential security incidents should be investigated promptly, privileged credentials rotated when necessary, affected systems contained, logs preserved appropriately and user/regulatory notification performed where required by applicable law.'),
    ('Compliance is ongoing', 'Legal and platform requirements change. FluentX should re-check its final production build, providers, data practices and public policies before each material release rather than treating compliance as a one-time task.'),
  ];
'''
legal.write_text(text[:start] + replacement + text[end:], encoding='utf-8')

# -----------------------------------------------------------------------------
# Routes + router
# -----------------------------------------------------------------------------
routes = root / 'lib/routes/route_paths.dart'
text = routes.read_text(encoding='utf-8')
insert_after = "  static const String termsOfService = '/terms-of-service';"
if "static const String legalCompliance" not in text:
    text = text.replace(insert_after, insert_after + "\n  static const String legalCompliance = '/legal-compliance';\n  static const String ipPolicy = '/ip-policy';\n  static const String dataCompliance = '/data-compliance';\n  static const String legalRequest = '/legal-request';", 1)
routes.write_text(text, encoding='utf-8')

router = root / 'lib/routes/app_router.dart'
text = router.read_text(encoding='utf-8')
if "legal_compliance_center_screen.dart" not in text:
    text = text.replace("import '../features/settings/presentation/screens/legal_document_screen.dart';", "import '../features/settings/presentation/screens/legal_document_screen.dart';\nimport '../features/settings/presentation/screens/legal_compliance_center_screen.dart';\nimport '../features/settings/presentation/screens/legal_request_screen.dart';", 1)
marker = "      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.adminConsole,"
if "path: RoutePaths.legalCompliance" not in text:
    pos = text.find(marker)
    if pos < 0: raise SystemExit('Admin route marker not found')
    block = r'''      GoRoute(
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
'''
    text = text[:pos] + block + text[pos:]
router.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# Settings: add legal center entry.
# -----------------------------------------------------------------------------
settings = root / 'lib/features/settings/presentation/screens/settings_screen.dart'
text = settings.read_text(encoding='utf-8')
if "label: 'Legal & Data Compliance'" not in text:
    marker = "                  ProfileMenuTile(\n                    icon: Icons.shield_outlined,\n                    label: 'Privacy Policy',"
    pos = text.find(marker)
    if pos < 0: raise SystemExit('Privacy settings marker not found')
    block = """                  ProfileMenuTile(\n                    icon: Icons.gavel_outlined,\n                    label: 'Legal & Data Compliance',\n                    onTap: () => context.push(RoutePaths.legalCompliance),\n                  ),\n                  const Divider(height: 1),\n"""
    text = text[:pos] + block + text[pos:]
settings.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# Onboarding: explicit legal acceptance before entering app.
# -----------------------------------------------------------------------------
onboarding = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
text = onboarding.read_text(encoding='utf-8')
if 'bool _legalAccepted = false;' not in text:
    text = text.replace('  bool _isSubmitting = false;', '  bool _isSubmitting = false;\n  bool _legalAccepted = false;', 1)

# Require acceptance in finish and persist versioned acceptance.
old_guard = "    if (_selectedAudience == null || _selectedGoal == null || _isSubmitting) return;"
new_guard = "    if (_selectedAudience == null || _selectedGoal == null || _isSubmitting || !_legalAccepted) return;"
text = text.replace(old_guard, new_guard, 1)
needle = "      await client.rpc('save_my_onboarding_profile', params: {"
if "accept_current_legal_documents" not in text:
    pos = text.find(needle)
    if pos < 0: raise SystemExit('Onboarding profile RPC marker not found')
    # Insert acceptance immediately before profile persistence.
    text = text[:pos] + "      await client.rpc('accept_current_legal_documents', params: {'p_source': 'onboarding'});\n" + text[pos:]

# Pass acceptance state into diagnostic page.
old = "                    isSubmitting: _isSubmitting,\n                    onSelectOption: (index) {"
new = "                    isSubmitting: _isSubmitting,\n                    legalAccepted: _legalAccepted,\n                    onLegalAcceptedChanged: (value) => setState(() => _legalAccepted = value),\n                    onSelectOption: (index) {"
if 'legalAccepted: _legalAccepted' not in text:
    text = text.replace(old, new, 1)

# Add constructor fields.
old = "    required this.isSubmitting,\n    required this.onSelectOption,"
new = "    required this.isSubmitting,\n    required this.legalAccepted,\n    required this.onLegalAcceptedChanged,\n    required this.onSelectOption,"
if 'required this.legalAccepted' not in text:
    text = text.replace(old, new, 1)
old = "  final bool isSubmitting;\n  final ValueChanged<int> onSelectOption;"
new = "  final bool isSubmitting;\n  final bool legalAccepted;\n  final ValueChanged<bool> onLegalAcceptedChanged;\n  final ValueChanged<int> onSelectOption;"
if 'final bool legalAccepted;' not in text:
    text = text.replace(old, new, 1)

# Replace final success block button with legal acceptance UI.
old = "            const SizedBox(height: AppSpacing.xxl),\n            PrimaryButton(label: 'Start Learning', isLoading: isSubmitting, onPressed: onFinish),"
new = r'''            const SizedBox(height: AppSpacing.lg),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              value: legalAccepted,
              onChanged: (value) => onLegalAcceptedChanged(value ?? false),
              title: const Text('I agree to the Terms of Use and acknowledge the Privacy Policy.'),
              subtitle: const Text('Effective 24 August 2026. You can review both documents anytime in Settings → Legal & Data Compliance.'),
            ),
            Row(children: [
              TextButton(
                onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const _OnboardingLegalPreview(title: 'Terms of Use', sections: LegalDocumentScreen.termsSections))),
                child: const Text('View Terms'),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const _OnboardingLegalPreview(title: 'Privacy Policy', sections: LegalDocumentScreen.privacySections))),
                child: const Text('View Privacy'),
              ),
            ]),
            const SizedBox(height: AppSpacing.sm),
            PrimaryButton(label: 'Start Learning', isLoading: isSubmitting, isEnabled: legalAccepted, onPressed: legalAccepted ? onFinish : null),'''
if 'View Terms' not in text:
    text = text.replace(old, new, 1)

# Add imports and lightweight legal preview class.
if "legal_document_screen.dart" not in text:
    text = text.replace("import '../../application/providers/onboarding_providers.dart';", "import '../../application/providers/onboarding_providers.dart';\nimport '../../../settings/presentation/screens/legal_document_screen.dart';", 1)
if 'class _OnboardingLegalPreview' not in text:
    text += r'''

class _OnboardingLegalPreview extends StatelessWidget {
  const _OnboardingLegalPreview({required this.title, required this.sections});
  final String title;
  final List<(String, String)> sections;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: sections.length,
      separatorBuilder: (_, __) => const SizedBox(height: 18),
      itemBuilder: (context, index) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(sections[index].$1, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text(sections[index].$2),
      ]),
    ),
  );
}
'''
onboarding.write_text(text, encoding='utf-8')

print('Full legal compliance applied: terms/privacy consent + IP policy/reporting + data compliance center + privacy/legal requests.')
