class DmsApiPaths {
  DmsApiPaths._();

  static const String uploadIntent = '/dms/upload-intent';
  static const String confirmUpload = '/dms/confirm-upload';
  static String asset(String id) => '/dms/assets/$id';
  static String assetContext(String id) => '/dms/assets/$id/context';
  static const String assets = '/dms/assets';
}