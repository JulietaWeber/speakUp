import { View, Text, TouchableOpacity } from "react-native";
import ConstructionBar from "../components/ConstructionBar";
import { useConstruction } from "../context/ConstructionContext";

export default function Comida() {
  const comidas = ["Milanesa", "Tomate", "Lechuga"];
  const { agregarPalabra } = useConstruction();

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
        Comida
      </Text>

      {comidas.map((comida) => (
        <TouchableOpacity
          key={comida}
          onPress={() => agregarPalabra(comida)}
          style={{
            backgroundColor: "#ffb703",
            padding: 20,
            borderRadius: 15,
            marginBottom: 10,
          }}
        >
          <Text style={{ fontSize: 18 }}>{comida}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}