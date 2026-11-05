import { useState } from "react";
import { Button, StyleSheet, Text, View } from "react-native";

export default function HomeScreen() {
  const [message, setMessage] = useState("Chưa kiểm tra kết nối.");
  const [loading, setLoading] = useState(false);

  async function checkBackend() {
    setLoading(true);
    setMessage("Đang kết nối…");

    try {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL;

      if (!apiUrl) {
        throw new Error("Thiếu EXPO_PUBLIC_API_URL trong mobile/.env");
      }

      const response = await fetch(`${apiUrl}/health`);

      if (!response.ok) {
        throw new Error(`Backend trả lỗi HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.status !== "ok") {
        throw new Error("Backend trả kết quả khác dự kiến.");
      }

      setMessage("Kết nối backend thành công! Status: ok");
    } catch (error) {
      const detail =
        error instanceof Error ? error.message : "Lỗi chưa xác định.";

      setMessage(`Chưa kết nối được. ${detail}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Solo Travelling Assistant</Text>

      <Text style={styles.message}>{message}</Text>

      <Button
        title={loading ? "Đang kiểm tra…" : "Kiểm tra backend"}
        onPress={checkBackend}
        disabled={loading}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    padding: 24,
    backgroundColor: "#f4f7ef",
  },
  title: {
    fontSize: 26,
    fontWeight: "bold",
    color: "#254d32",
    marginBottom: 24,
  },
  message: {
    fontSize: 17,
    marginBottom: 24,
  },
});