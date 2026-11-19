module.exports = ({ config }) => {
  if (process.env.EAS_BUILD_PROFILE === 'demo') {
    const raw = process.env.EXPO_PUBLIC_API_URL;
    if (!raw || !URL.canParse(raw) || new URL(raw).protocol !== 'https:') {
      throw new Error('Cấu hình EXPO_PUBLIC_API_URL bằng địa chỉ HTTPS của backend trước khi tạo APK.');
    }
  }
  return config;
};
