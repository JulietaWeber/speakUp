import { View, Text, TouchableOpacity } from "react-native";

export default function Categories() {
  const comidas = ["Milanesa", "Tomate", "Lechuga"];

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text style={{ fontSize: 28, marginBottom: 20, fontWeight: "bold" }}>

      </Text>

      {comidas.map((cat) => (
        <TouchableOpacity
          key={cat}
          style={{
            backgroundColor: "#ffb703",
            padding: 20,
            borderRadius: 15,
            marginBottom: 10,
          }}
        >
          <Text style={{ fontSize: 18 }}>{cat}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}