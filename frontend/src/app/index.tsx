import { View, Text, TouchableOpacity } from "react-native";
import { router } from "expo-router";

export default function Home() {
  return (
    <View
      style={{
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
        padding: 20,
      }}
    >
      <Text
        style={{
          fontSize: 32,
          marginBottom: 30,
          fontWeight: "bold",
        }}
      >
        Speak Up
      </Text>

      <TouchableOpacity
        onPress={() => router.push("/categories")}
        style={{
          backgroundColor: "#8ecae6",
          padding: 20,
          borderRadius: 15,
        }}
      >
        <Text>Entrar</Text>
      </TouchableOpacity>
    </View>
  );
}