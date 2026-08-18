import { useEffect, useState } from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ConstructionBar from "../components/ConstructionBar";
import { obtenerCategorias } from "../services/api";

export default function Categories() {
  const [categories, setCategories] = useState<any[]>([]);

  useEffect(() => {
    const cargarCategorias = async () => {
      try {
        const token = await AsyncStorage.getItem("token");

        if (!token) {
          console.log("No hay token");
          return;
        }

        const data = await obtenerCategorias(token);

        setCategories(data);
      } catch (error) {
        console.error("Error cargando categorías:", error);
      }
    };

    cargarCategorias();
  }, []);

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
          key={cat.id_categorias}
          onPress={() =>
            router.push({
              pathname: "/category",
              params: {
                id: cat.id_categorias.toString(),
                nombre: cat.nombre,
                color: cat.color,
              },
            })
          }
          style={{
            backgroundColor: "#ffb703",
            padding: 20,
            borderRadius: 15,
            marginBottom: 15,
          }}
        >
          <Text style={{ fontSize: 18 }}>{cat.nombre}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}