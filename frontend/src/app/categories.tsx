import { View, Text, TouchableOpacity } from "react-native";

export default function Categories() {
  const categories = ["Comida", "Emociones", "Escuela"];

  return (
    <View style={{ flex: 1, padding: 20 }}>
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
          key={cat}
          style={{
            backgroundColor: "#ffb703",
            padding: 20,
            borderRadius: 15,
            marginBottom: 15,
          }}
        >
          <Text>{cat}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}