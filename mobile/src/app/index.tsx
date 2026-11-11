
import { useEffect, useState } from "react";
import { router } from "expo-router";
import { Text, View } from "react-native";

import { Action, Page, styles } from "@/features/plan/ui";
import {
  me,
  token,
  logout,
  clearToken,
} from "@/features/plan/api";
import { usePlan } from "@/features/plan/state";

export default function Home() {
  const [info, setInfo] = useState("Đang kiểm tra phiên…");
  const [signed, setSigned] = useState(false);
  const [busy, setBusy] = useState(false);
  const [checking, setChecking] = useState(false);

  const { clearSession, setAccount } = usePlan();

  useEffect(() => {
    let active = true;

    async function checkSession() {
      try {
        const savedToken = await token();

        if (!active) return;

        if (!savedToken) {
          router.replace("/login");
          return;
        }

        await me();

        if (!active) return;

        setSigned(true);
        setAccount("Đã đăng nhập");
        setInfo("Đã đăng nhập");
        router.replace("/plan");
      } catch (error) {
        if (!active) return;

        if ((error as { status?: number }).status === 401) {
          await clearToken();
          await clearSession();

          if (active) router.replace("/login");
        } else {
          setInfo("Không có kết nối. Phiên của bạn vẫn được giữ.");
          router.replace("/plan");
        }
      }
    }

    checkSession();

    return () => {
      active = false;
    };
  }, []);

  async function checkBackend() {
    setChecking(true);
    setInfo("Đang kiểm tra kết nối…");

    try {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL;

      if (!apiUrl) {
        throw new Error("Thiếu EXPO_PUBLIC_API_URL");
      }

      const response = await fetch(
        `${apiUrl.replace(/\/$/, "")}/health`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.status !== "ok") {
        throw new Error("Backend trả kết quả không hợp lệ.");
      }

      setInfo("Kết nối backend thành công!");
    } catch (error) {
      setInfo(
        error instanceof Error
          ? `Không kết nối được: ${error.message}`
          : "Không kết nối được backend."
      );
    } finally {
      setChecking(false);
    }
  }

  async function signOut() {
    setBusy(true);
    setInfo("");

    try {
      await logout();
      await clearSession();
      setSigned(false);
      router.replace("/login");
    } catch (error) {
      setInfo(
        error instanceof Error
          ? error.message
          : "Không thể đăng xuất."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page>
      <View style={styles.card}>
        <Text style={styles.title}>
          Solo Travelling Assistant
        </Text>

        <Text style={styles.muted}>{info}</Text>

        <Action
          title="Lên kế hoạch chuyến đi"
          onPress={() => router.push("/plan")}
        />

        <Action
          title="Xem lịch đã lưu"
          secondary
          onPress={() => router.push("/current")}
        />

        <Action
          title="Điều chỉnh lịch trình"
          secondary
          onPress={() => router.push("/adapt")}
        />

        <Action
          title={
            checking
              ? "Đang kiểm tra…"
              : "Kiểm tra kết nối backend"
          }
          secondary
          disabled={checking}
          onPress={checkBackend}
        />

        {signed ? (
          <Action
            title={busy ? "Đang đăng xuất…" : "Đăng xuất"}
            disabled={busy}
            secondary
            onPress={signOut}
          />
        ) : (
          <Action
            title="Đăng nhập"
            onPress={() => router.push("/login")}
          />
        )}
      </View>
    </Page>
  );
}
