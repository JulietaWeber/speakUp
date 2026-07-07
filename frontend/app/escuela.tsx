import { View, Text, TouchableOpacity } from "react-native";
import ConstructionBar from "../components/ConstructionBar";
import { useConstruction } from "../context/ConstructionContext";

export default function Escuela() {
  const palabras = ["Profesor", "Aula", "Patio"];
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
        Escuela
      </Text>

      {palabras.map((palabra) => (
        <TouchableOpacity
          key={palabra}
          onPress={() => agregarPalabra(palabra)}
          style={{
            backgroundColor: "#ffb703",
            padding: 20,
            borderRadius: 15,
            marginBottom: 10,
          }}
        >
          <Text style={{ fontSize: 18 }}>{palabra}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}