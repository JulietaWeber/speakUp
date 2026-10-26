
import { Stack } from "expo-router";
import { ConstructionProvider } from "../context/ConstructionContext";
import { AccessibilityProvider } from "../context/AccessibilityContext";

export default function Layout() {
  return (
    <AccessibilityProvider>
      <ConstructionProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="register" />
          <Stack.Screen name="login" />
          <Stack.Screen name="categories" />
          <Stack.Screen name="category" />
        </Stack>
      </ConstructionProvider>
    </AccessibilityProvider>
  );
}
