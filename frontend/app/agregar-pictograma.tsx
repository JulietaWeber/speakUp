import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
} from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { crearPictogramaPersonalizado } from "../services/api";

export default function AgregarPictograma() {
  const { idCategoria } = useLocalSearchParams();

  const [nombre, setNombre] = useState("");

  const crearPictograma = async () => {
    const token = await AsyncStorage.getItem("token");

    if (!token) {
      console.log("No hay token");
      return;
    }

    await crearPictogramaPersonalizado(
      Number(idCategoria),
      nombre,
      token
    );

    router.back();
  };

  return (
    <View
      style={{
        flex: 1,
        padding: 20,
      }}
    >
      <Text
        style={{
          fontSize: 28,
          fontWeight: "bold",
          marginBottom: 20,
        }}
      >
        Agregar pictograma
      </Text>

      <Text
        style={{
          fontSize: 18,
          marginBottom: 10,
        }}
      >
        Nombre del pictograma
      </Text>

      <TextInput
        placeholder="Ej: Mamá"
        value={nombre}
        onChangeText={setNombre}
        style={{
          backgroundColor: "#CFE6F1",
          padding: 18,
          borderRadius: 16,
          fontSize: 18,
        }}
      />

      <TouchableOpacity
        onPress={crearPictograma}
        style={{
          backgroundColor: "#356071",
          padding: 18,
          borderRadius: 16,
          alignItems: "center",
          marginTop: 20,
        }}
      >
        <Text
          style={{
            color: "white",
            fontSize: 18,
            fontWeight: "bold",
          }}
        >
          Crear pictograma
        </Text>
      </TouchableOpacity>
    </View>
  );
}