import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/purchase_remote_datasource.dart';
import '../../data/repositories/purchase_repository_impl.dart';
import '../../domain/entities/subscription_status.dart';
import '../../domain/repositories/purchase_repository.dart';
import '../../domain/usecases/get_premium_packages.dart';
import '../../domain/usecases/purchase_package.dart';
import '../../domain/usecases/restore_purchases.dart';

final purchaseRemoteDataSourceProvider = Provider<PurchaseRemoteDataSource>((ref) {
  return PurchaseRemoteDataSourceImpl();
});

final purchaseRepositoryProvider = Provider<PurchaseRepository>((ref) {
  return PurchaseRepositoryImpl(ref.watch(purchaseRemoteDataSourceProvider));
});

final getPremiumPackagesUseCaseProvider = Provider<GetPremiumPackages>((ref) {
  return GetPremiumPackages(ref.watch(purchaseRepositoryProvider));
});

final purchasePackageUseCaseProvider = Provider<PurchasePackage>((ref) {
  return PurchasePackage(ref.watch(purchaseRepositoryProvider));
});

final restorePurchasesUseCaseProvider = Provider<RestorePurchases>((ref) {
  return RestorePurchases(ref.watch(purchaseRepositoryProvider));
});

/// Live subscription status — drives premium-gated UI everywhere
/// (Profile's crown badge, feature paywalls, etc). RevenueCat is the
/// single source of truth; nothing is cached in Supabase for this.
final subscriptionStatusProvider = StreamProvider<SubscriptionStatus>((ref) {
  return ref.watch(purchaseRepositoryProvider).subscriptionStatusChanges;
});

final premiumPackagesProvider = FutureProvider.autoDispose<List<PremiumPackage>>((ref) async {
  final result = await ref.watch(getPremiumPackagesUseCaseProvider).call();
  return result.match((failure) => throw failure, (packages) => packages);
});

class PurchaseController extends AutoDisposeAsyncNotifier<void> {
  @override
  Future<void> build() async {}

  Future<void> buy(String packageIdentifier) async {
    state = const AsyncLoading();
    final result = await ref.read(purchasePackageUseCaseProvider).call(packageIdentifier);
    state = result.match(
      (failure) => AsyncError<void>(failure, StackTrace.current),
      (_) => const AsyncData(null),
    );
  }

  Future<void> restore() async {
    state = const AsyncLoading();
    final result = await ref.read(restorePurchasesUseCaseProvider).call();
    state = result.match(
      (failure) => AsyncError<void>(failure, StackTrace.current),
      (_) => const AsyncData(null),
    );
  }
}

final purchaseControllerProvider = AutoDisposeAsyncNotifierProvider<PurchaseController, void>(
  PurchaseController.new,
);
