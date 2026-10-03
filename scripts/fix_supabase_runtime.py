#!/usr/bin/env python3
from pathlib import Path

root = Path("fluentx_admin_secure")

# 1) Remove deleted/foreign Supabase defaults. Runtime values must come from dart-defines.
env_config = root / "lib/core/config/env_config.dart"
env_text = env_config.read_text()
env_text = env_text.replace(
    "defaultValue: 'https://ampcghxowbeocfqqnnvk.supabase.co',",
    "defaultValue: '',",
)
env_text = env_text.replace(
    "defaultValue: 'sb_publishable_TF58ThseSYp-CERYJklnbA_PL_F_rGo',",
    "defaultValue: '',",
)
env_config.write_text(env_text)

# 2) Keep Failure.uiMessage and ensure screens/widgets using it import the extension.
for path in (root / "lib").rglob("*.dart"):
    if path.name == "failures.dart":
        continue
    src = path.read_text()
    if ".uiMessage" in src and "package:fluentx/core/error/failures.dart" not in src and "core/error/failures.dart" not in src:
        path.write_text("import 'package:fluentx/core/error/failures.dart';\n" + src)

# 3) Map low-level connectivity exceptions to NetworkException.
datasource = root / "lib/features/authentication/data/datasources/auth_remote_datasource.dart"
ds = datasource.read_text()
helper = """Exception _mapAuthInfrastructureException(Object error) {
  final message = error.toString();
  final lower = message.toLowerCase();
  if (lower.contains('socketexception') ||
      lower.contains('failed host lookup') ||
      lower.contains('clientexception') ||
      lower.contains('network is unreachable') ||
      lower.contains('connection refused') ||
      lower.contains('connection reset') ||
      lower.contains('connection timed out')) {
    return const NetworkException(
      'Unable to connect to FluentX. Check your internet connection and try again.',
    );
  }
  return ServerException(message);
}

"""
if "_mapAuthInfrastructureException" not in ds:
    ds = ds.replace("abstract class AuthRemoteDataSource {", helper + "abstract class AuthRemoteDataSource {")
ds = ds.replace("throw ServerException(e.toString());", "throw _mapAuthInfrastructureException(e);")
datasource.write_text(ds)

# 4) Convert NetworkException to Failure.network at repository boundary.
repo_file = root / "lib/features/authentication/data/repositories/auth_repository_impl.dart"
rs = repo_file.read_text()
old = """    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
"""
new = """    } on NetworkException catch (e) {
      return left(Failure.network(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
"""
rs = rs.replace(old, new)
repo_file.write_text(rs)

# 5) Never expose server internals in UI; auth/network messages remain useful.
failures = root / "lib/core/error/failures.dart"
fs = failures.read_text()
fs = fs.replace(
    "ServerFailure(:final message) => message,",
    "ServerFailure() => 'Something went wrong. Please try again.',",
)
failures.write_text(fs)

# 6) Regression tests for the screenshot failure mode.
test = root / "test/core/error/failures_test.dart"
test.parent.mkdir(parents=True, exist_ok=True)
test.write_text("""import 'package:flutter_test/flutter_test.dart';
import 'package:fluentx/core/error/failures.dart';

void main() {
  test('network failure exposes only a friendly UI message', () {
    const failure = Failure.network(
      message: 'Unable to connect to FluentX. Check your internet connection and try again.',
    );
    expect(failure.uiMessage, contains('Unable to connect to FluentX'));
    expect(failure.uiMessage, isNot(contains('supabase.co')));
    expect(failure.uiMessage, isNot(contains('SocketException')));
  });

  test('server failure does not leak internal details', () {
    const failure = Failure.server(
      message: "ClientException with SocketException: Failed host lookup: bad.supabase.co",
    );
    expect(failure.uiMessage, 'Something went wrong. Please try again.');
    expect(failure.uiMessage, isNot(contains('supabase.co')));
  });
}
""")

old_ref = "ampcghxowbeocfqqnnvk"
for path in (root / "lib").rglob("*.dart"):
    if old_ref in path.read_text():
        raise SystemExit(f"stale Supabase project ref remains in {path}")

print("Supabase runtime connection + auth error UX fixes applied")
