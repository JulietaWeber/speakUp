import { View, Text, TouchableOpacity } from "react-native";
import ConstructionBar from "../components/ConstructionBar";
import { useConstruction } from "../context/ConstructionContext";

export default function Emociones() {
  const emociones = ["Triste", "Feliz", "Enojado"];
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
        Emociones
      </Text>

      {emociones.map((emocion) => (
        <TouchableOpacity
          key={emocion}
          onPress={() => agregarPalabra(emocion)}
          style={{
            backgroundColor: "#ffb703",
            padding: 20,
            borderRadius: 15,
            marginBottom: 10,
          }}
        >
          <Text style={{ fontSize: 18 }}>{emocion}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}