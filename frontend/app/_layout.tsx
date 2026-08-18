import { Stack } from "expo-router";
import { ConstructionProvider } from "../context/ConstructionContext";

export default function Layout() {
  return (
    <ConstructionProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="register" />
        <Stack.Screen name="login" />
        <Stack.Screen name="categories" />
        <Stack.Screen name="category" />
      </Stack>
    </ConstructionProvider>
  );
}