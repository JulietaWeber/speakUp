import { View, Text, TouchableOpacity } from "react-native";
import { router } from "expo-router";
import ConstructionBar from "../components/ConstructionBar";

export default function Categories() {
  const categories: {
    name: string;
    route: "/comida" | "/emociones" | "/escuela";
  }[] = [
    { name: "Comida", route: "/comida" },
    { name: "Emociones", route: "/emociones" },
    { name: "Escuela", route: "/escuela" },
  ];

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <ConstructionBar />

      <Text
        style={{
          fontSize: 28,
          marginBottom: 20,
          fontWeight: "bold",
        }}
      >
        Categorías
      </Text>

      {categories.map((cat) => (
        <TouchableOpacity
          key={cat.name}
          onPress={() => router.push(cat.route)}
          style={{
            backgroundColor: "#ffb703",
            padding: 20,
            borderRadius: 15,
            marginBottom: 15,
          }}
        >
          <Text style={{ fontSize: 18 }}>{cat.name}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}