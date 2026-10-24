from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "fluentx_admin_secure")
path=root/"lib/features/admin/presentation/screens/admin_console_screen.dart"
s=path.read_text(encoding="utf8")
needle="if (factors.totp.isNotEmpty) {"
if needle not in s:raise SystemExit("MFA factor guard missing")
s=s.replace(needle,"if (factors.totp.where((f) => f.status.toString().split('.').last == 'verified').isNotEmpty) {",1)
# Pending factors must not block fresh setup. Recovery goes through Supabase Auth.
marker="      } else {\n        final enrollment = await _client.auth.mfa.enroll("
replacement="""      } else {
        // An interrupted MFA setup may leave unverified factors in Supabase.
        // Remove only this signed-in user's unverified factors so enrollment
        // can start again; verified factors are never removed.
        for(final factor in factors.all.where((f)=>f.factorType == FactorType.totp && f.status.toString().split('.').last == 'unverified')){
          await _client.auth.mfa.unenroll(factor.id);
        }
        final enrollment = await _client.auth.mfa.enroll("""
if marker not in s:raise SystemExit("MFA enrollment marker missing")
s=s.replace(marker,replacement,1)
path.write_text(s,encoding="utf8")
print("MFA_UNVERIFIED_RECOVERY_PATCH_APPLIED")
